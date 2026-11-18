"""Spec 01 section 5 truncation analysis (required before DEV freeze). CPU only, no model weights.

Tokenizer = the pinned Arctic tokenizer; cap 512 tokens; query side carries Arctic's 'query: ' prompt.
Samples (salted hash, declared): all VAL and P1-DEV queries; 20,000 TRAIN queries; 50,000 Challenge-1M passages.
Reports per set: token-length quantiles of each component and of the serialised text, share truncated,
share of claim/abstract tokens removed, variant counts. Never reads TEST queries (queries.jsonl has none).
Usage: python3 -I bridgeret_truncation_analysis.py <texts_dir> <arctic_dir> <out.json>
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from patent_to_pilot.research import bridgeret_query as q
except ImportError:
    import bridgeret_query as q

SALT = 'ptp-trunc-v1'
CAP = 512
QUERY_PROMPT = 'query: '


def h(x):
    return hashlib.sha256(f'{SALT}|{x}'.encode()).hexdigest()


def quant(xs):
    xs = sorted(xs)
    if not xs:
        return {}
    pick = lambda p: xs[min(len(xs) - 1, int(p * len(xs)))]
    return {'n': len(xs), 'p50': pick(.5), 'p90': pick(.9), 'p99': pick(.99), 'max': xs[-1],
            'mean': round(sum(xs) / len(xs), 1)}


def analyse(rows, count, prompt):
    comp = {k: [] for k in ('title', 'abstract', 'claim', 'full')}
    trunc = {'any': 0, 'claim': 0, 'abstract': 0, 'title_over_cap': 0}
    removed = {'claim': 0, 'abstract': 0}
    variants = {}
    for r in rows:
        for k in ('title', 'abstract', 'claim'):
            comp[k].append(count(r[k]) if r[k] else 0)
        full = '\n'.join(v for v in (r['title'], r['abstract'], r['claim']) if v)
        comp['full'].append(count(prompt + full))
        cl = [q.ClaimRow(1, r['claim'])] if r['claim'] else []
        s = q.serialise(r['title'] or '(no title)', r['abstract'], cl, lambda t: count(prompt + t), CAP)
        trunc['any'] += bool(s.truncated)
        for k, v in s.truncated.items():
            trunc[k] += 1
            removed[k] += v
        trunc['title_over_cap'] += 'title_over_cap' in s.variant
        v = r.get('claim_variant', '?') + ('|no_abstract' if not r['abstract'] else '')
        variants[v] = variants.get(v, 0) + 1
    n = len(rows)
    return {'n': n, 'tokens': {k: quant(v) for k, v in comp.items()},
            'share_truncated': {k: round(v / n, 4) for k, v in trunc.items()} if n else {},
            'removed_tokens_mean_when_truncated': {k: round(removed[k] / trunc[k], 1) if trunc[k] else 0 for k in removed},
            'variants': variants}


def main(argv):
    d, arctic, out = Path(argv[0]), argv[1], Path(argv[2])
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(arctic)
    count = lambda t: len(tok(t, add_special_tokens=True)['input_ids'])
    t0 = time.time()
    qs = [json.loads(l) for l in open(d / 'queries.jsonl', encoding='utf-8')]
    qs = [r for r in qs if r.get('doc')]
    sets = {'VAL': [r for r in qs if r['block'] == 'VAL'],
            'P1-DEV': [r for r in qs if r['block'] == 'P1-DEV'],
            'TRAIN-20k': sorted((r for r in qs if r['block'] == 'TRAIN'), key=lambda r: h(r['app_id']))[:20000]}
    corpus = []
    with open(d / 'corpus.jsonl', encoding='utf-8') as f:
        for l in f:
            r = json.loads(l)
            corpus.append((h(r['unit']), r))
    corpus = [r for _, r in sorted(corpus, key=lambda x: x[0])[:50000]]
    res = {'tokenizer': arctic, 'cap': CAP, 'query_prompt': QUERY_PROMPT, 'salt': SALT}
    for k, rows in sets.items():
        res[k] = analyse(rows, count, QUERY_PROMPT)
    res['CORPUS-50k'] = analyse(corpus, count, '')
    res['seconds'] = round(time.time() - t0, 1)
    out.write_text(json.dumps(res, indent=1))
    print(json.dumps({k: (v.get('share_truncated') if isinstance(v, dict) else v) for k, v in res.items()}, indent=1))


if __name__ == '__main__':
    main(sys.argv[1:])
