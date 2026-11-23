#!/usr/bin/env python3
"""decision-ledger: ADRs + decision log. Stdlib only.

Add decisions (title, context, decision, alternatives, owner, date,
review date, tags), list/search by status/tag, mark superseded (linked to
the superseding decision), list decisions due for review, and generate a
Markdown decision log. Superseded decisions are kept, never deleted.

All example decisions are fictional.
"""
import argparse, json, sys
from datetime import date
from pathlib import Path

VERSION = "0.1.0"
EXAMPLES = Path(__file__).resolve().parent / "examples" / "decisions.json"

def store_path(store):
    d = Path(store); d.mkdir(parents=True, exist_ok=True)
    return d / "decisions.json"

def load(store):
    p = store_path(store)
    if not p.exists():
        return []
    data = json.loads(p.read_text())
    if not isinstance(data, list):
        raise ValueError("decisions.json must be a JSON list")
    return data

def save(store, data):
    store_path(store).write_text(json.dumps(data, indent=2) + "\n")

def next_id(data):
    nums = [int(d["id"].split("-")[1]) for d in data
            if d.get("id", "").startswith("ADR-") and d["id"].split("-")[1].isdigit()]
    return f"ADR-{max(nums, default=0) + 1:04d}"

def valid_date(s):
    try:
        y, m, d = (int(x) for x in s.split("-"))
        date(y, m, d)
        return True
    except (ValueError, AttributeError):
        return False

def cmd_seed(args):
    data = load(args.store)
    if data:
        print("error: store already has decisions; seed only an empty store", file=sys.stderr)
        return 2
    examples = json.loads(EXAMPLES.read_text())
    save(args.store, examples)
    print(f"Seeded {len(examples)} fictional example decisions into {args.store}")
    return 0

def cmd_add(args):
    if not valid_date(args.date) or not valid_date(args.review_date):
        print("error: --date and --review-date must be valid YYYY-MM-DD dates", file=sys.stderr)
        return 2
    data = load(args.store)
    entry = {
        "id": next_id(data), "title": args.title, "context": args.context,
        "decision": args.decision, "alternatives": args.alternatives,
        "owner": args.owner, "date": args.date, "review_date": args.review_date,
        "tags": [t.strip() for t in args.tags.split(",") if t.strip()] if args.tags else [],
        "status": "active", "superseded_by": None, "supersede_reason": None,
    }
    data.append(entry)
    save(args.store, data)
    print(f"Added {entry['id']}: {entry['title']}")
    return 0

def cmd_list(args):
    data = load(args.store)
    rows = [d for d in data if (not args.status or d["status"] == args.status)]
    if not rows:
        print("No decisions recorded." if not data else "No decisions match the filter.")
        return 0
    for d in sorted(rows, key=lambda x: x["id"]):
        print(f"{d['id']}  [{d['status']}]  {d['title']}  (owner: {d['owner']}, review: {d['review_date']})")
    return 0

def cmd_search(args):
    data = load(args.store)
    q = (args.query or "").lower()
    hits = [d for d in data
            if (not args.tag or args.tag in d.get("tags", []))
            and (not q or q in " ".join(str(d[k]) for k in ("title", "context", "decision", "alternatives")).lower())]
    if not hits:
        print("No decisions match.")
        return 0
    for d in sorted(hits, key=lambda x: x["id"]):
        print(f"{d['id']}  [{d['status']}]  {d['title']}  (tags: {', '.join(d.get('tags', []))})")
    return 0

def cmd_supersede(args):
    data = load(args.store)
    by_id = {d["id"]: d for d in data}
    if args.id not in by_id:
        print(f"error: no decision with id {args.id!r}", file=sys.stderr)
        return 2
    if args.superseded_by not in by_id:
        print(f"error: no decision with id {args.superseded_by!r} to supersede with "
              f"(superseding decision must exist)", file=sys.stderr)
        return 2
    if args.id == args.superseded_by:
        print("error: a decision cannot supersede itself", file=sys.stderr)
        return 2
    entry = by_id[args.id]
    if entry["status"] == "superseded":
        print(f"error: {args.id} is already superseded by {entry['superseded_by']}", file=sys.stderr)
        return 2
    entry["status"] = "superseded"
    entry["superseded_by"] = args.superseded_by
    entry["supersede_reason"] = args.reason or ""
    save(args.store, data)
    print(f"{args.id} superseded by {args.superseded_by}" + (f" ({args.reason})" if args.reason else ""))
    return 0

