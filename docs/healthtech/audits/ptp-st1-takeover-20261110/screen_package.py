"""Bounded publication preflight; heuristic secret scan is not a security audit."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[4]
RUN = Path(__file__).resolve().parent
package = ROOT / "docs/healthtech/audits/ptp-three-study-planning-20261110"
files = json.loads((package / "package-files.json").read_text())["files"]
files += [str(p.relative_to(ROOT)).replace("\\", "/") for p in package.glob("*.json")]
files += [str(p.relative_to(ROOT)).replace("\\", "/") for p in RUN.glob("*") if p.is_file()]
files += ["scripts/healthtech/build_curator_bundle.py", "tests/test_curator_bundle.py",
          "docs/healthtech/research/PTP_SACR_VS_GRAPH_CONTRIBUTION_ASSESSMENT_20261110_EN.md",
          "docs/healthtech/audits/ptp-dapfam-dual-track-handoff-20261110/paper-move-manifest.json"]
files = sorted(set(files) - {str((RUN / "publication-screen.json").relative_to(ROOT)).replace("\\", "/")})
findings, hashes = [], {}
for name in files:
    path = ROOT / name
    assert path.suffix in {".md", ".json", ".py"}, name
    raw = path.read_bytes()
    assert len(raw) < 2_000_000, name
    text = raw.decode("utf-8-sig")
    if path.suffix == ".json":
        json.loads(text)
    for pattern in (r"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----", r"\bgh[pousr]_[A-Za-z0-9]{30,}",
                    r"\bsk-[A-Za-z0-9]{30,}"):
        if re.search(pattern, text):
            findings.append(name)
    hashes[name] = hashlib.sha256(raw).hexdigest()
assert not findings, findings
receipt = {"status": "ALLOWLIST_AND_HEURISTIC_SCAN_PASS", "files": files, "sha256": hashes,
           "limits": "Authored code/docs/aggregate receipts only; heuristic scan not full security audit. Owner external handoff, PDFs, corpora, model outputs and labels excluded."}
(RUN / "publication-screen.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"status": receipt["status"], "files": len(files)}))
