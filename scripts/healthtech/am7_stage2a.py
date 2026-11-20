"""AM-7 / AM-7.1 stage 2a on P1-DEV and VAL (descriptive; never TEST). CPU only.

Systems (frozen in AM-7 §4 and AM-7.1 §1-§6), all with the RPD mask (first_pub < filing date) and own-unit exclusion
as in dense_bridgeret_v3.py; E2 rankings also remove the anchor; ties by unit id:
  E1 (all block queries): U0 (= Z-PatEmbed), N4-E1(gamma), MMR(lambda), P* (after A* is selected).
  E2 (A-eligible cohort): U0, N1, N2, N3, N4-E2(gamma), N5, A1(beta), A2(gamma), A4', A4; controls: matched decoy,
  shuffled anchor (descriptive).
Selection on P1-DEV only (AM-7.1 §6; §4 for N*, L*); VAL is reported with the DEV-selected systems.
Usage: python3 am7_stage2a.py <prep_dir> <passages.f16.npy> <query_dir> <out_dir> [--batch 256]
  query_dir holds Q-<BLOCK>.f16.npy + Q-<BLOCK>.ids.json (rows in the order of the ids).
"""
import argparse, json, os, pickle, sys, time
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import am7_lib as L  # noqa: E402

A1_BETAS = (0.5, 1.0)
A2_GAMMAS = (0.25, 0.5)
N4_GAMMAS = (0.05, 0.10, 0.20, 'inf')
MMR_LAMBDAS = (0.5, 0.7, 0.9)
BLOCKS = ('P1-DEV', 'VAL')
INF_PENALTY = 10.0          # cos in [-1, 1]: subtracting 10 puts every shared unit after every non-shared unit
TEST_N = {'E1_OUT': (9500, 9800), 'E2': (7360, 7850), 'E2_clean': (2420, 2570)}


def gname(g):
    return 'inf' if g == 'inf' else f'{g:g}'


def pen(g):
    return INF_PENALTY if g == 'inf' else g


class Ctx:
    def __init__(self, prep, pfile, log):
        meta = pickle.load(open(prep / 'meta.pkl', 'rb'))
        self.units, self.unit_rank, self.unit_pub = meta['units'], meta['unit_rank'], meta['unit_pub']
        self.uidx = {u: i for i, u in enumerate(self.units)}
        self.ipc_inv, self.unit_has_ipc, self.Q = meta['ipc_inv'], meta['unit_has_ipc'], meta['queries']
        self.cc = L.CoCitation(pickle.load(open(prep / 'cocite.pkl', 'rb')))
        log('meta+cocite')
        self.P = np.load(pfile).astype(np.float32)
        if self.P.shape[0] != len(self.units):
            raise SystemExit('vector rows != units')
        log('vectors', self.P.shape)
        self.n = len(self.units)

    def shared_row(self, ipc3):
        s = np.zeros(self.n, dtype=bool)
        for c in ipc3:
            v = self.ipc_inv.get(c)
            if v is not None:
                s[v] = True
        return s

    def mask_matrix(self, qs, extra=None):
        M = self.unit_pub[None, :] >= np.array([q['fd'] for q in qs])[:, None]
        for r, q in enumerate(qs):
            own = self.uidx.get('A:' + q['app'])
            if own is not None:
                M[r, own] = True
            for i in (extra[r] if extra is not None else ()):
                if i is not None:
                    M[r, i] = True
        return M

    def masked(self, S, qs, extra=None):
        S[self.mask_matrix(qs, extra)] = -np.inf
        return S

    def n5(self, q, anchor, base_row):
        c, nsrc = self.cc.counts(anchor, q['mail'], q['app'], q['group'])
        c = {i: v for i, v in c.items() if np.isfinite(base_row[i])}
        return L.n5_ranking(c, base_row, self.unit_rank), len(c), nsrc


def e1_metrics(lst, q):
    pos = {k: set(v) for k, v in q['pos'].items()}
    out = {}
    for k, cut in (('OUT', 200), ('OUT', 1000), ('IN', 200), ('ALL', 200)):
        if pos[k]:
            out[f'{k}_R@{cut}'] = L.recall_at(lst, pos[k], cut)
    return out


