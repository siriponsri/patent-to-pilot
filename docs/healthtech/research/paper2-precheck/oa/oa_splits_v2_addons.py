"""P2-OA step R1b (merged plan v2): open-population corpus size, gold coverage, RPD/OAER, claim check.

Reads the private outputs of oa_temporal_splits.py (tasks.tsv, pairs.tsv) plus the raw tables.
No retrieval, no model, no text. Stdlib only.
Usage: python3 -I oa_splits_v2_addons.py <raw_dir> <private_dir> <aggregate.json>

Declared before the first run (no retrieval number exists; coverage is an aggregate of labels
over a label-independent population, it never changes membership):
  Open population (primary corpus candidates). A document is a US utility or reissue grant
  (g_patent) or a utility pre-grant publication (pg_published_application). Membership depends
  only on type and publication date, never on citation status:
    OP-<S>: published on or after S-01-01, for S in {1976, 1990, 2001, 2005};
    upper bound per split: RPD corpus = published before the split's latest task filing date;
    OAER corpus = published before the split's latest first-action mail date.
  Sizes are given as documents and as application-level units (a pre-grant publication and the
  grant of the same application count once; grants without an application record count alone).
  Stratified-sample variant: hash sample of applications at rate r in {0.25, 0.5}
  (sha256('p2-oa-pop-v1|' + unit id)); coverage is measured, not assumed.
  Temporal settings, per (task, cited) pair:
    RPD  eligible if the cited document's publication date < the task's filing date;
    OAER eligible if publication date < task filing date OR the cited document's US filing date
         < task filing date (proxy for 35 USC 102(a)(2) AIA / 102(e) pre-AIA; foreign priority
         and the pre-AIA invention date are not available). A task is AIA (proxy) if its filing
         date >= 2013-03-16; transition applications cannot be identified from these files.
  AMENDMENT 1 (after run 1, before any retrieval): run 1 kept only pre-grant publications typed
  'utility'. PatentsView types every 2001-2004 publication 'new' (751k documents; 118k cited), so
  run 1 silently dropped them. The population now admits pre-grant types {'utility', 'new',
  'new-utility'}; still type and date only, never citation status. Run 1 output is kept as
  oa-splits-v2-run1-asdeclared.json. Also added: number bins of cited patents with no record.
  Claim check: whether the first CTNF's 102/103 rejections include claim 1 (rejections.csv,
  joined on app_id + ifw_number). Amendments are not recorded in these files.
"""
import collections, csv, hashlib, io, json, re, sys, time, zipfile
from pathlib import Path

csv.field_size_limit(1 << 30)
raw, priv, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
t0 = time.time()
STARTS = (1976, 1990, 2001, 2005)
RATES = (0.25, 0.5)
AIA = '2013-03-16'
def log(*a): print(round(time.time() - t0), 's', *a, flush=True)
def rd_zip(name, member, delim=','):
    z = zipfile.ZipFile(raw / name)
    return csv.DictReader(io.TextIOWrapper(z.open(member), encoding='utf-8', errors='replace', newline=''), delimiter=delim)
def tsv(name): return rd_zip(f'{name}.tsv.zip', f'{name}.tsv', '\t')
def ok(d): return bool(d) and bool(re.fullmatch(r'(19|20)\d\d-\d\d-\d\d', d))
def h(u): return int(hashlib.sha256(('p2-oa-pop-v1|' + u).encode()).hexdigest()[:8], 16) / 2 ** 32

tasks = {}
with open(priv / 'tasks.tsv', encoding='utf-8') as f:
    for r in csv.DictReader(f, delimiter='\t'): tasks[r['app_id']] = r
pairs = []
with open(priv / 'pairs.tsv', encoding='utf-8') as f:
    for r in csv.DictReader(f, delimiter='\t'): pairs.append((r['app_id'], r['cited'], r['basis'], r['dom_ipc3']))
log('private', len(tasks), len(pairs))

