"""Run one local, rights-aware G5 task workflow over a real dossier.

This is an engineering dry-run, not a participant or commercial study. It
never loads credentials, calls a provider, or copies restricted source payloads
into the sanitized task receipt.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import argparse
import hashlib
import json
from pathlib import Path
from time import perf_counter
import sys
from typing import Any, Callable, TypeVar

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from patent_to_pilot.healthtech.contracts import DossierVersion
from patent_to_pilot.healthtech.engine import export_markdown, serialize_dossier
from patent_to_pilot.healthtech.history import (
    append_user_edits,
    history_manifest,
    save_version,
    select_version,
    source_view,
)
from patent_to_pilot.healthtech.rights import RightsBoundaryError


T = TypeVar("T")
EXPORT_PURPOSES = ("local_research", "product_display", "redistribution")


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run_step(steps: list[dict[str, Any]], name: str, action: Callable[[], T]) -> T:
    started = perf_counter()
    try:
        value = action()
    except Exception as exc:
        steps.append(
            {
                "name": name,
                "status": "FAIL",
                "elapsed_seconds": perf_counter() - started,
                "error_type": type(exc).__name__,
            }
        )
        raise
    steps.append(
        {
            "name": name,
            "status": "PASS",
            "elapsed_seconds": perf_counter() - started,
        }
    )
    return value


def _base_receipt(
    *,
    dossier: DossierVersion | None,
    input_name: str,
    purpose: str,
    steps: list[dict[str, Any]],
    started_at_utc: str,
    status: str,
) -> dict[str, Any]:
    return {
        "format": "ht-g5-pilot-task-receipt-v1",
        "status": status,
        "started_at_utc": started_at_utc,
        "input_name": input_name,
        "purpose": purpose,
        "case": None
        if dossier is None
        else {
            "query_id": dossier.query.query_id,
            "device_id_canonical": dossier.query.device_id_canonical,
            "company": dossier.query.company_metadata,
        },
        "participant_code": "ENGINEERING_DRY_RUN",
        "observed_user_validation": False,
        "observed_commercial_validation": False,
        "provider_calls": 0,
        "network_calls": 0,
        "paid_cost_usd": 0.0,
        "steps": steps,
        "failures": [],
        "not_run": [
            "participant elapsed time",
            "manual support time",
            "user-reported next decision",
            "repeat use, purchase, willingness to pay, or commercial demand",
        ],
    }


def run_pilot_task(
    dossier_path: Path,
    output_dir: Path,
    *,
    source_id: str,
    field: str | None = None,
    purpose: str = "local_research",
    seeded_key: str = "readiness-decision",
    seeded_value: str = "Seeded issue: source locator needs review.",
    correction_value: str = "Corrected: request component and claim-level review for disclosed links.",
) -> dict[str, Any]:
    """Execute one bounded local task and return a sanitized receipt."""
    if purpose not in EXPORT_PURPOSES:
        raise ValueError(f"purpose must be one of {EXPORT_PURPOSES}")
    if output_dir.exists():
        raise ValueError("output already exists; choose a fresh directory")

    output_dir.mkdir(parents=True, exist_ok=False)
    steps: list[dict[str, Any]] = []
    started_at_utc = datetime.now(timezone.utc).isoformat()
    started = perf_counter()
    dossier: DossierVersion | None = None
    try:
        dossier = _run_step(
            steps,
            "load_and_validate_dossier",
            lambda: DossierVersion.model_validate_json(
                dossier_path.read_text(encoding="utf-8")
            ),
        )
        if dossier.version != 1 or dossier.parent_version is not None:
            raise ValueError("pilot task requires an unedited version-1 dossier")
        if dossier.query.brief.data_class != "public":
            raise ValueError("pilot task requires a public dossier")
        if any(source.synthetic for source in dossier.sources):
            raise ValueError("pilot task rejects synthetic sources")

        inspected_source = _run_step(
            steps,
            "inspect_allowed_source_field",
            lambda: source_view(dossier, source_id, field, purpose=purpose),
        )

        candidate_counts = Counter(item.association_status for item in dossier.candidates)
        source_inspection = {
            "source_id": inspected_source["source_id"],
            "source_type": inspected_source["source_type"],
            "uri": inspected_source["uri"],
            "revision": inspected_source["revision"],
            "sha256": inspected_source["sha256"],
            "field": field,
            "payload_keys": sorted(inspected_source["payload"])
            if isinstance(inspected_source["payload"], dict)
            else [],
            "rights": inspected_source["rights"],
        }
        _write_json(output_dir / "source_inspection.json", source_inspection)

        history_dir = output_dir / "history"
        seeded = dossier.model_copy(update={"user_edits": {seeded_key: seeded_value}})
        _run_step(steps, "publish_seeded_version", lambda: save_version(history_dir, seeded))
        corrected = _run_step(
            steps,
            "append_correction_version",
            lambda: append_user_edits(
                history_dir,
                {seeded_key: correction_value},
                expected_parent_version=1,
            ),
        )
        manifest = _run_step(steps, "verify_history_chain", lambda: history_manifest(history_dir))
        if [item["version"] for item in manifest["versions"]] != [1, 2]:
            raise RuntimeError("history chain did not produce versions 1 and 2")
        if corrected.parent_version != 1 or corrected.user_edits.get(seeded_key) != correction_value:
            raise RuntimeError("correction was not attached to version 2")
        _write_json(output_dir / "history_manifest.json", manifest)

        selected = _run_step(
            steps,
            "select_corrected_version",
            lambda: select_version(history_dir, 2),
        )
        export_dir = output_dir / "export-v2"
        export_dir.mkdir(parents=True, exist_ok=False)
        export_payload = _run_step(
            steps,
            "build_rights_aware_json_export",
            lambda: serialize_dossier(selected, purpose=purpose),
        )
        _write_json(export_dir / "dossier.json", export_payload)
        (export_dir / "dossier.en.md").write_text(
            export_markdown(selected, language="en", purpose=purpose),
            encoding="utf-8",
        )
        (export_dir / "dossier.th.md").write_text(
            export_markdown(selected, language="th", purpose=purpose),
            encoding="utf-8",
        )

        blocked_source_ids = [
            source.source.source_id
            for source in selected.sources
            if source.rights is not None and source.rights.product_display == "BLOCKED_LOCAL"
        ]
        if export_payload["version"] != 2 or export_payload["user_edits"].get(seeded_key) != correction_value:
            raise RuntimeError("corrected export does not point to version 2")

        def check_external_projection() -> dict[str, Any]:
            try:
                external_payload = serialize_dossier(selected, purpose="product_display")
            except RightsBoundaryError:
                return {
                    "status": "BLOCKED_LOCAL",
                    "payload_written": False,
                    "blocked_source_ids": blocked_source_ids,
                }
            external_sources = {
                source["source"]["source_id"]: source
                for source in external_payload["sources"]
            }
            omitted = all(
                external_sources[source_id].get("payload") == {}
                for source_id in blocked_source_ids
            )
            if not omitted:
                raise RuntimeError("blocked source payload appeared in external export")
            return {
                "status": "PASS",
                "payload_written": False,
                "blocked_source_ids": blocked_source_ids,
            }

        external_projection = _run_step(
            steps,
            "verify_external_projection_boundary",
            check_external_projection,
        )

        artifact_paths = [
            output_dir / "source_inspection.json",
            output_dir / "history_manifest.json",
            export_dir / "dossier.json",
            export_dir / "dossier.en.md",
            export_dir / "dossier.th.md",
        ]
        receipt = _base_receipt(
            dossier=dossier,
            input_name=dossier_path.name,
            purpose=purpose,
            steps=steps,
            started_at_utc=started_at_utc,
            status="PASS_OFFLINE_ENGINEERING_TASK",
        )
        receipt.update(
            {
                "engineering_execution_seconds": perf_counter() - started,
                "candidate_counts": {
                    "disclosed_link": candidate_counts.get("disclosed_link", 0),
                    "retrieved_candidate": candidate_counts.get("retrieved_candidate", 0),
                    "total": len(dossier.candidates),
                },
                "source_inspection": {
                    "source_id": source_id,
                    "field": field,
                    "status": "PASS",
                    "rights_checked": True,
                },
                "seeded_issue": {"key": seeded_key, "corrected": True},
                "history": {
                    "versions": [1, 2],
                    "selected_version": 2,
                    "parent_version": selected.parent_version,
                    "user_edit_keys": sorted(selected.user_edits),
                },
                "export": {
                    "purpose": purpose,
                    "languages": ["json", "en", "th"],
                    "files": [path.relative_to(output_dir).as_posix() for path in artifact_paths[2:]],
                },
                "external_projection": external_projection,
                "artifact_sha256": {
                    path.relative_to(output_dir).as_posix(): _sha256_file(path)
                    for path in artifact_paths
                },
            }
        )
        _write_json(output_dir / "task_receipt.json", receipt)
        return receipt
    except Exception as exc:
        receipt = _base_receipt(
            dossier=dossier,
            input_name=dossier_path.name,
            purpose=purpose,
            steps=steps,
            started_at_utc=started_at_utc,
            status="FAILED_OFFLINE_ENGINEERING_TASK",
        )
        receipt.update(
            {
                "engineering_execution_seconds": perf_counter() - started,
                "failure_stage": steps[-1]["name"] if steps else "initialization",
                "failure_type": type(exc).__name__,
                "failures": [type(exc).__name__],
            }
        )
        _write_json(output_dir / "task_receipt.json", receipt)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dossier", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--field")
    parser.add_argument("--purpose", choices=EXPORT_PURPOSES, default="local_research")
    parser.add_argument("--seeded-key", default="readiness-decision")
    parser.add_argument("--seeded-value", default="Seeded issue: source locator needs review.")
    parser.add_argument(
        "--correction-value",
        default="Corrected: request component and claim-level review for disclosed links.",
    )
    args = parser.parse_args()
    receipt = run_pilot_task(
        args.dossier,
        args.output,
        source_id=args.source_id,
        field=args.field,
        purpose=args.purpose,
        seeded_key=args.seeded_key,
        seeded_value=args.seeded_value,
        correction_value=args.correction_value,
    )
    print(
        json.dumps(
            {
                "status": receipt["status"],
                "output": str(args.output),
                "selected_version": receipt.get("history", {}).get("selected_version"),
                "engineering_execution_seconds": receipt["engineering_execution_seconds"],
                "provider_calls": receipt["provider_calls"],
                "paid_cost_usd": receipt["paid_cost_usd"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
