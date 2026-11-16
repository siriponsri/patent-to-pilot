"""Paper 2 (P2-OA) step R1: eligible tasks, three-way temporal splits, corpus sizing.

No retrieval, no model, no text. Stdlib only. Run on the remote with nice.
Usage: python3 -I oa_temporal_splits.py <raw_dir> <private_out_dir> <aggregate.json>
  raw_dir: citations.csv.zip, office_actions.csv.zip (OA Research Dataset 2017) and the
           PatentsView tables g_application, g_patent, g_ipc_at_issue,
           pg_published_application, pg_ipc_at_issue (.tsv.zip)
  private_out_dir: per-application tables (tasks.tsv, pairs.tsv); kept on the remote, mode 700
  aggregate.json: aggregates only (this is what goes into the repo)

Task definition (merged plan 3.1, made exact here):
  - per application, the EARLIEST non-final rejection (document_cd CTNF) in the dataset,
    by (mail_dt, ifw_number); the dataset only holds application series 12-15, so this is the
    first non-final rejection the application received (if mailed before mid-2017);
  - it must be mailed 2008-01-01 .. 2017-12-31;
  - K(q) = distinct US documents cited in THAT action with citation_in_oa=1 and action_type
    102 or 103 (basis bit 1=102, 2=103); foreign/unparsed cited art is counted, not kept;
  - eligible if |K| >= 3, the application has IPC, >= 1 K document is OUT under IPC3
    (no shared IPC3 with the application; needs IPC on the cited side), and a filing date
    is known. A later action is never searched for when the first one does not qualify.

Cut-point rule (DECLARED before this script was first run; no retrieval number exists):
  R1  temporal key = application filing date (PatentsView; pre-grant record first, else grant record).
  R2  observation completeness per filing year Y:
        c(Y) = (# series 12-15 applications filed in Y known to PatentsView that have >= 1 CTNF
               in the dataset) / (# series 12-15 applications filed in Y known to PatentsView).
      Y is COMPLETE if its denominator >= 10,000 and c(Y) >= 0.9 * max c over such years.
      Incomplete years (right-censored by the mid-2017 end of the dataset, or partial series
      coverage) are excluded from every split and reported.
  R2a Only the contiguous run of complete years that ends at the newest complete year is used;
      complete years separated from it by an incomplete year are excluded too.
  R3  P3-TEST = the newest complete filing year; extend backward by whole complete years until
      it holds >= 1,000 eligible tasks.
  R4  P2-TEST = the next older block of whole complete years, built the same way (>= 1,000).
  R5  DEV = all remaining older years of that contiguous run.
  R6  The evaluated test sample is NOT the whole window: it is the first n tasks of the window
      ordered by sha256('p2-oa-split-v1|' + app_id), with n fixed later by the MDE rule of the
      pre-declaration. Corpus sizes are therefore reported per window AND for n = 1,000 / 2,000 / 5,000.
"""
import collections, csv, hashlib, io, json, os, re, statistics, sys, time, zipfile
from pathlib import Path

csv.field_size_limit(1 << 30)
raw, priv, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
t0 = time.time()
R = {'format': 'ptp-p2-oa-splits-v1', 'rule': {
    'temporal_key': 'application filing date', 'complete_min_denominator': 10000,
    'complete_frac_of_max': 0.9, 'min_test_tasks': 1000, 'mail_window': ['2008-01-01', '2017-12-31'],
    'min_K': 3, 'min_out3': 1, 'sample_salt': 'p2-oa-split-v1', 'sample_sizes': [1000, 2000, 5000]}}
MIN_K, SAMPLE_N = 3, (1000, 2000, 5000)
BN = {1: '102', 2: '103', 3: 'both'}
# Encoding scale (measured, DAPFAM stage 0, 2026-11-05): PatEmbed-large fp32 on the V100,
# 188,944 passages from 45,336 families in 5,182.267 s.
DAPFAM_PASSAGES, DAPFAM_FAMS, DAPFAM_SECONDS = 188944, 45336, 5182.267
PASS_PER_DOC = DAPFAM_PASSAGES / DAPFAM_FAMS
SEC_PER_PASS = DAPFAM_SECONDS / DAPFAM_PASSAGES

def log(*a): print(round(time.time() - t0), 's', *a, flush=True)

def rd_zip(name, member, delim=','):
    z = zipfile.ZipFile(raw / name)
    f = io.TextIOWrapper(z.open(member), encoding='utf-8', errors='replace', newline='')
    return csv.DictReader(f, delimiter=delim)

