import importlib.util, json
from pathlib import Path

spec = importlib.util.spec_from_file_location('s2', Path(__file__).resolve().parents[1] / 'scripts/healthtech/b53_stage2_eval.py')
s2 = importlib.util.module_from_spec(spec); spec.loader.exec_module(s2)


def test_rerank_ties_and_ndcg():
    sc = {('q', 'a'): 0.5, ('q', 'b'): 0.9, ('q', 'c'): 0.5}
    assert s2.rerank(['a', 'b', 'c'], sc, 'q') == ['b', 'a', 'c']        # ties keep first-stage order
    assert s2.ndcg100(['x', 'b'], {'b': 1.0}) == 1 / __import__('math').log2(3)
    assert s2.ndcg100(['x'], {'b': 1.0}) == 0.0


def test_end_to_end(tmp_path):
    runs, sc = tmp_path / 'runs', tmp_path / 'sc'; runs.mkdir(); sc.mkdir()
    (tmp_path / 'qrels-pos.jsonl').write_text(json.dumps({'query_id': 'Q', 'family': 'd2', 'score': 1.0, 'domain': 'OUT'}) + '\n')
    for F in s2.ARMS_F:
        (runs / f'{F}.tsv').write_text('Q\t1\td1\t1.0\nQ\t2\td2\t0.9\n')
    for i in s2.INSTR:
        hi = 'd2' if i == 'patent_aware' else 'd1'
        (sc / f'scores-{i}.tsv').write_text(f'Q\td1\t{0.9 if hi == "d1" else 0.1}\nQ\td2\t{0.9 if hi == "d2" else 0.1}\n')
    s2.main(tmp_path, runs, sc, tmp_path / 'o.json')
    r = json.loads((tmp_path / 'o.json').read_text())
    assert r['C'] == 1 and r['B53_3_primary_on_C']['F0|patent_aware-generic']['delta_C'] > 0
    assert r['B53_3_primary_on_C']['F0|claim_focused-generic']['delta_C'] == 0
