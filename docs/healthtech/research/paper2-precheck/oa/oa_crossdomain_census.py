"""Paper 2 stream 3: size an OA-derived cross-domain set and link it to DAPFAM dev.

Inputs (all public / dev-only; nothing written except aggregates):
  raw_dir: citations.csv.zip (USPTO OA Research Dataset 2017), PatentsView
           g_application, g_ipc_at_issue, g_patent, pg_published_application, pg_ipc_at_issue (.tsv.zip)
  dev_dir: staged DAPFAM dev (queries-ta ids, qrels-dev)
  dev_meta: private JSONL from export_dapfam_dev_meta.py (dev ids, jurisdiction, date, title, positive pairs)
Usage: python3 -I oa_crossdomain_census.py <raw_dir> <dev_meta.jsonl> <out.json>  (stdlib only)

A1: (application, cited US doc) pairs whose citation backs a 102 or 103 rejection
    (action_type in {102,103} and citation_in_oa=1), with IPC on both sides; IN/OUT by
    shared IPC3 (DAPFAM rule), shared IPC4 and IPC section.
A2: DAPFAM dev families mapped to US documents by exact normalised title (unique match,
    US document filed on/after the family's earliest claim date); then overlap with A1.
    Title matching is an approximation: ambiguous titles abstain and are counted.
"""
import collections, csv, io, json, re, sys, time, zipfile
from pathlib import Path

csv.field_size_limit(1 << 30)
raw, devmeta, out = map(Path, sys.argv[1:4])
t0 = time.time()
R = {}

def tsv(name):
    z = zipfile.ZipFile(raw / f'{name}.tsv.zip')
    f = io.TextIOWrapper(z.open(z.namelist()[0]), encoding='utf-8', errors='replace', newline='')
    return csv.DictReader(f, delimiter='\t')

def norm_id(s):
    s = s.strip().upper().replace(',', '')
    if re.fullmatch(r'\d{11}', s): return 'PG' + s           # pre-grant publication
    m = re.fullmatch(r'(RE|D|PP|H|T)?0*(\d{1,8})', s)
    if m: return 'P' + (m.group(1) or '') + m.group(2)         # patent
    return None                                                # foreign / unparseable

# ---- pass 1: OA citations backing 102/103
z = zipfile.ZipFile(raw / 'citations.csv.zip')
f = io.TextIOWrapper(z.open('citations.csv'), encoding='utf-8', errors='replace', newline='')
rows = 0; basis_rows = collections.Counter(); kinds = collections.Counter()
pairs = {}  # (app_id, cited) -> set of bases
apps_any = set()
for row in csv.DictReader(f):
    rows += 1
    apps_any.add(row['app_id'])
    at = row['action_type']
    if at not in ('102', '103') or row['citation_in_oa'] != '1':
        continue
    basis_rows[at] += 1
    cid = norm_id(row['parsed'] or row['citation_pat_pgpub_id'])
    kinds['PG' if cid and cid.startswith('PG') else 'P' if cid else 'foreign_or_unparsed'] += 1
    if not cid:
        continue
    k = (row['app_id'].zfill(8), cid); pairs[k] = pairs.get(k, 0) | (1 if at == '102' else 2)
R['oa_citation_rows'] = rows
R['oa_applications_any_citation'] = len(apps_any)
R['oa_rows_102_103_in_action'] = dict(basis_rows)
R['oa_rows_102_103_cited_kind'] = dict(kinds)
R['oa_pairs_102_103_us'] = len(pairs)
BN = {1: '102', 2: '103', 3: 'both'}
R['oa_pairs_by_basis'] = dict(collections.Counter(BN[b] for b in pairs.values()))
apps = {a for a, _ in pairs}
cited_p = {c[1:] for _, c in pairs if c.startswith('P') and not c.startswith('PG')}
cited_pg = {c[2:] for _, c in pairs if c.startswith('PG')}
R['oa_citing_applications_102_103'] = len(apps)
print('pass1', round(time.time() - t0), 's', len(pairs), 'pairs', flush=True)

# ---- IPC maps
app2pg = collections.defaultdict(set); app2pat = collections.defaultdict(set)
for r in tsv('pg_published_application'):
    a = r['application_id'].zfill(8)
    if a in apps: app2pg[a].add(r['pgpub_id'])
for r in tsv('g_application'):
    a = r['application_id'].zfill(8)
    if a in apps: app2pat[a].add(r['patent_id'])
need_pg = set().union(*app2pg.values()) | cited_pg if app2pg else set(cited_pg)
need_pat = set().union(*app2pat.values()) | cited_p if app2pat else set(cited_p)
pg_ipc = collections.defaultdict(set); pat_ipc = collections.defaultdict(set)
for r in tsv('pg_ipc_at_issue'):
    if r['pgpub_id'] in need_pg and r['section']:
        pg_ipc[r['pgpub_id']].add(r['section'] + r['ipc_class'].zfill(2) + r['subclass'])
for r in tsv('g_ipc_at_issue'):
    if r['patent_id'] in need_pat and r['section']:
        pat_ipc[r['patent_id']].add(r['section'] + r['ipc_class'].zfill(2) + r['subclass'])
print('ipc', round(time.time() - t0), 's', flush=True)

def app_ipc(a):
    s = set()
    for p in app2pg.get(a, ()): s |= pg_ipc.get(p, set())
    for p in app2pat.get(a, ()): s |= pat_ipc.get(p, set())
    return s
def cited_ipc(c):
    return pg_ipc.get(c[2:], set()) if c.startswith('PG') else pat_ipc.get(c[1:], set())

