import json
from datetime import datetime, timezone

import pytest

from test_healthtech_api_generation import _load_fixture_builder, MockGenerationTransport
from patent_to_pilot.healthtech.api_generation import OpenRouterQwenGenerationRunner, APIGenerationError, pricing_from_snapshot
from patent_to_pilot.healthtech.b4_live import B4Pricing, conservative_request_bound_usd
from patent_to_pilot.healthtech.generation_payload import build_generation_messages, build_rights_cleared_paired_payload, sha256_json, GenerationPayloadError
from patent_to_pilot.providers import MockHTTPResponse
from patent_to_pilot.providers.round1 import Round1ProjectBudget


def pricing():
    return B4Pricing(model="qwen/qwen3-32b", upstream_provider="DeepInfra", snapshot_sha256="a" * 64,
        snapshot_utc=datetime.now(timezone.utc).isoformat(), prompt_usd_per_million=.08,
        completion_usd_per_million=.28, max_price_prompt=.08, max_price_completion=.28)


def runner(tmp_path, factory):
    price = pricing()
    budget = Round1ProjectBudget(tmp_path / "mock.sqlite3", model_provider_map={price.model: price.upstream_provider},
        pricing_snapshot_sha256=price.snapshot_sha256, pricing_snapshot_utc=price.snapshot_utc, namespace="mock")
    return OpenRouterQwenGenerationRunner(budget=budget, pricing=price, transport_factory=factory,
        live_enabled=False, run_id="fixture", max_output_tokens=64, max_input_tokens=20000), budget


def rehash(pack):
    pack["pack_sha256"] = sha256_json({k: v for k, v in pack.items() if k != "pack_sha256"})


def remote(pack):
    return build_rights_cleared_paired_payload(pack, provider="openrouter", model="qwen/qwen3-32b", route="DeepInfra")


def test_failed_output_retains_cost_generation_id_and_wire_binding(tmp_path):
    pack = _load_fixture_builder()._synthetic_pack(tmp_path)
    seen = []
    class ChargedInvalidOutput:
        is_mock = True
        def send(self, *, config, request):
            seen.append(request)
            return MockHTTPResponse(200, {"id": "gen-fixture-" + request.request_id,
                "model": config.model, "provider": "DeepInfra",
                "choices": [{"message": {"content": "not JSON"}}],
                "usage": {"prompt_tokens": 2, "completion_tokens": 2, "total_tokens": 4, "cost": .000001}})
    execute, budget = runner(tmp_path, ChargedInvalidOutput)
    try:
        result = execute.run(pack)
        assert result["known_debit_usd"] == .000003
        assert result["mode"] == "mock" and result["paid_cost_usd"] == 0
        assert result["external_provider_calls"] == 0
        assert result["billing_complete"] is True
        assert len(seen) == 3
        for case in result["cases"]:
            assert case["status"] == "FAILED"
            assert case["actual_debit_usd"] == .000001
            assert case["provider_generation_id"].startswith("gen-fixture-")
            assert budget.db.execute("SELECT payload_sha256 FROM budget_attempts WHERE attempt_id=?", (case["attempt_id"],)).fetchone()[0] == case["wire_payload_sha256"]
    finally:
        budget.close()


def test_unknown_billing_preserves_unrun_cases_and_does_not_report_known_zero(tmp_path):
    pack = _load_fixture_builder()._synthetic_pack(tmp_path)
    class Timeout:
        is_mock = True
        def send(self, **kwargs):
            raise RuntimeError("SENSITIVE ERROR CONTENT")
    execute, budget = runner(tmp_path, Timeout)
    try:
        result = execute.run(pack)
        assert result["billing_complete"] is False and result["provider_calls"] is None
        assert [case["status"] for case in result["cases"]] == ["FAILED", "NOT_RUN", "NOT_RUN"]
        assert result["ledger_snapshot"]["unknown_or_pending"]
        assert "SENSITIVE ERROR CONTENT" not in json.dumps(execute.sanitized_receipt(result))
    finally:
        budget.close()


def test_full_utf8_message_and_schema_bounds_replace_chars_divided_by_four(tmp_path):
    pack = _load_fixture_builder()._synthetic_pack(tmp_path)
    pack["cases"][0]["query"]["technical_description"] = "\u0e44\u0e17\u0e22" * 100
    rehash(pack)
    execute, budget = runner(tmp_path, MockGenerationTransport)
    try:
        payload = remote(pack)["cases"][0]
        request, input_bound, framing, amount = execute._request_for_case(payload)
        assert input_bound >= sum(len(message["content"].encode("utf-8")) for message in payload["messages"])
        assert framing >= len(json.dumps(payload["response_schema"], separators=(",", ":")).encode())
        assert amount == request.cost_upper_bound_usd
    finally:
        budget.close()


