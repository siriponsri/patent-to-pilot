"""Build three local Abbott patent-linked dossier artifacts from a frozen cohort."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT))
sys.path.insert(0, str(_REPO_ROOT / "src"))
from patent_to_pilot.healthtech.abbott import build_abbott_case_inputs, promote_disclosed_links
from patent_to_pilot.healthtech.engine import export_markdown, run_dossier, serialize_dossier
from patent_to_pilot.healthtech.history import append_user_edits, history_manifest, save_version, select_version, source_view
from patent_to_pilot.healthtech.rights import source_rights_summary


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _case_manifest(dossier, events, manifest, input_data, history_dir: Path, protocol: dict | None) -> dict:
    disclosed = sum(item.association_status == "disclosed_link" for item in dossier.candidates)
    retrieved = sum(item.association_status == "retrieved_candidate" for item in dossier.candidates)
    return {
        "status": "PUBLIC_SOURCE_ENGINEERING_DRAFT",
        "query_id": dossier.query.query_id,
        "device_id": dossier.query.device_id_canonical,
        "device_name": dossier.query.device_id_raw,
        "policy_id": manifest.policy_id,
        "retrieval_order": "BM25/SQLite FTS5 lexical baseline first; disclosure annotation second",
        "patent_input_count": len(input_data.patents),
        "candidate_count": len(dossier.candidates),
        "retrieved_candidate_count": retrieved,
        "disclosed_link_count": disclosed,
        "evidence_count": len(dossier.evidence),
        "disclosure_evidence_ids": [e.evidence_id for e in dossier.evidence if e.evidence_kind == "patent_disclosure"],
        "sources": [
            {
                "source_id": source.source.source_id,
                "source_type": source.source.source_type,
                "version": source.source.version_label,
                "sha256": source.source.sha256,
                "uri": source.source.uri,
                "locator": source.source.locator,
                "limits": source.source.limits,
            }
            for source in dossier.sources
        ],
        "attempts": [
            {
                "step_id": event.step_id,
                "action_type": event.action_type,
                "status": "failed" if event.errors else "completed",
                "search_calls": event.search_calls,
                "returned_candidates": event.returned_candidates,
                "errors": event.errors,
                "cost_basis": event.cost_basis,
                "paid_cost_usd": event.paid_cost_usd,
            }
            for event in events
        ],
        "resources": {
            "actual_search_calls": manifest.actual_search_calls,
            "actual_returned_candidates": manifest.actual_returned_candidates,
            "elapsed_seconds": manifest.elapsed_seconds,
            "provider_calls": manifest.provider_calls,
            "paid_cost_usd": manifest.paid_cost_usd,
            "accounting": manifest.cost_accounting_version,
        },
        "gaps": dossier.unresolved_items,
        "rights_boundary": {
            "sources": [source_rights_summary(source) for source in dossier.sources],
            "product_display": "BLOCKED_LOCAL" if any(
                source.rights is None or source.rights.product_display not in {"ALLOWED", "ALLOWED_WITH_ATTRIBUTION"}
                for source in dossier.sources
            ) else "ALLOWED",
            "redistribution": "BLOCKED_LOCAL" if any(
                source.rights is None or source.rights.redistribution not in {"ALLOWED", "ALLOWED_WITH_ATTRIBUTION"}
                for source in dossier.sources
            ) else "ALLOWED",
        },
        "cohort_freeze": None if protocol is None else {
            "status": protocol["status"],
            "protocol_sha256": protocol.get("protocol_sha256"),
            "eligible_query_ids": protocol["eligible_query_ids"],
            "universe_patents": protocol["counts"]["universe_patents"],
            "unjudged_distractor_pairs": protocol["counts"]["unjudged_distractor_pairs"],
            "split_status": protocol["split"]["final_holdout"],
        },
        "history": history_manifest(history_dir),
        "artifacts": {
            "dossier": "dossier.json",
            "events": "acquisition_events.jsonl",
            "manifest": "engine_manifest.json",
            "source_view": "source-view.json",
            "history": "history",
            "selected_export": "export-v2",
        },
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cohort", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--protocol", type=Path)
    parser.add_argument("--rights-matrix", type=Path)
    parser.add_argument("--code-commit", default="working-tree")
    parser.add_argument("--purpose", choices=("local_research", "product_display", "redistribution"), default="local_research")
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output already exists; choose a fresh directory")
    args.output.mkdir(parents=True)
    cases = build_abbott_case_inputs(args.cohort, rights_matrix_path=args.rights_matrix)
    protocol = json.loads(args.protocol.read_text(encoding="utf-8")) if args.protocol else None
    for query_id, input_data in sorted(cases.items()):
        case_dir = args.output / query_id
        case_dir.mkdir()
        dossier, events, engine_manifest = run_dossier(input_data, run_id=f"{args.output.name}-{query_id}", code_commit=args.code_commit)
        dossier = promote_disclosed_links(dossier, input_data)
        _write_json(case_dir / "dossier.json", serialize_dossier(dossier, purpose=args.purpose))
        _write_json(case_dir / "engine_manifest.json", engine_manifest.model_dump(mode="json"))
        (case_dir / "acquisition_events.jsonl").write_text(
            "".join(json.dumps(event.model_dump(mode="json"), ensure_ascii=False, sort_keys=True) + "\n" for event in events),
            encoding="utf-8",
        )
        for language, filename in (("auto", "dossier.md"), ("en", "dossier.en.md"), ("th", "dossier.th.md")):
            (case_dir / filename).write_text(export_markdown(dossier, language=language, purpose=args.purpose), encoding="utf-8")
        source_id = input_data.query.selected_comparator_source_id
        _write_json(case_dir / "source-view.json", source_view(dossier, source_id, purpose=args.purpose))
        history_dir = case_dir / "history"
        save_version(history_dir, dossier)
        edited = append_user_edits(
            history_dir,
            {"review-note": "Review product-level disclosure against component and claim scope before any decision."},
            expected_parent_version=1,
        )
        export_dir = case_dir / "export-v2"
        export_dir.mkdir()
        selected = select_version(history_dir, 2)
        _write_json(export_dir / "dossier.json", serialize_dossier(selected, purpose=args.purpose))
        (export_dir / "dossier.md").write_text(export_markdown(selected, purpose=args.purpose), encoding="utf-8")
        (export_dir / "dossier.en.md").write_text(export_markdown(selected, language="en", purpose=args.purpose), encoding="utf-8")
        (export_dir / "dossier.th.md").write_text(export_markdown(selected, language="th", purpose=args.purpose), encoding="utf-8")
        _write_json(case_dir / "case-manifest.json", _case_manifest(dossier, events, engine_manifest, input_data, history_dir, protocol))
        print(json.dumps({
            "query_id": query_id,
            "candidates": len(dossier.candidates),
            "disclosed_links": sum(item.association_status == "disclosed_link" for item in dossier.candidates),
            "output": str(case_dir),
        }, ensure_ascii=False))


if __name__ == "__main__":
    main()