# ---- population: every grant / pre-grant publication with type and dates
doc = {}  # 'P..'/'PG..' -> (pubdate, unit, type)
unit_first = {}  # unit -> earliest publication date
g_app = {}
for r in tsv('g_application'):
    g_app[r['patent_id']] = (r['application_id'].zfill(8), r['filing_date'])
gtype = collections.Counter()
def pnorm(p):
    m = re.fullmatch(r'(RE|D|PP|H|T)?0*(\d{1,8})', p.strip().upper())
    return 'P' + (m.group(1) or '') + m.group(2) if m else None
doc_fd = {}
for r in tsv('g_patent'):
    t = r['patent_type']; gtype[t] += 1
    d = pnorm(r['patent_id'])
    if not d or not ok(r['patent_date']): continue
    a, fd = g_app.get(r['patent_id'], (None, None))
    u = ('A' + a) if a else ('U' + d)
    doc[d] = (r['patent_date'], u, t)
    if ok(fd): doc_fd[d] = fd
del g_app
ptype = collections.Counter()
for r in tsv('pg_published_application'):
    ptype[r['patent_type']] += 1
    if not ok(r['published_date']): continue
    d = 'PG' + r['pgpub_id']; a = r['application_id'].zfill(8)
    doc[d] = (r['published_date'], 'A' + a, r['patent_type'] or 'utility')
    if ok(r['filing_date']): doc_fd[d] = r['filing_date']
R = {'format': 'ptp-p2-oa-splits-v2-addons-v2', 'grant_types': dict(gtype), 'pgpub_types': dict(ptype)}
POP_TYPES = {'utility', 'reissue'}
PG_TYPES = {'utility', 'new', 'new-utility'}
def pop_ok(d, t): return t in (PG_TYPES if d.startswith('PG') else POP_TYPES)
def in_pop(d): return d in doc and pop_ok(d, doc[d][2])
for d, (pd, u, t) in doc.items():
    if pop_ok(d, t) and (u not in unit_first or pd < unit_first[u]): unit_first[u] = pd
log('population docs', len(doc), 'units', len(unit_first))

# day histograms for fast window counts
doc_day = collections.Counter(); unit_day = collections.Counter(); unit_day_r = {r: collections.Counter() for r in RATES}
for d, (pd, u, t) in doc.items():
    if pop_ok(d, t): doc_day[pd] += 1
for u, pd in unit_first.items():
    unit_day[pd] += 1
    x = h(u)
    for r in RATES:
        if x < r: unit_day_r[r][pd] += 1
def count(hist, lo, hi): return sum(v for k, v in hist.items() if lo <= k < hi)

# ---- per split
splits = collections.defaultdict(list)
for a, t in tasks.items(): splits[t['split']].append(a)
S = {}
for s, apps in splits.items():
    fds = [tasks[a]['filing_date'] for a in apps]; mails = [tasks[a]['mail_dt'] for a in apps]
    hi_rpd, hi_oaer = max(fds), max(mails)
    sizes = {}
    for st in STARTS:
        lo = f'{st}-01-01'
        sizes[f'OP-{st}'] = {
            'RPD_docs': count(doc_day, lo, hi_rpd), 'RPD_units': count(unit_day, lo, hi_rpd),
            'OAER_docs': count(doc_day, lo, hi_oaer), 'OAER_units': count(unit_day, lo, hi_oaer),
            **{f'RPD_units_sample_{r}': count(unit_day_r[r], lo, hi_rpd) for r in RATES}}
    S[s] = {'tasks': len(apps), 'aia_proxy_tasks': sum(f >= AIA for f in fds), 'rpd_upper_date': hi_rpd,
            'oaer_upper_date': hi_oaer, 'population_size': sizes}
log('sizes')

