"""Run a local public/synthetic dossier without network, models or secrets."""
from pathlib import Path
import argparse
import json
import subprocess
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
from patent_to_pilot.healthtech.engine import DossierInput, export_markdown, run_dossier


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input",type=Path)
    parser.add_argument("output",type=Path,help="fresh directory; existing outputs are never overwritten")
    args=parser.parse_args()
    data=DossierInput.model_validate_json(args.input.read_text(encoding="utf-8"))
    if args.output.exists():
        parser.error("output already exists; select a fresh directory")
    repo=Path(__file__).resolve().parents[2]
    try:
        commit=subprocess.check_output(["git","rev-parse","HEAD"],cwd=repo,text=True).strip()
        dirty=bool(subprocess.check_output(["git","status","--porcelain","--untracked-files=no"],cwd=repo,text=True).strip())
        if dirty:commit += "+dirty"
    except (OSError,subprocess.CalledProcessError):
        commit="unknown"
    dossier,events,manifest=run_dossier(data,run_id=args.output.name,code_commit=commit)
    # Exclusive mkdir: a concurrent run cannot overwrite an existing project.
    args.output.mkdir(parents=True,exist_ok=False)
    (args.output/"dossier.json").write_text(dossier.model_dump_json(indent=2)+"\n",encoding="utf-8")
    (args.output/"dossier.md").write_text(export_markdown(dossier),encoding="utf-8")
    (args.output/"dossier.en.md").write_text(export_markdown(dossier, language="en"),encoding="utf-8")
    (args.output/"dossier.th.md").write_text(export_markdown(dossier, language="th"),encoding="utf-8")
    (args.output/"acquisition_events.jsonl").write_text("\n".join(e.model_dump_json() for e in events)+"\n",encoding="utf-8")
    (args.output/"manifest.json").write_text(manifest.model_dump_json(indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":"ENGINEERING_DRAFT","output":str(args.output),"candidates":len(dossier.candidates),
                      "provider_calls":0,"paid_cost_usd":0,"stop_reason":manifest.stop_reason}))


if __name__=="__main__":
    main()
