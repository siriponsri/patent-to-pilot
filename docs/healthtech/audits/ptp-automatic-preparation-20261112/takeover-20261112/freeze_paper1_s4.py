"""Paper 1 S4: freeze ONE full-dev generation batch (journal stage 'full_dev') for an arm (FA|GR), batch 1..3, ONCE (no launch).

474 dev queries in pinned file order, 3 batches x 158 (one call per query; maximum_calls == queries).
The first S4 freeze (whichever arm/batch runs first) also appends the authority amendment: the full_dev stage
envelope {10800 s, 158 calls} (definable once; shared with SACR 6 x 79 x 2 calls) and the FA and GR full_dev
configurations. Owner authority: the Paper 1 freeze approval (S1-S6). Query texts never leave the remote.
The ledger must not change between this freeze and the claim.
"""
import copy, json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from takeover_lib import *
from patent_to_pilot.research.r6_dispatch_files import package_identity
from patent_to_pilot.research.automatic_cpu_booking import cpu_used, cpu_cap

ARM = sys.argv[1]; B = int(sys.argv[2]); assert ARM in ('FA', 'GR') and 1 <= B <= 3
low = ARM.lower(); N = 158
NAME = 'ptp-auto-paper1-%s-fulldev-b%d-20261113-v1' % (low, B); S = A/('paper1-s4-%s-b%d' % (low, B)); assert not S.exists()
PRED = 'ptp-auto-paper1-%s-pilot-retrieval-20261113-v1' % low
JOB = JOBS + '/' + NAME; CODE = JOBS + '/ptp-auto-paper1-gr-pilot-retrieval-20261113-v1/code/src'
QUERIES = JOBS + '/ptp-native-baseline-20261110-v1/runtime-dev/queries-ta.jsonl'
FREEZE = json.loads((A/'paper1-freeze/freeze-manifest.json').read_bytes())
RT = FREEZE['generation_runtime']; QSHA = FREEZE['dev_inputs']['queries_sha256']; assert FREEZE['dev_inputs']['queries'] == 3 * N
ENVELOPE = {'full_dev': {'seconds': 10800, 'maximum_calls': 158}}
CONTROLLER_CPU = 900  # supervise_paper1_rewrite.py full-dev controller limit
# Declared cumulative disk upper bound: the largest (prior + additional) over every local declaration so far.
DISK_PRIOR = max(x['disk_preexisting_upper_bound_bytes'] + x['additional_disk_bytes']
                 for x in (json.loads(p.read_bytes()) for p in A.rglob('declaration.json')) if 'disk_preexisting_upper_bound_bytes' in x)
SEG = 1 + max(int(re.fullmatch(r'segment(\d+)-booking\.json', p.name).group(1)) for p in A.rglob('segment*-booking.json'))


def configuration(arm):
    return {'stage': 'full_dev', 'track': 'PAPER1_' + arm, 'protocol': 'PAPER1-ACQUISITION-PROTOCOL (frozen 2026-11-13) S4 full-dev generation',
            'paper1_freeze_manifest_sha256': sha((A/'paper1-freeze/freeze-manifest.json').read_bytes()),
            'arm': FREEZE['arms'][arm], 'decoder_sha256': RT['decoder_sha256'], 'max_new_tokens': 4096, 'dtype': 'float16',
            'attention': 'eager', 'greedy': True, 'maximum_calls_per_query': 1, 'input_token_cap': RT['input_token_cap'],
            'max_consecutive_whitespaces': RT['max_consecutive_whitespaces'], 'force_json_field_order': RT['force_json_field_order'],
            'container': {'nano_cpus': 1, 'memory_bytes': 31*1024**3, 'network': 'none', 'gpu': 'single approved UUID'},
            'fallback': 'original query on input cap / output limit / schema or blank rejection; HOLD on unknown backend state',
            'batching': '474 dev queries in pinned file order, 3 batches x 158', 'identical_to': 'S3 pilot-20 configuration except stage and batching',
            'semantic_certification': False}


ledger = json.loads(L.read_bytes()); lsha = document_hash(ledger)
h = journal(CODE, "h,at=head()\nscope=json.loads(h[3]);st=scope['automatic_study']\n"
                  "env=dict(st['authority'].get('stage_envelopes',{}))\nfor a in st.get('authority_amendments',[]):env.update(a.get('add_stage_envelopes',{}))\n"
                  "print(json.dumps({'generation':h[1],'ledger_sha256':document_hash(json.loads(h[2])),'active':h[4],"
                  "'status':st['status'],'authority_sha256':st['authority_sha256'],'pred':st['stage_costs'].get('" + PRED + "'),"
                  "'envelope':env.get('full_dev'),'prior':[k for k in st['stage_costs'] if '-fulldev-' in k]}))\n")
