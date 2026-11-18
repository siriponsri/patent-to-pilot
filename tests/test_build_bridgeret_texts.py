"""Synthetic test of the BridgeRet text-table builder (authored rows only)."""
import importlib.util, json, pathlib, zipfile


def _z(d, name, rows):
    with zipfile.ZipFile(d / f'{name}.tsv.zip', 'w') as z:
        z.writestr(f'{name}.tsv', '\n'.join('\t'.join(r) for r in rows) + '\n')


def test_queries_non_test_only_and_corpus(tmp_path):
    p = pathlib.Path(__file__).resolve().parents[1] / 'scripts' / 'healthtech' / 'build_bridgeret_texts.py'
    spec = importlib.util.spec_from_file_location('bt', p); mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    pv = tmp_path / 'pv'; (pv / 'claims').mkdir(parents=True)
    _z(pv, 'pg_published_application', [('pgpub_id', 'application_id', 'patent_type', 'published_date', 'application_title'),
        ('20110000001', '12000001', 'utility', '2011-05-01', 'Pump'), ('20120000009', '12000001', 'utility', '2012-01-01', 'Pump B'),
        ('20120000002', '13000002', 'utility', '2012-06-01', 'Secret test app')])
    _z(pv, 'g_patent', [('patent_id', 'patent_title'), ('7000001', 'Valve')])
    _z(pv, 'g_patent_abstract', [('patent_id', 'patent_abstract'), ('7000001', 'A valve abstract.')])
    _z(pv, 'pg_published_application_abstract', [('pgpub_id', 'application_abstract'), ('20110000001', 'A pump abstract.')])
    _z(pv / 'claims', 'pg_claims_2011', [('pgpub_id', 'claim_sequence', 'claim_text', 'dependent', 'claim_number'),
        ('20110000001', '0', '1 . (canceled)', '', '00001'), ('20110000001', '2', '3 . The pump of claim 2.', 'claim 2', '00003'),
        ('20110000001', '1', '2 . A pump comprising a valve.', '', '00002')])
    _z(pv / 'claims', 'g_claims_2008', [('patent_id', 'claim_sequence', 'claim_text', 'dependent', 'claim_number', 'exemplary'),
        ('7000001', '0', '1. A valve.', '', '1', '')])
    man = {'frozen': True, 'manifest_sha256': 'x', 'blocks': {'TRAIN': [], 'VAL': [], 'P1-DEV': ['12000001'], 'P2-DEV': ['19999999'],
           'P1-TEST': ['13000002'], 'P2-TEST': [], 'P3-TEST': []}}
    mp_ = tmp_path / 'm.json'; mp_.write_text(json.dumps(man))
    units = tmp_path / 'u.tsv'; units.write_text('unit_id\trep_doc\tfirst_pub\nA:1\tP7000001\t2008-01-01\n')
    mod.main([str(pv), str(mp_), str(units), str(tmp_path / 'o'), '2'])
    qs = [json.loads(l) for l in (tmp_path / 'o' / 'queries.jsonl').read_text().splitlines()]
    assert {x['app_id'] for x in qs} == {'12000001', '19999999'}                 # TEST app never built
    q = next(x for x in qs if x['app_id'] == '12000001')
    assert q['doc'] == 'PG20110000001' and q['claim'] == 'A pump comprising a valve.' and q['abstract'] == 'A pump abstract.'
    assert next(x for x in qs if x['app_id'] == '19999999')['variant'] == 'no_pgpub'
    c = json.loads((tmp_path / 'o' / 'corpus.jsonl').read_text())
    assert c['title'] == 'Valve' and c['claim'] == 'A valve.' and c['abstract'] == 'A valve abstract.'