def tsv(name): return rd_zip(f'{name}.tsv.zip', f'{name}.tsv', '\t')

def norm_id(s):  # same rule as oa_crossdomain_census.py
    s = s.strip().upper().replace(',', '')
    if re.fullmatch(r'\d{11}', s): return 'PG' + s
    m = re.fullmatch(r'(RE|D|PP|H|T)?0*(\d{1,8})', s)
    if m: return 'P' + (m.group(1) or '') + m.group(2)
    return None

def year(d): return d[:4] if d and re.match(r'(19|20)\d\d', d[:4]) else None

# ---- pass 1: earliest CTNF per application
first = {}  # app -> (mail_dt, ifw, art_unit)
n_oa = 0
for r in rd_zip('office_actions.csv.zip', 'office_actions.csv'):
    n_oa += 1
    if r['document_cd'] != 'CTNF': continue
    a = r['app_id'].zfill(8); k = (r['mail_dt'], r['ifw_number'], r['art_unit'])
    if a not in first or k[:2] < first[a][:2]: first[a] = k
F = collections.OrderedDict()
F['apps_with_ctnf'] = len(first)
inwin = {a: v for a, v in first.items() if '2008-01-01' <= v[0] <= '2017-12-31'}
F['first_ctnf_mailed_2008_2017'] = len(inwin)
chosen = {(a, v[1]) for a, v in inwin.items()}
log('pass1', n_oa, 'OAs')

# ---- pass 2: K(q) from the chosen action
K = collections.defaultdict(dict); foreign = collections.Counter()
for r in rd_zip('citations.csv.zip', 'citations.csv'):
    if r['citation_in_oa'] != '1' or r['action_type'] not in ('102', '103'): continue
    a = r['app_id'].zfill(8)
    if (a, r['ifw_number']) not in chosen: continue
    cid = norm_id(r['parsed'] or r['citation_pat_pgpub_id'])
    if not cid: foreign[a] += 1; continue
    K[a][cid] = K[a].get(cid, 0) | (1 if r['action_type'] == '102' else 2)
F['first_ctnf_with_ge1_us_102_103'] = len(K)
F['first_ctnf_with_ge3_us_102_103'] = sum(len(v) >= MIN_K for v in K.values())
cand = {a for a, v in K.items() if len(v) >= MIN_K}
log('pass2', len(K), 'actions with K')

# ---- PatentsView: application <-> documents, dates, titles, completeness denominator
app2pg = collections.defaultdict(set); app2pat = collections.defaultdict(set)
app_fd = {}; app_title = {}
den = collections.Counter(); den_apps = {}
need_pg = {c[2:] for v in K.values() for c in v if c.startswith('PG')}
need_pat = {c[1:] for v in K.values() for c in v if c.startswith('P') and not c.startswith('PG')}
pg_date = {}; pg_app = {}; pg_fd = {}
for r in tsv('pg_published_application'):
    a = r['application_id'].zfill(8); p = r['pgpub_id']
    if a[:2] in ('12', '13', '14', '15') and year(r['filing_date']):
        den_apps.setdefault(a, r['filing_date'])
    if a in cand:
        app2pg[a].add(p)
        if a not in app_fd and year(r['filing_date']): app_fd[a] = r['filing_date']
        app_title.setdefault(a, r['application_title'])
    if p in need_pg:
        pg_date[p] = r['published_date']; pg_app[p] = a; pg_fd[p] = r['filing_date']
pat_app = {}
for r in tsv('g_application'):
    a = r['application_id'].zfill(8); p = r['patent_id']
    if a[:2] in ('12', '13', '14', '15') and year(r['filing_date']):
        den_apps.setdefault(a, r['filing_date'])
    if a in cand:
        app2pat[a].add(p)
        if a not in app_fd and year(r['filing_date']): app_fd[a] = r['filing_date']
    if p in need_pat: pat_app[p] = (a, r['filing_date'])
need_pg |= set().union(*app2pg.values()) if app2pg else set()
need_pat |= set().union(*app2pat.values()) if app2pat else set()
pat_date = {}
for r in tsv('g_patent'):
    if r['patent_id'] in need_pat: pat_date[r['patent_id']] = r['patent_date']
log('pv tables')

for a, fd in den_apps.items(): den[fd[:4]] += 1
num = collections.Counter(fd[:4] for a, fd in den_apps.items() if a in first)
R['completeness_by_filing_year'] = {y: {'den': den[y], 'num_with_ctnf': num[y],
                                        'c': round(num[y] / den[y], 4)} for y in sorted(den)}
del den_apps

