"""Scripted owner walkthrough of the RA Pharma dossier through the normal launcher.

    python examples/ra_pharma/walkthrough.py OUT_DIR [--render]

Starts ``scripts/ptp_run.py --serve`` on a fresh store inside OUT_DIR, runs the same
sequence as the browser walkthrough over HTTP, and writes every snapshot, the comparison,
the replay checks and the reply drafts to OUT_DIR. ``--render`` also prints the HTML reply
with a local Chromium and converts the DOCX with LibreOffice when either is installed;
those QA renderers are not part of the Workbench runtime.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
SOFFICE = Path(os.environ.get("PROGRAMFILES", r"C:\Program Files")) / "LibreOffice" / "program" / "soffice.exe"


def call(url, method="GET", body=None, raw=False):
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        payload = r.read()
    return payload if raw else json.loads(payload.decode("utf-8"))


def applicant(snap):
    return next(i for i in snap["items"] if i["item_id"] == "reg.R-P54.applicant-result")


def render(out: Path, base: str, sid: str) -> dict:
    result = {}
    try:
        from playwright.sync_api import sync_playwright
        exe = os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE")
        with sync_playwright() as p:
            browser = p.chromium.launch(**({"executable_path": exe} if exe else {}))
            page = browser.new_page()
            page.goto(f"{base}api/dossier/snapshots/{sid}/export/html")
            page.evaluate("document.fonts.ready")
            result["html_font_loaded"] = page.evaluate("document.fonts.check('16px Sarabun')")
            page.pdf(path=str(out / "reply-html.pdf"), format="A4", prefer_css_page_size=True)
            page.screenshot(path=str(out / "reply-html.png"), full_page=True)
            browser.close()
        result["html_render"] = "reply-html.pdf"
    except Exception as exc:  # renderer missing: say so rather than failing the walkthrough
        result["html_render"] = f"NOT_RUN: {type(exc).__name__}: {exc}"
    if SOFFICE.exists():
        profile = (out / "lo-profile").resolve().as_uri()
        done = subprocess.run([str(SOFFICE), "--headless", "--norestore", f"-env:UserInstallation={profile}",
                               "--convert-to", "pdf", "--outdir", str(out / "docx-render"), str(out / "reply.docx")],
                              capture_output=True, text=True)
        result["docx_render"] = "docx-render/reply.pdf" if done.returncode == 0 else f"FAILED: {done.stderr[-300:]}"
        shutil.rmtree(out / "lo-profile", ignore_errors=True)
    else:
        result["docx_render"] = "NOT_RUN: LibreOffice not found"
    return result


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("out")
    ap.add_argument("--render", action="store_true")
    args = ap.parse_args(argv)
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    proc = subprocess.Popen([sys.executable, "-X", "utf8", "-u", str(ROOT / "scripts" / "ptp_run.py"), "--serve",
                             "--port", "0", "--data-dir", str(out / "store")], stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, encoding="utf-8", env={**os.environ, "PTP_NO_BROWSER": "1"})
    try:
        base = next(line.split("URL:", 1)[1].strip() for line in proc.stdout if line.strip().startswith("URL:"))
        steps = []

        def build(label, **body):
            snap = call(base + "api/dossier/snapshots", "POST", {"label": label, **body})
            (out / f"snapshot-{snap['seq']}.json").write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
            res = applicant(snap)
            steps.append({"seq": snap["seq"], "label": label, "skill": snap["identity"]["skill"]["version"],
                          "branch": snap["claim_branch"], "applicant_status": res["status"], "value": res["value"],
                          "snapshot_id": snap["snapshot_id"]})
            return snap

        v1 = build("skill 1.0.0, no report")
        corr = call(base + "api/dossier/skills/corrections", "POST", {
            "snapshot_id": v1["snapshot_id"], "item_id": "reg.R-P54.applicant-result",
            "passage_id": "US20120276199A1#example-6", "to_role": "patent_disclosure"})
        spec = call(base + "api/dossier/skills/proposals", "POST", {"correction_id": corr["id"]})["spec"]
        evaluation = call(base + "api/dossier/skills/evaluations", "POST", {"version": spec["version"]})
        call(base + "api/dossier/skills/promotions", "POST", {"version": spec["version"]})
        before = build("before applicant report")
        after = build("after applicant report", attachments=["applicant-dissolution-report-1.0"])
        branch = build("claim 18 branch", attachments=["applicant-dissolution-report-1.0"], claim_branch="18")
        both = ["applicant-dissolution-report-1.0", "applicant-dissolution-report-1.1"]
        build("two report editions", attachments=both)
        chosen = build("operator chose edition 1.1", attachments=both, edition_choice={"QC-DIS-0459": "1.1"})
        diffs = {"before_after": call(f"{base}api/dossier/diff/{before['snapshot_id']}/{after['snapshot_id']}"),
                 "branch_15_18": call(f"{base}api/dossier/diff/{after['snapshot_id']}/{branch['snapshot_id']}")}
        verify = {s["seq"]: call(f"{base}api/dossier/snapshots/{s['snapshot_id']}/verify")
                  for s in (v1, before, after, chosen)}
        page = call(f"{base}api/dossier/snapshots/{after['snapshot_id']}/items/reg.R-P54.applicant-result/sources/0")
        call(f"{base}api/dossier/snapshots/{after['snapshot_id']}/letter", "POST",
             {"blocks": [{"block_id": "number", "text": "ที่ SCP-RA 045/2569"}], "note": "walkthrough edit"})
        (out / "reply.docx").write_bytes(call(f"{base}api/dossier/snapshots/{after['snapshot_id']}/export/docx", raw=True))
        (out / "reply.html").write_bytes(call(f"{base}api/dossier/snapshots/{after['snapshot_id']}/export/html", raw=True))
        rendering = render(out, base, after["snapshot_id"]) if args.render else {"render": "NOT_RUN (no --render)"}
        summary = {"url": base, "steps": steps, "skill_evaluation": {k: evaluation[k] for k in (
                       "candidate", "parent", "dev_family", "candidate_errors", "parent_errors", "regressions", "passed")},
                   "before_after_changed": [c["item_id"] for c in diffs["before_after"]["changed_items"]],
                   "before_after_letter_blocks": [c["block_id"] for c in diffs["before_after"]["letter_changes"]],
                   "branch_change_applicant_unchanged": "reg.R-P54.applicant-result" in diffs["branch_15_18"]["unchanged_items"],
                   "replay": {k: {"citations_ok": v["citations_ok"], "rebuild_matches": v["rebuild_matches"],
                                  "skill": v["skill_version"], "citations": len(v["citations"])} for k, v in verify.items()},
                   "sentence_to_page": {"open_url": page["open_url"], "verified": page["verified"],
                                        "quote": page["ref"]["quote"]},
                   "rendering": rendering}
        (out / "diffs.json").write_text(json.dumps(diffs, ensure_ascii=False, indent=1), encoding="utf-8")
        (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
        print(json.dumps(summary, ensure_ascii=False, indent=1))
        ok = (evaluation["passed"] and all(v["citations_ok"] and v["rebuild_matches"] for v in verify.values())
              and summary["branch_change_applicant_unchanged"] and page["verified"])
        return 0 if ok else 1
    finally:
        proc.terminate()
        proc.wait(timeout=10)
        proc.stdout.close()


if __name__ == "__main__":
    sys.exit(main())
