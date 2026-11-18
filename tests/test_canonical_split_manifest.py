"""Synthetic-fixture tests for the canonical split manifest. No real OA/PatentsView data is read."""
import hashlib
import io
import json

import pytest

from patent_to_pilot.research import canonical_split_manifest as m


def _tasks(per_year):
    rows = []
    for y, n in per_year.items():
        rows += [m.TaskMeta(f'{y}{i:06d}', y, f'AU{i % 7}', 'G06F') for i in range(n)]
    return rows


FIX = {2005: 3, 2006: 20, 2007: 20, 2008: 30, 2009: 30, 2010: 50, 2011: 400, 2012: 300, 2013: 40}


def _cfg(**kw):
    base = dict(n1=100, val_n=10, imbalance_tolerance=0.2)
    base.update(kw)
    return m.SplitConfig(**base)


def test_owner_2012_rule_matches_verbatim_spec():
    ids = [f'13{i:06d}' for i in range(500)]
    p1, p2 = m.split_2012(ids, n1=100)
    key = lambda a: hashlib.sha256(('p2-oa-split-v1|' + a).encode('utf-8')).hexdigest()
    ordered = sorted(ids, key=key, reverse=True)
    assert p1 == ordered[-100:] and p2 == ordered[:400]
    assert not set(p1) & set(p2)
    with pytest.raises(m.ManifestError):
        m.split_2012(ids, n1=100, n_p2=401)
    with pytest.raises(m.ManifestError):
        m.split_2012(ids, n1=501)


def test_p2_prefix_is_stable_under_smaller_n():
    ids = [f'x{i}' for i in range(300)]
    _, a = m.split_2012(ids, n1=50, n_p2=100)
    _, b = m.split_2012(ids, n1=50, n_p2=200)
    assert b[:100] == a


def test_dev_bucket_is_deterministic_and_group_level():
    g = m.build_groups(['a', 'b', 'c', 'd'], related_links=[('a', 'b'), ('b', 'c')])
    assert g.status == 'FAMILY_AWARE' and g.group_of['a'] == g.group_of['c'] != g.group_of['d']
    assert m.dev_bucket(g.group_of['a']) == m.dev_bucket(g.group_of['c'])
    assert m.dev_bucket('X') == m.dev_bucket('X')
    # a non-task sibling bridges two tasks
    g2 = m.build_groups(['a', 'z'], related_links=[('a', 'sib'), ('sib', 'z')])
    assert g2.group_of['a'] == g2.group_of['z'] and g2.max_group_size == 2


def test_grouping_precedence_and_pending_stamp():
    assert m.build_groups(['a'], family_ids={'a': 'F1'}).source == 'family_id'
    with pytest.raises(m.ManifestError):
        m.build_groups(['a', 'b'], family_ids={'a': 'F1'})
    s = m.build_groups(['a', 'b'])
    assert s.status == m.FAMILY_PENDING and s.source == 'singleton'


def test_blocks_disjoint_and_assertions_pass_singleton():
    tasks = _tasks(FIX)
    g = m.build_groups([t.app_id for t in tasks])
    man = m.build_manifest(tasks, g, _cfg(), {'tasks.tsv': 'f' * 64}, 'c' * 64, synthetic=True)
    c = man['block_counts']
    assert c['TRAIN'] == 100 and c['VAL'] == 10 and c['P1-TEST'] == 100 and c['P2-TEST'] == 200
    assert c['P1-DEV'] + c['P2-DEV'] == 400 and c['P3-TEST'] == 40
    res = {r['id']: r['result'] for r in man['assertions']}
    assert res['A1-A4'] == 'PASS' and res['A3'] == 'PASS' and res['L-B'] == 'NOT_ASSESSABLE'
    assert any(m.FAMILY_PENDING in n for n in man['notes'])
    assert any('2005' in n for n in man['notes'])       # out-of-scope year reported, not used


def test_family_conflict_option_a_shrinks_p2_only():
    tasks = _tasks({2012: 300})
    ids = [t.app_id for t in tasks]
    p1, p2 = m.split_2012(ids, n1=100)
    links = [(p1[i], p2[i]) for i in range(7)]       # 7 cross-block families
    g = m.build_groups(ids, related_links=links)
    a = m.assign_blocks(tasks, g, _cfg(val_n=0))
    assert a['blocks']['P1-TEST'] == sorted(p1)
    assert len(a['blocks']['P2-TEST']) == 193 and a['stats']['p2_test_removed_by_family_rule'] == 7
    assert any(m.SPLIT_RULE_CONFLICT in n for n in a['notes'])
    res = {r['id']: r for r in m.run_assertions(a['blocks'], g, 100, 300)}
    assert res['L-B']['result'] == 'PASS'