def test_model_snapshot_accepts_bounded_non_thinking_envelope():
    raw = pricing().model_dump(mode="json") | {"non_thinking_parameters": {"reasoning": {"enabled": False}}, "max_input_tokens": 6144}
    assert pricing_from_snapshot(raw).model == "qwen/qwen3-32b"
    with pytest.raises(APIGenerationError):
        pricing_from_snapshot(raw | {"secret_or_unknown": "must not be logged"})


def test_route_price_ceiling_is_in_reservation():
    price = pricing().model_copy(update={"max_price_prompt": 8.0, "max_price_completion": 28.0})
    assert conservative_request_bound_usd(input_tokens=1000, output_tokens=1000, pricing=price) >= .036


def test_pack_hash_is_checked_at_library_boundary(tmp_path):
    pack = _load_fixture_builder()._synthetic_pack(tmp_path)
    pack["cases"][0]["query"]["technical_description"] += "mutation"
    with pytest.raises(GenerationPayloadError, match="pack_sha256"):
        remote(pack)


def test_unknown_evidence_fields_never_enter_model_messages(tmp_path):
    pack = _load_fixture_builder()._synthetic_pack(tmp_path)
    pack["cases"][0]["evidence"][0]["raw_payload"] = "SENTINEL_PRIVATE_RAW"
    rehash(pack)
    assert "SENTINEL_PRIVATE_RAW" not in json.dumps(remote(pack))


@pytest.mark.parametrize("kind,key", [("sources", "source_id"), ("evidence", "evidence_id"), ("candidates", "patent_id_canonical")])
def test_duplicate_ids_cannot_shadow_rights_or_provenance(tmp_path, kind, key):
    pack = _load_fixture_builder()._synthetic_pack(tmp_path)
    pack["cases"][0][kind].append(dict(pack["cases"][0][kind][0]))
    rehash(pack)
    with pytest.raises(GenerationPayloadError, match="duplicate"):
        remote(pack)


def test_redistribution_label_alone_cannot_clear_query_and_association_text(tmp_path):
    pack = _load_fixture_builder()._synthetic_pack(tmp_path)
    source = pack["cases"][0]["sources"][0]
    source.update(synthetic=False, redistribution="ALLOWED", basis_url="https://example.invalid/terms", displayable_fields=["trade_name"])
    rehash(pack)
    with pytest.raises(GenerationPayloadError, match="model-visible fields"):
        remote(pack)
    case = pack["cases"][0]
    case["remote_transfer_review"] = {
        "purpose": "ht-o3-generation",
        "provider": "openrouter",
        "route": "DeepInfra",
        "message_sha256": sha256_json(build_generation_messages(pack, case)),
        "basis_reference": "SYNTHETIC-FIELD-REVIEW-ONLY",
    }
    rehash(pack)
    remote(pack)
    case["query"]["technical_description"] += "more source text"
    rehash(pack)
    with pytest.raises(GenerationPayloadError, match="model-visible fields"):
        remote(pack)


def test_transfer_review_route_is_case_normalized_without_aliasing(tmp_path):
    pack = _load_fixture_builder()._synthetic_pack(tmp_path)
    source = pack["cases"][0]["sources"][0]
    source.update(
        synthetic=False,
        redistribution="ALLOWED",
        basis_url="https://example.invalid/terms",
        displayable_fields=["trade_name"],
    )
    case = pack["cases"][0]
    case["remote_transfer_review"] = {
        "purpose": "ht-o3-generation",
        "provider": "openrouter",
        "route": "deepinfra",
        "message_sha256": sha256_json(build_generation_messages(pack, case)),
        "basis_reference": "SYNTHETIC-FIELD-REVIEW-ONLY",
    }
    rehash(pack)
    payload = remote(pack)
    assert payload["manifest"]["route"] == "deepinfra"


def test_transfer_review_rejects_a_different_route(tmp_path):
    pack = _load_fixture_builder()._synthetic_pack(tmp_path)
    source = pack["cases"][0]["sources"][0]
    source.update(
        synthetic=False,
        redistribution="ALLOWED",
        basis_url="https://example.invalid/terms",
        displayable_fields=["trade_name"],
    )
    case = pack["cases"][0]
    case["remote_transfer_review"] = {
        "purpose": "ht-o3-generation",
        "provider": "openrouter",
        "route": "different-route",
        "message_sha256": sha256_json(build_generation_messages(pack, case)),
        "basis_reference": "SYNTHETIC-FIELD-REVIEW-ONLY",
    }
    rehash(pack)
    with pytest.raises(GenerationPayloadError, match="model-visible fields"):
        remote(pack)
