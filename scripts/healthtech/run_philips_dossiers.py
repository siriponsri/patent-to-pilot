"""Build local Philips cardiovascular patent-linked dossier artifacts."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys


_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT))
sys.path.insert(0, str(_REPO_ROOT / "src"))

from patent_to_pilot.healthtech.contracts import content_hash
from patent_to_pilot.healthtech.engine import export_markdown, run_dossier, serialize_dossier
from patent_to_pilot.healthtech.history import (
    append_user_edits,
    history_manifest,
    save_version,
    select_version,
    source_view,
)
from patent_to_pilot.healthtech.philips import build_philips_case_inputs, promote_disclosed_links
from patent_to_pilot.healthtech.rights import source_rights_summary


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_summary(dossier) -> dict:
    return {
        "format": "ht-dossier-source-summary-v1",
        "sources": [
            {
                "source_id": source.source.source_id,
                "source_type": source.source.source_type,
                "version": source.source.version_label,
                "sha256": source.source.sha256,
                "uri": source.source.uri,
                "locator": source.source.locator,
                "jurisdiction": source.jurisdiction,
                "source_date": source.source_date.isoformat(),
                "limits": source.source.limits,
                "rights": source_rights_summary(source),
            }
            for source in dossier.sources
        ],
    }


def _case_manifest(dossier, events, manifest, input_data, history_dir: Path) -> dict:
    return {
        "format": "ht-philips-dossier-case-manifest-v1",
        "status": "PUBLIC_SOURCE_ENGINEERING_DRAFT",
        "query_id": dossier.query.query_id,
        "device_id": dossier.query.device_id_canonical,
        "device_name": dossier.query.device_id_raw,
        "policy_id": manifest.policy_id,
        "retrieval_order": "HT-B0b local lexical baseline first; official Philips marking annotation second",
        "patent_input_count": len(input_data.patents),
        "candidate_count": len(dossier.candidates),
        "retrieved_candidate_count": sum(item.association_status == "retrieved_candidate" for item in dossier.candidates),
        "disclosed_link_count": sum(item.association_status == "disclosed_link" for item in dossier.candidates),
        "evidence_count": len(dossier.evidence),
        "disclosure_evidence_ids": [
            evidence.evidence_id
            for evidence in dossier.evidence
            if evidence.evidence_kind == "patent_disclosure"
        ],
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
            "product_display": "BLOCKED_LOCAL"
            if any(
                source.rights is None
                or source.rights.product_display not in {"ALLOWED", "ALLOWED_WITH_ATTRIBUTION"}
                for source in dossier.sources
            )
            else "ALLOWED",
            "redistribution": "BLOCKED_LOCAL"
            if any(
                source.rights is None
                or source.rights.redistribution not in {"ALLOWED", "ALLOWED_WITH_ATTRIBUTION"}
                for source in dossier.sources
            )
            else "ALLOWED",
        },
        "history": history_manifest(history_dir),
        "artifacts": {
            "dossier": "dossier.json",
            "events": "acquisition_events.jsonl",
            "manifest": "engine_manifest.json",
            "source_view": "source-view.json",
            "source_summary": "source-summary.json",
            "resource_receipt": "resource-receipt.json",
            "history": "history",
            "history_manifest": "history/manifest.json",
            "selected_export": "export-v2",
        },
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }


def _write_case_exports(case_dir: Path, dossier, *, purpose: str) -> None:
    _write_json(case_dir / "dossier.json", serialize_dossier(dossier, purpose=purpose))
    for language, filename in (("auto", "dossier.md"), ("en", "dossier.en.md"), ("th", "dossier.th.md")):
        (case_dir / filename).write_text(
            export_markdown(dossier, language=language, purpose=purpose), encoding="utf-8"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cohort", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--rights-matrix", type=Path)
    parser.add_argument("--code-commit", default="working-tree")
    parser.add_argument(
        "--purpose", choices=("local_research", "product_display", "redistribution"), default="local_research"
    )
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output already exists; choose a fresh directory")
    cohort = args.cohort.resolve()
    if not (cohort / "manifest.json").is_file():
        parser.error(f"Philips cohort manifest is missing: {cohort / 'manifest.json'}")

    args.output.mkdir(parents=True)
    cases = build_philips_case_inputs(cohort, rights_matrix_path=args.rights_matrix)
    case_summaries = []
    totals = {"provider_calls": 0, "paid_cost_usd": 0.0, "actual_search_calls": 0, "actual_returned_candidates": 0}

    for query_id, input_data in sorted(cases.items()):
        case_dir = args.output / query_id
        case_dir.mkdir()
        dossier, events, engine_manifest = run_dossier(
            input_data,
            run_id=f"{args.output.name}-{query_id}",
            code_commit=args.code_commit,
        )
        dossier = promote_disclosed_links(dossier, input_data)
        _write_case_exports(case_dir, dossier, purpose=args.purpose)
        _write_json(case_dir / "engine_manifest.json", engine_manifest.model_dump(mode="json"))
        (case_dir / "acquisition_events.jsonl").write_text(
            "".join(json.dumps(event.model_dump(mode="json"), ensure_ascii=False, sort_keys=True) + "\n" for event in events),
            encoding="utf-8",
        )
        _write_json(
            case_dir / "source-view.json",
            source_view(dossier, input_data.query.selected_comparator_source_id, purpose=args.purpose),
        )
        _write_json(case_dir / "source-summary.json", _source_summary(dossier))
        _write_json(
            case_dir / "resource-receipt.json",
            {
                "format": "ht-dossier-resource-receipt-v1",
                "query_id": query_id,
                "provider_calls": engine_manifest.provider_calls,
                "paid_cost_usd": engine_manifest.paid_cost_usd,
                "actual_search_calls": engine_manifest.actual_search_calls,
                "actual_returned_candidates": engine_manifest.actual_returned_candidates,
                "failed_query_ids": engine_manifest.failed_query_ids,
                "stop_reason": engine_manifest.stop_reason,
                "cost_accounting_version": engine_manifest.cost_accounting_version,
            },
        )
        history_dir = case_dir / "history"
        save_version(history_dir, dossier)
        append_user_edits(
            history_dir,
            {
                "local-analyst-review-note": (
                    "Review the product-level Philips marking row against component and claim scope before any decision."
                )
            },
            expected_parent_version=1,
        )
        _write_json(history_dir / "manifest.json", history_manifest(history_dir))
        export_dir = case_dir / "export-v2"
        export_dir.mkdir()
        selected = select_version(history_dir, 2)
        _write_case_exports(export_dir, selected, purpose=args.purpose)
        _write_json(case_dir / "case-manifest.json", _case_manifest(dossier, events, engine_manifest, input_data, history_dir))

        totals["provider_calls"] += engine_manifest.provider_calls
        totals["paid_cost_usd"] += engine_manifest.paid_cost_usd
        totals["actual_search_calls"] += engine_manifest.actual_search_calls
        totals["actual_returned_candidates"] += engine_manifest.actual_returned_candidates
        case_summaries.append(
            {
                "query_id": query_id,
                "output": str(case_dir),
                "candidate_count": len(dossier.candidates),
                "disclosed_link_count": sum(
                    item.association_status == "disclosed_link" for item in dossier.candidates
                ),
                "history_versions": [1, 2],
                "provider_calls": engine_manifest.provider_calls,
                "paid_cost_usd": engine_manifest.paid_cost_usd,
            }
        )
        print(json.dumps(case_summaries[-1], ensure_ascii=False, sort_keys=True))

    _write_json(
        args.output / "manifest.json",
        {
            "format": "ht-philips-dossier-run-v1",
            "status": "PUBLIC_SOURCE_ENGINEERING_DRAFT",
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "cohort": str(cohort),
            "cohort_manifest_sha256": _sha256(cohort / "manifest.json"),
            "code_commit": args.code_commit,
            "purpose": args.purpose,
            "query_ids": sorted(cases),
            "case_count": len(cases),
            **totals,
            "cases": case_summaries,
            "limitations": [
                "Product-level Philips marking rows are disclosed associations, not claim-level semantic judgments.",
                "Unlisted device-patent pairs remain unjudged and are not negatives.",
                "Family identity is unknown and not inferred.",
                "Philips marking material and Google-derived patent text remain local-only.",
            ],
        },
    )
    _write_json(
        args.output / "receipt.json",
        {
            "format": "ht-philips-dossier-resource-receipt-v1",
            "status": "PASS_OFFLINE_ZERO_COST",
            "case_count": len(cases),
            **totals,
            "code_commit": args.code_commit,
            "cohort_manifest_sha256": _sha256(cohort / "manifest.json"),
            "input_hashes": {
                query_id: content_hash(input_data.model_dump(mode="json"))
                for query_id, input_data in sorted(cases.items())
            },
        },
    )


if __name__ == "__main__":
    main()
