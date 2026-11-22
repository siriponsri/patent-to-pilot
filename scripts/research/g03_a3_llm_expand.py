"""G03 amendment 3: LLM query expansion through OpenRouter (docs/healthtech/research/g03-dev/G03-DEV-AMENDMENT-3-20261122.md).

Runtime side only: reads query texts (title, abstract, first claim) of allowed DEV blocks, never labels. Stdlib only, so it
runs in the owner's .venv. The API key is read from the environment variable OPENROUTER_API_KEY and never printed or
written. Every attempt is appended to a JSONL ledger; the caller stops by itself at the envelope stop rules (USD 6.00
cumulative, 35,000 attempted requests across all models), so a later call never exceeds them.

Usage:
  python scripts/research/g03_a3_llm_expand.py --queries Q.jsonl --apps-file apps.json --model qwen/qwen3.7-flash \
      --ledger-root ../_private_artifacts/g03-a3 [--block P1-DEV] [--concurrency 8] [--max-usd 6.0] [--max-requests 35000]
  python scripts/research/g03_a3_llm_expand.py --summary --ledger-root ../_private_artifacts/g03-a3
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ENDPOINT = 'https://openrouter.ai/api/v1/chat/completions'
KEY_ENV = 'OPENROUTER_API_KEY'
PROTECTED = {'P1-TEST', 'P2-TEST', 'P3-TEST'}
ALLOWED_BLOCKS = {'P1-DEV', 'VAL', 'TRAIN'}      # TRAIN only for format smoke checks
MAX_TOKENS, TEMPERATURE, SEED, FIELD_CHARS = 400, 0, 20261122, 1500
RETRY_STATUS = {408, 429, 500, 502, 503, 504}
MAX_RETRIES = 2

SYSTEM = 'You are an experienced patent examiner searching for prior art.'
USER_TEMPLATE = (
    'Below is a patent application. Write three short hypothetical abstracts (50 to 70 words each) of EARLIER patent '
    'documents\nthat an examiner would likely cite against it. Make them different: (1) a document that solves the same '
    'technical\nproblem, (2) a document that discloses the key mechanism of the first claim, possibly in another field, '
    '(3) a document\nfrom a closely related or broader technical field. Use the technical vocabulary such documents would '
    'use, including\nsynonyms. Then write one keyword search query of 15 to 25 distinctive technical terms and synonyms. '
    'Do not mention this\napplication. Reply with JSON only: {{"priors": ["...", "...", "..."], "keywords": "..."}}\n\n'
    'Title: {title}\nAbstract: {abstract}\nFirst claim: {claim}')

# reasoning off: models whose OpenRouter entry lists effort "none" get it; the others get enabled=false
REASONING_OFF = {
    'deepseek/deepseek-v4-flash-0731': {'effort': 'none'},
    'anthropic/claude-haiku-5.5': {'effort': 'none'},
    'qwen/qwen3.7-flash': {'enabled': False},
    'qwen/qwen3-32b': {'enabled': False},
}


def cut(text: str, n: int = FIELD_CHARS) -> str:
    text = (text or '').strip()
    if len(text) <= n:
        return text
    head = text[:n]
    sp = head.rfind(' ')
    return head[:sp] if sp > 0 else head


def build_prompt(row: dict) -> str:
    return USER_TEMPLATE.format(title=(row.get('title') or '').strip(), abstract=cut(row.get('abstract')),
                                claim=cut(row.get('claim')))


_STR = re.compile(r'"((?:[^"\\]|\\.)*)"')


def parse_reply(text: str) -> dict:
    """Return {'priors': [...], 'keywords': str, 'usable': bool, 'parse': 'json'|'salvaged'|'none'}."""
    text = text or ''
    start = text.find('{')
    if start >= 0:
        depth, end, in_str, esc = 0, -1, False, False
        for i, ch in enumerate(text[start:], start):
            if in_str:
                if esc:
                    esc = False
                elif ch == '\\':
                    esc = True
                elif ch == '"':
                    in_str = False
            elif ch == '"':
                in_str = True
            elif ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    end = i
                    break
        if end > 0:
            try:
                obj = json.loads(text[start:end + 1])
                pri = [p.strip() for p in (obj.get('priors') or []) if isinstance(p, str) and p.strip()][:3]
                kw = obj.get('keywords')
                kw = ' '.join(kw) if isinstance(kw, list) else (kw or '')
                kw = kw.strip() if isinstance(kw, str) else ''
                return {'priors': pri, 'keywords': kw, 'usable': bool(pri or kw), 'parse': 'json'}
            except (ValueError, AttributeError):
                pass
        # cut at max_tokens: keep complete strings inside the priors array only
        m = re.search(r'"priors"\s*:\s*\[', text[start:])
        if m:
            body = text[start + m.end():]
            close = body.find(']')
            seg = body if close < 0 else body[:close]
            pri = []
            for s in _STR.findall(seg):
                try:
                    v = json.loads(f'"{s}"').strip()
                except ValueError:
                    continue
                if v:
                    pri.append(v)
            pri = pri[:3]
            return {'priors': pri, 'keywords': '', 'usable': bool(pri), 'parse': 'salvaged'}
    return {'priors': [], 'keywords': '', 'usable': False, 'parse': 'none'}


def ledger_totals(root: Path) -> tuple[float, int, int]:
    """Cumulative (usd, attempts, unknown_cost_attempts) over every ledger file under root."""
    usd, n, unknown = 0.0, 0, 0
    for p in root.rglob('*.jsonl'):
        with open(p, encoding='utf-8') as f:
            for line in f:
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                n += 1
                c = r.get('cost_usd')
                if c is None:
                    if r.get('status') != 'transport_error_unbilled':
                        unknown += 1
                else:
                    usd += float(c)
    return usd, n, unknown


class Budget:
    def __init__(self, usd: float, n: int, max_usd: float, max_requests: int):
        self.usd, self.n, self.max_usd, self.max_requests = usd, n, max_usd, max_requests
        self.lock = threading.Lock()
        self.stopped = ''

    def take(self) -> bool:
        with self.lock:
            if self.stopped:
                return False
            if self.usd >= self.max_usd:
                self.stopped = f'stop rule: USD {self.usd:.4f} >= {self.max_usd}'
                return False
            if self.n >= self.max_requests:
                self.stopped = f'stop rule: {self.n} attempted requests >= {self.max_requests}'
                return False
            self.n += 1
            return True

    def add(self, usd: float | None):
        with self.lock:
            if usd:
                self.usd += usd


def call(model: str, prompt: str, key: str, timeout: float = 120.0) -> tuple[int, dict | None, str]:
    body = {'model': model, 'messages': [{'role': 'system', 'content': SYSTEM}, {'role': 'user', 'content': prompt}],
            'max_tokens': MAX_TOKENS, 'temperature': TEMPERATURE, 'seed': SEED,
            'reasoning': REASONING_OFF.get(model, {'enabled': False})}
    req = urllib.request.Request(ENDPOINT, data=json.dumps(body).encode('utf-8'), method='POST', headers={
        'Authorization': f'Bearer {key}', 'Content-Type': 'application/json',
        'X-Title': 'patent-to-pilot research (G03 A3)'})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read().decode('utf-8')), ''
    except urllib.error.HTTPError as e:
        try:
            detail = e.read().decode('utf-8', 'replace')[:500]
        except Exception:  # noqa: BLE001
            detail = ''
        return e.code, None, detail
    except Exception as e:  # noqa: BLE001  (timeouts, connection errors)
        return 0, None, f'{type(e).__name__}: {e}'[:500]


def run(args) -> int:
    key = os.environ.get(KEY_ENV)
    if not key:
        raise SystemExit(f'{KEY_ENV} is not set; the owner sets it (the key is never stored in the repo)')
    blocks = set(args.block)
    if blocks & PROTECTED or not blocks <= ALLOWED_BLOCKS:
        raise SystemExit('refusing: TEST or unknown block')
    apps = set(json.loads(Path(args.apps_file).read_text(encoding='utf-8')))
    rows = []
    with open(args.queries, encoding='utf-8') as f:
        for line in f:
            r = json.loads(line)
            if r['block'] in blocks and r['app_id'] in apps:
                rows.append(r)
    root = Path(args.ledger_root)
    out = root / args.model.replace('/', '__') / f"{'+'.join(sorted(blocks))}.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if out.exists():
        with open(out, encoding='utf-8') as f:
            for line in f:
                r = json.loads(line)
                if r.get('status') in ('ok', 'content_unusable'):
                    done.add(r['app_id'])
    todo = sorted((r for r in rows if r['app_id'] not in done), key=lambda r: r['app_id'])
    usd, n, unknown = ledger_totals(root)
    budget = Budget(usd, n, args.max_usd, args.max_requests)
    print(f'{args.model}: {len(rows)} queries, {len(done)} done, {len(todo)} to call; ledger so far USD {usd:.4f}, '
          f'{n} attempts, {unknown} unknown-cost', flush=True)
    wlock = threading.Lock()
    fout = open(out, 'a', encoding='utf-8')
    t0 = time.time()
    stats = {'ok': 0, 'content_unusable': 0, 'failed': 0}

    def one(r):
        prompt = build_prompt(r)
        for attempt in range(MAX_RETRIES + 1):
            if not budget.take():
                return
            t = time.time()
            status, resp, err = call(args.model, prompt, key)
            rec = {'app_id': r['app_id'], 'block': r['block'], 'model': args.model, 'attempt': attempt,
                   'http': status, 'wall_s': round(time.time() - t, 2)}
            if resp is not None and status == 200 and resp.get('choices'):
                ch = resp['choices'][0]
                text = (ch.get('message') or {}).get('content') or ''
                usage = resp.get('usage') or {}
                parsed = parse_reply(text)
                rec.update({'status': 'ok' if parsed['usable'] else 'content_unusable', 'id': resp.get('id'),
                            'provider': resp.get('provider'), 'finish_reason': ch.get('finish_reason'),
                            'prompt_tokens': usage.get('prompt_tokens'),
                            'completion_tokens': usage.get('completion_tokens'),
                            'reasoning_tokens': (usage.get('completion_tokens_details') or {}).get('reasoning_tokens'),
                            'cost_usd': usage.get('cost'), 'raw': text, **parsed})
                budget.add(usage.get('cost'))
            else:
                billed_unknown = status == 0          # a timeout may have been billed upstream
                rec.update({'status': 'transport_error' if billed_unknown else 'transport_error_unbilled',
                            'cost_usd': None, 'error': err})
            with wlock:
                fout.write(json.dumps(rec, ensure_ascii=False) + '\n')
                fout.flush()
                stats[rec['status'] if rec['status'] in stats else 'failed'] += 1
            if rec['status'] in ('ok', 'content_unusable'):
                return
            if status and status not in RETRY_STATUS:
                return
            time.sleep(2 ** attempt * 3)

    try:
        with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
            for i, _ in enumerate(ex.map(one, todo), 1):
                if i % 200 == 0:
                    print(f'{time.time() - t0:7.1f}s {i}/{len(todo)} USD {budget.usd:.4f} attempts {budget.n} {stats}',
                          flush=True)
    finally:
        fout.close()
    print(f'END {args.model}: {stats}; ledger USD {budget.usd:.4f}, attempts {budget.n}'
          + (f'; {budget.stopped}' if budget.stopped else ''), flush=True)
    return 2 if budget.stopped else 0


def summary(args) -> int:
    root = Path(args.ledger_root)
    out = {}
    for p in sorted(root.rglob('*.jsonl')):
        agg = {'attempts': 0, 'ok': 0, 'content_unusable': 0, 'transport_error': 0, 'transport_error_unbilled': 0,
               'usd': 0.0, 'unknown_cost': 0, 'prompt_tokens': 0, 'completion_tokens': 0, 'reasoning_tokens': 0,
               'salvaged': 0, 'finish_length': 0, 'apps_usable': set(), 'providers': {}}
        with open(p, encoding='utf-8') as f:
            for line in f:
                r = json.loads(line)
                agg['attempts'] += 1
                agg[r['status']] = agg.get(r['status'], 0) + 1
                if r.get('cost_usd') is None:
                    agg['unknown_cost'] += r['status'] == 'transport_error'
                else:
                    agg['usd'] += r['cost_usd']
                for k in ('prompt_tokens', 'completion_tokens', 'reasoning_tokens'):
                    agg[k] += r.get(k) or 0
                agg['salvaged'] += r.get('parse') == 'salvaged'
                agg['finish_length'] += r.get('finish_reason') == 'length'
                if r['status'] == 'ok':
                    agg['apps_usable'].add(r['app_id'])
                if r.get('provider'):
                    agg['providers'][r['provider']] = agg['providers'].get(r['provider'], 0) + 1
        agg['apps_usable'] = len(agg['apps_usable'])
        agg['usd'] = round(agg['usd'], 6)
        out[str(p.relative_to(root)).replace('\\', '/')] = agg
    print(json.dumps(out, indent=1))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--queries')
    ap.add_argument('--apps-file')
    ap.add_argument('--model', choices=sorted(REASONING_OFF))
    ap.add_argument('--block', action='append', default=None)
    ap.add_argument('--ledger-root', required=True)
    ap.add_argument('--concurrency', type=int, default=8)
    ap.add_argument('--max-usd', type=float, default=6.0)
    ap.add_argument('--max-requests', type=int, default=35000)
    ap.add_argument('--summary', action='store_true')
    a = ap.parse_args(argv)
    if a.summary:
        return summary(a)
    if not (a.queries and a.apps_file and a.model):
        ap.error('--queries, --apps-file and --model are required')
    a.block = a.block or ['P1-DEV']
    a.concurrency = max(1, min(a.concurrency, 8))
    a.max_usd = min(a.max_usd, 6.0)
    a.max_requests = min(a.max_requests, 35000)
    return run(a)


if __name__ == '__main__':
    sys.exit(main())
