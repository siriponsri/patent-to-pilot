from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.healthtech.refresh_integration_contract import (
    IntegrationContractError,
    refresh_contract,
)


ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT / "docs/healthtech/integration/luna-g3-20261028-28dfb1d/adapter-contract.json"


def test_refresh_rebinds_backend_hashes_without_mutating_parent(tmp_path):
    output = tmp_path / "current-head" / "adapter-contract.json"
    refreshed = refresh_contract(PARENT, output, code_head="a" * 40, refresh_date="2026-10-30")
    parent = json.loads(PARENT.read_text(encoding="utf-8"))
    written = json.loads(output.read_text(encoding="utf-8"))

    assert refreshed["tested_code_head"] == "a" * 40
    assert written["tested_code_head"] == "a" * 40
    assert written["backend_source_hashes"] != parent["backend_source_hashes"]
    assert written["refresh"]["parent_contract"].endswith("adapter-contract.json")
    assert written["refresh"]["fixture_hashes_verified"] == 3
    assert json.loads(PARENT.read_text(encoding="utf-8")) == parent


def test_refresh_fails_closed_on_fixture_hash_drift(tmp_path):
    parent = json.loads(PARENT.read_text(encoding="utf-8"))
    parent["sanitized_fixture_hashes"][0]["sha256"] = "0" * 64
    mutated_parent = tmp_path / "parent.json"
    mutated_parent.write_text(json.dumps(parent), encoding="utf-8")

    with pytest.raises(IntegrationContractError, match="fixture hash drift"):
        refresh_contract(mutated_parent, tmp_path / "out.json", code_head="b" * 40)


def test_refresh_rejects_existing_output(tmp_path):
    output = tmp_path / "out.json"
    output.write_text("{}", encoding="utf-8")
    with pytest.raises(IntegrationContractError, match="refusing to overwrite"):
        refresh_contract(PARENT, output, code_head="c" * 40)


def test_refresh_rejects_path_escape(tmp_path):
    parent = json.loads(PARENT.read_text(encoding="utf-8"))
    parent["backend_source_hashes"] = {"../outside.py": "0" * 64}
    mutated_parent = tmp_path / "parent.json"
    mutated_parent.write_text(json.dumps(parent), encoding="utf-8")

    with pytest.raises(IntegrationContractError, match="escapes the repository"):
        refresh_contract(mutated_parent, tmp_path / "out.json", code_head="d" * 40)