pg_ipc = collections.defaultdict(dict); pat_ipc = collections.defaultdict(dict)  # id -> {ipc4: min seq}
for name, store, key in (('pg_ipc_at_issue', pg_ipc, 'pgpub_id'), ('g_ipc_at_issue', pat_ipc, 'patent_id')):
    need = need_pg if store is pg_ipc else need_pat
    for r in tsv(name):
        i = r[key]
        if i in need and r['section']:
            c4 = r['section'] + r['ipc_class'].zfill(2) + r['subclass']
            try: s = int(r['ipc_sequence'])
            except ValueError: s = 999
            if s < store[i].get(c4, 10 ** 6): store[i][c4] = s
log('ipc')

def app_ipc(a):
    s = set()
    for p in app2pg.get(a, ()): s |= set(pg_ipc.get(p, {}))
    for p in app2pat.get(a, ()): s |= set(pat_ipc.get(p, {}))
    return s
def app_primary(a):
    for src, ids in ((pg_ipc, sorted(app2pg.get(a, ()))), (pat_ipc, sorted(app2pat.get(a, ())))):
        best = None
        for p in ids:
            for c4, s in src.get(p, {}).items():
                if best is None or (s, c4) < best: best = (s, c4)
        if best: return best[1]
    return None
def doc_ipc(c): return set((pg_ipc if c.startswith('PG') else pat_ipc).get(c[2:] if c.startswith('PG') else c[1:], {}))
def doc_dates(c):  # (publication date, filing date, owning application)
    if c.startswith('PG'):
        p = c[2:]; return pg_date.get(p), pg_fd.get(p), pg_app.get(p)
    p = c[1:]; a, fd = pat_app.get(p, (None, None)); return pat_date.get(p), fd, a

# ---- eligibility
tasks = {}; pairs_rows = []
f_ipc = f_out = f_fd = 0
for a in sorted(cand):
    ai = app_ipc(a)
    if not ai: continue
    f_ipc += 1
    a3 = {x[:3] for x in ai}; asec = {x[0] for x in ai}
    rows = []; n_out3 = 0
    for c, b in K[a].items():
        ci = doc_ipc(c)
        dom3 = 'NOIPC' if not ci else ('IN3' if a3 & {x[:3] for x in ci} else 'OUT3')
        dom4 = 'NOIPC' if not ci else ('IN4' if ai & ci else 'OUT4')
        sec = 'NOIPC' if not ci else ('SAMESEC' if asec & {x[0] for x in ci} else 'SECMIS')
        n_out3 += dom3 == 'OUT3'
        rows.append((c, b, dom3, dom4, sec))
    if not n_out3: continue
    f_out += 1
    fd = app_fd.get(a)
    if not fd: continue
    f_fd += 1
    m = inwin[a]
    tasks[a] = {'fd': fd, 'mail': m[0], 'au': m[2], 'ipc4': app_primary(a), 'nK': len(rows), 'nOUT3': n_out3,
                'foreign': foreign.get(a, 0), 'title': re.sub(r'[^a-z0-9]+', ' ', (app_title.get(a) or '').lower()).strip()}
    pairs_rows.append((a, rows))
F['with_ge3_and_app_ipc'] = f_ipc
F['with_ge1_out3'] = f_out
F['eligible_with_filing_date'] = f_fd
R['funnel'] = F
log('eligible', len(tasks))

R['eligible_by_filing_year'] = dict(sorted(collections.Counter(t['fd'][:4] for t in tasks.values()).items()))
R['eligible_by_mail_year'] = dict(sorted(collections.Counter(t['mail'][:4] for t in tasks.values()).items()))
R['eligible_filing_x_mail_year'] = {f'{k[0]}|{k[1]}': v for k, v in sorted(
    collections.Counter((t['fd'][:4], t['mail'][:4]) for t in tasks.values()).items())}

# ---- cut points (rule R1-R5)
comp = R['completeness_by_filing_year']
big = {y: v['c'] for y, v in comp.items() if v['den'] >= 10000}
cmax = max(big.values())
complete = sorted(y for y, c in big.items() if c >= 0.9 * cmax)
R['complete_years'] = complete
R['incomplete_years_with_eligible_tasks'] = {y: n for y, n in R['eligible_by_filing_year'].items() if y not in complete}
ny = collections.Counter(t['fd'][:4] for t in tasks.values())
years_desc = []  # R2a: only the contiguous run of complete years ending at the newest complete year
y = int(max(complete))
while str(y) in complete:
    years_desc.append(str(y)); y -= 1
