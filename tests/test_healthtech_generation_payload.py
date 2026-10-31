from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from patent_to_pilot.healthtech.generation_payload import (
    GenerationPayloadError,
    build_generation_messages,
    build_rights_cleared_paired_payload,
    validate_generation_output,
)


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "healthtech" / "build_qwen_evidence_pack.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _synthetic_pack(tmp_path: Path) -> dict:
    builder = _load(SCRIPT, "qwen_pack_builder_payload")
    dossier_root = tmp_path / "dossiers"
    for index, case_id in enumerate(builder.CASE_ORDER, start=1):
        source_id = f"source-{index}"
        case_dir = dossier_root / case_id
        case_dir.mkdir(parents=True)
        dossier = {
            "query": {
                "query_id": case_id,
                "device_id_canonical": case_id,
                "device_id_raw": case_id,
                "jurisdiction": "US",
                "brief": "Synthetic test",
                "technical_description": "Synthetic device",
                "features_of_interest": ["feature"],
                "user_questions": ["What is supported?"],
                "evidence_cutoff": "2026-10-27",
                "permitted_inputs": [source_id],
                "selected_comparator_source_id": source_id,
            },
            "evidence": [{
                "evidence_id": f"evidence-{index}",
                "evidence_kind": "regulatory_record",
                "jurisdiction": "US",
                "locator": "field:trade_name",
                "payload_hash": "a" * 64,
                "source_date": "2026-10-27",
                "source_id": source_id,
                "source_version": "test",
                "statement": "trade_name: Synthetic",
                "structured_field": "trade_name",
                "structured_value": "Synthetic",
                "support_basis": "Supplied source field",
                "verification_status": "field_value_checked",
            }],
            "candidates": [{
                "association_status": "retrieved_candidate",
                "disclosure_evidence_id": None,
                "family_id": None,
                "family_source_id": None,
                "patent_id_canonical": f"US{index}B2",
                "patent_id_raw": f"US{index}B2",
                "retrieval_action_ids": ["step-1"],
                "scores": {"score": 1.0},
                "source_id": source_id,
                "source_revision": "test",
            }],
            "sources": [{
                "jurisdiction": "US",
                "payload": {"secret_payload": "must not be copied"},
                "rights": {
                    "rights_id": "test-rights",
                    "local_evaluation": "ALLOWED_LOCAL_RESEARCH",
                    "product_display": "BLOCKED_LOCAL",
                    "redistribution": "BLOCKED_LOCAL",
                    "displayable_fields": [],
                },
                "source": {
                    "source_id": source_id,
                    "source_type": "regulatory_record",
                    "version_label": "test",
                    "sha256": "b" * 64,
                    "uri": "https://example.invalid/source",
                    "locator": "field:trade_name",
                    "record_id": source_id,
                    "retrieved_at": "2026-10-27T00:00:00",
                    "limits": ["synthetic"],
                },
                "source_date": "2026-10-27",
                "synthetic": True,
            }],
            "unresolved_items": ["Synthetic fixture only"],
        }
        (case_dir / "dossier.json").write_text(json.dumps(dossier), encoding="utf-8")
    return builder.build_pack(dossier_root, tmp_path / "pack.json", captured_at_utc="2026-10-31T00:00:00Z")


def test_rights_cleared_payload_uses_shared_messages_and_excludes_raw_payload(tmp_path):
    pack = _synthetic_pack(tmp_path)
    payload = build_rights_cleared_paired_payload(
        pack,
        provider="openrouter",
        model="qwen/qwen3-32b",
        route="DeepInfra",
    )
    assert payload["decision"] == "ALLOWED"
    assert payload["manifest"]["manifest_sha256"]
    assert all("messages" not in case for case in payload["manifest"]["cases"])
    assert payload["cases"][0]["messages"] == build_generation_messages(pack, pack["cases"][0])
    assert "secret_payload" not in json.dumps(payload["cases"], ensure_ascii=False)


def test_non_synthetic_blocked_rights_cannot_form_remote_payload(tmp_path):
    pack = _synthetic_pack(tmp_path)
    pack["cases"][0]["sources"][0]["synthetic"] = False
    with pytest.raises(GenerationPayloadError, match="not rights-cleared"):
        build_rights_cleared_paired_payload(
            pack,
            provider="openrouter",
            model="qwen/qwen3-32b",
            route="DeepInfra",
        )


def test_candidate_outside_visible_preview_is_rejected(tmp_path):
    pack = _synthetic_pack(tmp_path)
    case = pack["cases"][0]
    extra = dict(case["candidates"][0])
    extra["patent_id_canonical"] = "US999B2"
    extra["patent_id_raw"] = "US999B2"
    case["candidates"] = [*case["candidates"], *[dict(extra, patent_id_canonical=f"US99{i}B2", patent_id_raw=f"US99{i}B2") for i in range(1, 7)]]
    hidden = case["candidates"][-1]
    with pytest.raises(ValueError, match="outside model-visible preview"):
        validate_generation_output({
            "device_id": case["query"]["device_id_canonical"],
            "device_name": case["query"]["device_id_raw"],
            "findings": [{
                "record_type": "candidate",
                "record_id": hidden["patent_id_canonical"],
                "source_id": hidden["source_id"],
                "locator": f"candidate:{hidden['patent_id_canonical']}",
                "classification": "retrieved_candidate",
                "summary": "Hidden candidate",
                "support_basis": "Synthetic source",
            }],
            "unresolved": [],
        }, case, max_findings=6)

def test_disclosed_candidate_requires_patent_disclosure_evidence(tmp_path):
    pack = _synthetic_pack(tmp_path)
    case = pack["cases"][0]
    case["candidates"][0]["association_status"] = "disclosed_link"
    case["candidates"][0]["disclosure_evidence_id"] = "missing-disclosure"
    with pytest.raises(ValueError, match="source-backed disclosure evidence"):
        validate_generation_output({
            "device_id": case["query"]["device_id_canonical"],
            "device_name": case["query"]["device_id_raw"],
            "findings": [],
            "unresolved": [],
        }, case, max_findings=6)\n