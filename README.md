# decision-ledger

ADRs + a decision log, as a tiny CLI: record a decision with its context,
the alternatives considered, an owner, and a review date — then list and
search by status or tag, mark decisions superseded (linked to the decision
that replaced them), and generate a Markdown decision log plus a
due-for-review list.

Built by Sean Steuer — Program Manager, AI Strategy & Operational
Transformation at Netflix. The format generalizes the architecture-decision
record (ADR) practice used in program and technical-program work. All
example decisions in this repo are fictional (Northlight Studios, Harbor
Lane Studio) and labeled as such.

## What it is

- A stdlib-only Python CLI + JSON store (`ledger.py`, no dependencies).
- `add` a decision: title, context, decision, alternatives considered,
  owner, date, review date, tags, status.
- `list` / `search` by status or tag.
- `supersede` a decision, linking it to the decision that replaced it —
  the old decision stays in the log, marked, never deleted.
- `review-due` lists decisions whose review date has arrived.
- `report` generates a Markdown decision log.

## What it is NOT

- Not a project-management tool, not a task tracker, and not a substitute
  for the discussion that produced the decision. It records the outcome
  and the reasoning, so a future reader can reconstruct *why*.
- Not a wiki. There is no web UI; the Markdown log is the readable output.

## Quick start

```bash
# Seed the fictional examples (or start empty and add your own)
python3 ledger.py seed --store ./ledger-data

# Add a decision
python3 ledger.py add --store ./ledger-data \
  --title "Use a single shared spend dashboard" \
  --context "Three teams track AI spend in three spreadsheets." \
  --decision "Adopt one shared dashboard, updated monthly." \
  --alternatives "Keep per-team sheets; buy a vendor tool" \
  --owner sean --date 2026-11-23 --review-date 2027-02-23 --tags spend,governance

# List, search, check what's due for review
python3 ledger.py list --store ./ledger-data
python3 ledger.py search --store ./ledger-data --tag governance
python3 ledger.py review-due --store ./ledger-data --as-of 2027-03-01

# A later decision replaces an earlier one — link them, don't delete
python3 ledger.py supersede --store ./ledger-data --id ADR-0001 \
  --superseded-by ADR-0004 --reason "Replaced by the vendor-tool decision."

# Generate the log
python3 ledger.py report --store ./ledger-data --out DECISIONS.md
```

Python 3.9+; no dependencies. Dates are `YYYY-MM-DD`.

## Data model

`ledger-data/decisions.json` — a list of decisions:

```json
{
  "id": "ADR-0001",
  "title": "Use a single shared spend dashboard",
  "context": "Three teams track AI spend in three spreadsheets.",
  "decision": "Adopt one shared dashboard, updated monthly.",
  "alternatives": "Keep per-team sheets; buy a vendor tool",
  "owner": "sean",
  "date": "2026-11-23",
  "review_date": "2027-02-23",
  "tags": ["spend", "governance"],
  "status": "active",
  "superseded_by": null,
  "supersede_reason": null
}
```

Statuses: `active`, `superseded`. Superseding requires the superseding
decision to exist — superseding a nonexistent decision fails cleanly
(exit code 2, no change written).

## Tests

```bash
python3 -m unittest discover -s tests -v
```

Tests cover add / list / search / supersede / review-due / report, the
negative path (superseding a nonexistent decision fails cleanly), and the
seeded fictional examples.

## Layout

```
ledger.py          CLI + store logic (stdlib only)
examples/decisions.json   The 4 fictional example decisions
tests/test_ledger.py
```
