from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.healthtech.analyze_matched_budget_prefix import analyze


def _receipt(tmp_path: Path) -> Path:
    rows = []
    for method, value in (("HT-B1", 0.4), ("HT-B2", 0.4), ("HT-B3", 0.4)):
        rows.append(
            {
                "method": method,
                "prefix": 1,
                "scheduled_query_count": 1,
                "query_calls": 3.0,
                "rerank_pairs": 123.0,
                "macro_known_link_recall_at_20_all_devices": value,
                "failed_query_count": 0,
                "not_realized_query_count": 0,
            }
        )
    path = tmp_path / "frontier.json"
    path.write_text(json.dumps({"quality_resource_frontier": {"rows": rows}, "code_commit": "old"}), encoding="utf-8")
    return path


def test_analyze_selects_only_equalized_required_methods(tmp_path: Path):
    result = analyze(_receipt(tmp_path), query_calls=3, rerank_pairs=123)

    assert result["status"] == "PASS_POSTHOC_DESCRIPTIVE_FIRST_ACTION_SLICE"
    assert [row["method"] for row in result["methods"]] == ["HT-B1", "HT-B2", "HT-B3"]
    assert result["summary"]["macro_recall_range"] == 0.0
    assert result["interpretation"]["adaptive_test"] == "NOT_ESTABLISHED"


def test_analyze_rejects_missing_budget_slice(tmp_path: Path):
    path = _receipt(tmp_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["quality_resource_frontier"]["rows"][0]["query_calls"] = 1
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="budget slice missing methods"):
        analyze(path, query_calls=3, rerank_pairs=123)
