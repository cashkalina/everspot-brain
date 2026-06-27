<!-- EXAMPLE — runs/v1/questions.md, the Gate-1 questionnaire RENDERED from the
     JSON question records in ledger/questions/. The operator edits this file
     in place (check a box / fill a blank), and the pipeline ingests the answers
     back into the ledger. Demonstrates the json→md render. See plan §4.3, §5. -->

# Acme Memorial Gardens — Migration Questions (Gate 1, snapshot v1)

3 questions need your input before mapping is finalized. Each shows a **proposed
answer** — accept it by leaving the proposal checked, or override. Then save.

---

## q_0007 — Value set: `MASTER_OWNERS.STAT` → customer status

> Source column `MASTER_OWNERS.STAT` has values **A, R, C**. How should each map to
> Everspot `customer.status` (`lead` | `customer`)?

_AI confidence: 0.62 · handoff: internal_

| Source value | Proposed | Override (write `lead` or `customer`) |
|---|---|---|
| `A` | `customer` | ____________ |
| `R` | `lead`     | ____________ |
| `C` | `lead`     | ____________ |

- [x] Accept proposed mapping for all values
- [ ] I overrode one or more above

---

## q_0011 — Mapping: which column is the interment space?

> `BURIALS` has both `PLOT_NO` and `GRAVE_REF`. Which identifies the **property**
> (interment space) the decedent is buried in?

_AI confidence: 0.55 · handoff: internal_

- [x] `PLOT_NO`  *(proposed — matches PLOTS.PLOT_NO)*
- [ ] `GRAVE_REF`
- [ ] Other: ____________

---

## q_0003 — Identity: what uniquely identifies a `BURIALS` row?

> `BURIALS` has no GUID. Which column(s) uniquely identify one interment record in
> your system? This becomes the record's permanent identity (`source_id`), so v2
> drops update rather than duplicate.

_AI confidence: — · handoff: internal · **blocking**_

Proposed: `DECEDENT_NAME` + `DOD` (composite — flagged fragile, two people can share both).

- [ ] Accept proposed composite key (`DECEDENT_NAME` + `DOD`)
- [ ] Use this column / these columns instead: ____________
- [ ] No stable key exists — fall back to a row hash (accept fragility)

---

_When done, save this file. The pipeline reads your edits, writes them into
`ledger/value_sets.yaml`, `ledger/mapping.yaml`, and `project.yaml`, marks each
question `answered`, and resumes. Answered questions are never re-asked on v2._
