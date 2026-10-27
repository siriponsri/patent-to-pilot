"""Read-only staged-bundle verification; no live/credential operation."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from patent_to_pilot.evaluation.stage_boundary import verify_bundle


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preflight", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("fresh evidence path required")
    preflight = json.loads(args.preflight.read_text(encoding="utf-8"))
    root = args.preflight.parent / "curator-staged-current-inputs"
    rows = preflight["staged_inputs"]
    identifiers = [(r["case_id"], r["state_id"]) for r in rows]
    if not rows or len(set(identifiers)) != len(rows):
        raise ValueError("nonempty unique stage identities required")
    results = [verify_bundle(root / r["case_id"] / r["state_id"], r["files"], allowed_root=root,
                             case_id=r["case_id"], state_id=r["state_id"]) for r in rows]
    report = {"status": "PASS", "verified_bundles": len(results), "results": results,
              "scientific_live_ready": False, "provider_calls": 0,
              "limits": ["No OS worker isolation", "Curator manifest must be trusted",
                         "No semantic-oracle proof or scientific evaluation"]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as out:
        json.dump(report, out, indent=2)
    print(json.dumps({k: v for k, v in report.items() if k != "results"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
