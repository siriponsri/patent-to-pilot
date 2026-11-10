"""Trusted-curator command: reads protected labels; not a development-agent task.

Use only in the authorized curator environment. Keep source and protected output
outside development mounts. This command does not establish OS isolation.
It refuses existing destinations and prints counts/status only.
"""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from patent_to_pilot.evaluation.mtm_staging import stage_metadata  # noqa: E402
from patent_to_pilot.research.mtm_runtime import InputBoundaryError  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--dev-eval-root", type=Path, required=True)
    parser.add_argument("--protected-root", type=Path, required=True)
    parser.add_argument("--trusted-curator", action="store_true", required=True,
                        help="explicit operator acknowledgement, not an access-control mechanism")
    args = parser.parse_args()
    try:
        receipt = stage_metadata(args.source, args.runtime_root, args.dev_eval_root, args.protected_root)
    except (InputBoundaryError, OSError):
        print("Staging failed; preserve this attempt and inspect it in the curator environment.", file=sys.stderr)
        return 1
    print(json.dumps({"status": receipt["status"],
                      "counts": {s: m["queries"] for s, m in receipt["runtime"].items()}}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
