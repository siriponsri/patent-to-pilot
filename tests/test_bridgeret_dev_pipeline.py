"""Synthetic tests for BridgeRet BM25 and the DEV evaluator (authored rows only)."""
import importlib.util, json, pathlib
import pytest

H = pathlib.Path(__file__).resolve().parents[1] / 'scripts' / 'healthtech'


def _load(name):
    spec = importlib.util.spec_from_file_location(name, H / f'{name}.py'); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def _fixture(tmp):
    (tmp / 's').mkdir()
    units = [('A:1', 'pump valve fluid', '2005-01-01'), ('A:2', 'optical lens coating', '2005-01-01'),
             ('A:3', 'pump valve pressure sensor', '2013-01-01'), ('A:20000001', 'pump valve fluid self', '2004-01-01')]
    units += [(f'A:9{i}', f'filler text number{i}', '2000-01-01') for i in range(1100)]
    with open(tmp / 's' / 'passages.jsonl', 'w') as f:
        for u, t, _ in units: f.write(json.dumps({'unit': u, 'text': t}) + '\n')
    (tmp / 'units.tsv').write_text('unit_id\trep_doc\tfirst_pub\n' + ''.join(f'{u}\tP\t{d}\n' for u, _, d in units))
    (tmp / 's' / 'queries.jsonl').write_text(json.dumps({'app_id': '20000001', 'block': 'P1-DEV', 'text': 'pump valve'}) + '\n')
    (tmp / 'tasks.tsv').write_text('app_id\tfiling_date\n20000001\t2011-03-01\n')
    (tmp / 'pairs.tsv').write_text('app_id\tblock\tcited\tunit\tbasis\tdom_ipc3\tunit_first_pub\n'
        '20000001\tP1-DEV\tP1\tA:1\t103\tOUT3\t2005-01-01\n'
        '20000001\tP1-DEV\tP2\tA:2\t103\tOUT3\t2005-01-01\n'
        '20000001\tP1-DEV\tP3\tA:3\t103\tOUT3\t2013-01-01\n'        # not RPD-visible -> excluded
        '20000001\tP1-DEV\tP4\tA:77\t102\tIN3\t1999-01-01\n')       # not in corpus -> strict miss only


def test_bm25_masks_rpd_and_self_then_eval(tmp_path):
    pytest.importorskip('sklearn')
    _fixture(tmp_path)
    _load('bm25_bridgeret').main([str(tmp_path / 's'), str(tmp_path / 'units.tsv'), str(tmp_path / 'tasks.tsv'), str(tmp_path / 'r'), 'P1-DEV'])
    run = (tmp_path / 'r' / 'run-P1-DEV.tsv').read_text().splitlines()[1:]
    got = [l.split('\t')[2] for l in run]
    assert got[0] == 'A:1' and 'A:3' not in got and 'A:20000001' not in got
    out = tmp_path / 'e.json'
    _load('eval_bridgeret_dev').main([str(tmp_path / 'r' / 'run-P1-DEV.tsv'), str(tmp_path / 'pairs.tsv'), str(tmp_path / 'units.tsv'),
                                      str(tmp_path / 'tasks.tsv'), 'P1-DEV', str(out)])
    m = json.loads(out.read_text())['metrics']
    assert m['OUT_R@200']['mean'] == 0.5                 # A:1 retrieved, A:2 shares no terms
    assert m['OUT_MRR']['mean'] == 1.0
    assert m['IN_strict_R@200']['mean'] == 0.0 and 'IN_R@200' not in m


def test_refuses_test_blocks(tmp_path):
    with pytest.raises(SystemExit):
        _load('bm25_bridgeret').main(['x', 'u', 't', str(tmp_path / 'o'), 'P1-TEST'])
    with pytest.raises(SystemExit):
        _load('eval_bridgeret_dev').main(['r', 'p', 'u', 't', 'P2-TEST', 'o'])
