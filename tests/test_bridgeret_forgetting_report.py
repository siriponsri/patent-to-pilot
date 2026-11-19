import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts' / 'healthtech'))
import bridgeret_forgetting_report as fr  # noqa: E402


def _eval(path, block, rows):
    metrics = {}
    for m in fr.METRICS:
        vals = [r[m] for r in rows.values() if m in r]
        metrics[m] = {'mean': sum(vals) / len(vals), 'n': len(vals)}
    path.write_text(json.dumps({'block': block, 'metrics': metrics, 'per_query': rows}), encoding='utf-8')
    return str(path)


def test_paired_deltas_and_flag(tmp_path):
    base = {f'q{i}': {'OUT_R@200': 0.2, 'IN_R@200': 0.5, 'ALL_R@200': 0.4} for i in range(40)}
    ft = {f'q{i}': {'OUT_R@200': 0.3, 'IN_R@200': 0.45, 'ALL_R@200': 0.4} for i in range(40)}
    ft['q0'].pop('IN_R@200')                         # query without an IN row is skipped for IN only
    b = _eval(tmp_path / 'b.json', 'P1-DEV', base)
    f = _eval(tmp_path / 'f.json', 'P1-DEV', ft)
    out = tmp_path / 'o.json'
    fr.main([b, str(out), f'S2={f}'])
    r = json.loads(out.read_text())['configs']['S2']
    assert r['OUT_R@200']['delta'] == pytest.approx(0.1)
    assert r['OUT_R@200']['wins'] == 40
    assert r['IN_R@200']['n'] == 39
    assert r['IN_R@200']['delta'] == pytest.approx(-0.05)
    assert r['IN_TRADEOFF'] is True
    assert r['ALL_R@200']['ties'] == 40


def test_refuses_test_block_and_mismatch(tmp_path):
    rows = {'q': {'OUT_R@200': 0.1, 'IN_R@200': 0.1, 'ALL_R@200': 0.1}}
    t = _eval(tmp_path / 't.json', 'P1-TEST', rows)
    d = _eval(tmp_path / 'd.json', 'P1-DEV', rows)
    v = _eval(tmp_path / 'v.json', 'VAL', rows)
    with pytest.raises(SystemExit):
        fr.main([t, str(tmp_path / 'o.json'), f'x={d}'])
    with pytest.raises(SystemExit):
        fr.main([d, str(tmp_path / 'o.json'), f'x={v}'])
