"""Challenge-1M v1: sealed corpus-membership builder (R-05 design, owner-approved 2026-11-18). Stdlib only.

DECLARED before the first run (no retrieval number exists for P1-BridgeRet):

Unit      = one US application (a grant and its pre-grant publication count once). Grants map through
            g_application (patent_id -> application_id), pre-grant publications through
            pg_published_application. A cited document that cannot be mapped is its own unit.
            first_pub = earliest publication date of the unit; rep_doc = that earliest document
            (the text the public could first read; used for the corpus passage).
Population = units with 1976-01-01 <= first_pub <= 2012-12-31 (corpus start year 1976, the higher-coverage
            option in OA-SPLITS R1b; upper date = last P1-TEST filing year). Grants of any type in g_patent;
            pre-grant publications of type utility/new/new-utility (OA-SPLITS amendment 1).
Tier 1    = every population unit cited in K(q) of a P1 evaluation task (P1-TEST, P1-DEV, VAL). Always kept.
Tier 2    = every population unit cited in K(q) of any other eligible task (natural, citation-enriched distractors).
Tier 3    = uniform sample of the remaining population by ascending sha256('ptp-challenge1m-v1|' + unit_id).
Size      = exactly 1,000,000 units: tier 1 in full; tier 2 in full if it fits, else its salted-hash prefix;
            tier 3 fills the rest. No label-dependent choice beyond these tiers; no rebalancing by hand.

Isolation (R-05): this is the ONLY process that reads pairs.tsv rows of protected tasks (P1-TEST, P2-TEST,
P3-TEST). It writes
  out/corpus-units.tsv       unit_id, rep_doc, first_pub   (ordered by salted hash; no tier/label column)
  out/pairs-dev.tsv          K pairs of TRAIN/VAL/P1-DEV/P2-DEV tasks mapped to units (developer-visible)
  out/sealed/qrels-p1-test.tsv  P1-TEST K pairs mapped to units (mode 600; opened only via ProtectedGoldGate)
  out/report.json            aggregate counts + sha256 of every output; per-task information never printed.
Usage: python3 -I build_challenge1m_sealed.py <pv_dir> <pairs.tsv> <frozen_manifest.json> <out_dir>
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
import sys
import time
import zipfile
from pathlib import Path

csv.field_size_limit(1 << 30)
SALT = 'ptp-challenge1m-v1'
SIZE = 1_000_000
START, END = '1976-01-01', '2012-12-31'
PG_TYPES = {'utility', 'new', 'new-utility'}
EVAL = ('P1-TEST', 'P1-DEV', 'VAL')
DEVVIS = ('TRAIN', 'VAL', 'P1-DEV', 'P2-DEV')
PROTECTED = ('P1-TEST', 'P2-TEST', 'P3-TEST')


def tsv(d: Path, name: str):
    z = zipfile.ZipFile(d / f'{name}.tsv.zip')
    return csv.DictReader(io.TextIOWrapper(z.open(f'{name}.tsv'), encoding='utf-8', newline=''), delimiter='\t')


def app_norm(s):
    t = re.sub(r'[\s/,]', '', s or '')
    return t if re.fullmatch(r'\d{8}', t) else None


def pat_key(pid):
    m = re.fullmatch(r'(RE|D|PP|H|T)?0*(\d{1,8})', (pid or '').strip().upper())
    return 'P' + (m.group(1) or '') + m.group(2) if m else 'P' + pid


def h(u):
    return hashlib.sha256(f'{SALT}|{u}'.encode()).hexdigest()


def fsha(p):
    x = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 22), b''):
            x.update(b)
    return x.hexdigest()


def main(argv):
    pv, pairs_p, man_p, out = Path(argv[0]), Path(argv[1]), Path(argv[2]), Path(argv[3])
    out.mkdir(parents=True, exist_ok=False)
    (out / 'sealed').mkdir(mode=0o700)
    t0 = time.time()
    man = json.loads(man_p.read_text())
    if not man.get('frozen'):
        raise SystemExit('manifest is not frozen')
    block_of = {a: b for b, ids in man['blocks'].items() for a in ids}

    # documents -> unit, first publication date
    doc_unit, unit_first = {}, {}

    def add(doc, unit, date):
        doc_unit[doc] = unit
        cur = unit_first.get(unit)
        if date and (cur is None or (date, doc) < cur):
            unit_first[unit] = (date, doc)

    pat_app = {r['patent_id']: app_norm(r['application_id']) for r in tsv(pv, 'g_application')}
    for r in tsv(pv, 'g_patent'):
        pid = r['patent_id']
        a = pat_app.get(pid)
        add(pat_key(pid), f'A:{a}' if a else f'D:{pat_key(pid)}', r['patent_date'])
    del pat_app
    for r in tsv(pv, 'pg_published_application'):
        if r['patent_type'] not in PG_TYPES:
            continue
        a = app_norm(r['application_id'])
        add('PG' + r['pgpub_id'], f'A:{a}' if a else f'D:PG{r["pgpub_id"]}', r['published_date'])
    population = {u for u, (d, _) in unit_first.items() if START <= d <= END}

    # pairs: the only pass over protected rows
    tier1, tier2 = set(), set()
    n_pairs = {b: 0 for b in list(DEVVIS) + list(PROTECTED) + ['OTHER']}
    unmapped = {'eval': 0, 'other': 0}
    f_dev = open(out / 'pairs-dev.tsv', 'w', encoding='utf-8')
    f_dev.write('app_id\tblock\tcited\tunit\tbasis\tdom_ipc3\tunit_first_pub\n')
    seal_path = out / 'sealed' / 'qrels-p1-test.tsv'
    f_seal = os.fdopen(os.open(seal_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'w', encoding='utf-8')
    f_seal.write('app_id\tcited\tunit\tbasis\tdom_ipc3\tunit_first_pub\n')
    with open(pairs_p, encoding='utf-8', newline='') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            b = block_of.get(r['app_id'], 'OTHER')
            n_pairs[b] += 1
            c = r['cited']
            u = doc_unit.get(c)
            up = unit_first.get(u, ('', ''))[0] if u else ''
            in_pop = u in population
            if b in EVAL:
                if in_pop:
                    tier1.add(u)
                elif not u:
                    unmapped['eval'] += 1
            elif in_pop:
                tier2.add(u)
            elif not u:
                unmapped['other'] += 1
            row = (r['app_id'], c, u or '', r['basis'], r['dom_ipc3'], up)
            if b in DEVVIS:
                f_dev.write(f'{row[0]}\t{b}\t' + '\t'.join(row[1:]) + '\n')
            elif b == 'P1-TEST':
                f_seal.write('\t'.join(row) + '\n')
    f_dev.close()
    f_seal.close()
    tier2 -= tier1
    if len(tier1) > SIZE:
        raise SystemExit('tier 1 alone exceeds the corpus size')
    room = SIZE - len(tier1)
    t2 = sorted(tier2, key=h)[:room] if len(tier2) > room else sorted(tier2)
    chosen = tier1 | set(t2)
    rest = sorted((u for u in population if u not in chosen), key=h)[:SIZE - len(chosen)]
    chosen |= set(rest)
    with open(out / 'corpus-units.tsv', 'w', encoding='utf-8') as f:
        f.write('unit_id\trep_doc\tfirst_pub\n')
        for u in sorted(chosen, key=h):
            d, doc = unit_first[u]
            f.write(f'{u}\t{doc}\t{d}\n')
    rep = {'format': 'ptp-challenge1m-v1', 'salt': SALT, 'size': len(chosen), 'window': [START, END],
           'population_units': len(population), 'tier1_units': len(tier1), 'tier2_units_total': len(tier2),
           'tier2_units_kept': len(t2), 'tier3_units': len(rest), 'pairs_by_block': n_pairs,
           'cited_docs_unmapped_pairs': unmapped, 'manifest_sha256': man['manifest_sha256'],
           'outputs_sha256': {p: fsha(out / p) for p in ('corpus-units.tsv', 'pairs-dev.tsv', 'sealed/qrels-p1-test.tsv')},
           'seconds': round(time.time() - t0, 1)}
    (out / 'report.json').write_text(json.dumps(rep, indent=1))
    os.chmod(seal_path, 0o400)
    print(json.dumps(rep, indent=1))


if __name__ == '__main__':
    main(sys.argv[1:])
