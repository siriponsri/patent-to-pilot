"""Live phase tracker for the outcome-based plan (owner note 22 Nov 2026).

The live registry (docs/tracking/owner-note-22112026/goal_registry.json) is the single source of truth. The CSV, the
Markdown board and the AFFiNE page projections are rendered from it, so the owner never enters progress twice.
The owner seed under docs/owner/owner-note-22112026/ is read-only input and is never modified.

Commands
  init                      copy the seeds into the live root when absent (never overwrites live state)
  merge                     add seed tasks/fields that are new, preserving live status/outcome/evidence/AFFiNE ids
  set TASK [--status S] [--outcome O] [--evidence URI] [--check C] [--next N] [--blocker B] [--note TEXT]
         [--spent X] [--reserved X] [--remaining X] [--affine-id ID] [--affine-url URL] [--affine-sync S]
  milestone NAME STATUS [--evidence URI]
  readiness KEY VALUE       set method_evidence / product_readiness / publication_readiness
  render                    rewrite phase_tasks.csv, PHASE_BOARD.md and affine/*.md from the registry
  show [TASK]               print a compact status table (or one task)

Every write appends an event to receipts/tracker_events.jsonl (timestamp for provenance only).
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SEED = REPO / "docs/owner/owner-note-22112026"
LIVE = REPO / "docs/tracking/owner-note-22112026"
REG = LIVE / "goal_registry.json"
CSV_PATH = LIVE / "phase_tasks.csv"
BOARD = LIVE / "PHASE_BOARD.md"
AFFINE_DIR = LIVE / "affine"
EVENTS = LIVE / "receipts/tracker_events.jsonl"

STATUS = ["NOT_STARTED", "READY", "IN_PROGRESS", "COMPLETE", "PARTIAL", "BLOCKED", "PARKED", "SKIPPED"]
OUTCOME = ["NOT_RUN", "ENGINEERING_VERIFIED", "EXPLORATORY_GAIN", "SUPPORTED_MATCHED_GAIN", "NO_GAIN", "INCONCLUSIVE",
           "UNRESOLVED"]
LIVE_FIELDS = ["status", "outcome", "evidence_uri", "check_result", "next_task", "blocker", "budget_spent_usd",
               "budget_reserved_usd", "budget_remaining_usd", "owner_decision_pending", "affine_item_id",
               "affine_item_url", "affine_sync_status", "notes"]
CSV_COLUMNS = ["task_id", "phase_id", "title", "status", "outcome", "depends_on", "condition", "execution_lane",
               "required_artifacts", "acceptance_evidence", "evidence_uri", "check_result", "next_task", "blocker",
               "budget_authority", "budget_spent_usd", "budget_reserved_usd", "budget_remaining_usd", "if_success",
               "if_partial", "if_no_gain", "if_blocked", "owner_input_if_required", "owner_decision_pending",
               "affine_item_id", "affine_item_url", "affine_sync_status"]
ICON = {"NOT_STARTED": "⏳", "READY": "🟢", "IN_PROGRESS": "🔄", "COMPLETE": "✅", "PARTIAL": "🟡", "BLOCKED": "⛔",
        "PARKED": "🅿️", "SKIPPED": "⏭️"}


def now() -> str:
    return dt.datetime.now(dt.timezone(dt.timedelta(hours=7))).isoformat(timespec="seconds")


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load() -> dict:
    return json.loads(REG.read_text(encoding="utf-8"))


def save(reg: dict, event: dict) -> None:
    reg["live_updated_at"] = now()
    tmp = REG.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(reg, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    tmp.replace(REG)
    EVENTS.parent.mkdir(parents=True, exist_ok=True)
    with EVENTS.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"at": reg["live_updated_at"], **event}, ensure_ascii=False) + "\n")
    render(reg)


def task(reg: dict, tid: str) -> dict:
    for t in reg["tasks"]:
        if t["task_id"] == tid:
            return t
    raise SystemExit(f"unknown task {tid}")


def cmd_init(_a) -> None:
    if REG.exists():
        print("live registry exists; use merge (init never overwrites live state)")
        return
    LIVE.mkdir(parents=True, exist_ok=True)
    (LIVE / "receipts").mkdir(exist_ok=True)
    reg = json.loads((SEED / "config/goal_registry.json").read_text(encoding="utf-8"))
    reg["config_kind"] = "LIVE_TRACKING_STATE"
    reg["seed_sources"] = {p: sha(SEED / p) for p in ("config/goal_registry.json", "tracking/phase_tasks.csv",
                                                       "tracking/PHASE_BOARD.md")}
    reg["seed_root"] = "docs/owner/owner-note-22112026 (owner-local, untracked, read-only)"
    for t in reg["tasks"]:
        t.setdefault("notes", "")
    save(reg, {"event": "init", "seed_sources": reg["seed_sources"]})
    print("initialised", REG)


def cmd_merge(_a) -> None:
    reg = load()
    seed = json.loads((SEED / "config/goal_registry.json").read_text(encoding="utf-8"))
    have = {t["task_id"]: t for t in reg["tasks"]}
    added, updated = [], []
    for st in seed["tasks"]:
        lt = have.get(st["task_id"])
        if lt is None:
            reg["tasks"].append({**st, "notes": ""})
            added.append(st["task_id"])
            continue
        for k, v in st.items():
            if k in LIVE_FIELDS:
                continue                                    # never reset live progress from the seed
            if lt.get(k) != v:
                lt[k] = v
                updated.append(f"{st['task_id']}.{k}")
    save(reg, {"event": "merge", "added": added, "definition_fields_updated": updated})
    print("added", added, "definition fields updated", len(updated))


def cmd_set(a) -> None:
    reg = load()
    t = task(reg, a.task)
    before = {k: t.get(k) for k in LIVE_FIELDS}
    if a.status:
        if a.status not in STATUS:
            raise SystemExit(f"status must be one of {STATUS}")
        t["status"] = a.status
    if a.outcome:
        if a.outcome not in OUTCOME:
            raise SystemExit(f"outcome must be one of {OUTCOME}")
        t["outcome"] = a.outcome
    for arg, key in (("evidence", "evidence_uri"), ("check", "check_result"), ("next", "next_task"),
                     ("blocker", "blocker"), ("affine_id", "affine_item_id"), ("affine_url", "affine_item_url"),
                     ("affine_sync", "affine_sync_status"), ("decision", "owner_decision_pending")):
        v = getattr(a, arg)
        if v is not None:
            t[key] = v
    for arg, key in (("spent", "budget_spent_usd"), ("reserved", "budget_reserved_usd"),
                     ("remaining", "budget_remaining_usd")):
        v = getattr(a, arg)
        if v is not None:
            t[key] = float(v)
    if a.note:
        t["notes"] = (t.get("notes") or "") + (" | " if t.get("notes") else "") + f"[{now()[:10]}] {a.note}"
    if t["status"] == "COMPLETE" and not t.get("evidence_uri"):
        raise SystemExit("COMPLETE requires --evidence")
    # a material change makes the AFFiNE projection stale until it is re-applied and read back
    if any(before[k] != t.get(k) for k in LIVE_FIELDS if not k.startswith("affine")) and a.affine_sync is None:
        t["affine_sync_status"] = "SYNC_PENDING" if t.get("affine_item_id") else "NOT_SYNCED"
    _phase_rollup(reg)
    save(reg, {"event": "set", "task": a.task, "before": before, "after": {k: t.get(k) for k in LIVE_FIELDS}})
    print(a.task, t["status"], t["outcome"], t.get("affine_sync_status"))


def _phase_rollup(reg: dict) -> None:
    by = {t["task_id"]: t for t in reg["tasks"]}
    for ph in reg["phases"]:
        sts = [by[i]["status"] for i in ph["task_ids"] if i in by]
        if sts and all(s in ("COMPLETE", "SKIPPED") for s in sts):
            ph["status"] = "COMPLETE"
        elif any(s in ("IN_PROGRESS", "COMPLETE", "PARTIAL", "BLOCKED") for s in sts):
            ph["status"] = "IN_PROGRESS"
        else:
            ph["status"] = "NOT_STARTED"


def cmd_milestone(a) -> None:
    reg = load()
    ms = reg.get("milestones")
    items = ms if isinstance(ms, list) else [{"name": k, **(v if isinstance(v, dict) else {"status": v})}
                                             for k, v in (ms or {}).items()]
    hit = next((m for m in items if (m.get("name") or m.get("milestone") or m.get("id")) == a.name), None)
    if hit is None:
        raise SystemExit(f"unknown milestone {a.name}")
    hit["status"] = a.status
    if a.evidence:
        hit["evidence_uri"] = a.evidence
    reg["milestones"] = items if isinstance(ms, list) else {m.pop("name"): m for m in items}
    save(reg, {"event": "milestone", "name": a.name, "status": a.status, "evidence": a.evidence})


def cmd_readiness(a) -> None:
    reg = load()
    if a.key not in ("method_evidence", "product_readiness", "publication_readiness"):
        raise SystemExit("key must be method_evidence, product_readiness or publication_readiness")
    old = reg.get(a.key)
    reg[a.key] = a.value
    save(reg, {"event": "readiness", "key": a.key, "before": old, "after": a.value})


def _cell(v) -> str:
    if isinstance(v, list):
        return "; ".join(str(x) for x in v)
    return "" if v is None else str(v)


def _milestones(reg: dict) -> list[dict]:
    ms = reg.get("milestones")
    if isinstance(ms, list):
        return [{"name": m.get("name") or m.get("milestone") or m.get("id"), **m} for m in ms]
    return [{"name": k, **(v if isinstance(v, dict) else {"status": v})} for k, v in (ms or {}).items()]


def render(reg: dict | None = None) -> None:
    reg = reg or load()
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=CSV_COLUMNS, lineterminator="\n", extrasaction="ignore")
    w.writeheader()
    for t in reg["tasks"]:
        w.writerow({k: _cell(t.get(k)) for k in CSV_COLUMNS})
    CSV_PATH.write_text(buf.getvalue(), encoding="utf-8")
    BOARD.write_text(_board(reg), encoding="utf-8")
    AFFINE_DIR.mkdir(exist_ok=True)
    (AFFINE_DIR / "00-dashboard.md").write_text(_dashboard(reg), encoding="utf-8")
    for ph in reg["phases"]:
        (AFFINE_DIR / f"{ph['phase_id']}-phase.md").write_text(_phase_page(reg, ph), encoding="utf-8")


def _status_line(t: dict) -> str:
    return f"{ICON.get(t['status'], '')} {t['status']} · {t['outcome']}"


def _board(reg: dict) -> str:
    by = {t["task_id"]: t for t in reg["tasks"]}
    out = ["# Phase board (live)", "",
           f"Rendered from `goal_registry.json` at {reg.get('live_updated_at', '')}. Do not edit by hand; use "
           "`python scripts/tracking/ptp_tracker.py set ...`. Status and research outcome are separate fields.", "",
           "## Readiness", "", "| Field | Value |", "|---|---|"]
    for k in ("method_evidence", "product_readiness", "publication_readiness"):
        out.append(f"| {k} | {reg.get(k, '')} |")
    out += ["", "## Milestones", "", "| Milestone | Status | Evidence |", "|---|---|---|"]
    for m in _milestones(reg):
        out.append(f"| {m['name']} | {m.get('status', '')} | {_cell(m.get('evidence_uri') or m.get('evidence_required'))} |")
    for ph in reg["phases"]:
        out += ["", f"## {ph['phase_id']} — {ph['name']}", "", f"Phase status: **{ph.get('status', '')}**", "",
                "| Task | Title | Status | Outcome | Evidence | Next | Blocker | AFFiNE |", "|---|---|---|---|---|---|---|---|"]
        for tid in ph["task_ids"]:
            t = by[tid]
            out.append(f"| {tid} | {t['title']} | {ICON.get(t['status'], '')} {t['status']} | {t['outcome']} | "
                       f"{_cell(t.get('evidence_uri')) or '—'} | {_cell(t.get('next_task'))} | {t.get('blocker') or '—'} | "
                       f"{t.get('affine_sync_status', '')} |")
    return "\n".join(out) + "\n"


def _dashboard(reg: dict) -> str:
    counts = {}
    for t in reg["tasks"]:
        counts[t["status"]] = counts.get(t["status"], 0) + 1
    out = ["# Patent-to-Pilot — Program dashboard", "",
           "Tracker projection of the live registry in the repository "
           "(`docs/tracking/owner-note-22112026/goal_registry.json`). Phases advance by verified outcomes, not dates.",
           "", "## Readiness", ""]
    for k in ("method_evidence", "product_readiness", "publication_readiness"):
        out.append(f"- **{k}**: {reg.get(k, '')}")
    out += ["", "## Milestones", ""]
    for m in _milestones(reg):
        out.append(f"- **{m['name']}**: {m.get('status', '')}")
    out += ["", "## Task counts", ""] + [f"- {ICON.get(s, '')} {s}: {n}" for s, n in sorted(counts.items())]
    out += ["", "## Phases", "", "| Phase | Name | Status | Tasks done |", "|---|---|---|---|"]
    by = {t["task_id"]: t for t in reg["tasks"]}
    for ph in reg["phases"]:
        done = sum(by[i]["status"] in ("COMPLETE", "SKIPPED") for i in ph["task_ids"])
        out.append(f"| {ph['phase_id']} | {ph['name']} | {ph.get('status', '')} | {done}/{len(ph['task_ids'])} |")
    blocked = [t for t in reg["tasks"] if t["status"] in ("BLOCKED", "PARTIAL") or t.get("owner_decision_pending")]
    out += ["", "## Needs attention", ""]
    out += [f"- **{t['task_id']}** {t['title']}: {t.get('blocker') or t.get('owner_decision_pending') or t['status']}"
            for t in blocked] or ["- Nothing blocked."]
    return "\n".join(out) + "\n"


def _phase_page(reg: dict, ph: dict) -> str:
    by = {t["task_id"]: t for t in reg["tasks"]}
    out = [f"# {ph['phase_id']} — {ph['name']}", "", f"Phase status: **{ph.get('status', '')}**", ""]
    for k in ("entry_rule", "exit_rule"):
        if ph.get(k):
            out.append(f"**{k.replace('_', ' ').capitalize()}:** {ph[k]}")
            out.append("")
    out += ["| Task | Title | Status | Outcome | Next |", "|---|---|---|---|---|"]
    for tid in ph["task_ids"]:
        t = by[tid]
        out.append(f"| {tid} | {t['title']} | {ICON.get(t['status'], '')} {t['status']} | {t['outcome']} | "
                   f"{_cell(t.get('next_task'))} |")
    for tid in ph["task_ids"]:
        t = by[tid]
        out += ["", f"## {tid} — {t['title']}", "",
                "- **Status:** see the table above (single place to update)",
                f"- **Depends on:** {_cell(t.get('depends_on')) or '—'}",
                f"- **Acceptance evidence:** {t.get('acceptance_evidence', '')}",
                f"- **Evidence:** {_cell(t.get('evidence_uri')) or 'pending'}",
                f"- **Check:** {t.get('check_result', '')}",
                f"- **Next:** {_cell(t.get('next_task'))}",
                f"- **Blocker:** {t.get('blocker') or '—'}"]
        if t.get("notes"):
            out.append(f"- **Notes:** {t['notes']}")
    return "\n".join(out) + "\n"


def cmd_show(a) -> None:
    reg = load()
    if a.task:
        print(json.dumps(task(reg, a.task), ensure_ascii=False, indent=1))
        return
    for t in reg["tasks"]:
        print(f"{t['task_id']:7} {t['status']:12} {t['outcome']:22} {t.get('affine_sync_status', ''):13} {t['title'][:60]}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init")
    sub.add_parser("merge")
    sub.add_parser("render")
    s = sub.add_parser("show")
    s.add_argument("task", nargs="?")
    s = sub.add_parser("set")
    s.add_argument("task")
    for k in ("status", "outcome", "evidence", "check", "next", "blocker", "note", "spent", "reserved", "remaining",
              "affine-id", "affine-url", "affine-sync", "decision"):
        s.add_argument(f"--{k}")
    m = sub.add_parser("milestone")
    m.add_argument("name")
    m.add_argument("status")
    m.add_argument("--evidence")
    r = sub.add_parser("readiness")
    r.add_argument("key")
    r.add_argument("value")
    a = ap.parse_args(argv)
    {"init": cmd_init, "merge": cmd_merge, "render": lambda _a: render(), "show": cmd_show, "set": cmd_set,
     "milestone": cmd_milestone, "readiness": cmd_readiness}[a.cmd](a)
    return 0


if __name__ == "__main__":
    sys.exit(main())
