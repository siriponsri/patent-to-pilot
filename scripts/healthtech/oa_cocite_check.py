"""Idea A label sufficiency check (am7/OA-COCITE-CHECK-PREDECLARATION.md). CPU, stdlib only, aggregates only.

Reads developer-visible labels (pairs-dev.tsv: TRAIN/VAL/P1-DEV used; no TEST block exists there) and the OA Research
Dataset 2017 tables filtered to those apps. Computes per block: C103 sets (evaluator conditional set restricted to
103), A-eligible (>=1 IN3 and >=1 OUT3 in C103), clean single-combination actions (n103_all == cite103_max >= 2).
Usage: python3 -I oa_cocite_check.py <pairs-dev.tsv> <corpus-units.tsv> <tasks.tsv> <oa2017_dir> <out.json>
"""
import collections, csv, io, json, re, statistics, sys, time, zipfile

csv.field_size_limit(1 << 30)
BLOCKS = ('TRAIN', 'VAL', 'P1-DEV')
GATE = {'G1_P1DEV_A_eligible_min': 2000, 'G2_TRAIN_A_eligible_min': 10000, 'G3_P1DEV_clean_A_eligible_min': 500}


def norm_id(s):  # same rule as oa_temporal_splits.py
    s = s.strip().upper().replace(',', '')
    if re.fullmatch(r'\d{11}', s):
        return 'PG' + s
    m = re.fullmatch(r'(RE|D|PP|H|T)?0*(\d{1,8})', s)
    if m:
        return 'P' + (m.group(1) or '') + m.group(2)
    return None


def rd_zip(path, member):
    z = zipfile.ZipFile(path)
    return csv.DictReader(io.TextIOWrapper(z.open(member), encoding='utf-8', errors='replace', newline=''))


def dist(xs):
    if not xs:
        return {}
    xs = sorted(xs)
    q = lambda p: xs[min(len(xs) - 1, int(p * len(xs)))]
    return {'n': len(xs), 'mean': round(statistics.mean(xs), 3), 'p50': q(0.5), 'p90': q(0.9), 'max': xs[-1]}