def e2_metrics(lst, q):
    e = q['e2']; t = set(e['targets'])
    m = {f'MR@{k}': L.recall_at(lst, t, k) for k in (50, 200, 1000)}
    m['MRR'] = L.mrr_first(lst, t)
    top = set(int(i) for i in lst[:200])
    m['MR@200_strict'] = sum(1 for i in t if i in top) / max(e['n_strict'], len(t))
    if e['unseen_targets']:
        m['MR@200_unseen'] = L.recall_at(lst, set(e['unseen_targets']), 200)
    if e['all_coref']:
        m['allcoref_R@200'] = L.recall_at(lst, set(e['all_coref']), 200)
    return m


def run_block(ctx, b, Qv, ids, batch, log):
    qs_all = ctx.Q[b]
    qmap = {q['app']: q for q in qs_all}
    rows = [qmap[a] for a in ids]
    E1 = defaultdict(dict)        # system -> app -> metrics
    E2 = defaultdict(dict)
    keep = defaultdict(dict)      # lists kept for phase 2: (system) -> app -> list
    aux = {}
    for s0 in range(0, len(rows), batch):
        qs = rows[s0:s0 + batch]
        Qb = Qv[s0:s0 + batch]
        S = ctx.masked(Qb @ ctx.P.T, qs)
        shared = np.stack([ctx.shared_row(q['ipc3']) for q in qs])
        u0 = L.topk_rows(S, ctx.unit_rank)
        for r, q in enumerate(qs):
            E1['U0'][q['app']] = e1_metrics(u0[r], q)
            keep['U0E1'][q['app']] = u0[r]
        for g in N4_GAMMAS:
            lst = L.topk_rows(S - np.float32(pen(g)) * shared, ctx.unit_rank)
            for r, q in enumerate(qs):
                E1[f'N4E1:{gname(g)}'][q['app']] = e1_metrics(lst[r], q)
        cand = np.stack([x[:L.DEPTH] for x in u0]) if all(len(x) == L.DEPTH for x in u0) else None
        if cand is not None:
            V = ctx.P[cand]
            qsims = np.take_along_axis(S, cand, axis=1)
            simm = np.matmul(V, np.swapaxes(V, 1, 2))
            for lam in MMR_LAMBDAS:
                mm = L.mmr_batch(cand, V, qsims.astype(np.float32), lam, sim=simm)
                for r, q in enumerate(qs):
                    E1[f'MMR:{lam:g}'][q['app']] = e1_metrics(mm[r], q)
        else:
            for r, q in enumerate(qs):
                c = u0[r]; V = ctx.P[c]
                for lam in MMR_LAMBDAS:
                    E1[f'MMR:{lam:g}'][q['app']] = e1_metrics(L.mmr(c, V, S[r, c], lam), q)
        # ---------------- E2 (cohort rows of this batch)
        ci = [r for r, q in enumerate(qs) if 'e2' in q]
        if ci:
            qe = [qs[r] for r in ci]
            anc = np.array([q['e2']['anchor'] for q in qe])
            c_qa = np.einsum('ij,ij->i', Qb[ci], ctx.P[anc])
            M = ctx.mask_matrix(qe, extra=[[a] for a in anc])
            Sq_raw = Qb[ci] @ ctx.P.T
            Sa_raw = ctx.P[anc] @ ctx.P.T
            mk = lambda X: np.where(M, np.float32(-np.inf), X).astype(np.float32, copy=False)
            Se, Sa = mk(Sq_raw), mk(Sa_raw)
            Sh = shared[ci]
            sys_lists = {'U0': L.topk_rows(Se, ctx.unit_rank), 'N1': L.topk_rows(Sa, ctx.unit_rank),
                         'N3': L.topk_rows(mk(Sq_raw + Sa_raw), ctx.unit_rank)}
            for be in A1_BETAS:
                sys_lists[f'A1:{be:g}'] = L.topk_rows(mk(Sq_raw - np.float32(be) * c_qa[:, None] * Sa_raw), ctx.unit_rank)
            for g in A2_GAMMAS:
                sys_lists[f'A2:{g:g}'] = L.topk_rows(mk(Sq_raw - np.float32(g) * Sa_raw), ctx.unit_rank)
            for g in N4_GAMMAS:
                sys_lists[f'N4E2:{gname(g)}'] = L.topk_rows(Se - np.float32(pen(g)) * Sh, ctx.unit_rank)
            del Sq_raw, Sa_raw
            sys_lists['N2'] = [L.rrf([sys_lists['U0'][r], sys_lists['N1'][r]], unit_rank=ctx.unit_rank) for r in range(len(ci))]
            n5l, a4p = [], []
            for r, q in enumerate(qe):
                lst, npos, nsrc = ctx.n5(q, int(anc[r]), Se[r])
                n5l.append(lst); aux[q['app']] = {'n5_pos': npos, 'n5_src': nsrc}
                a4p.append(L.rrf([sys_lists['U0'][r], lst], unit_rank=ctx.unit_rank))
            sys_lists['N5'], sys_lists['A4p'] = n5l, a4p
            for name, lists in sys_lists.items():
                for r, q in enumerate(qe):
                    E2[name][q['app']] = e2_metrics(lists[r], q)
            for name in ['U0', 'N5'] + [f'A1:{x:g}' for x in A1_BETAS] + [f'A2:{x:g}' for x in A2_GAMMAS]:
                for r, q in enumerate(qe):
                    keep[name][q['app']] = sys_lists[name][r]
            for r, q in enumerate(qe):        # decoy candidates (AM-7.1 §5) from the anchor-removed U0 list
                top = sys_lists['U0'][r]
                d = L.matched_decoy(top, Se[r, top], Sh[r, top], set(q['k_units']), int(anc[r]),
                                    float(c_qa[r]), ctx.unit_rank)
                aux[q['app']].update({'decoy': d, 'c_qa': float(c_qa[r])})
        log(b, 'batch', s0 + len(qs), '/', len(rows))
    return rows, E1, E2, keep, aux


