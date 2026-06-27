"""Stage 3 — Profile. Per-column statistics + candidate keys + value-sets + data-shape signals.

Reads the ingested snapshot tables (``snapshots/<v>/tables/*.parquet``) and writes a
real, deterministic profile that the AUTO-DRAFT MAPPING stage (§8 stage 5) and the
SINGLE QUESTION ROUND (§9) consume. The profile answers the first review lens
("shape", §15.3) WITHOUT any LLM or network call.

Per table (``snapshots/<v>/profile/<table>.json``):
  - per column: non-null count/%, distinct count, blank/whitespace count, inferred
    dtype, min/max for numerics & dates, and a capped sample of values that is REDACTED
    (short stable hash) for any column the profiler flags with a PII signal
    (name/phone/address/etc.) and kept verbatim only for non-PII columns;
  - candidate keys: single + composite column sets that are (near-)unique across rows,
    each with a uniqueness ratio — so intake can confirm the source_key (§5.1);
  - value-set candidates: low-cardinality string columns (distinct ≤ a threshold) with
    a value→frequency map — feeds value_sets drafting + the question round (§9.2);
  - data-shape signals: columns that look like joint-names, split-name parts, dates,
    split Y/M/D date families, phones, money, addresses — each tagged so the
    knowledge INDEX triggers (§11.3) can route topic files to the right stage.

Plus a top-level ``profile/summary.json`` aggregating signals across all tables.

This module is GENERAL: it carries NO client column names — every heuristic keys off
the column's *values and name shape* at run time, never a hardcoded client field.

Design references: SPEC §8 stage 3, §9 (question round inputs), §11.3 (trigger tags),
§15.3 (the "shape" lens).
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from itertools import combinations
from pathlib import Path
from typing import Any, Optional

import pandas as pd

from identity import KEY_STATUS_COL, ROW_HASH_COL, SOURCE_ID_COL

VERSION = "1.0.0"

# Identity/bookkeeping columns ingest adds — never profiled as source data.
_RESERVED_COLS = {SOURCE_ID_COL, ROW_HASH_COL, KEY_STATUS_COL}

# A string column is a value-set candidate when its distinct count is small both in
# absolute terms and relative to the row count (so a 3-value "STATUS" column flags but a
# unique-per-row id column does not). Tunable; deterministic.
_VALUE_SET_MAX_DISTINCT = 50
_VALUE_SET_MAX_RATIO = 0.20

# How many sample values / value-set entries we serialize. We CAP and never dump entire
# columns (SPEC §8 "PII-aware — cap and don't dump entire columns"); on top of the cap,
# columns flagged with a PII signal have their sample values REDACTED (see below).
_SAMPLE_CAP = 10
_VALUE_FREQ_CAP = 50

# Signals that mark a column as carrying PII whose VALUES must never be emitted verbatim
# into committed profile artifacts. Sample values for such columns are replaced with a
# short stable hash so the count/cardinality structure is still visible without the PII.
_PII_SIGNALS = {"name", "joint_name", "reversed_name", "phone", "address"}
_REDACT_HASH_LEN = 10


def _redact_sample_value(value: str) -> str:
    """Replace a PII value with a short, stable, non-reversible token.

    Equal inputs map to equal tokens (so duplicate structure stays visible), but the raw
    value cannot be recovered. Used for sample/value-set entries of PII-flagged columns.
    """
    digest = hashlib.sha256(str(value).encode("utf-8")).hexdigest()[:_REDACT_HASH_LEN]
    return f"[redacted:{digest}]"


def _has_pii_signal(signals: list[str]) -> bool:
    return bool(set(signals) & _PII_SIGNALS)

# Composite-key search: cap the combination size so the search stays cheap on wide tables.
_MAX_COMPOSITE_KEY_COLS = 5
_CANDIDATE_KEY_MIN_RATIO = 0.98  # report keys that are at least near-unique

# Combinatorial-blowup guards (M6). Without these the composite search enumerates
# combinations(all_cols, 2..5) — on a wide table (~40 cols) with no early low-arity key
# that is ~10^5-10^6 full-table groupbys (a DoS-grade blowup). We:
#   (1) restrict composite candidates to the top-K highest-cardinality columns — the only
#       columns that can plausibly contribute to a (near-)unique key (K chosen so the
#       per-size combination count stays bounded: C(15,5)=3003, well inside the budget,
#       while still comfortably covering real natural keys which are short);
#   (2) skip any combo that CANNOT reach near-uniqueness: a groupby over a column subset
#       has at most product(distinct_i) groups, so if that product is below the near-unique
#       row threshold the combo can never be (near-)unique — skip it without a scan;
#   (3) cap the TOTAL number of combos evaluated with a hard budget and record TRUNCATION
#       when the cap is hit, so an incomplete search is never silently reported as complete.
_COMPOSITE_KEY_TOP_K = 15
# Budget < the worst-case top-K enumeration (C(15,2..5) = 4928) so it is a genuine
# binding guard: a wide table with many high-cardinality-but-non-keying columns trips it
# and the search is flagged TRUNCATED rather than silently treated as exhaustive. Natural
# keys are short and surface well before this cap, so real keys are never missed.
_COMPOSITE_KEY_BUDGET = 2500

# Module-level record of whether the most recent candidate_keys() composite search hit its
# budget (and was therefore truncated). Read via last_keysearch_truncated().
_LAST_KEYSEARCH_TRUNCATED = False


def last_keysearch_truncated() -> bool:
    """True iff the most recent candidate_keys() composite search hit its combo budget.

    A truncated search may have missed a larger composite unique key; callers/artifacts
    should surface this so the search is never silently treated as exhaustive.
    """
    return _LAST_KEYSEARCH_TRUNCATED


# --------------------------------------------------------------------------- #
# Shape heuristics (value- and name-driven; no client column names)            #
# --------------------------------------------------------------------------- #
_JOINT_NAME_RE = re.compile(r"\s+(?:&|\band\b)\s+", re.IGNORECASE)
_PHONE_RE = re.compile(r"^[\s().+-]*\d[\d\s().+-]{6,}$")
_MONEY_RE = re.compile(r"^\s*[-(]?\s*\$?\s*\d[\d,]*(?:\.\d{1,2})?\s*\)?\s*$")
_DATE_RE = re.compile(
    r"^\s*\d{1,4}[-/.]\d{1,2}[-/.]\d{1,4}\s*$"  # 1/2/2003, 2003-01-02, 02.01.2003
    r"|^\s*\d{1,2}[-/. ][A-Za-z]{3,9}[-/. ]\d{2,4}\s*$"  # 2 Jan 2003
)
_TWO_DIGIT_YEAR_RE = re.compile(r"[-/.]\d{2}\s*$")
_ADDRESS_RE = re.compile(
    r"\b\d+\s+\S+.*\b(st|street|ave|avenue|rd|road|dr|drive|ln|lane|blvd|ct|court|"
    r"way|pl|place|hwy|highway|cir|circle|ste|suite|apt)\b",
    re.IGNORECASE,
)

# Name-shape hints by COLUMN-NAME token (generic English tokens, not client fields).
_NAME_TOKENS = {"name", "sur", "surname", "first", "last", "middle", "fname", "lname", "mname", "deceased", "person"}
_SPLIT_DATE_PARTS = {
    "year": {"year", "yr", "yyyy"},
    "month": {"month", "mon", "mm"},
    "day": {"day", "dd"},
}
_DATE_TOKENS = {"date", "dob", "dod", "doi", "born", "birth", "death", "died", "buried", "interred"}
_COORD_TOKENS = {"latitude", "longitude", "lat", "lng", "lon", "geo", "coordinate", "coord"}


def _tokens(name: str) -> set[str]:
    return set(re.split(r"[^a-z0-9]+", name.lower())) - {""}


def _frac_match(values: list[str], pattern: re.Pattern) -> float:
    if not values:
        return 0.0
    hits = sum(1 for v in values if pattern.search(v))
    return hits / len(values)


def _looks_numeric(value: str) -> bool:
    try:
        float(value.replace(",", "").strip())
        return True
    except (ValueError, AttributeError):
        return False


def _infer_dtype(series: pd.Series, non_null: list[str]) -> str:
    """Infer a coarse logical dtype from the (string) cell values."""
    if not non_null:
        return "empty"
    n = len(non_null)

    def _int_ok(v: str) -> bool:
        v = v.strip().lstrip("-")
        return v.isdigit()

    def _float_ok(v: str) -> bool:
        try:
            float(v.replace(",", ""))
            return True
        except ValueError:
            return False

    if all(_int_ok(v) for v in non_null):
        return "integer"
    # Money requires a money MARKER ($, comma-grouping, decimal, or parens-negative) on a
    # strong majority — a column of bare integers is an integer/id, never money.
    money_marker = re.compile(r"[$,]|\.\d{1,2}\b|^\s*\(.*\)\s*$")
    money_hits = sum(1 for v in non_null if _MONEY_RE.match(v) and money_marker.search(v))
    if money_hits / n >= 0.9:
        return "money"
    if all(_float_ok(v) for v in non_null):
        return "number"
    if _frac_match(non_null, _DATE_RE) >= 0.9:
        return "date"
    if {v.lower() for v in non_null} <= {"true", "false", "yes", "no", "y", "n", "1", "0", "t", "f"}:
        return "boolean"
    return "string"


def _numeric_min_max(non_null: list[str]) -> Optional[dict[str, float]]:
    nums: list[float] = []
    for v in non_null:
        try:
            nums.append(float(v.replace(",", "").replace("$", "").strip("()")))
        except ValueError:
            return None
    if not nums:
        return None
    return {"min": min(nums), "max": max(nums)}


def _date_min_max(non_null: list[str]) -> Optional[dict[str, str]]:
    parsed: list[date] = []
    for v in non_null:
        d = _try_parse_date(v)
        if d is None:
            return None
        parsed.append(d)
    if not parsed:
        return None
    return {"min": min(parsed).isoformat(), "max": max(parsed).isoformat()}


def _try_parse_date(value: str) -> Optional[date]:
    value = value.strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%d/%m/%Y", "%Y/%m/%d", "%m-%d-%Y", "%d-%b-%Y", "%d %b %Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


# --------------------------------------------------------------------------- #
# Column profiling                                                             #
# --------------------------------------------------------------------------- #
@dataclass(slots=True)
class ColumnProfile:
    name: str
    count: int
    non_null: int
    non_null_pct: float
    blank: int
    distinct: int
    distinct_ratio: float
    dtype: str
    sample: list[str]
    min: Any = None
    max: Any = None
    signals: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        out = {
            "count": self.count,
            "non_null": self.non_null,
            "non_null_pct": round(self.non_null_pct, 4),
            "blank_or_whitespace": self.blank,
            "distinct": self.distinct,
            "distinct_ratio": round(self.distinct_ratio, 4),
            "dtype": self.dtype,
            "sample": self.sample,
            "signals": self.signals,
        }
        if self.min is not None or self.max is not None:
            out["min"] = self.min
            out["max"] = self.max
        return out


def _string_cells(series: pd.Series) -> tuple[list[str], int, int]:
    """Return (non_null_non_blank_values, null_count, blank_or_whitespace_count)."""
    non_null: list[str] = []
    nulls = 0
    blanks = 0
    for v in series:
        if v is None or (isinstance(v, float) and pd.isna(v)):
            nulls += 1
            continue
        try:
            if pd.isna(v):
                nulls += 1
                continue
        except (TypeError, ValueError):
            pass
        s = str(v)
        if s.strip() == "":
            blanks += 1
            continue
        non_null.append(s)
    return non_null, nulls, blanks


def _column_signals(name: str, dtype: str, non_null: list[str]) -> list[str]:
    """Tag a column with data-shape signals → knowledge/INDEX trigger tags (§11.3)."""
    signals: list[str] = []
    name_toks = _tokens(name)

    if dtype == "money":
        signals.append("money")
    if (name_toks & _COORD_TOKENS) and dtype in ("number", "integer", "string"):
        # A lat/long column is a derived measurement — a poor natural key even if unique.
        if all(_looks_numeric(v) for v in non_null[:50]):
            signals.append("coordinate")
    if dtype == "date" or (name_toks & _DATE_TOKENS):
        if dtype == "date":
            signals.append("date")
        if _frac_match(non_null, _TWO_DIGIT_YEAR_RE) >= 0.1:
            signals.append("two_digit_year")
    if dtype != "money" and _frac_match(non_null, _PHONE_RE) >= 0.8 and dtype not in ("integer", "number"):
        # avoid mislabelling plain integer ids as phones
        if any(len(re.sub(r"\D", "", v)) >= 7 for v in non_null[:50]):
            signals.append("phone")
    if _frac_match(non_null, _ADDRESS_RE) >= 0.3:
        signals.append("address")

    # Name shapes: joint-name ("&"/" and "), or a name-bearing column.
    if name_toks & _NAME_TOKENS or _frac_match(non_null, _JOINT_NAME_RE) >= 0.1:
        if _frac_match(non_null, _JOINT_NAME_RE) >= 0.05:
            signals.append("joint_name")
        # A "Last, First" reversed-name shape.
        if name_toks & _NAME_TOKENS:
            signals.append("name")
            if sum(1 for v in non_null[:100] if "," in v) / max(1, len(non_null[:100])) >= 0.3:
                signals.append("reversed_name")

    # Split Y/M/D date family — flagged on the part columns (year/month/day).
    for part, toks in _SPLIT_DATE_PARTS.items():
        if name_toks & toks and (name_toks & _DATE_TOKENS or part in name_toks):
            signals.append(f"split_date_{part}")

    return signals


def profile_column(series: pd.Series, name: str, row_count: int) -> ColumnProfile:
    non_null, nulls, blanks = _string_cells(series)
    distinct_vals = sorted(set(non_null))
    distinct = len(distinct_vals)
    dtype = _infer_dtype(series, non_null)

    cp = ColumnProfile(
        name=name,
        count=row_count,
        non_null=len(non_null),
        non_null_pct=(len(non_null) / row_count) if row_count else 0.0,
        blank=blanks,
        distinct=distinct,
        distinct_ratio=(distinct / row_count) if row_count else 0.0,
        dtype=dtype,
        sample=distinct_vals[:_SAMPLE_CAP],
    )

    if dtype in ("integer", "number", "money"):
        mm = _numeric_min_max(non_null)
        if mm is not None:
            cp.min, cp.max = mm["min"], mm["max"]
    elif dtype == "date":
        mm = _date_min_max(non_null)
        if mm is not None:
            cp.min, cp.max = mm["min"], mm["max"]

    cp.signals = _column_signals(name, dtype, non_null)
    if _has_pii_signal(cp.signals):
        cp.sample = [_redact_sample_value(v) for v in cp.sample]
    return cp


# --------------------------------------------------------------------------- #
# Candidate keys + value-sets                                                  #
# --------------------------------------------------------------------------- #
def _is_unique(df: pd.DataFrame, cols: list[str]) -> tuple[bool, float]:
    """Uniqueness over a column subset → (is_fully_unique, uniqueness_ratio)."""
    n = len(df)
    if n == 0:
        return False, 0.0
    distinct = df.groupby(list(cols), dropna=False).ngroups
    ratio = distinct / n
    return distinct == n, ratio


# Signals that make a column a POOR business key (derived coords, formatted values),
# even when it happens to be unique. A natural source_key is a stable identifier, not a
# measurement — so these are penalized in the key-quality ranking.
_POOR_KEY_SIGNALS = {"phone", "money", "address", "joint_name", "date", "two_digit_year", "coordinate"}


def _key_quality(df_n: int, columns: list[str], profiles: dict[str, ColumnProfile]) -> float:
    """Heuristic 0..1 quality of a unique key: prefer complete, identifier-like columns.

    A good source_key is short, fully populated, and made of stable identifiers — not of
    derived/measured fields (lat/long, formatted phones/money) that merely happen to be
    unique. This lets the natural business key surface ahead of an accidental one.
    """
    completeness = sum(profiles[c].non_null_pct for c in columns) / len(columns)
    poor = sum(1 for c in columns if set(profiles[c].signals) & _POOR_KEY_SIGNALS)
    poor_penalty = poor / len(columns)
    brevity = 1.0 / len(columns)
    # Weighted: completeness dominates (a key with nulls is fragile), then non-poor cols.
    return round(0.55 * completeness + 0.30 * (1 - poor_penalty) + 0.15 * brevity, 5)


def candidate_keys(df: pd.DataFrame, profiles: dict[str, ColumnProfile]) -> list[dict[str, Any]]:
    """Single + composite key candidates, each with a uniqueness ratio + a quality score.

    Single columns are tried first; then MINIMAL unique composites across sizes (a
    composite is reported only when no already-found unique key is a subset of it). All
    minimal unique keys at the smallest unique size are reported (not just the first), so
    the natural business key is surfaced alongside any accidental one. Keys are ranked by
    quality (completeness + identifier-likeness + brevity) so the natural source_key —
    the column(s) a human would confirm — leads.
    """
    n = len(df)
    if n == 0:
        return []
    cols = [c for c in df.columns if c not in _RESERVED_COLS]
    out: list[dict[str, Any]] = []
    seen_unique_sets: list[set[str]] = []

    def _record(columns: list[str], unique: bool, ratio: float) -> None:
        out.append({
            "columns": columns,
            "unique": unique,
            "uniqueness_ratio": round(ratio, 5),
            "quality": _key_quality(n, columns, profiles),
        })

    # Single-column candidates (near-unique and up).
    for c in cols:
        unique, ratio = _is_unique(df, [c])
        if ratio >= _CANDIDATE_KEY_MIN_RATIO:
            _record([c], unique, ratio)
            if unique:
                seen_unique_sets.append({c})

    # Composite candidates, built from the TOP-K most-distinct columns (M6): only the
    # highest-cardinality columns can plausibly contribute to a (near-)unique key, and
    # restricting to top-K bounds the per-size combination count on wide tables.
    ranked = sorted(cols, key=lambda c: profiles[c].distinct, reverse=True)[:_COMPOSITE_KEY_TOP_K]

    # Near-unique row threshold: a combo whose product of per-column distinct counts is
    # below this can never reach near-uniqueness, so it is skipped without a table scan.
    near_unique_floor = _CANDIDATE_KEY_MIN_RATIO * n

    global _LAST_KEYSEARCH_TRUNCATED
    _LAST_KEYSEARCH_TRUNCATED = False
    budget = _COMPOSITE_KEY_BUDGET
    evaluated = 0

    first_unique_size: Optional[int] = None
    for size in range(2, min(_MAX_COMPOSITE_KEY_COLS, len(ranked)) + 1):
        # Stop deepening once we have minimal unique keys AND went one size past them:
        # larger composites can only be supersets (non-minimal) of what we found.
        if first_unique_size is not None and size > first_unique_size:
            break
        if evaluated >= budget:
            _LAST_KEYSEARCH_TRUNCATED = True
            break
        for combo in combinations(ranked, size):
            combo_set = set(combo)
            if any(u <= combo_set for u in seen_unique_sets):
                continue  # non-minimal: a known unique key is already a subset
            # Distinct-product upper bound: skip combos that mathematically cannot key.
            distinct_product = 1
            for c in combo:
                distinct_product *= max(1, profiles[c].distinct)
                if distinct_product >= near_unique_floor:
                    break
            if distinct_product < near_unique_floor:
                continue  # can never reach near-uniqueness — no scan needed
            if evaluated >= budget:
                _LAST_KEYSEARCH_TRUNCATED = True
                break
            evaluated += 1
            unique, ratio = _is_unique(df, list(combo))
            if unique:
                _record(list(combo), True, ratio)
                seen_unique_sets.append(combo_set)
                if first_unique_size is None:
                    first_unique_size = size

    # Natural-key completion: an accidental unique key (lat/long + grave) is often a worse
    # source_key than a near-unique BUSINESS grouping (e.g. section+row+grave at 0.999)
    # completed to uniqueness with identifier-like columns (name parts). The smallest
    # unique key is not always the natural one, so we explicitly surface completed
    # business keys too. We seed from high-quality near-unique composites of non-poor,
    # well-populated columns and greedily add the best identifier-like columns until unique.
    # The completion search shares the SAME combo budget (its seeds count against what the
    # composite search already spent), so total scans stay bounded on wide tables.
    out.extend(_completed_business_keys(df, profiles, cols, seen_unique_sets, budget - evaluated))

    out.sort(key=lambda o: (not o["unique"], -o["quality"], len(o["columns"]), -o["uniqueness_ratio"]))
    # De-duplicate by column SET (a key may be found by two passes).
    deduped: list[dict[str, Any]] = []
    seen: list[frozenset] = []
    for o in out:
        fs = frozenset(o["columns"])
        if fs in seen:
            continue
        seen.append(fs)
        deduped.append(o)
    return deduped


def _is_identifier_like(cp: ColumnProfile) -> bool:
    """A column usable in a natural key: not a derived measure (coords/phone/money/date).

    Name columns count even when sparsely populated — they are the canonical
    disambiguator for otherwise-equal locator rows (two people in one grave). A derived
    measurement (lat/long/phone/money/date) does not, even when unique.
    """
    poor = set(cp.signals) & _POOR_KEY_SIGNALS
    if poor:
        return False
    if "name" in cp.signals:
        return True
    return cp.non_null_pct >= 0.95


def _completed_business_keys(
    df: pd.DataFrame,
    profiles: dict[str, ColumnProfile],
    cols: list[str],
    already_unique: list[set[str]],
    seed_budget: int = _COMPOSITE_KEY_BUDGET,
) -> list[dict[str, Any]]:
    """Surface near-unique BUSINESS groupings completed to uniqueness with id-like columns.

    Seeds from the best near-unique composite of identifier-like columns (e.g. a
    section/row/grave locator at ~0.999 uniqueness) and greedily appends the
    highest-quality identifier-like columns (name parts, etc.) until the key is unique —
    the key a human would actually confirm. Returns at most a couple completions so the
    natural key is visible without flooding the list.
    """
    n = len(df)
    id_cols = [c for c in cols if _is_identifier_like(profiles[c])]
    if not id_cols:
        return []

    # Bound the seed search on wide tables (M6): restrict to the top-K id-like columns by
    # cardinality (a natural locator's parts are still reasonably distinct) and stop once a
    # shared seed budget is spent — the same combinatorial guard as the main search.
    id_cols = sorted(id_cols, key=lambda c: profiles[c].distinct, reverse=True)[:_COMPOSITE_KEY_TOP_K]

    # Find the best near-unique (but not unique) seed: a small group of id-like, low-ish
    # cardinality columns that nearly identifies a row (a natural locator).
    seeds: list[tuple[float, list[str]]] = []
    seed_evaluated = 0
    for size in (2, 3):
        if seed_evaluated >= seed_budget:
            global _LAST_KEYSEARCH_TRUNCATED
            _LAST_KEYSEARCH_TRUNCATED = True
            break
        for combo in combinations(id_cols, size):
            if seed_evaluated >= seed_budget:
                _LAST_KEYSEARCH_TRUNCATED = True
                break
            seed_evaluated += 1
            unique, ratio = _is_unique(df, list(combo))
            if 0.90 <= ratio < 1.0:
                seeds.append((ratio, list(combo)))
    if not seeds:
        return []
    seeds.sort(key=lambda s: -s[0])

    out: list[dict[str, Any]] = []
    for _ratio, seed in seeds[:2]:
        chosen = list(seed)
        chosen_set = set(chosen)
        # Greedily add the id-like column that most increases distinctness until unique.
        extras = [c for c in id_cols if c not in chosen_set]
        # Prefer name columns, surname before given name (the conventional name key),
        # then by cardinality, for disambiguation.
        def _name_rank(c: str) -> tuple:
            toks = _tokens(c)
            is_name = "name" in profiles[c].signals
            is_surname = bool(toks & {"sur", "surname", "last", "lname"})
            return (not is_name, not is_surname, -profiles[c].distinct)
        extras.sort(key=_name_rank)
        prev_ratio = _is_unique(df, chosen)[1]
        for c in extras:
            unique, ratio = _is_unique(df, chosen + [c])
            if ratio > prev_ratio:
                chosen.append(c)
                prev_ratio = ratio
            if _is_unique(df, chosen)[0]:
                break
        unique, ratio = _is_unique(df, chosen)
        # A completed BUSINESS key is intentionally surfaced even when it is a superset of
        # an accidental minimal key (e.g. row+first_name) — it is the key a human confirms.
        # Only skip it if it IS one of the already-found keys (exact set).
        if unique and set(chosen) not in [set(u) for u in already_unique]:
            out.append({
                "columns": chosen,
                "unique": True,
                "uniqueness_ratio": round(ratio, 5),
                "quality": _key_quality(n, chosen, profiles),
            })
    return out


def value_set_candidates(df: pd.DataFrame, profiles: dict[str, ColumnProfile]) -> dict[str, dict[str, Any]]:
    """Low-cardinality string columns → value→frequency map (value-set drafting input)."""
    n = len(df)
    out: dict[str, dict[str, Any]] = {}
    for name, cp in profiles.items():
        if cp.dtype not in ("string", "boolean"):
            continue
        if cp.distinct == 0 or cp.distinct > _VALUE_SET_MAX_DISTINCT:
            continue
        if n and cp.distinct_ratio > _VALUE_SET_MAX_RATIO:
            continue
        non_null, _, _ = _string_cells(df[name])
        freq = pd.Series(non_null).value_counts()
        redact = _has_pii_signal(cp.signals)
        values = {
            (_redact_sample_value(k) if redact else str(k)): int(v)
            for k, v in list(freq.items())[:_VALUE_FREQ_CAP]
        }
        out[name] = {"distinct": cp.distinct, "values": values, "truncated": cp.distinct > _VALUE_FREQ_CAP}
    return out


# --------------------------------------------------------------------------- #
# Orchestration                                                               #
# --------------------------------------------------------------------------- #
@dataclass(slots=True)
class TableProfile:
    table: str
    row_count: int
    columns: dict[str, ColumnProfile]
    candidate_keys: list[dict[str, Any]]
    value_sets: dict[str, dict[str, Any]]
    candidate_keys_truncated: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile_version": VERSION,
            "table": self.table,
            "row_count": self.row_count,
            "columns": {name: cp.to_dict() for name, cp in self.columns.items()},
            "candidate_keys": self.candidate_keys,
            "candidate_keys_truncated": self.candidate_keys_truncated,
            "value_set_candidates": self.value_sets,
            "signals": self._signal_index(),
        }

    def _signal_index(self) -> dict[str, list[str]]:
        idx: dict[str, list[str]] = {}
        for name, cp in self.columns.items():
            for sig in cp.signals:
                idx.setdefault(sig, []).append(name)
        return idx


def profile_table(df: pd.DataFrame, table: str) -> TableProfile:
    n = len(df)
    profiles: dict[str, ColumnProfile] = {}
    for col in df.columns:
        if col in _RESERVED_COLS:
            continue
        profiles[col] = profile_column(df[col], col, n)
    keys = candidate_keys(df, profiles)
    return TableProfile(
        table=table,
        row_count=n,
        columns=profiles,
        candidate_keys=keys,
        value_sets=value_set_candidates(df, profiles),
        candidate_keys_truncated=last_keysearch_truncated(),
    )


def profile_snapshot(snapshot_dir: str | Path) -> dict[str, Any]:
    """Profile every table in a snapshot; write ``profile/<table>.json`` + ``summary.json``.

    Returns the summary dict.
    """
    snap = Path(snapshot_dir)
    tables_dir = snap / "tables"
    if not tables_dir.is_dir():
        raise FileNotFoundError(f"no tables dir at {tables_dir} — run `migrate ingest` first.")
    out_dir = snap / "profile"
    out_dir.mkdir(parents=True, exist_ok=True)

    tables_summary: dict[str, Any] = {}
    signal_rollup: dict[str, dict[str, list[str]]] = {}
    for parquet in sorted(tables_dir.glob("*.parquet")):
        df = pd.read_parquet(parquet)
        table = parquet.stem
        tp = profile_table(df, table)
        (out_dir / f"{table}.json").write_text(json.dumps(tp.to_dict(), indent=2, default=str), encoding="utf-8")

        td = tp.to_dict()
        top_keys = td["candidate_keys"][:5]
        tables_summary[table] = {
            "row_count": tp.row_count,
            "columns": len(tp.columns),
            "candidate_keys": top_keys,
            "value_set_columns": sorted(tp.value_sets.keys()),
            "signals": td["signals"],
        }
        for sig, cols in td["signals"].items():
            signal_rollup.setdefault(sig, {})[table] = cols

    summary = {
        "profile_version": VERSION,
        "snapshot": snap.name,
        "tables": tables_summary,
        "signals_across_tables": signal_rollup,
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    return summary
