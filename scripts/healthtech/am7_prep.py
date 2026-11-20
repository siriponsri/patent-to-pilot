"""AM-7 / AM-7.1 stage-2a data preparation (CPU; developer-visible data only; never reads a TEST label).

Builds private tables for blocks P1-DEV and VAL:
  queries: filing date, chosen-action mail date, art unit, IPC3 set, continuity group, E1 positives (as
           eval_bridgeret_dev.py: K units RPD-visible, not own unit; conditional = in corpus), E2 cohort fields (AM-7 §3:
           anchor, targets, strict misses, clean flag, all K units, unseen targets, shuffled-anchor partner).
  units:   corpus order (runs/z-patembed/units.json), first_pub, unit-id rank, IPC3 inverted index (AM-7.1 §1).
  cocite:  N5 source actions (AM-7.1 §3): every OA action with citation_in_oa = 1 and action_type 102/103, as corpus
           unit indices with mail date, application and continuity-group root. Rows of applications in P1-TEST,
           P2-TEST or P3-TEST are skipped before any cited field is read.
Usage: python3 -I am7_prep.py <bridgeret_dir> <challenge1m_out> <tasks.tsv> <manifest-private.json> <oa2017_dir>
                              <patentsview_dir> <out_dir>
"""
import collections, csv, io, json, os, pickle, re, sys, time, zipfile
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import am7_lib as L  # noqa: E402
import build_continuity_related as bcr  # noqa: E402

csv.field_size_limit(1 << 30)
BLOCKS = ('P1-DEV', 'VAL')


def norm_id(s):  # oa_temporal_splits.py rule
    s = s.strip().upper().replace(',', '')
    if re.fullmatch(r'\d{11}', s):
        return 'PG' + s
    m = re.fullmatch(r'(RE|D|PP|H|T)?0*(\d{1,8})', s)
    if m:
        return 'P' + (m.group(1) or '') + m.group(2)
    return None


def pat_key(pid):  # build_challenge1m_sealed.py rule
    m = re.fullmatch(r'(RE|D|PP|H|T)?0*(\d{1,8})', (pid or '').strip().upper())
    return 'P' + (m.group(1) or '') + m.group(2) if m else 'P' + pid


def rd_zip(path, member, delim=','):
    z = zipfile.ZipFile(path)
    return csv.DictReader(io.TextIOWrapper(z.open(member), encoding='utf-8', errors='replace', newline=''), delimiter=delim)


def ymd(s):
    return int(s.replace('-', '')) if s else 0


