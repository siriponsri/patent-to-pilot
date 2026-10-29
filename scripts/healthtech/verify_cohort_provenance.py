"""Verify evaluator-only HealthTech disclosure provenance for one cohort."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT))
sys.path.insert(0, str(_REPO_ROOT / "src"))

from patent_to_pilot.evaluation.healthtech.provenance import verify_cohort_provenance


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cohort", type=Path, required=True)
    parser.add_argument("--rights-matrix", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = verify_cohort_provenance(args.cohort, rights_matrix_path=args.rights_matrix)
    rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        if args.output.exists():
            parser.error("output already exists; choose a fresh path")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()
