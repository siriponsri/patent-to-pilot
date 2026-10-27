"""Initialize and append local dossier versions without a server."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from patent_to_pilot.healthtech.contracts import DossierVersion
from patent_to_pilot.healthtech.history import append_user_edits, history_manifest, load_versions, save_version


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init")
    init.add_argument("dossier", type=Path)
    init.add_argument("history_dir", type=Path)
    edit = sub.add_parser("edit")
    edit.add_argument("history_dir", type=Path)
    edit.add_argument("--key", required=True)
    edit.add_argument("--value", required=True)
    manifest = sub.add_parser("manifest")
    manifest.add_argument("history_dir", type=Path)
    args = parser.parse_args()
    if args.command == "init":
        dossier = DossierVersion.model_validate_json(args.dossier.read_text(encoding="utf-8"))
        path = save_version(args.history_dir, dossier)
        print(json.dumps({"status": "INITIALIZED", "path": str(path), "version": dossier.version}))
    elif args.command == "edit":
        dossier = append_user_edits(args.history_dir, {args.key: args.value})
        print(json.dumps({"status": "VERSION_CREATED", "version": dossier.version, "parent_version": dossier.parent_version}))
    else:
        print(json.dumps(history_manifest(args.history_dir), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
