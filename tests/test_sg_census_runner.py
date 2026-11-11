import hashlib
import json
import pytest
from patent_to_pilot.research.sg_census_runner import run_census, config_hash
from patent_to_pilot.research.mtm_runtime import InputBoundaryError


def setup(tmp_path, rows=None):
    rows = rows if rows is not None else [
        {'id': 'A', 'title': '', 'abstract': 'A unit configured to reduce pressure.', 'claims': ''},
        {'id': 'B', 'title': '', 'abstract': 'A unit configured to reduce pressure.', 'claims': ''}]
    raw = b''.join((json.dumps(row)+'\n').encode() for row in rows)
    source = tmp_path/'synthetic.jsonl'; source.write_bytes(raw)
    args = dict(expected_sha256=hashlib.sha256(raw).hexdigest(), expected_families=2,
                expected_config_sha256=config_hash(), max_seconds=5, max_input_bytes=4096)
    return source, tmp_path/'attempt', args


def test_complete_and_no_source_leaks(tmp_path):
    src, out, args = setup(tmp_path)
    receipt = run_census(src, out, **args)
    assert receipt['status'] == 'COMPLETE_SIGNATURE_CENSUS_NOT_FIDELITY'
    assert receipt['partial_counts']['cross_family_pair_key_incidences'] == 1
    assert 'reduce pressure' not in (out/'receipt.json').read_text()
    with pytest.raises(FileExistsError): run_census(src, out, **args)


@pytest.mark.parametrize('fault', ['hash', 'config', 'rows', 'line', 'size', 'deadline'])
def test_failure_receipt_no_false_completion(tmp_path, fault):
    src, out, args = setup(tmp_path)
    if fault == 'hash': args['expected_sha256'] = '0'*64
    if fault == 'config': args['expected_config_sha256'] = '0'*64
    if fault == 'rows': args['expected_families'] = 3
    if fault == 'line': args['max_line_bytes'] = 10
    if fault == 'size': args['max_input_bytes'] = 10
    if fault == 'deadline':
        ticks = iter([0, 10, 11]); args['clock'] = lambda: next(ticks)
    with pytest.raises((InputBoundaryError, TimeoutError)): run_census(src, out, **args)
    receipt = json.loads((out/'receipt.json').read_text())
    assert receipt['status'] == 'INCOMPLETE'
    assert receipt['elapsed_seconds'] >= 0 and receipt['retry'] is False


def test_duplicate_family_fails_with_partial_count(tmp_path):
    row = {'id': 'A', 'title': '', 'abstract': '', 'claims': ''}
    src, out, args = setup(tmp_path, [row, row])
    with pytest.raises(InputBoundaryError): run_census(src, out, **args)
    assert json.loads((out/'receipt.json').read_text())['rows_read'] == 1