def cmd_review_due(args):
    as_of = args.as_of or date.today().isoformat()
    if not valid_date(as_of):
        print("error: --as-of must be a valid YYYY-MM-DD date", file=sys.stderr)
        return 2
    data = load(args.store)
    due = [d for d in data if d["status"] == "active" and d["review_date"] <= as_of]
    if not due:
        print(f"No decisions due for review as of {as_of}.")
        return 0
    for d in sorted(due, key=lambda x: x["review_date"]):
        print(f"{d['id']}  review was {d['review_date']}  {d['title']}  (owner: {d['owner']})")
    return 0

def cmd_report(args):
    data = load(args.store)
    lines = ["# Decision Log", "",
             f"Decisions: **{len(data)}** — active: **{sum(1 for d in data if d['status']=='active')}**, "
             f"superseded: **{sum(1 for d in data if d['status']=='superseded')}**",
             "",
             "> Example decisions in this repo are fictional. Superseded decisions "
             "are kept in the log with a link to the decision that replaced them.",
             ""]
    for d in sorted(data, key=lambda x: x["id"]):
        lines += [f"## {d['id']} — {d['title']}", "",
                  f"- **Status:** {d['status']}" + (f" (superseded by {d['superseded_by']})" if d.get("superseded_by") else ""),
                  f"- **Owner:** {d['owner']} · **Date:** {d['date']} · **Review date:** {d['review_date']}",
                  f"- **Tags:** {', '.join(d.get('tags', [])) or '—'}",
                  "",
                  f"**Context:** {d['context']}", "",
                  f"**Decision:** {d['decision']}", "",
                  f"**Alternatives considered:** {d['alternatives']}"]
        if d.get("supersede_reason"):
            lines.append("")
            lines.append(f"**Supersede reason:** {d['supersede_reason']}")
        lines.append("")
    out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines))
    print(f"Wrote {out} ({len(data)} decisions)")
    return 0

def main(argv=None):
    p = argparse.ArgumentParser(prog="ledger.py", description="ADRs + decision log.")
    p.add_argument("--version", action="version", version=VERSION)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("seed", help="Seed the 4 fictional example decisions into an empty store")
    s.add_argument("--store", required=True); s.set_defaults(fn=cmd_seed)
    a = sub.add_parser("add", help="Add a decision")
    a.add_argument("--store", required=True); a.add_argument("--title", required=True)
    a.add_argument("--context", required=True); a.add_argument("--decision", required=True)
    a.add_argument("--alternatives", required=True); a.add_argument("--owner", required=True)
    a.add_argument("--date", required=True); a.add_argument("--review-date", required=True)
    a.add_argument("--tags", default=""); a.set_defaults(fn=cmd_add)
    l = sub.add_parser("list", help="List decisions"); l.add_argument("--store", required=True)
    l.add_argument("--status", choices=["active", "superseded"]); l.set_defaults(fn=cmd_list)
    se = sub.add_parser("search", help="Search decisions"); se.add_argument("--store", required=True)
    se.add_argument("--query"); se.add_argument("--tag"); se.set_defaults(fn=cmd_search)
    sup = sub.add_parser("supersede", help="Mark a decision superseded by another")
    sup.add_argument("--store", required=True); sup.add_argument("--id", required=True)
    sup.add_argument("--superseded-by", required=True); sup.add_argument("--reason"); sup.set_defaults(fn=cmd_supersede)
    rd = sub.add_parser("review-due", help="List decisions due for review")
    rd.add_argument("--store", required=True); rd.add_argument("--as-of"); rd.set_defaults(fn=cmd_review_due)
    rep = sub.add_parser("report", help="Generate the Markdown decision log")
    rep.add_argument("--store", required=True); rep.add_argument("--out", required=True); rep.set_defaults(fn=cmd_report)
    args = p.parse_args(argv)
    return args.fn(args)

if __name__ == "__main__":
    raise SystemExit(main())