# ---- temporal rules and coverage per pair
cov = collections.defaultdict(collections.Counter)
for a, c, basis, d3 in pairs:
    t = tasks[a]; s = t['split']; fd = t['filing_date']
    keys = ['ALL', d3, basis, f'{basis}|{d3}', 'AIA' if fd >= AIA else 'preAIA']
    info = doc.get(c)
    pd = info[0] if info else None
    dfd = doc_fd.get(c)
    rpd = bool(pd and pd < fd)
    oaer = rpd or bool(dfd and dfd < fd)
    status = []
    status.append('rpd_eligible' if rpd else ('rpd_excluded' if pd else 'date_unknown'))
    status.append('oaer_eligible' if oaer else ('oaer_excluded' if (pd or dfd) else 'oaer_date_unknown'))
    if rpd and not oaer: status.append('BUG')
    status.append('in_population_types' if in_pop(c) else ('other_type' if info else 'no_pv_record'))
    if info:
        u = info[1]
        for st in STARTS:
            if in_pop(c) and pd >= f'{st}-01-01':
                if rpd: status.append(f'covered_RPD_OP-{st}')
                if oaer: status.append(f'covered_OAER_OP-{st}')
                if rpd and st == 2001:
                    x = h(u)
                    for r in RATES:
                        if x < r: status.append(f'covered_RPD_OP-2001_sample_{r}')
    for k in keys:
        cov[(s, k)]['pairs'] += 1
        for st_ in status: cov[(s, k)][st_] += 1
for (s, k), c in cov.items():
    n = c['pairs']
    S[s].setdefault('pair_status', {})[k] = {kk: (v if kk == 'pairs' else round(v / n, 4)) for kk, v in sorted(c.items())}
# tasks with zero covered OUT3 references (RPD, OP-1976 and OP-2001)
zero = collections.defaultdict(collections.Counter)
tout = collections.defaultdict(lambda: [0, 0, 0])
for a, c, basis, d3 in pairs:
    if d3 != 'OUT3': continue
    t = tasks[a]; info = doc.get(c)
    pd = info[0] if info else None
    if pd and pd < t['filing_date'] and in_pop(c):
        tout[a][0] += 1
        if pd >= '2001-01-01': tout[a][1] += 1
    tout[a][2] += 1
for a in tasks:
    s = tasks[a]['split']; v = tout.get(a, [0, 0, 0])
    zero[s]['tasks'] += 1
    zero[s]['zero_covered_OUT3_RPD_OP-1976'] += v[0] == 0
    zero[s]['zero_covered_OUT3_RPD_OP-2001'] += v[1] == 0
for s in S: S[s]['tasks_with_zero_covered_OUT3'] = dict(zero[s])
log('coverage')

# ---- claim check: first CTNF rejections include claim 1?
first = {}
for r in rd_zip('office_actions.csv.zip', 'office_actions.csv'):
    if r['document_cd'] != 'CTNF': continue
    a = r['app_id'].zfill(8)
    if a not in tasks: continue
    k = (r['mail_dt'], r['ifw_number'])
    if a not in first or k < first[a]: first[a] = k
want = {(a, k[1]) for a, k in first.items()}
cl = {}
for r in rd_zip('rejections.csv.zip', 'rejections.csv'):
    a = r['app_id'].zfill(8)
    if (a, r['ifw_number']) not in want or r['action_type'] not in ('102', '103'): continue
    nums = {x.strip() for x in r['claim_numbers'].split(',')}
    cl[a] = cl.get(a, False) or ('1' in nums)
cc = collections.defaultdict(collections.Counter)
for a, t in tasks.items():
    cc[t['split']]['tasks'] += 1
    cc[t['split']]['joined_rejection_rows' if a in cl else 'no_rejection_row'] += 1
    cc[t['split']]['claim1_rejected_102_103'] += bool(cl.get(a))
for s in S: S[s]['claim_check'] = dict(cc[s])
miss = collections.Counter()
for c in {c for _, c, _, _ in pairs if c not in doc}:
    if c.startswith('PG'): miss['PG'] += 1
    elif c[1:].isdigit(): miss['P<=3930270' if int(c[1:]) <= 3930270 else 'P>3930270'] += 1
    else: miss['P_other_prefix'] += 1
R['cited_docs_without_pv_record'] = dict(miss)
R['splits'] = S
R['wall_seconds'] = round(time.time() - t0, 1)
out.write_text(json.dumps(R, indent=1), encoding='utf-8')
log('done')