R['usable_contiguous_years'] = sorted(years_desc)
def take_block(ys):
    blk, n = [], 0
    while ys and n < 1000:
        y = ys.pop(0); blk.append(y); n += ny[y]
    return sorted(blk), n
p3, n3 = take_block(years_desc); p2, n2 = take_block(years_desc)
dev = sorted(years_desc)
split_of_year = {**{y: 'DEV' for y in dev}, **{y: 'P2-TEST' for y in p2}, **{y: 'P3-TEST' for y in p3}}
R['cut_points'] = {'DEV': dev, 'P2-TEST': p2, 'P3-TEST': p3}
for a, t in tasks.items(): t['split'] = split_of_year.get(t['fd'][:4], 'EXCLUDED')
log('cuts', R['cut_points'])

# ---- private per-application tables (remote only)
priv.mkdir(parents=True, exist_ok=True); os.chmod(priv, 0o700)
with open(priv / 'tasks.tsv', 'w', encoding='utf-8') as f:
    f.write('app_id\tsplit\tfiling_date\tmail_dt\tart_unit\tipc4_primary\tn_K\tn_K_out3\tn_foreign_102_103\n')
    for a in sorted(tasks):
        t = tasks[a]
        f.write(f"{a}\t{t['split']}\t{t['fd']}\t{t['mail']}\t{t['au']}\t{t['ipc4'] or ''}\t{t['nK']}\t{t['nOUT3']}\t{t['foreign']}\n")
with open(priv / 'pairs.tsv', 'w', encoding='utf-8') as f:
    f.write('app_id\tcited\tbasis\tdom_ipc3\tdom_ipc4\tsection\n')
    for a, rows in pairs_rows:
        for c, b, d3, d4, s in rows: f.write(f'{a}\t{c}\t{BN[b]}\t{d3}\t{d4}\t{s}\n')
for p in ('tasks.tsv', 'pairs.tsv'): os.chmod(priv / p, 0o600)

# ---- pass 3: other (non-K) US citations of eligible applications, any action/form = unjudged pool
other = collections.defaultdict(set)
for r in rd_zip('citations.csv.zip', 'citations.csv'):
    a = r['app_id'].zfill(8)
    if a not in tasks: continue
    cid = norm_id(r['parsed'] or r['citation_pat_pgpub_id'])
    if cid and cid not in K[a]: other[a].add(cid)
log('pass3')

# ---- per-split aggregates
own = {}  # document -> split of the task whose application it is
for a, t in tasks.items():
    for p in app2pg.get(a, ()): own['PG' + p] = t['split']
    for p in app2pat.get(a, ()): own['P' + p] = t['split']
SPL = ['DEV', 'P2-TEST', 'P3-TEST', 'EXCLUDED']
by = collections.defaultdict(list)
for a, rows in pairs_rows: by[tasks[a]['split']].append((a, rows))
docs_by_split = {}
def q(v, p): return sorted(v)[min(len(v) - 1, int(p * len(v)))] if v else None
def sk(a): return hashlib.sha256(('p2-oa-split-v1|' + a).encode()).hexdigest()
def encode_est(n_docs):
    pas = n_docs * PASS_PER_DOC
    return {'docs': n_docs, 'passages_est': round(pas), 'v100_fp32_hours_est': round(pas * SEC_PER_PASS / 3600, 1)}
