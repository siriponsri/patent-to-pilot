"""Synthetic test of the BridgeRet hard-negative miner (guards and IN/OUT tags)."""
import importlib.util, json, pathlib, zipfile


def _z(d, name, rows):
    with zipfile.ZipFile(d / f'{name}.tsv.zip', 'w') as z:
        z.writestr(f'{name}.tsv', '\n'.join('\t'.join(r) for r in rows) + '\n')


def test_guards_and_domains(tmp_path):
    p = pathlib.Path(__file__).resolve().parents[1] / 'scripts' / 'healthtech' / 'mine_negatives_bridgeret.py'
    spec = importlib.util.spec_from_file_location('mn', p); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    pv = tmp_path / 'pv'; pv.mkdir()
    _z(pv, 'g_ipc_at_issue', [('patent_id', 'section', 'ipc_class'), ('1', 'A', '61'), ('2', 'H', '01'), ('3', 'A', '61'), ('4', 'H', '01')])
    _z(pv, 'pg_ipc_at_issue', [('pgpub_id', 'section', 'ipc_class'), ('20080000001', 'A', '61')])
    ser = tmp_path / 'ser'; ser.mkdir(); tx = tmp_path / 'tx'; tx.mkdir()
    (ser / 'passages.jsonl').write_text(''.join(json.dumps({'unit': u, 'text': t}) + '\n' for u, t in
                                         [('A:1', 'pos text'), ('A:2', 'other'), ('A:3', 'pos text'), ('A:4', 'more')]))
    (tx / 'queries.jsonl').write_text(json.dumps({'app_id': '10000009', 'block': 'TRAIN', 'doc': 'PG20080000001'}) + '\n')
    (tmp_path / 'pairs.tsv').write_text('app_id\tblock\tcited\tunit\tbasis\tdom_ipc3\tunit_first_pub\n10000009\tTRAIN\tP1\tA:1\t103\tIN3\t2001-01-01\n')
    (tmp_path / 'units.tsv').write_text('unit_id\trep_doc\tfirst_pub\n' + ''.join(f'A:{i}\tP{i}\t2001-01-01\n' for i in range(1, 5)))
    run = 'app_id\trank\tunit\tscore\n' + ''.join(f'10000009\t{k}\tA:{u}\t{1 - k / 1000:.3f}\n' for k, u in [(1, 1), (25, 2), (30, 3), (40, 4)])
    (tmp_path / 'bm.tsv').write_text(run); (tmp_path / 'de.tsv').write_text(run)
    m.main([str(pv), str(ser), str(tx), str(tmp_path / 'pairs.tsv'), str(tmp_path / 'units.tsv'), str(tmp_path / 'bm.tsv'), str(tmp_path / 'de.tsv'), str(tmp_path / 'o')])
    r = json.loads((tmp_path / 'o' / 'mined-TRAIN.jsonl').read_text())
    assert r['pos'] == ['A:1'] and r['pos_dense'] == 0.999
    assert [x[0] for x in r['dense']] == ['A:2', 'A:4']          # A:1 positive, A:3 identical text to a positive
    assert {x[0]: x[3] for x in r['dense']} == {'A:2': 'OUT', 'A:4': 'OUT'}
    assert [x[0] for x in r['bm25']] == ['A:2', 'A:4']
