import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from patent_to_pilot.evaluation.pilot_readiness import ROOT, current_stage
from patent_to_pilot.evaluation.stage_boundary import verify_bundle


@pytest.fixture
def bundle(tmp_path):
    # Build from tracked public fixtures, never from a prior local run receipt.
    target = tmp_path / "stages/PTP-0001/S0"
    target.mkdir(parents=True)
    (target / "runtime-input.json").write_text(json.dumps(current_stage("PTP-0001", "S0")[0]), encoding="utf-8")
    schema = ROOT / "methodology/evaluation/cases/PTP-0001/public-input/output-schema.json"
    (target / "output-contract.json").write_bytes(schema.read_bytes())
    return target, tmp_path / "stages"


def hashes(directory):
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in directory.iterdir() if p.is_file()}


def verify(bundle, expected=None, **kw):
    directory, root = bundle
    return verify_bundle(directory, expected or hashes(directory), allowed_root=root,
                         case_id="PTP-0001", state_id="S0", **kw)


def mutate(bundle, change):
    path = bundle[0] / "runtime-input.json"
    obj = json.loads(path.read_text())
    change(obj)
    path.write_text(json.dumps(obj))


def test_valid_positive_has_explicit_limits(bundle):
    result = verify(bundle)
    assert result["status"] == "PASS"
    assert result["os_process_isolation"] == "NOT_VERIFIED"
    assert result["semantic_oracle_detection"] == "NOT_CLAIMED"


def test_hash_mismatch_rejects_without_resigning(bundle):
    expected = hashes(bundle[0])
    mutate(bundle, lambda d: d["packet"].update(brief="changed after approval"))
    with pytest.raises(ValueError, match="hash mismatch"):
        verify(bundle, expected)


@pytest.mark.parametrize("filename", ["S1.json", "expected_answers.json", ".hidden"])
def test_extra_future_or_hidden_file_is_rejected(bundle, filename):
    (bundle[0] / filename).write_text("{}")
    with pytest.raises(ValueError, match="unexpected"):
        verify(bundle, {k:v for k,v in hashes(bundle[0]).items() if k in {"runtime-input.json", "output-contract.json"}})


def test_traversal_manifest_name_rejected(bundle):
    with pytest.raises(ValueError, match="exact two-file"):
        verify(bundle, {"../S1.json": "a"*64, "output-contract.json": "b"*64})


def test_outside_root_rejected(bundle):
    with pytest.raises(ValueError, match="escapes"):
        verify_bundle(bundle[0], hashes(bundle[0]), allowed_root=bundle[0]/"child", case_id="PTP-0001", state_id="S0")


def test_reparse_link_rejected_before_content_access(bundle):
    # No symlink privilege or ACL change needed for this deterministic control.
    original = Path.is_symlink
    def marked(path):
        return path == bundle[0]/"runtime-input.json" or original(path)
    with patch.object(Path, "is_symlink", marked):
        with pytest.raises(ValueError, match="reparse"):
            verify(bundle)


def test_oversized_input_rejected(bundle):
    with pytest.raises(ValueError, match="size bound"):
        verify(bundle, max_file_bytes=32)


@pytest.mark.parametrize("raw", ['{"packet": {}, "packet": {}, "profile": {}}', '{"packet": NaN, "profile": {}}'])
def test_strict_json_rejects_ambiguous_or_nonfinite_values(bundle, raw):
    (bundle[0]/"runtime-input.json").write_text(raw)
    with pytest.raises(ValueError, match="duplicate|non-finite"):
        verify(bundle)


def test_closed_envelope_rejects_extra_material(bundle):
    mutate(bundle, lambda d: d.update(evaluator={"gold_answer": "hidden"}))
    with pytest.raises(ValueError, match="closed"):
        verify(bundle)


@pytest.mark.parametrize("layer", ["packet", "profile", "schema"])
def test_nested_oracle_or_future_data_rejected_even_with_new_hash(bundle, layer):
    if layer == "schema":
        p=bundle[0]/"output-contract.json"
        d=json.loads(p.read_text());d["extra"]=[{"future_events": ["hidden"]}];p.write_text(json.dumps(d))
    else:
        mutate(bundle, lambda d: d[layer].update(extra=[{"gold_answer":"hidden"}]))
    with pytest.raises(ValueError, match="evaluator-only"):
        verify(bundle)


def test_wrong_state_or_profile_version_rejected(bundle):
    mutate(bundle, lambda d: d["packet"].update(state_id="S1"))
    with pytest.raises(ValueError, match="case/state"):
        verify(bundle)
    mutate(bundle, lambda d: d["packet"].update(state_id="S0", profile_version="UNAPPROVED"))
    with pytest.raises(ValueError, match="profile"):
        verify(bundle)