def main(a):
    br, c1m, tasks_p, man_p, oa, pv, out = map(Path, a)
    out.mkdir(parents=True, exist_ok=False); os.chmod(out, 0o700)
    t0 = time.time(); log = lambda *x: print(round(time.time() - t0), 's', *x, flush=True)
    man = json.load(open(man_p))
    protected = set()
    for b in L.PROTECTED:
        protected |= set(man['blocks'][b])
    block_of = {x: b for b in BLOCKS + ('TRAIN',) for x in man['blocks'][b]}
    units = json.load(open(br / 'runs/z-patembed/units.json'))
    uidx = {u: i for i, u in enumerate(units)}
    unit_rank = np.empty(len(units), dtype=np.int64); unit_rank[np.argsort(np.array(units, dtype=object))] = np.arange(len(units))
    pub = {}
    for r in csv.DictReader(open(c1m / 'corpus-units.tsv', encoding='utf-8'), delimiter='\t'):
        pub[r['unit_id']] = ymd(r['first_pub'])
    unit_pub = np.array([pub[u] for u in units], dtype=np.int64)
    corpus = set(units)
    task = {}
    for r in csv.DictReader(open(tasks_p, encoding='utf-8'), delimiter='\t'):
        if r['app_id'] in block_of:
            task[r['app_id']] = r
    log('units/tasks', len(units), len(task))
    # pairs (developer-visible)
    rows = collections.defaultdict(list); train_seen = set()
    for r in csv.DictReader(open(c1m / 'pairs-dev.tsv', encoding='utf-8'), delimiter='\t'):
        if r['block'] in L.PROTECTED:
            raise SystemExit('TEST block in pairs-dev')
        if r['block'] == 'TRAIN' and r['unit']:
            train_seen.add(r['unit'])
        if r['block'] in BLOCKS:
            rows[r['app_id']].append(r)
    train_seen |= {'A:' + x for x in man['blocks']['TRAIN']}
    log('pairs')
    # PatentsView: doc -> unit (builder rule), doc IPC4, application IPC (oa_temporal_splits rule)
    pat_app = {r['patent_id']: bcr.app_norm(r['application_id']) for r in rd_zip(pv / 'g_application.tsv.zip', 'g_application.tsv', '\t')}
    doc_unit = {}; app_pats = collections.defaultdict(set); app_pgs = collections.defaultdict(set)
    for r in rd_zip(pv / 'g_patent.tsv.zip', 'g_patent.tsv', '\t'):
        pid = r['patent_id']; ap = pat_app.get(pid)
        doc_unit[pat_key(pid)] = f'A:{ap}' if ap else f'D:{pat_key(pid)}'
        if ap:
            app_pats[ap].add(pid)
    for r in rd_zip(pv / 'pg_published_application.tsv.zip', 'pg_published_application.tsv', '\t'):
        ap = bcr.app_norm(r['application_id'])
        if r['patent_type'] in ('utility', 'new', 'new-utility'):
            doc_unit['PG' + r['pgpub_id']] = f'A:{ap}' if ap else f'D:PG{r["pgpub_id"]}'
        if ap:
            app_pgs[ap].add(r['pgpub_id'])
    log('doc_unit', len(doc_unit))
    # IPC3 per unit (union over the unit's documents) and per query application
    need_q = set(task)
    unit_ipc = collections.defaultdict(set); app_ipc = collections.defaultdict(set)
    pg_unit = {p: f'A:{ap}' for ap, ps in app_pgs.items() for p in ps}
    pat_unit = {p: f'A:{ap}' for ap, ps in app_pats.items() for p in ps}
    for name, key, umap in (('pg_ipc_at_issue', 'pgpub_id', pg_unit), ('g_ipc_at_issue', 'patent_id', pat_unit)):
        for r in rd_zip(pv / f'{name}.tsv.zip', f'{name}.tsv', '\t'):
            if not r['section']:
                continue
            c3 = r['section'] + r['ipc_class'].zfill(2)
            i = r[key]
            u = umap.get(i) or (('D:PG' + i) if key == 'pgpub_id' else ('D:' + pat_key(i)))
            if u in corpus:
                unit_ipc[u].add(c3)
            ap = u[2:] if u.startswith('A:') else None
            if ap in need_q:
                app_ipc[ap].add(c3)
    inv = collections.defaultdict(list)
    for u, cs in unit_ipc.items():
        for c in cs:
            inv[c].append(uidx[u])
    ipc_inv = {c: np.array(sorted(v), dtype=np.int64) for c, v in inv.items()}
    unit_has_ipc = np.zeros(len(units), dtype=bool); unit_has_ipc[[uidx[u] for u in unit_ipc]] = True
    log('ipc', len(unit_ipc), len(app_ipc))
    del pg_unit, pat_unit
    # continuity groups (build_continuity_related primary rule) over all applications
    uf = bcr.UF()
    pg_app = {p: ap for ap, ps in app_pgs.items() for p in ps}

    def node(num, kind):
        if kind == 'parent-grant-document':
            x = pat_app.get(num.lstrip('0') if num.isdigit() else num) or pat_app.get(num)
            return f'A:{x}' if x else f'P:{num}'
        if kind == 'parent-pct-document':
            return 'W:' + re.sub(r'[^0-9A-Z]', '', num.upper())
        x = bcr.app_norm(num)
        return f'A:{x}' if x else f'X:{num}'
    for table, idcol, idmap in (('g_us_rel_doc', 'patent_id', pat_app), ('pg_us_rel_doc', 'pgpub_id', pg_app)):
        for r in rd_zip(pv / f'{table}.tsv.zip', f'{table}.tsv', '\t'):
            if r['related_doc_type'] not in bcr.PRIMARY:
                continue
            src = idmap.get(r[idcol])
            if src:
                uf.union(f'A:{src}', node(r['related_doc_number'].strip(), r.get('related_doc_kind', '')))
    log('continuity', len(uf.p))
    del pat_app, pg_app
    # office actions: mail dates; chosen action (earliest CTNF 2008-2017) and cite103_max for queries
    mail = {}; first = {}; c103max = {}
    for r in rd_zip(oa / 'office_actions.csv.zip', 'office_actions.csv'):
        ap = r['app_id'].zfill(8)
        if ap in protected:
            continue
        mail[(ap, r['ifw_number'])] = ymd(r['mail_dt'])
        if ap in need_q and r['document_cd'] == 'CTNF':
            k = (r['mail_dt'], r['ifw_number'])
            if ap not in first or k < first[ap]:
                first[ap] = k; c103max[ap] = r['cite103_max']
    chosen = {(ap, v[1]): ap for ap, v in first.items() if '2008-01-01' <= v[0] <= '2017-12-31'}
    log('office_actions', len(mail))
    # citations: N5 source actions + clean flag (n103_all) for queries
    act_units = collections.defaultdict(set); refs103 = collections.defaultdict(set)
    for r in rd_zip(oa / 'citations.csv.zip', 'citations.csv'):
        ap = r['app_id'].zfill(8)
        if ap in protected:
            continue                                   # TEST rows: skipped before any cited field is read
        if r['citation_in_oa'] != '1' or r['action_type'] not in ('102', '103'):
            continue
        raw = (r['parsed'] or r['citation_pat_pgpub_id']).strip()
        key = (ap, r['ifw_number'])
        if r['action_type'] == '103' and key in chosen:
            refs103[ap].add(norm_id(raw) or ('F:' + raw.upper()))
        d = norm_id(raw)
        u = doc_unit.get(d) if d else None
        if u in uidx:
            act_units[key].add(uidx[u])
    actions = []
    for (ap, ifw), us in act_units.items():
        if len(us) >= 2 and (ap, ifw) in mail:
            actions.append((mail[(ap, ifw)], ap, uf.find('A:' + ap), tuple(sorted(us))))
    log('actions', len(actions))
    del act_units, doc_unit
    # queries
    rng_order = {}
    Q = {}
    for b in BLOCKS:
        qs = []
        for ap in sorted(x for x in man['blocks'][b] if x in task):
            t = task[ap]; fd = t['filing_date']; rs = rows.get(ap, [])
            pos = {'ALL': set(), 'OUT': set(), 'IN': set()}; strict = {'OUT': set()}
            for r in rs:
                u = r['unit']
                if not u or not r['unit_first_pub'] or r['unit_first_pub'] >= fd or u == 'A:' + ap:
                    continue
                kinds = ['ALL'] + (['OUT'] if r['dom_ipc3'] == 'OUT3' else ['IN'] if r['dom_ipc3'] == 'IN3' else [])
                if 'OUT' in kinds:
                    strict['OUT'].add(u)
                if u in uidx:
                    for k in kinds:
                        pos[k].add(uidx[u])
            c = L.c103_set(rs, fd, ap, corpus)
            q = {'app': ap, 'fd': ymd(fd), 'mail': ymd(t['mail_dt']), 'au': t['art_unit'], 'ipc3': sorted(app_ipc.get(ap, ())),
                 'group': uf.find('A:' + ap), 'pos': {k: sorted(v) for k, v in pos.items()}, 'n_out_strict': len(strict['OUT']),
                 'k_units': sorted(uidx[r['unit']] for r in rs if r['unit'] in uidx)}
            if c['IN3'] and c['OUT3']:
                a = L.anchor_of(ap, c['IN3'])
                tg = sorted(uidx[u] for u in c['OUT3'])
                so = L.strict_out103(rs, fd, ap)
                try:
                    m = int(float(c103max.get(ap) or 0))
                except ValueError:
                    m = 0
                q['e2'] = {'anchor': uidx[a], 'targets': tg, 'n_strict': len(so),
                           'clean': m >= 2 and len(refs103.get(ap, ())) == m,
                           'unseen_targets': sorted(uidx[u] for u in c['OUT3'] if u not in train_seen),
                           'all_coref': sorted(uidx[u] for s in c.values() for u in s if u != a)}
            qs.append(q)
        coh = sorted((q for q in qs if 'e2' in q), key=lambda q: L.sha(f'{L.SHUFFLE_SALT}|{q["app"]}'))
        for i, q in enumerate(coh):
            q['e2']['shuffle_anchor'] = coh[(i + 1) % len(coh)]['e2']['anchor']
        Q[b] = qs
        log(b, len(qs), 'cohort', len(coh))
    pickle.dump({'units': units, 'unit_rank': unit_rank, 'unit_pub': unit_pub, 'ipc_inv': ipc_inv,
                 'unit_has_ipc': unit_has_ipc, 'queries': Q}, open(out / 'meta.pkl', 'wb'), protocol=4)
    pickle.dump(actions, open(out / 'cocite.pkl', 'wb'), protocol=4)
    summ = {'format': 'ptp-p1-am7-prep-v1', 'seconds': round(time.time() - t0, 1), 'n_units': len(units),
            'units_with_ipc': int(unit_has_ipc.sum()), 'n_source_actions': len(actions),
            'blocks': {b: {'queries': len(Q[b]), 'cohort': sum('e2' in q for q in Q[b]),
                           'clean': sum(q.get('e2', {}).get('clean', False) for q in Q[b]),
                           'queries_with_ipc': sum(bool(q['ipc3']) for q in Q[b]),
                           'out_eval_queries': sum(bool(q['pos']['OUT']) for q in Q[b])} for b in BLOCKS}}
    json.dump(summ, open(out / 'prep-summary.json', 'w'), indent=1)
    print(json.dumps(summ, indent=1))


if __name__ == '__main__':
    main(sys.argv[1:])
