"""Initialize and append local dossier versions without a server."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from patent_to_pilot.healthtech.contracts import DossierVersion
from patent_to_pilot.healthtech.engine import export_markdown
from patent_to_pilot.healthtech.history import append_user_edits, history_manifest, save_version, select_version


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
    edit.add_argument("--expected-version", type=int, help="require this version to remain the current parent")
    export = sub.add_parser("export")
    export.add_argument("history_dir", type=Path)
    export.add_argument("output_dir", type=Path)
    export.add_argument("--version", type=int, help="export this version; defaults to the latest")
    manifest = sub.add_parser("manifest")
    manifest.add_argument("history_dir", type=Path)
    args = parser.parse_args()
    if args.command == "init":
        dossier = DossierVersion.model_validate_json(args.dossier.read_text(encoding="utf-8"))
        path = save_version(args.history_dir, dossier)
        print(json.dumps({"status": "INITIALIZED", "path": str(path), "version": dossier.version}))
    elif args.command == "edit":
        dossier = append_user_edits(args.history_dir, {args.key: args.value}, expected_parent_version=args.expected_version)
        print(json.dumps({"status": "VERSION_CREATED", "version": dossier.version, "parent_version": dossier.parent_version}))
    elif args.command == "export":
        if args.output_dir.exists():
            parser.error("output already exists; choose a fresh directory")
        dossier = select_version(args.history_dir, args.version)
        args.output_dir.mkdir(parents=True)
        (args.output_dir / "dossier.json").write_text(dossier.model_dump_json(indent=2) + "\n", encoding="utf-8")
        (args.output_dir / "dossier.md").write_text(export_markdown(dossier), encoding="utf-8")
        (args.output_dir / "dossier.en.md").write_text(export_markdown(dossier, language="en"), encoding="utf-8")
        (args.output_dir / "dossier.th.md").write_text(export_markdown(dossier, language="th"), encoding="utf-8")
        print(json.dumps({"status": "EXPORTED", "version": dossier.version, "output": str(args.output_dir)}))
    else:
        print(json.dumps(history_manifest(args.history_dir), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
