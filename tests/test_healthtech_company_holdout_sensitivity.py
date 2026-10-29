import json
from pathlib import Path

from scripts.healthtech.run_company_holdout_sensitivity import (
    build_baseline_command,
    build_compose_command,
    _record_command,
    summarize_baseline,
)


def test_build_commands_preserve_frozen_inputs(tmp_path: Path):
    boston = tmp_path / "boston"
    stryker = tmp_path / "stryker"
    cook = tmp_path / "cook"
    mapping = tmp_path / "family.json"
    output = tmp_path / "out"
    command = build_compose_command(
        boston_cohort=boston,
        stryker_cohort=stryker,
        additional_cohorts=[("cook", cook)],
        holdout_company="Cook Medical",
        family_mapping=mapping,
        output=output,
    )
    assert command[command.index("--holdout-company") + 1] == "Cook Medical"
    assert "cook=" + str(cook) in command
    assert command[command.index("--family-mapping") + 1] == str(mapping)

    baseline = build_baseline_command(
        runtime=output / "runtime.json",
        references=output / "references.json",
        groups=output / "groups.json",
        model_root=tmp_path / "models",
        output=tmp_path / "baseline",
        code_commit="abc123",
        protocol_hash="p" * 64,
        cohort_manifest_hash="c" * 64,
        candidate_depth=31,
        rerank_depth=31,
    )
    assert baseline[baseline.index("--candidate-depth") + 1] == "31"
    assert baseline[baseline.index("--rerank-depth") + 1] == "31"
    assert baseline[baseline.index("--protocol-hash") + 1] == "p" * 64

    recorded = _record_command(command, [boston, stryker, cook, mapping, output])
    assert recorded[0] == "python"
    assert recorded[1].endswith("scripts/healthtech/compose_multicompany_cohort.py")
    assert "cook=" + str(cook) in recorded


def test_summarize_baseline_keeps_metrics_and_hashes(tmp_path: Path):
    output = tmp_path / "baseline"
    output.mkdir()
    (output / "receipt.json").write_text(json.dumps({
        "status": "REAL_PUBLIC_DEVELOPMENT_RUN",
        "devices": 2,
        "patents": 7,
        "reference_pairs": 3,
        "provider_calls": 0,
        "paid_cost_usd": 0,
    }), encoding="utf-8")
    (output / "frontier_diagnostics.json").write_text(json.dumps({
        "by_method": {
            "HT-B0b": {
                "macro_known_link_recall_at_20": 0.5,
                "failed_device_count": 0,
                "query_calls": 2,
                "rerank_pairs": 0,
                "returned_candidates": 14,
            },
        },
    }), encoding="utf-8")

    summary = summarize_baseline(output)

    assert summary["devices"] == 2
    assert summary["metrics"]["HT-B0b"]["macro_known_link_recall_at_20"] == 0.5
    assert len(summary["receipt_sha256"]) == 64
    assert len(summary["frontier_sha256"]) == 64
