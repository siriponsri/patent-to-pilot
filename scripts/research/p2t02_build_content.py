"""P2-T02 step 1: complete per-unit content, C1 flat windows and C2 structural passages (protocol §3, frozen bd30d3f7).

Protocol: docs/healthtech/research/p2-coverage/P2-T02-COVERAGE-CONTROL-PROTOCOL.md. Index side only; no query, no label,
no TEST block is read here.

Content per unit (corpus order of bridgeret/texts-v1/corpus.jsonl = order of runs/z-arctic/units.json):
  - seg0 = title + "\\n" + abstract exactly as texts-v1 (the C0 join; '(no title)' if empty, abstract omitted if empty);
  - the live claims of the SAME publication as the unit's text (texts-v1 field `doc` = rep_doc: 'PG...' rows come only
    from pg_claims_*, 'P...' rows only from g_claims_*; a grant's claims can never reach a pre-grant unit), cancelled
    and empty rows dropped (bridgeret_query.is_cancelled), ordered by claim number (claim_number, else claim_sequence,
    unparsable -> 10**6; ties by file order), each cleaned with bridgeret_query._clean.
  - full text (BM25-full) = "\\n".join([seg0] + claims)   (reading order, untruncated).
Tokens: Arctic tokenizer, add_special_tokens=False, each segment (seg0, each claim) tokenized separately so that C1 and
C2 hold the identical token ids. A 512-token window = CLS + 510 content tokens + SEP (the C0 serialiser also counts the
special tokens inside its 512 cap).
  - C1: concat(seg0, claim_1 .. claim_n in reading order) cut into consecutive 510-content-token windows, no overlap.
  - C2: passage 0 = seg0 (cut flat into 510-token windows in the rare case it is longer; counted). Then one group per
    independent claim (no `dependent` field and no dependency regex = the C0 definition), followed by its dependent
    claims in reading order. A dependent claim's parent = first referenced claim number that exists in the document
    (PatentsView `dependent` field; regex fallback on the claim text), followed up to its root independent claim.
    Unresolvable dependents join the nearest preceding group (counted); a dependent with no preceding group opens its
    own group (counted). A group over 510 content tokens is cut into windows: the first window is the group's first 510
    tokens (it already starts with the independent claim); every further window = the independent claim's first 64
    tokens (parent context, counted as overhead) + the next 446 group tokens.
Outputs (<out>): units.json, c1.ids.u32 / c1.len.npy / c1.unit.npy, c2.* (same layout), ser-full/passages.jsonl
({unit, text}), stats.json, manifest.json (sha256 of every output and of the inputs/code).
Usage: python p2t02_build_content.py <bridgeret_dir> <pv_claims_dir> <out_dir> [--workers 32] [--limit N]
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import multiprocessing as mp
import os
import re
import shutil
import sys
import time
import zipfile
from pathlib import Path

csv.field_size_limit(1 << 30)
TOKDIR = '/data/ptp-paper2/models/arctic-embed-m-v2.0'
WIN, PARENT = 510, 64
CHUNK = 5000
# copied verbatim from bridgeret_query.py (the C0 serialiser)
CANCELLED = re.compile(r'^\s*\d*\s*\.?\s*\(\s*(canceled|cancelled|deleted|withdrawn)\s*\)\s*\.?\s*$', re.I)
DEPENDENCY = re.compile(r'\b(?:of|in|to|by|with|under)\s+(?:any\s+(?:one\s+)?of\s+)?claims?\s+\d+'
                        r'|\bas\s+(?:claimed|recited|defined|set\s+forth)\s+in\s+(?:any\s+(?:one\s+)?of\s+)?claims?\s+\d+'
                        r'|\bclaims?\s+\d+\s*(?:or|and|-|to)\s*\d+', re.I)
LEADING_NUMBER = re.compile(r'^\s*\d+\s*\.\s*')
DEPNUM = re.compile(r'\d+')

NEED: set = set()
CORPUS: list = []
CLAIMS: dict = {}
TOK = None
SHARDS: Path | None = None


def clean(text):
    return re.sub(r'\s+', ' ', LEADING_NUMBER.sub('', text or '')).strip()


def is_cancelled(text):
    return bool(CANCELLED.match(text or '')) or not clean(text)


def pat_key(pid):
    m = re.fullmatch(r'(RE|D|PP|H|T)?0*(\d{1,8})', (pid or '').strip().upper())
    return 'P' + (m.group(1) or '') + m.group(2) if m else 'P' + pid


def fsha(p):
    x = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 22), b''):
            x.update(b)
    return x.hexdigest()


# ---------------------------------------------------------------- phase A: claims scan
def init_scan(need):
    global NEED
    NEED = need


def scan(path):
    p = Path(path)
    pg = p.name.startswith('pg_')
    z = zipfile.ZipFile(p)
    rd = csv.reader(io.TextIOWrapper(z.open(z.namelist()[0]), encoding='utf-8', newline=''), delimiter='\t')
    h = next(rd)
    ix = {k: h.index(k) for k in ('claim_sequence', 'claim_text', 'dependent', 'claim_number')}
    idc = h.index('pgpub_id' if pg else 'patent_id')
    per, n_cancel, k = {}, 0, 0
    for r in rd:
        doc = ('PG' + r[idc]) if pg else pat_key(r[idc])
        if doc not in NEED:
            continue
        k += 1
        text = r[ix['claim_text']]
        if is_cancelled(text):
            n_cancel += 1
            continue
        num_s = r[ix['claim_number']].strip() or r[ix['claim_sequence']]
        try:
            num = int(num_s)
        except ValueError:
            num = 10 ** 6
        per.setdefault(doc, []).append((num, k, r[ix['dependent']].strip(), clean(text)))
    return p.name, per, n_cancel


# ---------------------------------------------------------------- phase B: tokenise and cut
def init_tok(shards):
    global TOK, SHARDS
    import gc
    gc.disable()          # never traverse the inherited (frozen) parent heap: avoids copy-on-write of the claims table
    os.environ['TOKENIZERS_PARALLELISM'] = 'false'
    from transformers import AutoTokenizer
    from transformers.utils import logging as hl
    hl.set_verbosity_error()
    TOK = AutoTokenizer.from_pretrained(TOKDIR)
    SHARDS = shards


def groups_for(rows):
    """rows: live claims in reading order (num, k, dep, text). Returns (list of member-index lists, counters)."""
    nums = {}
    for i, r in enumerate(rows):
        nums.setdefault(r[0], i)
    parent = [None] * len(rows)
    kind = ['indep'] * len(rows)
    for i, (num, _, dep, text) in enumerate(rows):
        if dep:
            refs, kind[i] = DEPNUM.findall(dep), 'field'
        else:
            m = DEPENDENCY.search(text)
            if not m:
                continue
            refs, kind[i] = DEPNUM.findall(m.group(0)), 'regex'
        for x in refs:
            j = nums.get(int(x))
            if j is not None and j != i:
                parent[i] = j
                break
        if parent[i] is None:
            kind[i] += '_unresolved'

    def root(i):
        seen = set()
        while kind[i] != 'indep' and parent[i] is not None and i not in seen:
            seen.add(i)
            i = parent[i]
        return i if kind[i] == 'indep' else None

    cnt = {'dep_field': 0, 'dep_regex': 0, 'dep_unresolved_attached': 0, 'dep_orphan_head': 0,
           'dep_chain_to_nonindep': 0}
    groups = {i: [i] for i in range(len(rows)) if kind[i] == 'indep'}   # head index -> members
    for i in range(len(rows)):
        if kind[i] == 'indep':
            continue
        cnt['dep_field' if kind[i].startswith('field') else 'dep_regex'] += 1
        r = root(i) if parent[i] is not None else None
        if r is not None:
            groups[r].append(i)
            continue
        if parent[i] is not None:
            cnt['dep_chain_to_nonindep'] += 1       # chain ends in an unresolved dependent (or a cycle)
        prev = max((h for h in groups if h < i), default=None)
        if prev is not None:
            cnt['dep_unresolved_attached'] += 1
            groups[prev].append(i)
        else:
            cnt['dep_orphan_head'] += 1
            groups[i] = [i]
    out = [[h] + sorted(groups[h][1:]) for h in sorted(groups)]       # groups in reading order of their head
    assert sorted(i for g in out for i in g) == list(range(len(rows)))
    return out, cnt


def windows(ids):
    return [ids[k:k + WIN] for k in range(0, len(ids), WIN)] or [ids]


def chunk_jobs(jobs):
    """Ship each chunk's rows WITH the job (pickled), so workers never read the parent's claims table."""
    for cid, lo, hi in jobs:
        part = CORPUS[lo:hi]
        yield cid, lo, part, {c[1]: CLAIMS.get(c[1], []) for c in part}


def mem_available_gib():
    avail = float('inf')
    with open('/proc/meminfo') as f:
        for line in f:
            if line.startswith('MemAvailable:'):
                avail = int(line.split()[1]) / 2 ** 20
                break
    # amendment A1: a container (RunPod pod) sees the host's /proc/meminfo; honour its cgroup memory limit too
    # Working set = usage minus reclaimable inactive file cache (as kubelet counts it); page cache alone must not abort.
    for lim_p, use_p, stat_p, key in (
            ('/sys/fs/cgroup/memory.max', '/sys/fs/cgroup/memory.current', '/sys/fs/cgroup/memory.stat', 'inactive_file'),
            ('/sys/fs/cgroup/memory/memory.limit_in_bytes', '/sys/fs/cgroup/memory/memory.usage_in_bytes',
             '/sys/fs/cgroup/memory/memory.stat', 'total_inactive_file')):
        try:
            lim = open(lim_p).read().strip()
            if lim != 'max' and int(lim) < 2 ** 60:
                used = int(open(use_p).read())
                try:
                    for line in open(stat_p):
                        k, v = line.split()
                        if k == key:
                            used -= int(v)
                            break
                except (OSError, ValueError):
                    pass
                avail = min(avail, (int(lim) - used) / 2 ** 30)
            break
        except (OSError, ValueError):
            continue
    return avail


def start_watchdog(min_gib, on_low):
    """dr-train is shared: abort the build before the host runs out of memory (22 Nov incident)."""
    import threading

    def run():
        while True:
            if mem_available_gib() < min_gib:
                print(f'MEMORY_GUARD: MemAvailable < {min_gib} GiB, aborting build', flush=True)
                on_low()
                os._exit(3)
            time.sleep(5)
    threading.Thread(target=run, daemon=True).start()


def process(job):
    import numpy as np
    cid, lo, part, claims = job
    hi = lo + len(part)
    c1_ids, c1_len, c1_unit, c2_ids, c2_len, c2_unit = [], [], [], [], [], []
    st = {'units': 0, 'no_claims': 0, 'n_claims': [], 'n_groups': [], 'tok_full': [], 'c1_n': [], 'c2_n': [],
          'c2_overhead': [], 'seg0_over_window': 0, 'groups_split': 0, 'first_claim_mismatch': 0,
          'dep_field': 0, 'dep_regex': 0, 'dep_unresolved_attached': 0, 'dep_orphan_head': 0,
          'dep_chain_to_nonindep': 0, 'join_token_diff_sample': []}
    with open(SHARDS / f'full-{cid:04d}.jsonl', 'w', encoding='utf-8') as fj:
        for ui in range(lo, hi):
            unit, doc, title, abstract, first = part[ui - lo]
            rows = sorted(claims.get(doc, []), key=lambda r: (r[0], r[1]))
            seg0 = '\n'.join(x for x in (clean(title) or '(no title)', clean(abstract)) if x)
            ctexts = [r[3] for r in rows]
            full = '\n'.join([seg0] + ctexts)
            fj.write(json.dumps({'unit': unit, 'text': full}, ensure_ascii=False) + '\n')
            enc = TOK([seg0] + ctexts, add_special_tokens=False)['input_ids']
            ids0, cids = enc[0], enc[1:]
            # first independent claim of these rows must equal the texts-v1 claim (same publication check)
            fi = next((r[3] for r in rows if not r[2] and not DEPENDENCY.search(r[3])), rows[0][3] if rows else '')
            st['first_claim_mismatch'] += int(fi != (first or ''))
            # C1
            seq = list(ids0)
            for c in cids:
                seq.extend(c)
            w1 = windows(seq)
            # C2
            p2 = windows(ids0)
            st['seg0_over_window'] += int(len(ids0) > WIN)
            overhead = 0
            if rows:
                groups, cnt = groups_for(rows)
                for k in cnt:
                    st[k] += cnt[k]
                for g in groups:
                    gid = []
                    for i in g:
                        gid.extend(cids[i])
                    if len(gid) <= WIN:
                        p2.append(gid)
                        continue
                    st['groups_split'] += 1
                    ctx = cids[g[0]][:PARENT]
                    p2.append(gid[:WIN])
                    pos, take = WIN, WIN - len(ctx)
                    while pos < len(gid):
                        p2.append(ctx + gid[pos:pos + take])
                        overhead += len(ctx)
                        pos += take
                st['n_groups'].append(len(groups))
            else:
                st['no_claims'] += 1
                st['n_groups'].append(0)
            assert sum(map(len, w1)) == len(seq) == sum(map(len, p2)) - overhead, unit
            for w in w1:
                c1_ids.append(np.asarray(w, dtype=np.uint32)); c1_len.append(len(w)); c1_unit.append(ui)
            for w in p2:
                c2_ids.append(np.asarray(w, dtype=np.uint32)); c2_len.append(len(w)); c2_unit.append(ui)
            st['units'] += 1
            st['n_claims'].append(len(rows))
            st['tok_full'].append(len(seq))
            st['c1_n'].append(len(w1))
            st['c2_n'].append(len(p2))
            st['c2_overhead'].append(overhead)
            if ui % 500 == 0:   # joined-text vs per-segment tokenisation, deterministic sample
                st['join_token_diff_sample'].append(len(TOK(full, add_special_tokens=False)['input_ids']) - len(seq))
    for arm, ids, ln, un in (('c1', c1_ids, c1_len, c1_unit), ('c2', c2_ids, c2_len, c2_unit)):
        np.concatenate(ids).astype(np.uint32).tofile(SHARDS / f'{arm}-{cid:04d}.u32')
        np.save(SHARDS / f'{arm}-{cid:04d}.len.npy', np.asarray(ln, dtype=np.int32))
        np.save(SHARDS / f'{arm}-{cid:04d}.unit.npy', np.asarray(un, dtype=np.int32))
    return cid, st


def pct(xs):
    import numpy as np
    if not len(xs):
        return {}
    a = np.asarray(xs, dtype=np.float64)
    return {'n': int(a.size), 'sum': float(a.sum()), 'mean': round(float(a.mean()), 4),
            **{f'p{q}': float(np.percentile(a, q)) for q in (10, 50, 90, 99)}, 'max': float(a.max())}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('bridgeret')
    ap.add_argument('claims')
    ap.add_argument('out')
    ap.add_argument('--workers', type=int, default=32, help='claims-scan workers (one zip each)')
    ap.add_argument('--tok-workers', type=int, default=16, help='tokenisation workers')
    ap.add_argument('--min-free-gib', type=float, default=24.0, help='abort if MemAvailable falls below this')
    ap.add_argument('--limit', type=int, default=0, help='smoke: first N corpus units only')
    a = ap.parse_args()
    assert not os.environ.get('CUDA_VISIBLE_DEVICES'), 'CPU only'
    import numpy as np
    t0 = time.time()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=False)
    shards = out / 'shards'
    shards.mkdir()
    bdir = Path(a.bridgeret)
    corpus_p = bdir / 'texts-v1/corpus.jsonl'
    with open(corpus_p, encoding='utf-8') as f:
        for i, l in enumerate(f):
            if a.limit and i >= a.limit:
                break
            r = json.loads(l)
            CORPUS.append((r['unit'], r['doc'], r['title'], r['abstract'], r['claim']))
    units = [c[0] for c in CORPUS]
    ref_units = json.loads((bdir / 'runs/z-arctic/units.json').read_text())
    assert units == ref_units[:len(units)], 'corpus order differs from the C0 (z-arctic) unit order'
    need = {c[1] for c in CORPUS}
    print(f'{time.time() - t0:7.1f}s corpus {len(CORPUS)} units, {len(need)} docs', flush=True)
    files = sorted(str(p) for p in Path(a.claims).glob('*_claims_*.tsv.zip'))
    assert len(files) == 54, len(files)
    n_cancel = 0
    with mp.get_context('fork').Pool(min(a.workers, len(files)), initializer=init_scan, initargs=(need,)) as pool:
        for name, per, nc in pool.imap_unordered(scan, sorted(files, key=lambda p: -os.path.getsize(p))):
            n_cancel += nc
            pg = name.startswith('pg_')
            for d, rows in per.items():
                assert d.startswith('PG') == pg       # a publication only receives rows of its own kind
                CLAIMS.setdefault(d, []).extend(rows)
    print(f'{time.time() - t0:7.1f}s claims scanned: {len(CLAIMS)} docs with live claims, {n_cancel} cancelled rows',
          flush=True)
    jobs = [(k, lo, min(lo + CHUNK, len(CORPUS))) for k, lo in enumerate(range(0, len(CORPUS), CHUNK))]
    agg = {}
    import gc
    gc.collect()
    gc.freeze()           # parent heap -> permanent generation: forked workers' GC never touches (copies) it
    print(f'{time.time() - t0:7.1f}s MemAvailable {mem_available_gib():.1f} GiB before tokenising', flush=True)
    with mp.get_context('fork').Pool(a.tok_workers, initializer=init_tok, initargs=(shards,),
                                     maxtasksperchild=8) as pool:
        start_watchdog(a.min_free_gib, pool.terminate)
        for n, (cid, st) in enumerate(pool.imap_unordered(process, chunk_jobs(jobs)), 1):
            agg[cid] = st
            if n % 20 == 0 or n == len(jobs):
                print(f'{time.time() - t0:7.1f}s tokenised {n}/{len(jobs)} chunks; MemAvailable '
                      f'{mem_available_gib():.1f} GiB', flush=True)
    # merge shards in corpus order
    for arm in ('c1', 'c2'):
        with open(out / f'{arm}.ids.u32', 'wb') as g:
            for k, _, _ in jobs:
                with open(shards / f'{arm}-{k:04d}.u32', 'rb') as f:
                    shutil.copyfileobj(f, g, 1 << 24)
        np.save(out / f'{arm}.len.npy', np.concatenate([np.load(shards / f'{arm}-{k:04d}.len.npy') for k, _, _ in jobs]))
        np.save(out / f'{arm}.unit.npy', np.concatenate([np.load(shards / f'{arm}-{k:04d}.unit.npy') for k, _, _ in jobs]))
    (out / 'ser-full').mkdir()
    with open(out / 'ser-full/passages.jsonl', 'wb') as g:
        for k, _, _ in jobs:
            with open(shards / f'full-{k:04d}.jsonl', 'rb') as f:
                shutil.copyfileobj(f, g, 1 << 24)
    shutil.rmtree(shards)
    (out / 'units.json').write_text(json.dumps(units))
    # integrity: lengths vs ids files, units contiguous and covered
    for arm in ('c1', 'c2'):
        ln = np.load(out / f'{arm}.len.npy'); un = np.load(out / f'{arm}.unit.npy')
        assert (out / f'{arm}.ids.u32').stat().st_size == 4 * int(ln.sum())
        assert np.all(np.diff(un) >= 0) and np.array_equal(np.unique(un), np.arange(len(units)))
        assert ln.min() >= 1 and ln.max() <= WIN
    S = {k: [] for k in ('n_claims', 'n_groups', 'tok_full', 'c1_n', 'c2_n', 'c2_overhead', 'join_token_diff_sample')}
    C = {}
    for st in agg.values():
        for k, v in st.items():
            if k in S:
                S[k].extend(v)
            else:
                C[k] = C.get(k, 0) + v
    ln1, ln2 = np.load(out / 'c1.len.npy'), np.load(out / 'c2.len.npy')
    stats = {
        'protocol': 'docs/healthtech/research/p2-coverage/P2-T02-COVERAGE-CONTROL-PROTOCOL.md@bd30d3f7',
        'window_content_tokens': WIN, 'window_model_positions': WIN + 2, 'parent_context_tokens': PARENT,
        'units': len(units), 'docs_with_live_claims': sum(1 for c in CORPUS if c[1] in CLAIMS),
        'unit_doc_kind': {'pregrant_PG': sum(c[1].startswith('PG') for c in CORPUS),
                          'grant_P': sum(not c[1].startswith('PG') for c in CORPUS)},
        'cancelled_rows_dropped': n_cancel, 'counters': C,
        'c1_passages': int(ln1.size), 'c2_passages': int(ln2.size),
        'c1_tokens': int(ln1.sum()), 'c2_tokens': int(ln2.sum()),
        'c2_parent_context_overhead_tokens': int(sum(S['c2_overhead'])),
        'c2_parent_context_overhead_share_of_content': round(sum(S['c2_overhead']) / max(1, int(ln1.sum())), 6),
        'per_unit': {k: pct(v) for k, v in S.items()},
        'passage_len': {'c1': pct(ln1), 'c2': pct(ln2)},
        'seconds': round(time.time() - t0, 1),
    }
    (out / 'stats.json').write_text(json.dumps(stats, indent=1))
    outputs = ['units.json', 'c1.ids.u32', 'c1.len.npy', 'c1.unit.npy', 'c2.ids.u32', 'c2.len.npy', 'c2.unit.npy',
               'ser-full/passages.jsonl', 'stats.json']
    man = {'script': Path(__file__).name, 'script_sha256': fsha(__file__), 'argv': sys.argv[1:],
           'inputs': {'texts-v1/corpus.jsonl': fsha(corpus_p), 'claims_files': len(files),
                      'tokenizer': TOKDIR, 'tokenizer_json_sha256': fsha(Path(TOKDIR) / 'tokenizer.json')},
           'outputs_sha256': {p: fsha(out / p) for p in outputs}, 'seconds': round(time.time() - t0, 1)}
    (out / 'manifest.json').write_text(json.dumps(man, indent=1))
    print(json.dumps({k: stats[k] for k in ('units', 'c1_passages', 'c2_passages', 'c1_tokens', 'c2_tokens',
                                            'c2_parent_context_overhead_tokens', 'counters')}, indent=1))
    print('BUILD_DONE', round(time.time() - t0, 1), flush=True)


if __name__ == '__main__':
    main()