assert h['active'] is None and h['ledger_sha256'] == lsha and h['status'] == 'IDLE', h
assert h['pred'] and h['pred']['stage'] == 'pilot' and h['pred']['calls_complete'] is True, h
assert all(('ptp-auto-paper1-%s-fulldev-b%d-20261113-v1' % (low, b)) in h['prior'] for b in range(1, B)), 'earlier batches of this arm must be settled first'
FIRST = h['envelope'] is None
if not FIRST: assert h['envelope'] == ENVELOPE['full_dev'], h
assert type(ledger.get('full_dev_charged_seconds')) in (int, float), 'full-dev accounting must be initialized'
blobs, pins = package(['run_paper1_rewrite.py', 'supervise_paper1_rewrite.py'])
package_sha = package_identity(pins)
for f in ('src/patent_to_pilot/research/paper1_rewrite_arms.py', 'src/patent_to_pilot/research/r6_backend.py'):
    assert pins[f] == FREEZE['files_sha256'][f], 'frozen file changed: ' + f
S.mkdir()
seg = segment_booking(SEG, lsha)
after = copy.deepcopy(ledger); after['r6_phase0_cpu']['local_cpu_conservative_charged_seconds'] += seg['conservative_cpu_seconds']
(S/('segment%d-booking.json' % SEG)).write_text(json.dumps(seg, indent=2) + '\n')
out = book(CODE, [seg], h['generation']); assert document_hash(out['ledger']) == document_hash(after); write_ledger(out['ledger'])
ledger_sha = document_hash(after); gen = h['generation'] + 1
files = {'code/' + n: b for n, b in blobs.items()}
files.update({n: blobs['scripts/healthtech/' + n] for n in ('supervise_paper1_rewrite.py', 'supervise_sacr_r5_engine.py', 'r3_engine_client.py')})
transport = stage(NAME, files)
built = ssh(f"""import json,hashlib
from pathlib import Path
raw=Path('{QUERIES}').read_bytes();assert hashlib.sha256(raw).hexdigest()=='{QSHA}'
rows=[json.loads(l) for l in raw.decode('utf-8').splitlines() if l.strip()];assert len(rows)==474
part=rows[{N}*({B}-1):{N}*{B}];assert len(part)=={N}
d=Path('{JOB}')/'dispatch';d.mkdir()
data=''.join(json.dumps({{'id':r['id'],'text':r['text']}},ensure_ascii=False)+'\\n' for r in part).encode()
(d/'queries.jsonl').write_bytes(data)
print(json.dumps({{'sha256':hashlib.sha256(data).hexdigest(),'queries':len(part)}}))
""")
assert built['queries'] == N
config = configuration(ARM); config_sha = document_hash(config)
operation = {'stage': 'full_dev', 'arm': ARM, 'batch': B, 'input_sha256': built['sha256'], 'configuration_sha256': config_sha, 'package_sha256': package_sha}
results = {'s3': sha((A/'PAPER1-S3-SUMMARY.json').read_bytes()), 'pred': sha((A/('paper1-s3-%s-retrieval' % low)/'settlement.json').read_bytes())}
cpu = after['r6_phase0_cpu']
base = {'status': 'PASS', 'package_sha256': package_sha, 'configuration_sha256': config_sha}
gates = {'integrity': dict(base, gate='integrity', source_commit=git('rev-parse', 'HEAD').decode().strip(), files=len(pins),
             evidence='committed blobs; frozen FA/GR files match the Paper 1 freeze manifest; worker unchanged since S3; supervisor change = full-dev job names + controller CPU limit 900 s (measured poll cost)'),
         'isolation': dict(base, gate='isolation', evidence='same supervisor/isolation as the S3 pilot-20 runs; re-validated before start'),
         'runtime': dict(base, gate='runtime', s3_summary_sha256=results['s3'], predecessor_settlement_sha256=results['pred'], decoder_sha256=RT['decoder_sha256'],
             evidence='S3: this arm 20/20 REWRITE_VALIDATED on pilot-20, exit 0, about 23 s/query; pilot retrieval settled'),
         'resources': dict(base, gate='resources', live_admission_required=True, gpu_remaining_seconds=after['gpu_remaining_seconds'],
             full_dev_charged_seconds=after['full_dev_charged_seconds'], disk_preexisting_upper_bound_bytes=DISK_PRIOR),
         'accounting': dict(base, gate='accounting', ledger_sha256=ledger_sha, cpu_remaining_seconds=cpu_cap(cpu) - cpu_used(cpu),
             gpu_stage_host_cpu='TELEMETRY_NOT_CHARGED_TO_CPU_CAP')}
