"""Read-only aggregate of the Paper 1 S3 pilot-20 technical runs (throughput/failures only; no texts, no scores)."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from takeover_lib import *

out = {'stage': 'Paper 1 S3 technical pilot on pilot-20 (journal stage fidelity); throughput and failures only, not evaluated',
       'input_sha256': json.loads((A/'native-sacr-pilot20-v5/freeze-summary.json').read_bytes())['input_sha256'], 'arms': {}}
for arm in ('fa', 'gr'):
    name = 'ptp-auto-paper1-%s-pilot20-20261113-v1' % arm
    v = ssh(f"""import json,statistics
from pathlib import Path
p=Path('{JOBS}/{name}');o=p/'out/attempt'
ms=[];lex=[];chars=[]
for q in sorted((o/'queries').iterdir()):
    r=json.loads((q/'result.json').read_bytes())
    if (q/'rewrite-metrics.json').exists(): ms.append(json.loads((q/'rewrite-metrics.json').read_bytes()))
    if r['text']: lex.append(r['lexical_descriptives']);chars.append(len(r['text']))
g=[m['gpu_seconds'] for m in ms];ot=[m['output_tokens'] for m in ms];it=[m['input_tokens'] for m in ms]
ret=[x['numbers_retained_share'] for x in lex if x['numbers_retained_share'] is not None]
ab=[x['content_words_absent_share'] for x in lex]
print(json.dumps({{'completion':json.loads((o/'completion.json').read_bytes()),'terminal':json.loads((p/'terminal.json').read_bytes()),
 'admission':json.loads((o/'before-model-input-admission.json').read_bytes()),
 'calls':len(ms),'generation_seconds':{{'sum':sum(g),'mean':statistics.mean(g),'median':statistics.median(g),'max':max(g)}},
 'input_tokens':{{'mean':statistics.mean(it),'max':max(it)}},'output_tokens':{{'mean':statistics.mean(ot),'max':max(ot)}},
 'output_tokens_per_second':sum(ot)/sum(g),'peak_gpu_bytes':max(m['peak_memory_bytes'] for m in ms),
 'rewrite_chars':{{'mean':statistics.mean(chars),'max':max(chars)}},
 'lexical_descriptive_not_a_gate':{{'queries_with_numbers':len(ret),'numbers_retained_share_mean':statistics.mean(ret) if ret else None,
  'content_words_absent_share_mean':statistics.mean(ab)}}}}))
""")
    c, t = v.pop('completion'), v.pop('terminal')
    settlement = json.loads((A/('paper1-s3-' + arm)/'settlement.json').read_bytes())
    out['arms'][arm.upper()] = dict(job=name, exit=t['container_state']['ExitCode'], queries=c['queries'], rewrites_used=c['rewrites_used'],
        fallbacks=c['fallbacks'], reasons=c['reasons'], whole_wall_seconds=t['whole_wall_seconds'],
        gpu_charged_seconds=settlement['study']['stage_costs'][name]['seconds'], settled_generation=settlement['generation'],
        load_and_overhead_seconds=t['whole_wall_seconds'] - v['generation_seconds']['sum'], **v)
out['semantic_certified'] = False; out['evaluated'] = False
out['note'] = 'Lexical descriptives are not a fidelity certification and not a gate. No retrieval score exists for these outputs.'
(A/'PAPER1-S3-SUMMARY.json').write_text(json.dumps(out, indent=2) + '\n'); print(json.dumps(out)[:3000])
