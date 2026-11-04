"""Verify a Qwen snapshot against its downloader manifest."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    model = manifest["models"][0]
    expected = {row["path"]: row for row in model["files"]}
    actual = sorted(path for path in args.root.rglob("*") if path.is_file())
    actual_paths = {path.relative_to(args.root).as_posix() for path in actual}
    missing = sorted(set(expected) - actual_paths)
    extra = sorted(actual_paths - set(expected))
    bad = []
    total = 0
    for path in actual:
        relative = path.relative_to(args.root).as_posix()
        row = expected.get(relative)
        if row is None:
            continue
        total += path.stat().st_size
        if path.stat().st_size != row["bytes"] or sha256_file(path) != row["sha256"]:
            bad.append(relative)

    passed = (
        model["repo_id"] == "Qwen/Qwen3-8B"
        and model["revision"] == "b968826d9c46dd6066d109eabc6255188de91218"
        and model["license"] == "apache-2.0"
        and len(actual) == len(expected)
        and total == model["total_bytes"]
        and not missing
        and not extra
        and not bad
    )
    print(json.dumps({
        "status": "PASS_VERIFIED" if passed else "FAIL_VERIFICATION",
        "repo_id": model["repo_id"],
        "revision": model["revision"],
        "license": model["license"],
        "file_count": len(actual),
        "total_bytes": total,
        "missing_files": missing,
        "extra_files": extra,
        "bad_files": bad,
    }, ensure_ascii=False))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
