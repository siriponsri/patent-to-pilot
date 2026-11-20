import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts' / 'healthtech'))
import am7_lib as L  # noqa: E402


def row(u, basis='103', dom='OUT3', pub='2005-01-01'):
    return {'unit': u, 'basis': basis, 'dom_ipc3': dom, 'unit_first_pub': pub}


def test_c103_set_rules():
    rows = [row('A:1', dom='IN3'), row('A:2'), row('A:3', basis='102'), row('A:4', pub='2012-01-01'),
            row('A:5', pub=''), row('A:00000009'), row('A:6', dom='NOIPC'), row('A:7')]
    s = L.c103_set(rows, '2011-06-01', '00000009', corpus={'A:1', 'A:2', 'A:3', 'A:4', 'A:5', 'A:00000009', 'A:6'})
    assert s['IN3'] == {'A:1'} and s['OUT3'] == {'A:2'} and s['NOIPC'] == {'A:6'}


def test_anchor_is_hash_rule_and_order_free():
    a = L.anchor_of('12345678', ['A:1', 'A:2', 'A:3'])
    assert a == L.anchor_of('12345678', ['A:3', 'A:1', 'A:2'])
    assert a == min(['A:1', 'A:2', 'A:3'], key=lambda u: L.sha(f'p1-am7-anchor-v1|12345678|{u}'))


def test_rank_ties_by_unit_rank_and_mask():
    s = np.array([0.5, 0.9, 0.5, -np.inf, 0.5])
    ur = np.array([4, 0, 1, 2, 3])
    assert L.rank_from_scores(s, ur, depth=3).tolist() == [1, 2, 4]
    assert L.rank_from_scores(s, ur, depth=10).tolist() == [1, 2, 4, 0]


def test_topk_rows_matches_reference():
    rng = np.random.default_rng(0)
    S = np.round(rng.random((5, 400)), 2).astype(np.float32)   # many ties
    S[0, :50] = -np.inf
    ur = rng.permutation(400)
    got = L.topk_rows(S, ur, depth=30, slack=4)
    for r in range(5):
        assert got[r].tolist() == L.rank_from_scores(S[r], ur, 30).tolist()


def test_rrf():
    out = L.rrf([np.array([1, 2, 3]), np.array([3, 2, 4])], k=60, depth=10, unit_rank=np.arange(10))
    assert out.tolist()[:2] == [3, 2] and set(out.tolist()) == {1, 2, 3, 4}


def test_n5_ranking_counts_first_then_u0():
    base = np.array([0.1, 0.9, 0.8, -np.inf, 0.7, 0.6])
    out = L.n5_ranking({5: 2, 0: 2, 3: 9, 4: 1}, base, unit_rank=np.arange(6), depth=6)
    assert out.tolist() == [5, 0, 4, 1, 2]          # masked unit 3 dropped; ties by U0 score; rest in U0 order


def test_mmr_batch_equals_single():
    rng = np.random.default_rng(1)
    V = rng.normal(size=(2, 20, 8)); V /= np.linalg.norm(V, axis=2, keepdims=True)
    q = rng.normal(size=(2, 8)); q /= np.linalg.norm(q, axis=1, keepdims=True)
    qs = np.einsum('bnd,bd->bn', V, q)
    order = np.argsort(-qs, axis=1)
    cands = np.take_along_axis(np.tile(np.arange(100, 120), (2, 1)), order, axis=1)
    Vs = np.take_along_axis(V, order[:, :, None], axis=1); qss = np.take_along_axis(qs, order, axis=1)
    b = L.mmr_batch(cands, Vs.astype(np.float32), qss.astype(np.float32), 0.7, depth=10)
    for i in range(2):
        assert b[i].tolist() == L.mmr(cands[i], Vs[i], qss[i], 0.7, depth=10).tolist()
    assert L.mmr_batch(cands, Vs.astype(np.float32), qss.astype(np.float32), 1.0, depth=10)[0].tolist() == cands[0, :10].tolist()


def test_metrics():
    r = np.array([5, 1, 7, 2])
    assert L.recall_at(r, {1, 2}, 2) == 0.5 and L.recall_at(r, set(), 2) is None
    assert L.mrr_first(r, {7}) == pytest.approx(1 / 3) and L.mrr_first(r, {9}) == 0.0