def a_star_list(ctx, kind, param, qs, Qb, anchors, extra_remove, abar=None):
    """A*(q, anchor) for kind in A1/A2/A4p/A4 with an arbitrary anchor (pseudo-anchor, decoy, shuffled)."""
    M = ctx.mask_matrix(qs, extra=[[a] + list(x) for a, x in zip(anchors, extra_remove)])
    mk = lambda X: np.where(M, np.float32(-np.inf), X).astype(np.float32, copy=False)
    Sq_raw = Qb @ ctx.P.T
    S = mk(Sq_raw)
    anc = np.array(anchors)
    out = []
    need_vec = kind in ('A1', 'A2') or (kind == 'A4' and abar[0] in ('A1', 'A2'))
    if need_vec:
        Sa_raw = ctx.P[anc] @ ctx.P.T
        c_qa = np.einsum('ij,ij->i', Qb, ctx.P[anc])

    def vec_list(k, p):
        if k == 'A1':
            return L.topk_rows(mk(Sq_raw - np.float32(p) * c_qa[:, None] * Sa_raw), ctx.unit_rank)
        return L.topk_rows(mk(Sq_raw - np.float32(p) * Sa_raw), ctx.unit_rank)
    if kind in ('A1', 'A2'):
        return vec_list(kind, param)
    u0 = L.topk_rows(S, ctx.unit_rank)
    base = vec_list(*abar) if kind == 'A4' else u0
    for r, q in enumerate(qs):
        n5, _, _ = ctx.n5(q, int(anc[r]), S[r])
        out.append(L.rrf([base[r], n5], unit_rank=ctx.unit_rank))
    return out


EMPTY = np.empty(0, dtype=np.int64)
CONTROLS = ('A*|decoy', 'A*|shuffle')