def test_cross_year_family_reported_not_deleted():
    tasks = _tasks({2009: 5, 2012: 150})
    ids = [t.app_id for t in tasks]
    g = m.build_groups(ids, related_links=[(ids[0], ids[5])])  # TRAIN task <-> 2012 task
    a = m.assign_blocks(tasks, g, _cfg(n1=50, val_n=0))
    assert sum(len(a['blocks'][b]) for b in ('P1-TEST', 'P2-TEST')) == 150
    x = {r['id']: r for r in m.run_assertions(a['blocks'], g, 50, 150)}['L-B-xyear']
    assert x['result'] == 'REPORT' and sum(x['detail'].values()) == 1


def test_overlap_assertion_fails_and_blocks_freeze():
    g = m.build_groups(['a', 'b', 'c'])
    blocks = {b: [] for b in m.BLOCKS}
    blocks['TRAIN'], blocks['P1-TEST'] = ['a', 'b'], ['b']
    res = m.run_assertions(blocks, g, 1, 1)
    assert {r['id']: r['result'] for r in res}['A1-A4'] == 'FAIL'
    with pytest.raises(m.ManifestError):
        m.assert_all_pass(res)


def test_imbalance_flag_does_not_rebalance():
    tasks = _tasks({2011: 10, 2012: 20})
    g = m.build_groups([t.app_id for t in tasks])
    a = m.assign_blocks(tasks, g, _cfg(n1=5, val_n=0, imbalance_tolerance=0.0))
    n0, n1 = len(a['blocks']['P1-DEV']), len(a['blocks']['P2-DEV'])
    assert n0 + n1 == 10
    if n0 != n1:
        assert not a['stats']['dev_2011_imbalance_ok']


def test_metadata_reader_ignores_label_columns_and_refuses_requests():
    tsv = ('app_id\tsplit\tfiling_date\tmail_dt\tart_unit\tipc4_primary\tn_K\tn_K_out3\n'
           '12000001\tDEV\t2011-03-02\t2012-01-01\t1712\tA61B\t4\t2\n')
    rows = m.read_task_metadata(io.StringIO(tsv))
    assert rows == [m.TaskMeta('12000001', 2011, '1712', 'A61B')]
    assert not hasattr(rows[0], 'n_K')
    with pytest.raises(m.ProtectedAccessError):
        m.assert_metadata_only(['app_id', 'n_K'])
    with pytest.raises(m.ManifestError):
        m.read_task_metadata(io.StringIO('app_id\tfiling_date\na\t2011\na\t2011\n'))


def test_manifest_hash_is_content_bound_and_synthetic_cannot_freeze():
    tasks = _tasks(FIX)
    g = m.build_groups([t.app_id for t in tasks])
    a = m.build_manifest(tasks, g, _cfg(), {'x': '0' * 64}, 'c' * 64, synthetic=True)
    b = m.build_manifest(tasks, g, _cfg(), {'x': '0' * 64}, 'c' * 64, synthetic=True)
    assert a['manifest_sha256'] == b['manifest_sha256']
    c = m.build_manifest(tasks, g, _cfg(n1=101), {'x': '0' * 64}, 'c' * 64, synthetic=True)
    assert c['manifest_sha256'] != a['manifest_sha256']
    with pytest.raises(m.ManifestError):
        m.freeze(a)
    tampered = dict(a, synthetic=False)          # content changed after hashing
    with pytest.raises(m.ManifestError):
        m.freeze(tampered)


def _frozen_fixture():
    tasks = _tasks(FIX)
    g = m.build_groups([t.app_id for t in tasks])
    man = m.build_manifest(tasks, g, _cfg(), {'x': '0' * 64}, 'c' * 64, synthetic=False)
    return m.freeze(man)


