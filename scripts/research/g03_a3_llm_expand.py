"""G03 amendment 3: LLM query expansion through OpenRouter (docs/healthtech/research/g03-dev/G03-DEV-AMENDMENT-3-20261122.md).

Runtime side only: reads query texts (title, abstract, first claim) of allowed blocks, never labels. Stdlib only, so it
runs in the owner's .venv. The API key is read from an environment variable (OPENROUTER_API_KEY for OpenRouter models)
and never printed or written.

Two records are kept:
* Science record: one JSON line per attempt (raw text, parsed fields, tokens, cost) under --ledger-root, as before.
* Money record: the shared budget ledger (src/patent_to_pilot/budget/ledger.py, owner task P0-T05). Before EVERY HTTP
  attempt (retries included) the caller atomically reserves the attempt's conservative maximum cost in the envelope;
  after the answer it settles the reservation with OpenRouter's ``usage.cost``. An HTTP error answer releases it (not
  billed); a timeout after sending or a 200 answer without ``usage.cost`` marks it UNKNOWN, which pauses all further
  dispatch on the envelope until it is reconciled (``python -m patent_to_pilot.budget.ledger reconcile ...``).
  The ledger also enforces the envelope's USD stop/hard limit and attempted-request cap across processes.

Protocols:
* A3r0 (default, no --config): frozen prompt, the four A3r0 models, max_tokens 400, envelope E1 (stop USD 6.00,
  35,000 requests). Request bodies are byte-identical to the frozen A3r0 caller.
* A3r1 and later (--config FILE): model list, endpoints, reasoning switches, provider routing, max_tokens, envelope and
  enable flags come from a JSON config. Accepted shapes: the tracked caller config
  (docs/healthtech/research/g03-dev/a3r1/a3r1-caller-config.json, key "models") or the owner's proposal shape
  (a3r1_proposed.json with "primary_profile_ids", resolved through model_profiles.json given by --profiles).
  The prompt stays the frozen A3r0 prompt.

--calibration: the fixed TRAIN formatting sample (default 32 cases per model, the same cases for every model). The input
must be a TRAIN-only extract; any other block aborts. Selection (deterministic, model-independent): h(app) =
sha256("g03-a3r1-calibration-v1:" + app_id); take the 8 cases with the longest built prompt in UTF-8 bytes (ties by h),
then the 24 smallest h among the rest. The manifest is written once per protocol and reused; no retrieval scoring.

Usage:
  python scripts/research/g03_a3_llm_expand.py --queries Q.jsonl --apps-file apps.json --model qwen/qwen3.7-flash \
      --ledger-root ../_private_artifacts/g03-a3 [--block P1-DEV] [--concurrency 8] [--max-usd 6.0] [--max-requests 35000]
  python scripts/research/g03_a3_llm_expand.py --config docs/healthtech/research/g03-dev/a3r1/a3r1-caller-config.json \
      --calibration --queries train.jsonl --model qwen/qwen3-32b --ledger-root ../_private_artifacts/g03-a3
  python scripts/research/g03_a3_llm_expand.py ... --plan          (no key, no network, no ledger write: cost bounds)
  python scripts/research/g03_a3_llm_expand.py --summary --ledger-root ../_private_artifacts/g03-a3
Budget ledger location: --budget-ledger PATH, else %PTP_BUDGET_LEDGER%, else %LOCALAPPDATA%/PatentToPilot/budget.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import socket
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
from patent_to_pilot.budget.ledger import (BudgetLedger, BudgetRefused, estimate_chat_max_usd,  # noqa: E402
                                           price_for)

ENDPOINT = 'https://openrouter.ai/api/v1/chat/completions'
KEY_ENV = 'OPENROUTER_API_KEY'
PROTECTED = {'P1-TEST', 'P2-TEST', 'P3-TEST'}
ALLOWED_BLOCKS = {'P1-DEV', 'VAL', 'TRAIN'}      # TRAIN only for format smoke checks
MAX_TOKENS, TEMPERATURE, SEED, FIELD_CHARS = 400, 0, 20261122, 1500
RETRY_STATUS = {408, 429, 500, 502, 503, 504}
MAX_RETRIES = 2
BACKOFF_S = 3                                    # sleep 3 s, 6 s before retries (tests set 0)
SCOPE = 'g03_a3'
A3R0_ENVELOPE = 'E1'
CALIBRATION_SALT = 'g03-a3r1-calibration-v1'
CALIBRATION_CASES, CALIBRATION_LONG = 32, 8

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


# ------------------------------------------------------------------------------------------- configuration
def a3r0_config() -> dict:
    """The frozen A3r0 settings, expressed in the same shape as a loaded config."""
    models = {m: {'model_id': m, 'provider': 'openrouter', 'endpoint': ENDPOINT, 'key_env': KEY_ENV,
                  'reasoning': r, 'provider_routing': None, 'reservation_price': None}
              for m, r in REASONING_OFF.items()}
    return {'protocol_id': 'A3r0', 'config_sha256': None, 'config_path': None, 'max_tokens': MAX_TOKENS,
            'temperature': TEMPERATURE, 'seed': SEED, 'envelope': A3R0_ENVELOPE, 'execution_enabled': True,
            'calibration_enabled': True, 'calibration_cases': CALIBRATION_CASES, 'calibration_long': CALIBRATION_LONG,
            'calibration_salt': CALIBRATION_SALT, 'reservation_margin': 1.0, 'models': models}


def load_config(path: str | Path, profiles_path: str | Path | None = None) -> dict:
    raw = Path(path).read_bytes()
    cfg = json.loads(raw.decode('utf-8'))
    out = {'config_sha256': hashlib.sha256(raw).hexdigest(), 'config_path': str(path),
           'temperature': TEMPERATURE, 'seed': SEED, 'reservation_margin': 1.0,
           'calibration_cases': CALIBRATION_CASES, 'calibration_long': CALIBRATION_LONG,
           'calibration_salt': CALIBRATION_SALT}
    if 'models' in cfg:                                     # tracked caller config
        cal = cfg.get('calibration') or {}
        out.update({'protocol_id': cfg['protocol_id'], 'max_tokens': int(cfg['max_tokens']),
                    'temperature': cfg.get('temperature', TEMPERATURE), 'seed': cfg.get('seed', SEED),
                    'envelope': cfg['budget_envelope'], 'execution_enabled': bool(cfg.get('execution_enabled')),
                    'calibration_enabled': bool(cfg.get('calibration_enabled')),
                    'reservation_margin': float(cfg.get('reservation_margin', 1.0)),
                    'calibration_cases': int(cal.get('cases_per_model', CALIBRATION_CASES)),
                    'calibration_long': int(cal.get('long_cases', CALIBRATION_LONG)),
                    'calibration_salt': cal.get('salt', CALIBRATION_SALT)})
        models = {}
        for m in cfg['models']:
            models[m['model_id']] = {'model_id': m['model_id'], 'provider': m['provider'], 'endpoint': m['endpoint'],
                                     'key_env': m['key_env'], 'reasoning': m.get('reasoning'),
                                     'provider_routing': m.get('provider_routing'),
                                     'reservation_price': m.get('reservation_price'),
                                     'profile_id': m.get('profile_id')}
    elif 'primary_profile_ids' in cfg:                      # owner proposal shape (a3r1_proposed.json)
        pp = Path(profiles_path) if profiles_path else Path(path).with_name('model_profiles.json')
        try:
            profiles = {p['profile_id']: p for p in
                        json.loads(pp.read_text(encoding='utf-8'))['generation_profiles']}
        except (OSError, KeyError, ValueError) as e:
            raise SystemExit(f'owner-shape config needs the model profiles file (--profiles): {e}')
        models = {}
        for pid in cfg['primary_profile_ids']:
            if pid not in profiles:
                raise SystemExit(f'profile {pid} is not in {pp}')
            p = profiles[pid]
            openrouter = p['provider'] == 'openrouter'
            models[p['model_id']] = {
                'model_id': p['model_id'], 'provider': p['provider'],
                'endpoint': p['base_url'].rstrip('/') + '/chat/completions', 'key_env': p['key_env'],
                'reasoning': REASONING_OFF.get(p['model_id'], {'enabled': False}) if openrouter else None,
                'provider_routing': None, 'reservation_price': None, 'profile_id': pid}
        out.update({'protocol_id': cfg['protocol_id'], 'max_tokens': int(cfg['output_tokens']),
                    'envelope': 'E1R' if 'E1R' in str(cfg.get('budget_authority', '')) else A3R0_ENVELOPE,
                    'execution_enabled': bool(cfg.get('execution_enabled')),
                    'calibration_enabled': bool(cfg.get('calibration_enabled', cfg.get('execution_enabled'))),
                    'calibration_cases': int(cfg.get('format_calibration_queries_per_model', CALIBRATION_CASES))})
    else:
        raise SystemExit('config must have "models" (tracked caller config) or "primary_profile_ids" (owner shape)')
    out['models'] = models
    return out


def build_body(mcfg: dict, prompt: str, max_tokens: int, temperature, seed) -> dict:
    """A3r0 models give exactly the frozen A3r0 body (same keys, same order)."""
    body = {'model': mcfg['model_id'],
            'messages': [{'role': 'system', 'content': SYSTEM}, {'role': 'user', 'content': prompt}],
            'max_tokens': max_tokens, 'temperature': temperature, 'seed': seed}
    if mcfg.get('reasoning') is not None:
        body['reasoning'] = mcfg['reasoning']
    if mcfg.get('provider_routing'):
        body['provider'] = mcfg['provider_routing']
    return body


def reservation_usd(mcfg: dict, body_bytes: bytes, max_tokens: int, margin: float) -> float | None:
    price = mcfg.get('reservation_price') or price_for(mcfg['provider'], mcfg['model_id'])
    return estimate_chat_max_usd(price, len(body_bytes), max_tokens, margin=margin)


# ------------------------------------------------------------------------------------------- transport
def _post(url: str, data: bytes, headers: dict, timeout: float) -> tuple[int, bytes]:
    req = urllib.request.Request(url, data=data, method='POST', headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status, resp.read()


def call(mcfg: dict, body_bytes: bytes, key: str, timeout: float = 120.0) -> tuple[int, dict | None, str, str]:
    """Returns (http_status, json|None, error, sent) with sent in {'answered', 'not_sent', 'unknown'}:
    'unknown' means the request may have reached the provider and been billed (timeouts, broken connections)."""
    headers = {'Authorization': f'Bearer {key}', 'Content-Type': 'application/json',
               'X-Title': 'patent-to-pilot research (G03 A3)'}
    try:
        status, raw = _post(mcfg['endpoint'], body_bytes, headers, timeout)
    except urllib.error.HTTPError as e:
        try:
            detail = e.read().decode('utf-8', 'replace')[:500]
        except Exception:  # noqa: BLE001
            detail = ''
        return e.code, None, detail, 'answered'
    except urllib.error.URLError as e:
        reason = getattr(e, 'reason', e)
        sent = 'not_sent' if isinstance(reason, (ConnectionRefusedError, socket.gaierror)) else 'unknown'
        return 0, None, f'URLError: {reason}'[:500], sent
    except Exception as e:  # noqa: BLE001  (timeouts, resets after sending)
        return 0, None, f'{type(e).__name__}: {e}'[:500], 'unknown'
    try:
        return status, json.loads(raw.decode('utf-8')), '', 'answered'
    except (UnicodeDecodeError, ValueError):
        return status, None, 'response is not JSON', 'unknown'


# ------------------------------------------------------------------------------------------- inputs
def _h(app_id: str, salt: str) -> str:
    return hashlib.sha256(f'{salt}:{app_id}'.encode('utf-8')).hexdigest()


def select_calibration(rows: list[dict], n: int = CALIBRATION_CASES, n_long: int = CALIBRATION_LONG,
                       salt: str = CALIBRATION_SALT) -> list[dict]:
    """Deterministic, model-independent TRAIN formatting sample (see module docstring)."""
    rows = sorted({r['app_id']: r for r in rows}.values(), key=lambda r: _h(r['app_id'], salt))
    by_len = sorted(rows, key=lambda r: (-len(build_prompt(r).encode('utf-8')), _h(r['app_id'], salt)))
    long_ = by_len[:min(n_long, n)]
    ids = {r['app_id'] for r in long_}
    rest = [r for r in rows if r['app_id'] not in ids][:max(0, n - len(long_))]
    out = [dict(r, _selected='long') for r in long_] + [dict(r, _selected='hash') for r in rest]
    return sorted(out, key=lambda r: _h(r['app_id'], salt))


def load_rows(args, cfg) -> list[dict]:
    apps = set(json.loads(Path(args.apps_file).read_text(encoding='utf-8'))) if args.apps_file else None
    blocks = set(args.block)
    rows = []
    with open(args.queries, encoding='utf-8') as f:
        for line in f:
            r = json.loads(line)
            if args.calibration and r.get('block') != 'TRAIN':
                raise SystemExit('calibration input must be a TRAIN-only extract (found block '
                                 f'{r.get("block")!r}); no other block is read in calibration mode')
            if r['block'] in blocks and (apps is None or r['app_id'] in apps):
                rows.append(r)
    if args.calibration:
        rows = select_calibration(rows, cfg['calibration_cases'], cfg['calibration_long'], cfg['calibration_salt'])
    return rows


def protocol_dir(root: Path, cfg: dict, calibration: bool) -> Path | None:
    if cfg['protocol_id'] == 'A3r0' and not calibration:
        return None                                        # historical A3r0 layout: root/<model>/<blocks>.jsonl
    base = root / cfg['protocol_id']
    return base / 'calibration' if calibration else base


def write_calibration_manifest(pdir: Path, rows: list[dict], cfg: dict, queries: str) -> Path:
    man = {'format': 'ptp-g03-a3-calibration-manifest-v1', 'protocol_id': cfg['protocol_id'], 'block': 'TRAIN',
           'rule': f'{cfg["calibration_long"]} longest built prompts (UTF-8 bytes; ties by h) + smallest h for the '
                   f'rest; h = sha256("{cfg["calibration_salt"]}:" + app_id); same cases for every model',
           'cases': len(rows), 'queries_sha256': hashlib.sha256(Path(queries).read_bytes()).hexdigest(),
           'config_sha256': cfg['config_sha256'], 'max_tokens': cfg['max_tokens'],
           'items': [{'app_id': r['app_id'], 'h': _h(r['app_id'], cfg['calibration_salt']), 'selected': r['_selected'],
                      'prompt_bytes': len(build_prompt(r).encode('utf-8'))} for r in rows],
           'no_retrieval_scoring': True}
    p = pdir / 'calibration-manifest.json'
    if p.exists():
        old = json.loads(p.read_text(encoding='utf-8'))
        if [i['app_id'] for i in old['items']] != [i['app_id'] for i in man['items']]:
            raise SystemExit(f'{p} lists a different calibration sample; the sample is fixed once per protocol')
        return p
    pdir.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(man, indent=1) + '\n', encoding='utf-8')
    return p


# ------------------------------------------------------------------------------------------- run
def plan(args, cfg) -> int:
    """No key, no network, no ledger write: the conservative reservation bound of the selected work."""
    mcfg = cfg['models'][args.model]
    rows = load_rows(args, cfg)
    est = []
    for r in rows:
        b = json.dumps(build_body(mcfg, build_prompt(r), args.max_tokens, cfg['temperature'], cfg['seed'])).encode()
        est.append(reservation_usd(mcfg, b, args.max_tokens, cfg['reservation_margin']))
    known = [e for e in est if e is not None]
    print(json.dumps({'protocol_id': cfg['protocol_id'], 'config_sha256': cfg['config_sha256'], 'model': args.model,
                      'calibration': bool(args.calibration), 'rows': len(rows), 'max_tokens': args.max_tokens,
                      'envelope': args.envelope, 'price_known': len(known) == len(est),
                      'reservation_per_attempt_usd': {'min': min(known) if known else None,
                                                      'max': max(known) if known else None},
                      'sum_of_first_attempt_bounds_usd': round(sum(known), 6) if known else None,
                      'note': 'upper bound per attempt (prompt bytes + 256 tokens, max_tokens output); retries extra'},
                     indent=1))
    return 0


def run(args, cfg) -> int:
    mcfg = cfg['models'][args.model]
    if args.calibration and not cfg['calibration_enabled']:
        raise SystemExit(f'calibration is disabled in {cfg["config_path"]} (calibration_enabled=false); enable it only '
                         'after the budget authority for this protocol is recorded')
    if not args.calibration and not cfg['execution_enabled']:
        raise SystemExit(f'execution is disabled in {cfg["config_path"]} (execution_enabled=false; freeze first)')
    key = os.environ.get(mcfg['key_env'])
    if not key:
        raise SystemExit(f'{mcfg["key_env"]} is not set; the owner sets it (the key is never stored in the repo)')
    blocks = set(args.block)
    rows = load_rows(args, cfg)
    root = Path(args.ledger_root)
    pdir = protocol_dir(root, cfg, args.calibration)
    if args.calibration:
        print(f'calibration manifest: {write_calibration_manifest(pdir, rows, cfg, args.queries)}', flush=True)
    base = root if pdir is None else pdir
    out = base / args.model.replace('/', '__') / f"{'+'.join(sorted(blocks))}.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if out.exists():
        with open(out, encoding='utf-8') as f:
            for line in f:
                r = json.loads(line)
                if r.get('status') in ('ok', 'content_unusable'):
                    done.add(r['app_id'])
    todo = sorted((r for r in rows if r['app_id'] not in done), key=lambda r: r['app_id'])
    ledger = BudgetLedger(args.budget_ledger)
    stale = ledger.recover_stale(args.stale_after_s)
    st = ledger.status(args.envelope)
    print(f'{args.model} [{cfg["protocol_id"]}, max_tokens {args.max_tokens}, envelope {args.envelope} '
          f'{st["approval"]}]: {len(rows)} queries, {len(done)} done, {len(todo)} to call; envelope committed USD '
          f'{st["committed_usd"]:.6f} of {st["operational_limit_usd"]:.2f} ({st["operational_limit_kind"]}), '
          f'{st["attempted_requests"]}/{st["max_requests"]} attempts, {len(st["unknown_entry_ids"])} unknown-cost'
          + (f'; {stale} stale reservation(s) marked unknown' if stale else ''), flush=True)
    wlock = threading.Lock()
    stop = threading.Event()
    stop_reason: list[str] = []
    fout = open(out, 'a', encoding='utf-8')
    t0 = time.time()
    stats = {'ok': 0, 'content_unusable': 0, 'failed': 0}
    money = {'usd': 0.0, 'attempts': 0}

    def halt(reason: str):
        with wlock:
            if not stop_reason:
                stop_reason.append(reason)
        stop.set()

    def one(r):
        prompt = build_prompt(r)
        body_bytes = json.dumps(build_body(mcfg, prompt, args.max_tokens, cfg['temperature'], cfg['seed'])).encode(
            'utf-8')
        est = reservation_usd(mcfg, body_bytes, args.max_tokens, cfg['reservation_margin'])
        for attempt in range(MAX_RETRIES + 1):
            if stop.is_set():
                return
            try:
                res = ledger.reserve(mcfg['provider'], est, scope=SCOPE, envelope_id=args.envelope,
                                     model=args.model, tag=f'{cfg["protocol_id"]}/{args.model}', attempt=attempt,
                                     run_usd_cap=args.max_usd, run_max_requests=args.max_requests,
                                     detail={'app_id': r['app_id'], 'protocol': cfg['protocol_id'],
                                             'calibration': bool(args.calibration)})
            except BudgetRefused as e:
                halt(f'budget: {e.reason}: {e}')
                return
            if res.notify:
                print(f'NOTIFY {res.envelope_id}: committed USD {res.committed_after:.4f} reached the notify '
                      'threshold', flush=True)
            t = time.time()
            status, resp, err, sent = call(mcfg, body_bytes, key)
            rec = {'app_id': r['app_id'], 'block': r['block'], 'model': args.model, 'attempt': attempt,
                   'http': status, 'wall_s': round(time.time() - t, 2), 'protocol': cfg['protocol_id'],
                   'max_tokens': args.max_tokens, 'config_sha256': cfg['config_sha256'],
                   'ledger_entry': res.entry_id, 'envelope': res.envelope_id, 'reserved_usd': res.reserved_usd}
            if resp is not None and status == 200 and resp.get('choices'):
                ch = resp['choices'][0]
                text = (ch.get('message') or {}).get('content') or ''
                usage = resp.get('usage') or {}
                parsed = parse_reply(text)
                cost, cost_source = usage.get('cost'), 'usage.cost'
                if cost is None and mcfg['provider'] != 'openrouter':   # non-OpenRouter: price x reported tokens
                    price = mcfg.get('reservation_price') or price_for(mcfg['provider'], args.model)
                    pt, ct = usage.get('prompt_tokens'), usage.get('completion_tokens')
                    if price and isinstance(pt, int) and isinstance(ct, int):
                        cost = (pt * float(price['input']) + ct * float(price['output'])) / 1_000_000
                        cost_source = 'computed_from_reported_tokens'
                rec['cost_source'] = cost_source
                rec.update({'status': 'ok' if parsed['usable'] else 'content_unusable', 'id': resp.get('id'),
                            'provider': resp.get('provider'), 'finish_reason': ch.get('finish_reason'),
                            'prompt_tokens': usage.get('prompt_tokens'),
                            'completion_tokens': usage.get('completion_tokens'),
                            'reasoning_tokens': (usage.get('completion_tokens_details') or {}).get('reasoning_tokens'),
                            'cost_usd': cost, 'raw': text, **parsed})
                fin = ledger.settle(res.entry_id, cost, generation_id=resp.get('id'), outcome=rec['status'])
                if fin['status'] == 'unknown':
                    rec['cost_status'] = 'unknown_paused'
                    halt(f'paused: response {resp.get("id")} has no usage.cost; reconcile ledger entry {res.entry_id}')
                else:
                    with wlock:
                        money['usd'] += cost
            elif sent == 'unknown' or (resp is None and status == 200):
                rec.update({'status': 'transport_error', 'cost_usd': None, 'error': err, 'cost_status': 'unknown_paused'})
                ledger.mark_unknown(res.entry_id, outcome=f'transport_unknown:{err[:80]}')
                halt(f'paused: attempt for {r["app_id"]} may have been billed ({err[:80]}); reconcile ledger entry '
                     f'{res.entry_id}')
            else:
                rec.update({'status': 'transport_error_unbilled', 'cost_usd': None, 'error': err})
                ledger.release(res.entry_id, outcome=f'http_{status}' if status else 'not_sent')
            with wlock:
                money['attempts'] += 1
                fout.write(json.dumps(rec, ensure_ascii=False) + '\n')
                fout.flush()
                stats[rec['status'] if rec['status'] in stats else 'failed'] += 1
            if rec['status'] in ('ok', 'content_unusable') or rec.get('cost_status') == 'unknown_paused':
                return
            if status and status not in RETRY_STATUS:
                return
            if attempt < MAX_RETRIES:
                time.sleep(2 ** attempt * BACKOFF_S)

    try:
        with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
            for i, _ in enumerate(ex.map(one, todo), 1):
                if i % 200 == 0:
                    print(f'{time.time() - t0:7.1f}s {i}/{len(todo)} this run USD {money["usd"]:.4f} attempts '
                          f'{money["attempts"]} {stats}', flush=True)
    finally:
        fout.close()
    st = ledger.status(args.envelope)
    print(f'END {args.model}: {stats}; this run USD {money["usd"]:.6f} (settled), {money["attempts"]} attempts; '
          f'envelope {args.envelope} committed USD {st["committed_usd"]:.6f}, {st["attempted_requests"]} attempts, '
          f'{len(st["unknown_entry_ids"])} unknown-cost' + (f'; STOP {stop_reason[0]}' if stop_reason else ''),
          flush=True)
    return 2 if stop_reason else 0


def summary(args) -> int:
    root = Path(args.ledger_root)
    out = {}
    for p in sorted(root.rglob('*.jsonl')):
        agg = {'attempts': 0, 'ok': 0, 'content_unusable': 0, 'transport_error': 0, 'transport_error_unbilled': 0,
               'usd': 0.0, 'unknown_cost': 0, 'prompt_tokens': 0, 'completion_tokens': 0, 'reasoning_tokens': 0,
               'salvaged': 0, 'finish_length': 0, 'complete_3_priors_and_keywords': 0, 'apps_usable': set(),
               'providers': {}, 'max_tokens': set()}
        with open(p, encoding='utf-8') as f:
            for line in f:
                r = json.loads(line)
                agg['attempts'] += 1
                agg[r['status']] = agg.get(r['status'], 0) + 1
                if r.get('cost_usd') is None:
                    agg['unknown_cost'] += r['status'] == 'transport_error' or r.get('cost_status') == 'unknown_paused'
                else:
                    agg['usd'] += r['cost_usd']
                for k in ('prompt_tokens', 'completion_tokens', 'reasoning_tokens'):
                    agg[k] += r.get(k) or 0
                agg['salvaged'] += r.get('parse') == 'salvaged'
                agg['finish_length'] += r.get('finish_reason') == 'length'
                agg['complete_3_priors_and_keywords'] += len(r.get('priors') or []) == 3 and bool(r.get('keywords'))
                agg['max_tokens'].add(r.get('max_tokens', MAX_TOKENS))
                if r['status'] == 'ok':
                    agg['apps_usable'].add(r['app_id'])
                if r.get('provider'):
                    agg['providers'][r['provider']] = agg['providers'].get(r['provider'], 0) + 1
        agg['apps_usable'] = len(agg['apps_usable'])
        agg['max_tokens'] = sorted(agg['max_tokens'])
        agg['usd'] = round(agg['usd'], 6)
        out[str(p.relative_to(root)).replace('\\', '/')] = agg
    print(json.dumps(out, indent=1))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--queries')
    ap.add_argument('--apps-file')
    ap.add_argument('--model')
    ap.add_argument('--block', action='append', default=None)
    ap.add_argument('--ledger-root', required=True)
    ap.add_argument('--concurrency', type=int, default=8)
    ap.add_argument('--max-usd', type=float, default=None, help='extra ceiling on the envelope committed USD')
    ap.add_argument('--max-requests', type=int, default=None, help='extra ceiling on envelope attempted requests')
    ap.add_argument('--summary', action='store_true')
    ap.add_argument('--config', help='protocol config JSON (A3r1+); omitted = frozen A3r0')
    ap.add_argument('--profiles', help='model_profiles.json for an owner-shape config')
    ap.add_argument('--max-tokens', type=int, default=None, help='default: 400 for A3r0, the config value otherwise')
    ap.add_argument('--calibration', action='store_true', help='fixed TRAIN formatting sample, no retrieval scoring')
    ap.add_argument('--plan', action='store_true', help='print cost bounds only: no key, no network, no ledger write')
    ap.add_argument('--envelope', help='budget envelope (default: E1 for A3r0, the config value otherwise)')
    ap.add_argument('--budget-ledger', help='shared budget ledger path (default: env PTP_BUDGET_LEDGER, else the user data dir)')
    ap.add_argument('--stale-after-s', type=float, default=900.0)
    a = ap.parse_args(argv)
    if a.summary:
        return summary(a)
    cfg = load_config(a.config, a.profiles) if a.config else a3r0_config()
    if not (a.queries and a.model) or not (a.apps_file or a.calibration):
        ap.error('--queries and --model are required, and --apps-file unless --calibration')
    if a.model not in cfg['models']:
        ap.error(f'--model must be one of {sorted(cfg["models"])} for {cfg["protocol_id"]}')
    if a.calibration:
        if a.block and set(a.block) != {'TRAIN'}:
            ap.error('--calibration reads the TRAIN block only')
        a.block = ['TRAIN']
    a.block = a.block or ['P1-DEV']
    if set(a.block) & PROTECTED or not set(a.block) <= ALLOWED_BLOCKS:
        raise SystemExit('refusing: TEST or unknown block')
    a.max_tokens = cfg['max_tokens'] if a.max_tokens is None else a.max_tokens
    if not 1 <= a.max_tokens <= 8192:
        ap.error('--max-tokens must be between 1 and 8192')
    a.envelope = a.envelope or cfg['envelope']
    a.concurrency = max(1, min(a.concurrency, 8))
    if cfg['protocol_id'] == 'A3r0':                   # frozen A3r0 stop rules (amendment 3 section 5)
        a.max_usd = min(a.max_usd if a.max_usd is not None else 6.0, 6.0)
        a.max_requests = min(a.max_requests if a.max_requests is not None else 35000, 35000)
    if a.plan:
        return plan(a, cfg)
    return run(a, cfg)


if __name__ == '__main__':
    sys.exit(main())
