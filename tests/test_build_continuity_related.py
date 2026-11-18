"""Synthetic smoke for the continuity link builder (no real PatentsView data)."""
import importlib.util
import json
import pathlib
import zipfile


def _z(d, name, rows):
    with zipfile.ZipFile(d / f'{name}.tsv.zip', 'w') as z:
        z.writestr(f'{name}.tsv', '\n'.join('\t'.join(r) for r in rows) + '\n')


def test_components_primary_and_provisional(tmp_path):
    p = pathlib.Path(__file__).resolve().parents[1] / 'scripts' / 'healthtech' / 'build_continuity_related.py'
    spec = importlib.util.spec_from_file_location('bcr', p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    pv = tmp_path / 'pv'
    pv.mkdir()
    _z(pv, 'g_application', [('application_id', 'patent_id'), ('11111111', '7000001'), ('22222222', '7000002')])
    _z(pv, 'pg_published_application', [('pgpub_id', 'application_id'), ('20090000001', '33333333'), ('20090000002', '44444444')])
    _z(pv, 'g_us_rel_doc', [('patent_id', 'related_doc_number', 'related_doc_type', 'related_doc_kind'),
                            ('7000002', '7000001', 'continuation', 'parent-grant-document'),
                            ('7000002', '20090000002', 'related-publication', '')])
    _z(pv, 'pg_us_rel_doc', [('pgpub_id', 'related_doc_number', 'related_doc_type', 'related_doc_kind'),
                             ('20090000001', '60/123,456', 'us-provisional-application', ''),
                             ('20090000002', '60123456', 'us-provisional-application', '')])
    tasks = tmp_path / 'tasks.tsv'
    tasks.write_text('app_id\tfiling_date\n11111111\t2011\n22222222\t2012\n33333333\t2011\n44444444\t2012\n55555555\t2013\n')
    mod.main([str(pv), str(tasks), str(tmp_path / 'out')])
    s = json.loads((tmp_path / 'out' / 'continuity-stats.json').read_text())
    prim, prov = s['variants']['primary'], s['variants']['with_provisional']
    assert prim['n_groups'] == 4 and prim['tasks_in_multi_task_groups'] == 2   # 1111 <-> 2222 via parent grant
    assert prov['n_groups'] == 3 and prov['tasks_in_multi_task_groups'] == 4   # 3333 <-> 4444 via shared provisional
    assert prim['tasks_with_any_link'] == 2
    rows = (tmp_path / 'out' / 'related-primary.tsv').read_text().splitlines()
    rel = dict(r.split('\t') for r in rows[1:])
    assert rel['11111111'] == rel['22222222'] != rel['33333333']
