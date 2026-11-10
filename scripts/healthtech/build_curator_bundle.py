"""Build code-only curator archive, retaining exact historically bound source bytes.

Does not deploy, read datasets, run staging, or alter the trusted identity report.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile

BUILDER = "src/patent_to_pilot/evaluation/dapfam_acquisition.py"
REPORT = "docs/healthtech/audits/ptp-method-first-r1-vectors-20261110/vector-identity.json"
WRAPPER = "docs/healthtech/audits/ptp-solo-runtime-20261110/owner-stage-mtm.sh"


def restore_bound_bytes(raw: bytes, expected: str) -> bytes:
    """Accept only exact bytes or a proved newline-only reconstruction."""
    candidates = [raw, raw.replace(b"\r\n", b"\n"),
                  raw.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")]
    for value in candidates:
        if hashlib.sha256(value).hexdigest() == expected:
            return value
    raise ValueError("historically bound source cannot be reconstructed from this revision")


def build(revision: str, output: Path) -> dict:
    if output.exists():
        raise FileExistsError("preserve existing bundle")
    commit = subprocess.check_output(["git", "rev-parse", revision + "^{commit}"]).decode().strip()
    paths = ["src", "scripts/healthtech/stage_mtm_metadata.py",
             "scripts/healthtech/prepare_mtm_dev_assets.py", REPORT, WRAPPER]
    raw = subprocess.check_output(["git", "-c", "core.autocrlf=false", "-c", "core.eol=lf",
                                   "archive", "--format=tar", commit, *paths])
    stream = io.BytesIO()
    with tarfile.open(fileobj=io.BytesIO(raw)) as source, tarfile.open(fileobj=stream, mode="w") as dest:
        report_bytes = source.extractfile(REPORT).read()
        expected = json.loads(report_bytes)["identity"]["corpus"]["passage_builder_source_sha256"]
        original = source.extractfile(BUILDER).read()
        restored = restore_bound_bytes(original, expected)
        for member in source.getmembers():
            content = source.extractfile(member).read() if member.isfile() else None
            if member.name == BUILDER:
                content = restored
                member.size = len(content)
            dest.addfile(member, io.BytesIO(content) if content is not None else None)
    payload = stream.getvalue()
    with output.open("xb") as handle:
        handle.write(payload)
    return {"commit": commit, "archive_sha256": hashlib.sha256(payload).hexdigest(),
            "archive_bytes": len(payload), "report_sha256": hashlib.sha256(report_bytes).hexdigest(),
            "builder_git_blob_sha256": hashlib.sha256(original).hexdigest(),
            "builder_packaged_sha256": hashlib.sha256(restored).hexdigest(),
            "transformation": "none" if original == restored else "newline-only-exact-hash-reconstruction",
            "staging_executed": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.revision, args.output), indent=2))