d = {'attempt_id': NAME, 'arm': ARM, 'stage': 'full_dev', 'batch': B, 'retry': False, 'queries': N, 'maximum_calls': N, 'seconds': 10800,
     'input_token_cap': RT['input_token_cap'], 'max_consecutive_whitespaces': RT['max_consecutive_whitespaces'],
     'force_json_field_order': RT['force_json_field_order'], 'cpu_seconds': 10800 + CONTROLLER_CPU, 'cpu_charge_basis': 'GPU_STAGE_SAFETY_BOUND_TELEMETRY_ONLY',
     'additional_disk_bytes': 256*1024**2, 'disk_preexisting_upper_bound_bytes': DISK_PRIOR, 'package_sha256': package_sha,
     'files_sha256': pins, 'configuration_sha256': config_sha, 'input_manifest_sha256': built['sha256'], 'km_sha256': pins[KM],
     'model_sha256': pins[IDENT], 'tokenizer_sha256': RT['tokenizer_sha256'], 'decoder_sha256': RT['decoder_sha256'],
     'lmfe_source_sha256': RT['lmfe_source_sha256'], 'predecessor_attempt_id': PRED, 'operation_sha256': document_hash(operation),
     'gate_receipts': {k: document_hash(v) for k, v in gates.items()}}
assert d['model_sha256'] == RT['model_sha256']
raw = json.dumps(d, indent=2).encode() + b'\n'
for n, v in (('configuration.json', config), ('gates.json', gates), ('operation.json', operation)): (S/n).write_text(json.dumps(v, indent=2) + '\n')
(S/'declaration.json').write_bytes(raw)
ssh(f"""import hashlib
from pathlib import Path
d=Path('{JOB}')/'dispatch'
(d/'declaration.json').write_bytes({raw!r});(d/'gates.json').write_bytes({(S/'gates.json').read_bytes()!r})
assert hashlib.sha256((d/'declaration.json').read_bytes()).hexdigest()=='{sha(raw)}'
print('{{}}')
""")
code2 = JOB + '/code/src'
body = "from patent_to_pilot.research.automatic_dispatch_journal import AutomaticDispatchJournal\nd=json.loads(" + repr(json.dumps(d)) + ")\n"
body += "j=AutomaticDispatchJournal(path,'" + IDENTITY + "')\nh,at=head();assert h[1]==" + str(gen) + "\nam=None\n"
if FIRST:
    amendment = {'kind': 'AUTHORITY_AMENDMENT', 'owner_approval_sha256': sha((A/'owner-paper1-freeze-approval.json').read_bytes()),
                 'evidence_sha256': results['s3'], 'add_configuration_sha256': [document_hash(configuration('FA')), document_hash(configuration('GR'))],
                 'additional_synthetic_attempts': 0, 'round': 'paper1-s4', 'add_stage_envelopes': ENVELOPE,
                 'authority_sha256': h['authority_sha256'], 'ledger_sha256': ledger_sha, 'scope_sha256': None,
                 'reason': 'Paper 1 frozen protocol S4: full-dev generation; envelope 10800 s / 158 calls per job (FA, GR: 3 x 158 queries; SACR: 6 x 79 x 2 calls)'}
    body += ("am=json.loads(" + repr(json.dumps(amendment)) + ")\nam['scope_sha256']=document_hash(json.loads(h[3]))\n"
             "j.amend_authority(expected_generation=" + str(gen) + ",receipt=am,receipt_sha256=document_hash(am))\n")
    qgen = gen + 1
else:
    qgen = gen
body += ("h,at=head();scope=json.loads(h[3])\n"
         "q={'declaration':d,'authority_sha256':scope['automatic_study']['authority_sha256'],'ledger_sha256':document_hash(json.loads(h[2])),'scope_sha256':document_hash(scope)}\n"
         "j.qualify_stage(expected_generation=" + str(qgen) + ",receipt=q,receipt_sha256=document_hash(q))\n"
         "h,at=head();scope=json.loads(h[3])\nassert h[1]==" + str(qgen + 1) + " and h[4] is None\n"
         "print(json.dumps({'generation':h[1],'ledger_sha256':document_hash(json.loads(h[2])),'amendment':am,'qualification':q,"
         "'qualified':'" + NAME + "' in scope['automatic_study']['qualified_dispatches'],'status':scope['automatic_study']['status']}))\n")
res = journal(code2, body)
assert res['ledger_sha256'] == ledger_sha and res['qualified'], res
if res['amendment']: (S/'authority-amendment.json').write_text(json.dumps(res['amendment'], indent=2) + '\n')
(S/'qualification-receipt.json').write_text(json.dumps(res['qualification'], indent=2) + '\n')
summary = {'status': 'STAGED_QUALIFIED_NOT_LAUNCHED', 'job': NAME, 'arm': ARM, 'batch': B, 'supervisor': 'supervise_paper1_rewrite.py',
           'declaration_sha256': sha(raw), 'package_sha256': package_sha, 'configuration_sha256': config_sha, 'input_sha256': built['sha256'],
           'transport': transport, 'journal_generation': res['generation'], 'ledger_sha256': ledger_sha, 'study_status': res['status'],
           'segment': SEG, 'segment_seconds': seg['conservative_cpu_seconds'], 'disk_preexisting_upper_bound_bytes': DISK_PRIOR,
           'cpu_remaining_seconds': gates['accounting']['cpu_remaining_seconds']}
(S/'freeze-summary.json').write_text(json.dumps(summary, indent=2) + '\n'); print(json.dumps(summary))