tab = collections.Counter(); secx = collections.Counter(); a_ok = c_ok = 0
app_cache = {}
for (a, c), b in pairs.items():
    ai = app_cache.get(a)
    if ai is None: ai = app_cache[a] = app_ipc(a)
    ci = cited_ipc(c)
    a_ok += bool(ai); c_ok += bool(ci)
    if not ai or not ci:
        tab[('no_ipc',)] += 1; continue
    basis = BN[b]
    in3 = bool({x[:3] for x in ai} & {x[:3] for x in ci})
    in4 = bool(ai & ci)
    insec = bool({x[0] for x in ai} & {x[0] for x in ci})
    tab[(basis, 'IN3' if in3 else 'OUT3')] += 1
    tab[(basis, 'IN4' if in4 else 'OUT4')] += 1
    tab[(basis, 'SAMESEC' if insec else 'SECMISMATCH')] += 1
    if not insec:
        secx[min(ai)[0] + '->' + min(ci)[0]] += 1
R['a1_pairs_citing_has_ipc'] = a_ok
R['a1_pairs_cited_has_ipc'] = c_ok
R['a1_crosstab'] = {'|'.join(k): v for k, v in sorted(tab.items())}
R['a1_section_mismatch_by_first_sections'] = dict(secx.most_common())
oa_apps_out3 = collections.Counter()
for (a, c), b in pairs.items():
    ai, ci = app_cache.get(a) or set(), cited_ipc(c)
    if ai and ci and not ({x[:3] for x in ai} & {x[:3] for x in ci}):
        oa_apps_out3[a] += 1
R['a1_applications_with_ge1_OUT3_pair'] = len(oa_apps_out3)
R['a1_applications_with_ge3_OUT3_pairs'] = sum(v >= 3 for v in oa_apps_out3.values())
print('a1', round(time.time() - t0), 's', flush=True)

# ---- A2: DAPFAM dev linkage by exact normalised title
def nt(s): return re.sub(r'[^a-z0-9]+', ' ', (s or '').lower()).strip()
fam = {}; qids = []; pos = []
for l in open(devmeta, encoding='utf-8'):
    r = json.loads(l)
    if r['role'] == 'pair':
        pos.append({'query_id': r['q'], 'relevant_id': r['t'], 'domain_rel': r['domain']}); continue
    fam[r['id']] = {'jurisdiction': r['jurisdiction'], 'earliest_claim_date': r['date'], 'title_en': r['title']}
    if r['role'] == 'query': qids.append(r['id'])
tgt = {r['relevant_id'] for r in pos}
title2fam = collections.defaultdict(set)
for k, r in fam.items():
    if 'US' in (r['jurisdiction'] or []) and nt(r['title_en']): title2fam[nt(r['title_en'])].add(k)
cand = collections.defaultdict(set)  # family -> {('APP', app_id) | ('P', id) | ('PG', id)}
def take(title, date, docs):
    t = nt(title)
    for k in title2fam.get(t, ()):
        d0 = fam[k]['earliest_claim_date']
        if d0 is None or not date or date >= str(d0)[:10]:
            cand[k].update(docs)
for r in tsv('pg_published_application'):
    take(r['application_title'], r['filing_date'], {('APP', r['application_id'].zfill(8)), ('PG', r['pgpub_id'])})
pat2app = {}
for r in tsv('g_patent'):
    take(r['patent_title'], r['patent_date'], {('P', r['patent_id'])})
for r in tsv('g_application'):
    pat2app[r['patent_id']] = r['application_id'].zfill(8)
for k, s in cand.items():
    for kind, v in list(s):
        if kind == 'P' and v in pat2app: s.add(('APP', pat2app[v]))
title_n = collections.Counter(nt(r['title_en']) for r in fam.values())
def mapped(k):
    s = cand.get(k, set())
    apps_k = {v for kind, v in s if kind == 'APP'}
    if not s or title_n[nt(fam[k]['title_en'])] > 1 or len(apps_k) > 3:
        return None  # unmatched or ambiguous -> abstain
    return s
qmap = {q: mapped(q) for q in qids}
tmap = {t: mapped(t) for t in tgt}
R['a2_dev_queries'] = len(qids)
R['a2_queries_mapped_to_us_docs'] = sum(v is not None for v in qmap.values())
R['a2_queries_with_oa_102_103'] = sum(bool(v and ({x for k_, x in v if k_ == 'APP'} & apps)) for v in qmap.values())
R['a2_queries_with_any_oa_citation_row'] = sum(bool(v and ({x for k_, x in v if k_ == 'APP'} & {a.zfill(8) for a in apps_any})) for v in qmap.values())
R['a2_dev_positive_targets'] = len(tgt)
R['a2_targets_mapped'] = sum(v is not None for v in tmap.values())
x = collections.Counter()
for r in pos:
    qa, ta = qmap.get(r['query_id']), tmap.get(r['relevant_id'])
    if not qa or not ta:
        x[(r['domain_rel'], 'unmapped')] += 1; continue
    qapps = {v for k_, v in qa if k_ == 'APP'}
    tdocs = {(('PG' if k_ == 'PG' else 'P') + v) for k_, v in ta if k_ in ('P', 'PG')}
    bases = 0
    for a in qapps:
        for d in tdocs:
            bases |= pairs.get((a, d), 0)
    if not qapps & apps:
        x[(r['domain_rel'], 'query_no_oa_102_103')] += 1
    elif not bases:
        x[(r['domain_rel'], 'mapped_not_cited_102_103')] += 1
    else:
        x[(r['domain_rel'], 'cited_' + BN[bases])] += 1
R['a2_dev_positive_pairs'] = len(pos)
R['a2_pairs_crosstab'] = {'|'.join(k): v for k, v in sorted(x.items())}
R['wall_seconds'] = round(time.time() - t0, 1)
out.write_text(json.dumps(R, indent=1), encoding='utf-8')
print(json.dumps(R, indent=1))
