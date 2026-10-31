"""Validate completed vector bundles and print compact binding summaries."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from patent_to_pilot.evaluation.healthtech.vector_artifacts import load_vector_bundle, sha256_file


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundles", type=Path, nargs="+")
    args = parser.parse_args()
    payload = []
    for path in args.bundles:
        bundle = load_vector_bundle(path)
        payload.append({
            "path": str(path.resolve()),
            "manifest_sha256": sha256_file(path / "manifest.json"),
            "status": bundle.manifest["status"],
            "rows": bundle.manifest["row_count"],
            "dimension": bundle.manifest["dimension"],
            "shards": len(bundle.manifest["shards"]),
            "model": bundle.manifest["model"],
            "config": bundle.manifest["config"],
        })
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
