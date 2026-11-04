"""Explicitly authorized read-only metadata; no model calls or ledger changes."""
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from patent_to_pilot.providers.metadata_observation import run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--key-file", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--allow-credits-if-management", action="store_true")
    args = parser.parse_args()
    try:
        print(run(args.key_file, args.output, allow_credits_if_management=args.allow_credits_if_management))
    except Exception:
        raise SystemExit("OBSERVATION_FAILED_NO_RAW_DETAILS") from None


if __name__ == "__main__":
    main()
