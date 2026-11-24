"""P2-T02 amendment A2 (owner D19): gates of the complete-content follow-up. Stdlib only. P1-DEV only; never reads TEST.

Amendment: docs/healthtech/research/p2-coverage/P2-T02-AMENDMENT-A2-D19-FOLLOWUP.md, section 4.
  relay   <model> <bridgeret_dir> <out.json>
          C-R: the C0 reference is the gated A3r1 relay: its gate record passed, its evaluation is P1-DEV with
          n_queries_run 25,626 and per-query values, and its unit order equals the corpus order (runs/z-arctic/units.json).
  content <archived_manifest.json> <rebuilt_manifest.json> <out.json>
          C-A: the content build, run on this pod with NO override (Arctic tokenizer) over the uploaded (filtered) claims,
          reproduces every P2-T02 data output byte for byte (units.json, c1.*, c2.*, ser-full/passages.jsonl). This proves
          that the filtered claims and the A2 override code leave the P2-T02 build unchanged.
  final   <model> <out.json> <part.json>...
          preflight, weights, relay, content, validate and c0check passed for this model, and the model's C1 content
          was built with the tokenizer and window in window.json.
Exit 0 only if the part passed.
"""
import json
import sys
from pathlib import Path

DATA_OUTPUTS = ('units.json', 'c1.ids.u32', 'c1.len.npy', 'c1.unit.npy', 'c2.ids.u32', 'c2.len.npy', 'c2.unit.npy',
                'ser-full/passages.jsonl')


def relay(model, br):
    br = Path(br)
    g = json.loads((br / f'logs/gate-{model}.json').read_text())
    ev = json.loads((br / f'evals-a3r1/z-{model}.json').read_text())
    units = json.loads((br / f'runs/z-{model}/units.json').read_text())
    corpus = json.loads((br / 'runs/z-arctic/units.json').read_text())
    res = {'part': 'relay', 'model': model, 'relay_gate_passed': bool(g.get('gate_passed')),
           'eval_block': ev['block'], 'n_queries_run': ev['n_queries_run'], 'per_query': len(ev.get('per_query', {})),
           'ALL_R@200': ev['metrics']['ALL_R@200']['mean'], 'unit_order_equals_corpus': units == corpus}
    res['passed'] = bool(res['relay_gate_passed'] and ev['block'] == 'P1-DEV' and ev['n_queries_run'] == 25626
                         and res['per_query'] > 0 and res['unit_order_equals_corpus'])
    return res


def content(archived, rebuilt):
    a, b = json.loads(Path(archived).read_text()), json.loads(Path(rebuilt).read_text())
    rows = {k: {'archived': a['outputs_sha256'][k], 'rebuilt': b['outputs_sha256'].get(k),
                'identical': a['outputs_sha256'][k] == b['outputs_sha256'].get(k)} for k in DATA_OUTPUTS}
    res = {'part': 'content', 'outputs': rows,
           'corpus_input_identical': a['inputs']['texts-v1/corpus.jsonl'] == b['inputs']['texts-v1/corpus.jsonl'],
           'tokenizer_json_identical': a['inputs']['tokenizer_json_sha256'] == b['inputs']['tokenizer_json_sha256'],
           'claims_files': b['inputs']['claims_files'], 'rebuilt_env_overrides': b['inputs'].get('env_overrides', {})}
    res['passed'] = bool(all(r['identical'] for r in rows.values()) and res['corpus_input_identical']
                         and res['tokenizer_json_identical'] and res['claims_files'] == 54
                         and not res['rebuilt_env_overrides'])
    return res


def final(model, parts):
    got = {}
    for p in parts:
        d = json.loads(Path(p).read_text())
        passed = d.get('passed') is True or d.get('status') == 'PASS'
        got[Path(p).stem] = {'passed': passed, 'record': d}
    res = {'part': 'final', 'model': model, 'parts': {k: v['passed'] for k, v in got.items()},
           'records': {k: v['record'] for k, v in got.items()}}
    win = res['records'].get('window', {})
    st = res['records'].get('stats', {})
    overrides = st.get('env_overrides', {})
    res['window_matches_content'] = bool(
        win and st and st['window_content_tokens'] == win['window']
        and st['window_model_positions'] == win['max_positions']
        and st['segment_separator_ids'] == win['segment_separator_ids']
        and overrides.get('P2T02_WIN') == str(win['window'])
        and overrides.get('P2T02_TOKDIR') == win['model_dir']
        and overrides.get('P2T02_SEG_SEP') == win['segment_separator']
    )
    model_parts = ('preflight', 'weights-model', 'relay', 'validate', 'c0check', 'window')
    needed = (*model_parts, 'weights-arctic', 'content-arctic', 'stats')
    res['missing'] = [n for n in needed if n not in got]
    res['model_matches'] = all(res['records'].get(n, {}).get('model') == model for n in model_parts)
    res['gate_passed'] = bool(
        not res['missing'] and res['window_matches_content'] and res['model_matches']
        and res['records']['weights-arctic'].get('model') == 'arctic'
        and all(got[n]['passed'] for n in needed if n not in ('window', 'stats'))
    )
    return res


def main(argv):
    cmd = argv[0]
    if cmd == 'relay':
        res, out = relay(argv[1], argv[2]), argv[3]
    elif cmd == 'content':
        res, out = content(argv[1], argv[2]), argv[3]
    elif cmd == 'final':
        res, out = final(argv[1], argv[3:]), argv[2]
    else:
        raise SystemExit(__doc__)
    res['amendment'] = 'P2-T02-AMENDMENT-A2-D19-FOLLOWUP.md'
    Path(out).write_text(json.dumps(res, indent=1))
    ok = res.get('passed', res.get('gate_passed'))
    print(json.dumps({k: v for k, v in res.items() if k != 'records'}, indent=1))
    print(f'D19_GATE_{cmd.upper()}_' + ('PASSED' if ok else 'FAILED'), flush=True)
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main(sys.argv[1:])