def test_cluster_bootstrap_and_mde():
    v = np.r_[np.full(500, 0.02), np.full(500, 0.0)]
    m, lo, hi = L.cluster_bootstrap(v, np.arange(1000) // 20, b=500)
    assert m == pytest.approx(0.01) and lo < 0.01 < hi
    assert L.mde(0.3, 10000) == pytest.approx(3.083024 * 0.3 / 100, rel=1e-4)


def test_pick_param_and_first_best():
    assert L.pick_param({0.05: 0.30, 0.1: 0.3005, 'inf': 0.2}) == 0.05
    assert L.pick_param({0.5: 0.2, 0.7: 0.2004, 0.9: 0.1}, prefer='large') == 0.7
    assert L.pick_first_best(['a', 'b', 'c'], {'a': 0.30, 'b': 0.3008, 'c': 0.2}) == 'a'


def test_select_across_margin():
    n = 2000
    cl = np.arange(n) % 100
    base = np.zeros(n)
    pq = {'A1': base, 'A2': base + 0.005, 'A4p': base + 0.03, 'A4': base + 0.031}
    best, log = L.select_across(['A1', 'A2', 'A4p', 'A4'], pq, cl)
    assert best == 'A4p' and [x['replaced'] for x in log] == [False, True, False]


def test_cocitation_filters_and_guard():
    acts = [(20100101, 'X1', 'g1', (1, 2, 3)), (20120101, 'X2', 'g2', (1, 4)), (20100101, 'Q', 'gq', (1, 5)),
            (20100101, 'Y', 'gq', (1, 6)), (20090101, 'X3', 'g3', (1, 2))]
    cc = L.CoCitation(acts)
    c, n = cc.counts(1, 20110101, 'Q', 'gq')
    assert dict(c) == {2: 2, 3: 1} and n == 2
    with pytest.raises(RuntimeError):
        cc.counts(1, 20110101, 'Q', 'gq', protected_apps=frozenset({'X3'}))


def test_matched_decoy():
    d = L.matched_decoy([10, 11, 12, 13], [0.9, 0.8, 0.79, 0.5], [True, True, True, False], {12}, 10, 0.795,
                        unit_rank=np.arange(20))
    assert d == 11
    assert L.matched_decoy([10], [0.9], [True], set(), 10, 0.9, np.arange(20)) is None


def _synthetic(tmp_path, n=300, d=16, seed=3):
    import json, pickle
    rng = np.random.default_rng(seed)
    P = rng.normal(size=(n, d)); P /= np.linalg.norm(P, axis=1, keepdims=True)
    units = [f'A:{10000000 + i}' for i in range(n)]
    pub = rng.integers(19900101, 20100101, size=n)
    codes = ['A01', 'B02', 'C03', 'G06']
    uipc = {i: set(rng.choice(codes, size=rng.integers(1, 3), replace=False)) for i in range(n) if i % 7}
    inv = {}
    for i, cs in uipc.items():
        for c in cs:
            inv.setdefault(c, []).append(i)
    ipc_inv = {c: np.array(sorted(v)) for c, v in inv.items()}
    has = np.zeros(n, dtype=bool); has[list(uipc)] = True
    Q = {}; qd = tmp_path / 'q'; qd.mkdir()
    for b, m in (('P1-DEV', 60), ('VAL', 12)):
        qs, ids = [], []
        V = rng.normal(size=(m, d)); V /= np.linalg.norm(V, axis=1, keepdims=True)
        for j in range(m):
            app = f'{20000000 + j}' if b == 'P1-DEV' else f'{30000000 + j}'
            fd = 20110101
            vis = [i for i in range(n) if pub[i] < fd]
            tg = sorted(rng.choice(vis, size=3, replace=False).tolist())
            q = {'app': app, 'fd': fd, 'mail': 20120101, 'au': str(j % 6), 'ipc3': ['A01'], 'group': 'A:' + app,
                 'pos': {'ALL': tg, 'OUT': tg[:2], 'IN': tg[2:]}, 'n_out_strict': 2, 'k_units': tg}
            if j % 4:
                q['e2'] = {'anchor': tg[2], 'targets': tg[:2], 'n_strict': 3, 'clean': j % 2 == 0,
                           'unseen_targets': tg[:1], 'all_coref': tg[:2]}
            qs.append(q); ids.append(app)
        coh = [q for q in qs if 'e2' in q]
        for i, q in enumerate(coh):
            q['e2']['shuffle_anchor'] = coh[(i + 1) % len(coh)]['e2']['anchor']
        Q[b] = qs
        np.save(qd / f'Q-{b}.f16.npy', V.astype(np.float16)); json.dump(ids, open(qd / f'Q-{b}.ids.json', 'w'))
    rank = np.empty(n, dtype=np.int64); rank[np.argsort(np.array(units, dtype=object))] = np.arange(n)
    prep = tmp_path / 'prep'; prep.mkdir()
    pickle.dump({'units': units, 'unit_rank': rank, 'unit_pub': pub, 'ipc_inv': ipc_inv, 'unit_has_ipc': has,
                 'queries': Q}, open(prep / 'meta.pkl', 'wb'))
    acts = [(20100101 + k, f'4{k:07d}', f'g{k}', tuple(sorted(rng.choice(n, size=3, replace=False).tolist()))) for k in range(400)]
    pickle.dump(acts, open(prep / 'cocite.pkl', 'wb'))
    np.save(tmp_path / 'P.f16.npy', P.astype(np.float16))
    return prep, qd, P, pub, Q


def test_stage2a_end_to_end_synthetic(tmp_path, monkeypatch):
    import json
    import am7_stage2a as S2
    prep, qd, P, pub, Q = _synthetic(tmp_path)
    out = tmp_path / 'out'
    monkeypatch.setattr(sys, 'argv', ['x', str(prep), str(tmp_path / 'P.f16.npy'), str(qd), str(out), '--batch', '16'])
    S2.main()
    res = json.load(open(out / 'stage2a-results.json'))
    sel = res['selection']
    assert sel['A_star'] in ('A1:0.5', 'A1:1', 'A2:0.25', 'A2:0.5', 'A4p', 'A4')
    assert sel['N_star'] in ('N1', 'N2', 'N3', 'N5') or sel['N_star'].startswith('N4E2:')
    dev = res['blocks']['P1-DEV']
    assert dev['n_cohort'] == 45 and 'P*' in dev['E1'] and 'A*|shuffle' in dev['E2']
    # U0 E1 OUT recall equals a brute-force recomputation with the same mask (fp16-rounded vectors)
    Pf = np.load(tmp_path / 'P.f16.npy').astype(np.float32)
    V = np.load(qd / 'Q-P1-DEV.f16.npy').astype(np.float32)
    vals = []
    for j, q in enumerate(Q['P1-DEV']):
        s = V[j] @ Pf.T; s[pub >= q['fd']] = -np.inf
        top = set(np.argsort(-s, kind='stable')[:200].tolist())
        vals.append(sum(t in top for t in q['pos']['OUT']) / len(q['pos']['OUT']))
    assert dev['E1']['U0']['OUT_R@200'][0] == pytest.approx(round(float(np.mean(vals)), 5), abs=1e-5)
    assert set(res['power']) == {'D1', 'D2', 'C4'}


def test_sensitivity_synthetic_reordered_backbone(tmp_path, monkeypatch):
    import json, pickle
    import am7_stage2a as S2
    import am7_sensitivity as SE
    prep, qd, P, pub, Q = _synthetic(tmp_path)
    out = tmp_path / 'out'
    monkeypatch.setattr(sys, 'argv', ['x', str(prep), str(tmp_path / 'P.f16.npy'), str(qd), str(out), '--batch', '16'])
    S2.main()
    units = pickle.load(open(prep / 'meta.pkl', 'rb'))['units']
    ser = tmp_path / 'ser'; ser.mkdir()
    order = list(range(len(units)))[::-1]                      # a different corpus row order
    with open(ser / 'passages.jsonl', 'w') as f:
        for i in order:
            f.write(json.dumps({'unit': units[i], 'text': 'x'}) + '\n')
    np.save(tmp_path / 'Pq.f16.npy', P[order].astype(np.float16))
    bm = tmp_path / 'bm'; bm.mkdir()
    for b, qs in Q.items():
        with open(bm / f'run-{b}.tsv', 'w') as f:
            f.write('app_id\trank\tunit\tscore\n')
            for q in qs:
                for r, i in enumerate(range(0, 300, 3)):
                    f.write(f"{q['app']}\t{r + 1}\t{units[i]}\t{1.0 / (r + 1)}\n")
    res = tmp_path / 'sens.json'
    SE.main([str(prep), str(out / 'stage2a-results.json'), str(tmp_path / 'Pq.f16.npy'), str(ser), str(qd), str(bm), str(res)])
    r = json.load(open(res))
    main_u0 = json.load(open(out / 'stage2a-results.json'))['blocks']['P1-DEV']['E2']['U0']['MR@200'][0]
    assert r['blocks']['P1-DEV']['U0_qwen3_MR@200'][0] == pytest.approx(main_u0, abs=1e-6)   # same vectors, reordered


def test_stage2a_queries_without_vector_score_zero(tmp_path, monkeypatch):
    import json
    import am7_stage2a as S2
    prep, qd, P, pub, Q = _synthetic(tmp_path)
    ids = json.load(open(qd / 'Q-P1-DEV.ids.json')); V = np.load(qd / 'Q-P1-DEV.f16.npy')
    json.dump(ids[5:], open(qd / 'Q-P1-DEV.ids.json', 'w')); np.save(qd / 'Q-P1-DEV.f16.npy', V[5:])
    out = tmp_path / 'out'
    monkeypatch.setattr(sys, 'argv', ['x', str(prep), str(tmp_path / 'P.f16.npy'), str(qd), str(out), '--batch', '16'])
    S2.main()
    dev = json.load(open(out / 'stage2a-results.json'))['blocks']['P1-DEV']
    assert dev['n_queries'] == 60 and dev['n_queries_with_vector'] == 55 and dev['n_cohort'] == 45
    assert dev['E1']['U0']['OUT_R@200'][1] == 60 and dev['E2']['U0']['MR@200'][1] == 45


def test_render_synthetic(tmp_path, monkeypatch):
    import json
    import am7_stage2a as S2
    import render_am7_stage2a as R
    prep, qd, P, pub, Q = _synthetic(tmp_path)
    out = tmp_path / 'out'
    monkeypatch.setattr(sys, 'argv', ['x', str(prep), str(tmp_path / 'P.f16.npy'), str(qd), str(out), '--batch', '16'])
    S2.main()
    md = R.render(json.load(open(out / 'stage2a-results.json')))
    assert r'**A\* =' in md and '| U0 |' in md and 'Owner gate' in md