def main(pairs_p, units_p, tasks_p, oa_dir, out_p):
    t0 = time.time()
    block_of, rows = {}, collections.defaultdict(list)
    with open(pairs_p, encoding='utf-8') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            if r['block'] in ('P1-TEST', 'P2-TEST', 'P3-TEST'):
                raise SystemExit('TEST block found in pairs-dev; refusing')
            if r['block'] in BLOCKS:
                block_of[r['app_id']] = r['block']; rows[r['app_id']].append(r)
    apps = set(block_of)
    corpus = set()
    with open(units_p, encoding='utf-8') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            corpus.add(r['unit_id'])
    fd = {}
    with open(tasks_p, encoding='utf-8') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            if r['app_id'] in apps:
                fd[r['app_id']] = r['filing_date']
    # C103 sets
    C = {}
    for a, rs in rows.items():
        s = {'IN3': set(), 'OUT3': set(), 'NOIPC': set()}
        for r in rs:
            u = r['unit']
            if r['basis'] not in ('103', 'both') or not u or not r['unit_first_pub'] or u not in corpus:
                continue
            if a not in fd or r['unit_first_pub'] >= fd[a] or u == 'A:' + a:
                continue
            s.setdefault(r['dom_ipc3'], set()).add(u)
        C[a] = s
    # chosen action per app (earliest CTNF by (mail_dt, ifw_number), mailed 2008-2017)
    first, c103max = {}, {}
    for r in rd_zip(f'{oa_dir}/office_actions.csv.zip', 'office_actions.csv'):
        if r['document_cd'] != 'CTNF':
            continue
        a = r['app_id'].zfill(8)
        if a not in apps:
            continue
        k = (r['mail_dt'], r['ifw_number'])
        if a not in first or k < first[a]:
            first[a] = k; c103max[a] = r['cite103_max']
    chosen = {(a, v[1]): a for a, v in first.items() if '2008-01-01' <= v[0] <= '2017-12-31'}
    n103rows, claims_present = collections.Counter(), collections.Counter()
    for r in rd_zip(f'{oa_dir}/rejections.csv.zip', 'rejections.csv'):
        key = (r['app_id'].zfill(8), r['ifw_number'])
        if key in chosen and r['action_type'] == '103':
            n103rows[chosen[key]] += 1
            if r['claim_numbers'].strip():
                claims_present[chosen[key]] += 1
    refs103 = collections.defaultdict(set)
    for r in rd_zip(f'{oa_dir}/citations.csv.zip', 'citations.csv'):
        key = (r['app_id'].zfill(8), r['ifw_number'])
        if key not in chosen or r['citation_in_oa'] != '1' or r['action_type'] != '103':
            continue
        raw = (r['parsed'] or r['citation_pat_pgpub_id']).strip()
        refs103[chosen[key]].add(norm_id(raw) or ('F:' + raw.upper()))
    res = {'format': 'ptp-p1-oa-cocite-check-v1', 'predeclaration': 'docs/healthtech/research/paper1-bridgeret/am7/OA-COCITE-CHECK-PREDECLARATION.md',
           'gate': GATE, 'blocks': {}}
    for b in BLOCKS:
        A = [a for a in apps if block_of[a] == b]
        elig = [a for a in A if C[a]['IN3'] and C[a]['OUT3']]

        def clean(a):
            try:
                m = int(float(c103max.get(a) or 0))
            except ValueError:
                return False
            return m >= 2 and len(refs103.get(a, ())) == m
        res['blocks'][b] = {
            'tasks': len(A),
            'chosen_action_found': sum(1 for a in A if a in first and '2008-01-01' <= first[a][0] <= '2017-12-31'),
            'tasks_C103_ge2': sum(1 for a in A if sum(len(v) for v in C[a].values()) >= 2),
            'A_eligible': len(elig),
            'clean': sum(1 for a in A if clean(a)),
            'clean_A_eligible': sum(1 for a in elig if clean(a)),
            'single_103_row_A_eligible': sum(1 for a in elig if n103rows[a] == 1),
            'C103_size_all_tasks': dist([sum(len(v) for v in C[a].values()) for a in A]),
            'OUT_targets_per_eligible': dist([len(C[a]['OUT3']) for a in elig]),
            'IN_anchors_per_eligible': dist([len(C[a]['IN3']) for a in elig]),
            'n103_rows_per_action_eligible': dict(sorted(collections.Counter(min(n103rows[a], 5) for a in elig).items())),
            'claim_numbers_present_share_eligible': round(sum(1 for a in elig if claims_present[a]) / max(1, len(elig)), 4),
            'cite103_max_eligible': dist([int(float(c103max[a])) for a in elig if (c103max.get(a) or '').replace('.', '', 1).isdigit()]),
            'n103_all_eligible': dist([len(refs103.get(a, ())) for a in elig]),
        }
    B = res['blocks']
    g1 = B['P1-DEV']['A_eligible'] >= GATE['G1_P1DEV_A_eligible_min']
    g2 = B['TRAIN']['A_eligible'] >= GATE['G2_TRAIN_A_eligible_min']
    g3 = B['P1-DEV']['clean_A_eligible'] >= GATE['G3_P1DEV_clean_A_eligible_min']
    res['G1'], res['G2'], res['G3'] = g1, g2, g3
    res['outcome'] = 'SUFFICIENT' if g1 and g2 and g3 else 'PARTIAL' if g1 and g2 else 'INSUFFICIENT'
    res['P1_TEST_A_eligible_estimate_n1_10000'] = round(10000 * B['P1-DEV']['A_eligible'] / B['P1-DEV']['tasks'])
    res['P1_TEST_clean_A_eligible_estimate_n1_10000'] = round(10000 * B['P1-DEV']['clean_A_eligible'] / B['P1-DEV']['tasks'])
    res['seconds'] = round(time.time() - t0, 1)
    json.dump(res, open(out_p, 'w'), indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != 'blocks'}, indent=1))
    for b in BLOCKS:
        print(b, {k: B[b][k] for k in ('tasks', 'A_eligible', 'clean', 'clean_A_eligible', 'single_103_row_A_eligible')})


if __name__ == '__main__':
    main(*sys.argv[1:])
