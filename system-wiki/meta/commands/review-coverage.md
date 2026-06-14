---
title: Review-coverage Command
purpose: Analyze the fallback log to identify recurring gaps and propose concrete improvements
last_updated: 2026-06-14
---

# Review-coverage

**Purpose:** Analyze the fallback log to identify recurring gaps and propose concrete improvements.

**Operation type:** Read-only

**Inputs:**
- `.fallback.log` (gitignored, written by the agent when it reads Everspot source instead of wiki)
- Current wiki state

**Preconditions:**
- Fallback log exists and has entries (if not, report "no fallback data")

**Log entry format:**

Each entry is appended when the agent cannot answer from the wiki alone:

```
[2026-06-12 14:23:15] Topic: How does payment refund validation work?
Consulted: modules/transaction/models/payment.md, modules/transaction/models/refund.md
Source read: modules/Transaction/Models/Payment.php (method validateRefund, lines 45-67)
---
```

**Process:**

### Parse log

1. Read all entries from `.fallback.log`.
2. For each entry, extract:
   - Topic (the question or task)
   - Consulted docs (which wiki documents were read)
   - Source read (which Everspot files and what content was accessed)

### Identify patterns

**Recurring topics:**

1. Group entries by similar topic strings (fuzzy match, keyword overlap).
2. If the same topic or closely related topics appear multiple times, flag as recurring.

**Recurring source files:**

1. Count how often each Everspot source file appears in "Source read."
2. If a file is read frequently and is not a model class (e.g., a service, a helper, a config), it may warrant a new wiki document.

**Recurring gaps in existing docs:**

1. If the same model document is consulted repeatedly, but the agent always falls back to source for the same kind of information (e.g., a specific method, a specific relationship detail), that section may be incomplete or unclear.

### Propose adjustments

Based on patterns, generate proposals:

- **Missing documents:** "Frequently consulted source file `modules/Transaction/Services/PaymentProcessor.php` is not documented. Consider creating a service documentation page."
- **Sections to expand:** "Model document `payment.md` consulted 8 times, but `validateRefund` method required reading source every time. Consider expanding the Key Methods section with this method's logic and validation rules."
- **Links to add:** "Topic 'payment and invoice relationship' recurs. Documents consulted: `payment.md`, `invoice.md`. Neither links to the other. Add cross-references."
- **New coverage rules:** "Non-model class `app/Services/TenantProvisioner.php` read 5 times. Current coverage rule excludes services. Consider extending documentation scope."

### Output

Generate a report:

1. **Summary statistics:** total fallback entries, date range, most-consulted documents, most-read source files.
2. **Recurring patterns:** grouped topics, gap types.
3. **Concrete proposals:** enumerated list of suggested additions, expansions, and links, with evidence (frequency, entry excerpts).

**Outputs:**
- Report written to terminal or `meta/coverage-review-<date>.md`
- Proposals are actionable: specific document, specific section, specific reason

**Error handling:**
- Log file missing or empty — report "no fallback data, coverage cannot be assessed"
- Malformed log entries — skip invalid entries, report count of skipped
- Review-coverage never fails; it reports what it can analyze
