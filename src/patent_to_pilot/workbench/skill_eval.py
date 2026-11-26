"""Evaluate a proposed evidence-role skill before promotion.

This module is the evaluator. It reads the expected outcomes in
``sample/ra_pharma/dev/expected.json``; the dossier runtime never does. A candidate
passes when it is correct on every development case of the separate inhaler family and
on the dossier regression cases, and is never worse than its parent on any case.
"""
from __future__ import annotations

import json
from pathlib import Path

from patent_to_pilot.workbench import letters
from patent_to_pilot.workbench.dossier import apply_skill, document_meta, source, spec_sha

EVALUATOR = "evidence-role-skill-eval/1.0.0"


def _main_cases(pack: dict, pack_dir: Path) -> list[dict]:
    ex6 = source(pack, "US20120276199A1", "example-6")
    patent = {"passage_id": "US20120276199A1#example-6", "source_kind": "patent", "owner_name": ex6["owner"],
              "subject_text": "Example 6 of US20120276199A1", "text": ex6["text"]}
    by_id = {d["doc_id"]: d for d in pack["documents"]}
    report_id = "applicant-dissolution-report-1.1"
    layout = letters.read_layout((pack_dir / by_id[report_id]["file"]).read_bytes())
    meta = document_meta(layout)
    pages = [{"passage_id": f"{report_id}#page-{p['page']}", "source_kind": "applicant_document",
              "owner_name": meta["owner_name"], "subject_text": meta["product_line"],
              "text": letters.page_text(layout, p["page"]), "edition": meta.get("edition"),
              "report_id": meta.get("report_id")} for p in layout["pages"]]
    task = pack["tasks"][0]
    return [{"case_id": "main-no-report", "family": "dossier-regression", "task": task, "dossier": pack["dossier"],
             "passages": [patent]},
            {"case_id": "main-report-1.1", "family": "dossier-regression", "task": task, "dossier": pack["dossier"],
             "passages": [patent, *pages]}]


def _dev_cases(pack_dir: Path) -> list[dict]:
    dev = json.loads((pack_dir / "dev" / "inhaler-dev.json").read_text(encoding="utf-8"))
    passages = {p["passage_id"]: p for p in dev["passages"]}
    return [{"case_id": c["case_id"], "family": dev["fixture_id"], "task": dev["task"], "dossier": dev["dossier"],
             "passages": [passages[p] for p in c["passages"]]} for c in dev["cases"]]


def _decide(spec, case):
    result = apply_skill(spec, case["task"], case["passages"], case["dossier"])
    accepted = [c["passage_id"] for c in result["accepted"]]
    if spec["accept"]["source_kinds"] == ["*"]:
        accepted = accepted[:1]   # the version 1 rule uses the first value found
    return accepted


def evaluate(spec: dict, parent: dict | None, pack: dict, pack_dir: Path) -> dict:
    expected = json.loads((pack_dir / "dev" / "expected.json").read_text(encoding="utf-8"))["cases"]
    rows = []
    for case in _dev_cases(pack_dir) + _main_cases(pack, pack_dir):
        want = expected[case["case_id"]]["accepted"]
        got = _decide(spec, case)
        row = {"case_id": case["case_id"], "family": case["family"], "expected": want, "candidate": got,
               "candidate_correct": got == want}
        if parent:
            before = _decide(parent, case)
            row.update(parent=before, parent_correct=before == want)
        rows.append(row)
    regressions = [r["case_id"] for r in rows if parent and r["parent_correct"] and not r["candidate_correct"]]
    dev_rows = [r for r in rows if r["family"] != "dossier-regression"]
    return {"evaluator": EVALUATOR, "candidate": spec["version"], "candidate_sha256": spec_sha(spec),
            "parent": parent and parent["version"], "cases": rows,
            "dev_family": dev_rows[0]["family"] if dev_rows else None,
            "candidate_errors": sum(not r["candidate_correct"] for r in rows),
            "parent_errors": sum(not r["parent_correct"] for r in rows) if parent else None,
            "regressions": regressions,
            "passed": all(r["candidate_correct"] for r in rows) and not regressions}
