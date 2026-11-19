import importlib.util, json, sys
from pathlib import Path

spec = importlib.util.spec_from_file_location('b53', Path(__file__).resolve().parents[1] / 'scripts/healthtech/b53_first_stage.py')
b53 = importlib.util.module_from_spec(spec); spec.loader.exec_module(b53)


def _inputs(d):
    (d / 'corpus.jsonl').write_text(''.join(json.dumps({'id': f'D{i}', 'text': t}) + '\n' for i, t in enumerate(
        ['pump valve flow', 'battery cell anode', 'valve seat seal', 'pump motor rotor', 'anode coating'])))
    (d / 'queries.jsonl').write_text(json.dumps({'id': 'Q1', 'text': 'valve flow pump'}) + '\n' + json.dumps({'id': 'Q2', 'text': 'anode battery'}) + '\n')
    (d / 'qrels-pos.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in [
        {'query_id': 'Q1', 'family': 'D2', 'score': 1.0, 'domain': 'OUT'}, {'query_id': 'Q1', 'family': 'D0', 'score': 1.0, 'domain': 'IN'},
        {'query_id': 'Q2', 'family': 'D3', 'score': 1.0, 'domain': 'OUT'}]))


def test_bm25_rrf_eval(tmp_path):
    _inputs(tmp_path); runs = tmp_path / 'runs'
    b53.cmd_bm25(tmp_path, runs)
    r = b53.read_run(runs / 'F1.tsv')
    assert r['Q1'][0] == 'D0' and 'D3' not in r['Q2']           # only matching docs are returned
    b53.write_run(runs / 'F0.tsv', {'Q1': [('D2', 0.9), ('D0', 0.5)], 'Q2': [('D3', 0.8)]})
    b53.cmd_rrf(runs, 'F2', 'F1', 'F0')
    assert set(b53.read_run(runs / 'F2.tsv')['Q2']) == {'D1', 'D4', 'D3'}
    b53.cmd_eval(tmp_path, runs, tmp_path / 'res.json')
    res = json.loads((tmp_path / 'res.json').read_text())
    assert res['cohorts']['OUT'] == 2
    assert res['arms']['F0']['pi100'] == 1.0 and res['arms']['F1']['pi100'] == 0.5
    c = res['b53_1_contrasts']['F1']
    assert c['delta_pi100_vs_F0'] == -0.5 and c['lost'] == 1 and c['gained'] == 0


def test_mcnemar_holm():
    assert b53.mcnemar([1, 1, 0], [0, 0, 0])[:2] == (2, 0)
    assert b53.holm([0.01, 0.04]) == [0.02, 0.04]