def test_gold_gate_requires_bound_approval_and_single_look(tmp_path):
    man = _frozen_fixture()
    log = tmp_path / 'open-log.jsonl'
    reader = lambda: {'gold': 'fixture'}
    assert m.ProtectedGoldGate(man, log).open('P1-DEV', reader) == {'gold': 'fixture'}
    with pytest.raises(m.ProtectedAccessError):
        m.ProtectedGoldGate(man, log).open('P1-TEST', reader)
    wrong = m.GoldApproval('0' * 64, ('P1-TEST',), 'owner', '2026-11-18', 'test')
    with pytest.raises(m.ProtectedAccessError):
        m.ProtectedGoldGate(man, log, wrong).open('P1-TEST', reader)
    ok = m.GoldApproval(man['manifest_sha256'], ('P1-TEST',), 'owner', '2026-11-18', 'test')
    with pytest.raises(m.ProtectedAccessError):
        m.ProtectedGoldGate(man, log, ok).open('P2-TEST', reader)
    assert m.ProtectedGoldGate(man, log, ok).open('P1-TEST', reader) == {'gold': 'fixture'}
    with pytest.raises(m.ProtectedAccessError):
        m.ProtectedGoldGate(man, log, ok).open('P1-TEST', reader)
    unfrozen = dict(man, frozen=False)
    with pytest.raises(m.ProtectedAccessError):
        m.ProtectedGoldGate(unfrozen, tmp_path / 'l2', ok).open('P1-TEST', reader)


def test_approval_loader_validates_fields(tmp_path):
    p = tmp_path / 'a.json'
    p.write_text(json.dumps({'manifest_sha256': 'x', 'blocks': ['P1-TEST']}), encoding='utf-8')
    with pytest.raises(m.ProtectedAccessError):
        m.load_approval(p)


def test_sealed_corpus_union_hides_positive_ids():
    out = m.sealed_corpus_union(lambda: ['p1', 'p2'], ['d1', 'd2', 'p2'], 'corpus-v1')
    assert out['n_corpus'] == 4 and out['n_enriched_positive'] == 2
    assert set(out['corpus_doc_ids']) == {'p1', 'p2', 'd1', 'd2'}
    assert 'p1' not in json.dumps({k: v for k, v in out.items() if k != 'corpus_doc_ids'})
    assert out['corpus_doc_ids'] == m.sealed_corpus_union(lambda: ['p2', 'p1'], ['d2', 'd1'], 'corpus-v1')['corpus_doc_ids']


def test_leakage_audits():
    claim = 'a pump comprising a reservoir a controller and a valve that opens below five kpa'
    strata = m.near_duplicate_strata({'q1': claim, 'q2': 'an optical lens with a coated surface for imaging'},
                                     {'t1': claim + ' wherein'})
    assert strata == {'q1': True, 'q2': False}
    tags = m.unseen_document_tags({'q1': ['d1', 'd2'], 'q2': ['d3']}, ['d1'], ['d9'])
    assert tags['tasks_all_unseen'] == 1 and tags['share_positives_seen'] == pytest.approx(1 / 3)
    assert m.self_target_violations({'q1': ['own', 'd2'], 'q2': ['d3']}, {'q1': 'own', 'q2': 'x'}) == ['q1']


def test_public_view_has_no_raw_ids():
    man = _frozen_fixture()
    pv = m.public_view(man, 'release-salt')
    raw = json.dumps(pv)
    assert 'blocks' not in pv and '2012000001' not in raw
    assert len(pv['blocks_hashed']['P1-TEST']) == 100


def test_cli_synthetic_smoke_and_real_data_guard(tmp_path):
    import importlib.util, pathlib
    p = pathlib.Path(__file__).resolve().parents[1] / 'scripts' / 'healthtech' / 'build_canonical_split_manifest.py'
    spec = importlib.util.spec_from_file_location('bcsm', p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.main(['--synthetic', str(tmp_path / 'o')]) == 0
    pub = json.loads((tmp_path / 'o' / 'manifest-public.json').read_text(encoding='utf-8'))
    assert pub['synthetic'] is True and pub['frozen'] is False and 'blocks' not in pub
    with pytest.raises(m.ManifestError):
        mod.main(['--synthetic', str(tmp_path / 'o')])          # never overwrite
    with pytest.raises(SystemExit):
        mod.main(['--tasks', 'x.tsv', str(tmp_path / 'r')])     # no approval -> refuse
    bad = tmp_path / 'appr.json'
    bad.write_text('{"action": "other", "approved_by": "x"}', encoding='utf-8')
    salt = tmp_path / 's.txt'; salt.write_text('s', encoding='utf-8')
    tsv = tmp_path / 't.tsv'; tsv.write_text('app_id\tfiling_date\na\t2012-01-01\n', encoding='utf-8')
    with pytest.raises(m.ManifestError):
        mod.main(['--tasks', str(tsv), '--build-approval', str(bad), '--release-salt-file', str(salt), str(tmp_path / 'r')])