def fill_missing(qs_all, E1, E2):
    """AM-7 §3 / evaluator convention: a query with no output (no query text, hence no vector) scores 0."""
    n = 0
    for q in qs_all:
        for name, d in E1.items():
            if q['app'] not in d:
                d[q['app']] = e1_metrics(EMPTY, q); n += 1
        if 'e2' in q:
            for name, d in E2.items():
                if name not in CONTROLS and q['app'] not in d:
                    d[q['app']] = e2_metrics(EMPTY, q)
    return n


def mean_of(d, key, apps=None):
    v = [m[key] for a, m in d.items() if (apps is None or a in apps) and m.get(key) is not None]
    return (round(float(np.mean(v)), 5), len(v)) if v else (None, 0)


def per_query(d, key, apps):
    return np.array([d[a][key] for a in apps], dtype=np.float64)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('prep'); ap.add_argument('pfile'); ap.add_argument('qdir'); ap.add_argument('out')
    ap.add_argument('--batch', type=int, default=256)
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=False); os.chmod(out, 0o700)
    t0 = time.time(); log = lambda *x: print(round(time.time() - t0), 's', *x, flush=True)
    ctx = Ctx(Path(a.prep), a.pfile, log)
    R = {}
    for b in BLOCKS:
        ids = json.load(open(Path(a.qdir) / f'Q-{b}.ids.json'))
        Qv = np.load(Path(a.qdir) / f'Q-{b}.f16.npy').astype(np.float32)
        R[b] = run_block(ctx, b, Qv, ids, a.batch, log) + (Qv, ids)
    for b in BLOCKS:
        fill_missing(ctx.Q[b], R[b][1], R[b][2])
    # ---------------- selection on P1-DEV (AM-7.1 §1, §2, §4, §6)
    rows, E1, E2, keep, aux, Qv, ids = R['P1-DEV']
    coh = [q['app'] for q in ctx.Q['P1-DEV'] if 'e2' in q]
    au = {q['app']: q['au'] for q in ctx.Q['P1-DEV']}
    sel = {}
    sel['A1_beta'] = L.pick_param({x: mean_of(E2[f'A1:{x:g}'], 'MR@200')[0] for x in A1_BETAS})
    sel['A2_gamma'] = L.pick_param({x: mean_of(E2[f'A2:{x:g}'], 'MR@200')[0] for x in A2_GAMMAS})
    sel['N4E2_gamma'] = L.pick_param({x: mean_of(E2[f'N4E2:{gname(x)}'], 'MR@200')[0] for x in N4_GAMMAS})
    sel['N4E1_gamma'] = L.pick_param({x: mean_of(E1[f'N4E1:{gname(x)}'], 'OUT_R@200')[0] for x in N4_GAMMAS})
    sel['MMR_lambda'] = L.pick_param({x: mean_of(E1[f'MMR:{x:g}'], 'OUT_R@200')[0] for x in MMR_LAMBDAS}, prefer='large')
    a1n, a2n = f"A1:{sel['A1_beta']:g}", f"A2:{sel['A2_gamma']:g}"
    clusters = np.array([au[x] for x in coh])
    pq = {n: per_query(E2[n], 'MR@200', coh) for n in (a1n, a2n, 'A4p')}
    inc12, log12 = L.select_across([a1n, a2n], {k: pq[k] for k in (a1n, a2n)}, clusters)
    sel['Abar'] = inc12
    abar = ('A1', sel['A1_beta']) if inc12 == a1n else ('A2', sel['A2_gamma'])
    # A4 = RRF(Abar, N5) on both blocks
    for b in BLOCKS:
        rws, e1, e2, kp, ax, _, _ = R[b]
        for q in rws:
            if 'e2' in q:
                e2['A4'][q['app']] = e2_metrics(L.rrf([kp[inc12][q['app']], kp['N5'][q['app']]], unit_rank=ctx.unit_rank), q)
    for b in BLOCKS:
        fill_missing(ctx.Q[b], R[b][1], R[b][2])
    pq['A4'] = per_query(E2['A4'], 'MR@200', coh)
    astar, logx = L.select_across([inc12, 'A4p', 'A4'], {k: pq[k] for k in (inc12, 'A4p', 'A4')}, clusters)
    sel['A_star'] = astar; sel['selection_log'] = log12 + logx
    kind = {'A4p': ('A4p', None), 'A4': ('A4', None)}.get(astar, abar)
    n_names = ['N1', 'N2', 'N3', f"N4E2:{gname(sel['N4E2_gamma'])}", 'N5']
    sel['N_star'] = L.pick_first_best(n_names, {n: mean_of(E2[n], 'MR@200')[0] for n in n_names})
    l_names = ['U0', f"N4E1:{gname(sel['N4E1_gamma'])}", f"MMR:{sel['MMR_lambda']:g}"]
    sel['L_star'] = L.pick_first_best(l_names, {n: mean_of(E1[n], 'OUT_R@200')[0] for n in l_names})
    log('selected', sel)
    # ---------------- phase 2: P*, decoy, shuffled anchor (both blocks)
    for b in BLOCKS:
        rws, e1, e2, kp, ax, Qv, ids = R[b]
        for s0 in range(0, len(rws), a.batch):
            qs = rws[s0:s0 + a.batch]; Qb = Qv[s0:s0 + a.batch]
            pseudo = [int(kp['U0E1'][q['app']][0]) for q in qs]
            ast = a_star_list(ctx, kind[0], kind[1], qs, Qb, pseudo, [()] * len(qs), abar)
            for r, q in enumerate(qs):
                e1['P*'][q['app']] = e1_metrics(L.rrf([kp['U0E1'][q['app']], ast[r]], unit_rank=ctx.unit_rank), q)
            ci = [r for r, q in enumerate(qs) if 'e2' in q]
            for ctl in ('decoy', 'shuffle'):
                cj = [r for r in ci if (ax[qs[r]['app']]['decoy'] is not None if ctl == 'decoy' else True)]
                if not cj:
                    continue
                qe = [qs[r] for r in cj]
                alt = [ax[q['app']]['decoy'] if ctl == 'decoy' else q['e2']['shuffle_anchor'] for q in qe]
                lst = a_star_list(ctx, kind[0], kind[1], qe, Qb[cj], alt, [(q['e2']['anchor'],) for q in qe], abar)
                for r, q in enumerate(qe):
                    e2[f'A*|{ctl}'][q['app']] = e2_metrics(lst[r], q)
            log(b, 'phase2', s0 + len(qs))
    missing = {b: fill_missing(ctx.Q[b], R[b][1], R[b][2]) for b in BLOCKS}
    # ---------------- report
    astar_name = astar
    res = {'format': 'ptp-p1-am7-stage2a-v1', 'descriptive_only': True, 'selection_block': 'P1-DEV', 'selection': sel,
           'blocks': {}}
    for b in BLOCKS:
        rws_v, e1, e2, kp, ax, _, _ = R[b]
        rws = ctx.Q[b]                                   # every block query (no-vector queries scored 0)
        cohort = [q['app'] for q in rws if 'e2' in q]
        clean = {q['app'] for q in rws if q.get('e2', {}).get('clean')}
        blk = {'n_queries': len(rws), 'n_queries_with_vector': len(rws_v),
               'n_cohort_with_vector': sum('e2' in q for q in rws_v), 'n_cohort': len(cohort), 'n_clean': len(clean), 'E1': {}, 'E2': {}, 'E2_clean': {}}
        for name in sorted(e1):
            blk['E1'][name] = {k: mean_of(e1[name], k) for k in ('OUT_R@200', 'OUT_R@1000', 'IN_R@200', 'ALL_R@200')}
        for name in sorted(e2):
            blk['E2'][name] = {k: mean_of(e2[name], k) for k in ('MR@50', 'MR@200', 'MR@1000', 'MRR', 'MR@200_strict',
                                                                 'MR@200_unseen', 'allcoref_R@200')}
            blk['E2_clean'][name] = mean_of(e2[name], 'MR@200', clean)
        cl = np.array([{q['app']: q['au'] for q in rws}[x] for x in cohort])
        contr = {}
        for lab, x, y in (('D1', astar_name, 'U0'), ('D2', astar_name, sel['N_star'])):
            d = np.array([e2[x][q]['MR@200'] - e2[y][q]['MR@200'] for q in cohort])
            m, lo, hi = L.cluster_bootstrap(d, cl)
            contr[lab] = {'contrast': f'{x} - {y}', 'delta': round(m, 5), 'ci95_artunit': [round(lo, 5), round(hi, 5)],
                          'sd_diff': round(float(d.std()), 4), 'deff': round(L.design_effect(d, cl), 3)}
        oq = [q['app'] for q in rws if q['pos']['OUT']]
        clo = np.array([{q['app']: q['au'] for q in rws}[x] for x in oq])
        d = np.array([e1['P*'][q]['OUT_R@200'] - e1[sel['L_star']][q]['OUT_R@200'] for q in oq])
        m, lo, hi = L.cluster_bootstrap(d, clo)
        contr['C4'] = {'contrast': f"P* - {sel['L_star']}", 'delta': round(m, 5), 'ci95_artunit': [round(lo, 5), round(hi, 5)],
                       'sd_diff': round(float(d.std()), 4), 'deff': round(L.design_effect(d, clo), 3)}
        for ctl in ('decoy', 'shuffle'):
            apps = [q for q in cohort if q in e2.get(f'A*|{ctl}', {})]
            if apps:
                dd = np.array([e2[astar_name][q]['MR@200'] - e2[f'A*|{ctl}'][q]['MR@200'] for q in apps])
                cla = np.array([{q['app']: q['au'] for q in rws}[x] for x in apps])
                m, lo, hi = L.cluster_bootstrap(dd, cla)
                contr[f'{ctl}_control'] = {'contrast': f'A*(q,a) - A*(q,{ctl})', 'n': len(apps), 'delta': round(m, 5),
                                           'ci95_artunit': [round(lo, 5), round(hi, 5)]}
        blk['contrasts_descriptive'] = contr
        cv = [q for q in cohort if q in ax]
        blk['n5_coverage'] = round(sum(1 for q in cv if ax[q]['n5_pos'] > 0) / max(1, len(cv)), 4)
        blk['n5_source_actions_median'] = float(np.median([ax[q]['n5_src'] for q in cv])) if cv else None
        blk['decoy_missing'] = sum(1 for q in cv if ax[q]['decoy'] is None)
        blk['queries_with_ipc'] = sum(bool(q['ipc3']) for q in rws)
        res['blocks'][b] = blk
    dev = res['blocks']['P1-DEV']
    best_n = max(dev['E2'][sel['N_star']]['MR@200'][0], dev['E2']['U0']['MR@200'][0])
    cands = [a1n, a2n, 'A4p', 'A4']
    res['owner_gate_AM7_6_4'] = {'rule': 'some stage-2a candidate beats both U0 and N* by >= 0.010 on P1-DEV MR@200',
                                 'passes': {c: dev['E2'][c]['MR@200'][0] - best_n >= 0.010 for c in cands}}
    res['power'] = {lab: {f'MDE@{n}': round(L.mde(c['sd_diff'], n, c['deff']), 4)
                          for n in (TEST_N['E1_OUT'] if lab == 'C4' else TEST_N['E2'])}
                    for lab, c in dev['contrasts_descriptive'].items() if lab in ('D1', 'D2', 'C4')}
    res['units_with_ipc_share'] = round(float(ctx.unit_has_ipc.mean()), 4)
    res['seconds'] = round(time.time() - t0, 1)
    json.dump(res, open(out / 'stage2a-results.json', 'w'), indent=1)
    pickle.dump({b: {'E1': dict(R[b][1]), 'E2': dict(R[b][2]), 'aux': R[b][4]} for b in BLOCKS},
                open(out / 'per-query.pkl', 'wb'), protocol=4)
    log('done')


if __name__ == '__main__':
    main()
