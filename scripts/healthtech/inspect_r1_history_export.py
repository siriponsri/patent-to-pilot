"""Check a sanitized all-attempt export offline; never write a budget journal."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from patent_to_pilot.providers.history_export import inspect_history_export


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        raw = json.loads(args.export.read_text(encoding="utf-8"))
        result = inspect_history_export(raw)
        with args.output.open("x", encoding="utf-8") as handle:
            json.dump(result, handle, indent=2)
            handle.write("\n")
    except (OSError, ValueError, TypeError):
        raise SystemExit("Recovery check failed; no journal or authorization was changed") from None
    print(result["status"])


if __name__ == "__main__":
    main()
