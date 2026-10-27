"""Print one pinned dossier source or field for local inspection."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from patent_to_pilot.healthtech.contracts import DossierVersion
from patent_to_pilot.healthtech.history import source_view


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dossier", type=Path)
    parser.add_argument("source_id")
    parser.add_argument("--field")
    args = parser.parse_args()
    dossier = DossierVersion.model_validate_json(args.dossier.read_text(encoding="utf-8"))
    print(json.dumps(source_view(dossier, args.source_id, args.field), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