S = {}
for s in SPL:
    L = by.get(s, [])
    if not L: continue
    pc = collections.Counter(); docs = set(); avail = 0
    nk = []; no3 = []; temporal = collections.Counter(); links = collections.Counter(); oth = []
    for a, rows in L:
        t = tasks[a]; nk.append(t['nK']); no3.append(t['nOUT3']); oth.append(len(other.get(a, ())))
        for c, b, d3, d4, sec in rows:
            pc['pairs'] += 1; pc[BN[b]] += 1; pc[d3] += 1; pc[d4] += 1; pc[sec] += 1
            pc[f'{BN[b]}|{d3}'] += 1
            docs.add(c)
            pub, dfd, dapp = doc_dates(c)
            temporal['pub_before_filing' if pub and pub < t['fd'] else 'pub_on_or_after_filing' if pub else 'pub_unknown'] += 1
            temporal['docfiled_before_filing' if dfd and dfd < t['fd'] else 'docfiled_on_or_after_filing' if dfd else 'docfiled_unknown'] += 1
            links['cited_doc_is_task_app_in_' + own[c] if c in own else 'cited_doc_not_a_task_app'] += 1
    docs_by_split[s] = docs
    avail = sum(1 for c in docs if (pg_date.get(c[2:]) if c.startswith('PG') else pat_date.get(c[1:])))
    au = collections.Counter(tasks[a]['au'] for a, _ in L)
    ip = collections.Counter(tasks[a]['ipc4'] for a, _ in L)
    tc = collections.Counter((tasks[a]['au'] or '')[:2] for a, _ in L)
    order = sorted((a for a, _ in L), key=sk)
    samples = {}
    for n in SAMPLE_N:
        if n > len(order): continue
        sd = set(); so = 0; sp = 0
        sub = set(order[:n])
        for a, rows in L:
            if a in sub:
                for c, *_ in rows: sd.add(c)
                so += tasks[a]['nOUT3']; sp += tasks[a]['nK']
        samples[str(n)] = {'distinct_cited': len(sd), 'pairs': sp, 'out3_pairs': so,
                           'corpus_1to1': encode_est(2 * len(sd)), 'corpus_1to3': encode_est(4 * len(sd))}
    S[s] = {
        'filing_years': R['cut_points'].get(s), 'tasks': len(L),
        'pairs': pc['pairs'], 'distinct_cited_docs': len(docs),
        'distinct_cited_with_pv_record': avail,
        'share_102_only': round(pc['102'] / pc['pairs'], 4), 'share_103_only': round(pc['103'] / pc['pairs'], 4),
        'share_both': round(pc['both'] / pc['pairs'], 4),
        'share_OUT3': round(pc['OUT3'] / pc['pairs'], 4), 'share_IN3': round(pc['IN3'] / pc['pairs'], 4),
        'share_noipc_cited': round(pc['NOIPC'] / pc['pairs'], 4),
        'share_OUT4': round(pc['OUT4'] / pc['pairs'], 4), 'share_section_mismatch': round(pc['SECMIS'] / pc['pairs'], 4),
        'pair_counts': dict(sorted(pc.items())),
        'K_per_task': {'mean': round(statistics.mean(nk), 2), 'median': statistics.median(nk), 'p90': q(nk, .9), 'max': max(nk)},
        'OUT3_per_task': {'mean': round(statistics.mean(no3), 2), 'median': statistics.median(no3), 'p90': q(no3, .9),
                          'tasks_ge3_out3': sum(x >= 3 for x in no3)},
        'unjudged_other_us_citations_per_task': {'mean': round(statistics.mean(oth), 2), 'median': statistics.median(oth)},
        'clusters': {'art_units': len(au), 'largest_art_unit_share': round(au.most_common(1)[0][1] / len(L), 4),
                     'art_units_ge20_tasks': sum(v >= 20 for v in au.values()),
                     'technology_centers': len(tc), 'ipc4_primary_subclasses': len(ip),
                     'largest_ipc4_share': round(ip.most_common(1)[0][1] / len(L), 4), 'tasks_without_ipc4_primary': ip[None]},
        'temporal_K_pairs': dict(temporal),
        'cross_split_doc_links_K_pairs': dict(links),
        'corpus_full_window': {'1to1': encode_est(2 * len(docs)), '1to3': encode_est(4 * len(docs))},
        'corpus_per_sample': samples,
    }
R['splits'] = S
sh = {}
for i, s1 in enumerate(SPL):
    for s2 in SPL[i + 1:]:
        if s1 in docs_by_split and s2 in docs_by_split:
            sh[f'{s1}&{s2}'] = len(docs_by_split[s1] & docs_by_split[s2])
R['cited_docs_shared_between_splits'] = sh
# continuation proxy: same normalised pre-grant title and same primary IPC4 in two different splits
tw = collections.defaultdict(set)
for a, t in tasks.items():
    if t['title'] and t['ipc4']: tw[(t['title'], t['ipc4'])].add(t['split'])
tw_tasks = collections.Counter()
for a, t in tasks.items():
    if t['title'] and t['ipc4'] and len(tw[(t['title'], t['ipc4'])]) > 1: tw_tasks[t['split']] += 1
R['continuation_proxy_title_ipc4_twins_across_splits'] = dict(tw_tasks)
R['encoding_scale'] = {'source': 'DAPFAM stage 0 (2026-11-05), PatEmbed-large fp32, V100',
                       'passages': DAPFAM_PASSAGES, 'families': DAPFAM_FAMS, 'seconds': DAPFAM_SECONDS,
                       'passages_per_doc_assumed': round(PASS_PER_DOC, 3), 'passages_per_second': round(1 / SEC_PER_PASS, 2)}
R['wall_seconds'] = round(time.time() - t0, 1)
out.write_text(json.dumps(R, indent=1), encoding='utf-8')
log('done')
