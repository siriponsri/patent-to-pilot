import importlib.util
from pathlib import Path

SPEC = importlib.util.spec_from_file_location('review_coverage', Path(__file__).with_name('run_coverage.py'))
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_detects_same_length_content_change(tmp_path):
    data = tmp_path / 'data.bin'
    data.write_bytes(b'first')
    before = MODULE.hashes({'data': data})
    data.write_bytes(b'other')
    after = MODULE.hashes({'data': data})
    assert MODULE.changed_inputs(before, after) == ['data']


def test_detects_added_or_missing_inputs_and_accepts_stable_snapshot():
    assert MODULE.changed_inputs({'data': 'abc'}, {'data': 'abc'}) == []
    assert MODULE.changed_inputs({'data': 'abc'}, {}) == ['data']
    assert MODULE.changed_inputs({}, {'source': 'abc'}) == ['source']
