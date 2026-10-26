"""Run the bounded offline G10 comparison slice."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from patent_to_pilot.evaluation.comparison import OfflineComparisonRunner  # noqa: E402


DEFAULT_RUN_ID = "g10-correctness-search-2026-10-27-r1"
DEFAULT_OUTPUT = ROOT / "results" / "development" / DEFAULT_RUN_ID


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the bounded offline G10 correctness/search comparison.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--run-id", default=DEFAULT_RUN_ID)
    args = parser.parse_args()
    output = args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir
    runner = OfflineComparisonRunner(run_id=args.run_id)
    report = runner.run()
    runner.write_reports(report, output)
    print(f"run_id={report['run_id']}")
    print(f"status={report['status']}")
    print(f"wrote {output / 'comparison.json'}")
    print(f"wrote {output / 'comparison.md'}")
    print(f"wrote {output / 'before-after-diff.json'}")
    print(f"wrote {output / 'validator-results.json'}")
    print(f"wrote {output / 'method-traces.json'}")
    print(f"wrote {output / 'search-pool-readiness.json'}")
    print(f"wrote {output / 'candidate-source-manifest.json'}")
    print(f"wrote {output / 'evidence-manifest.json'}")
    print(f"states={len(report['state_ids'])} methods={len(report['methods'])} mock_calls={report['accounting']['mock_provider_calls']}")


if __name__ == "__main__":
    main()
