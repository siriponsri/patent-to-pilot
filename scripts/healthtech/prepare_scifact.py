"""Create a provenance receipt for a local, pinned SciFact release."""
from __future__ import annotations

import argparse
from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from patent_to_pilot.evaluation.healthtech.scifact import sha256_file, summarize_release


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data_dir", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--repo-commit", default="68b98a56d93e0f9da0d2aab4e6c3294699a0f72")
    parser.add_argument("--data-url", default="https://scifact.s3-us-west-2.amazonaws.com/release/latest/data.tar.gz")
    parser.add_argument("--license-url", default="https://raw.githubusercontent.com/allenai/scifact/68b98a56d93e0f9da0d2aab4e6c3294699a0f72/LICENSE.md")
    parser.add_argument("--archive", type=Path, help="local release archive used before extraction")
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output already exists; select a fresh receipt path")
    summary = summarize_release(args.data_dir)
    receipt = {
        "status": "LOCAL_FORMAT_VERIFIED",
        "source_repo": "https://github.com/allenai/scifact",
        "repo_commit": args.repo_commit,
        "data_url": args.data_url,
        "license_url": args.license_url,
        "summary": summary,
        "archive": ({"path": str(args.archive), "bytes": args.archive.stat().st_size,
                      "sha256": sha256_file(args.archive)} if args.archive else None),
        "runtime_files": ["corpus.jsonl", "claims_test.jsonl"],
        "evaluator_files": ["claims_train.jsonl", "claims_dev.jsonl"],
        "rights_and_limits": [
            "Claims and annotations are CC BY 4.0; abstracts are ODC-By 1.0; code is Apache 2.0.",
            "The latest release URL is mutable; the local tarball and extracted file hashes are the pinned evidence.",
            "Official test labels are absent, so this receipt does not claim reproduced held-out test scores.",
            "SciFact verifies evidence claims as a component task and is not patent-device gold.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": receipt["status"], "output": str(args.output), **summary}, ensure_ascii=False))


if __name__ == "__main__":
    main()
