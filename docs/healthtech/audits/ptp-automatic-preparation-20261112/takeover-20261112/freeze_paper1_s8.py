"""Paper 1 S8 (owner go 2026-11-15, option a): freeze ONE test generation batch ONCE (no launch).

Usage: freeze_paper1_s8.py ARM B   (ARM in FA, GR, SACR; FA/GR B=1..5 x 158 (last 141); SACR B=1..10 x 79 (last 62)).
Order FA -> GR -> SACR; every earlier batch must be settled first. Configurations = the settled full-dev ones with only
stage/batching changed (test_configs.py). The first S8 freeze appends authority amendment round 'paper1-s7-test':
the test stage envelope {10800 s, 158 calls} and the FA, GR, SACR and retrieval test configurations.
Workers: identical to their CPU-fixture-qualified files except the added 'test' stage name (checked by reverting it).
Predecessor: the arm's first settled full-dev batch (calls complete). The ledger must not change between freeze and claim.
"""
import copy, json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from takeover_lib import *
from test_configs import TEST_INPUT, TEST_SHA, TEST_N, ORDER, ENVELOPE, job, rows, configuration
from patent_to_pilot.research.r6_dispatch_files import package_identity
from patent_to_pilot.research.automatic_cpu_booking import cpu_used, cpu_cap

ARM, B = sys.argv[1], int(sys.argv[2]); assert (ARM, B) in ORDER
NAME = job(ARM, B); S = A/('paper1-s8-%s-b%d' % (ARM.lower(), B)); assert not S.exists()
EARLIER = [job(a, b) for a, b in ORDER[:ORDER.index((ARM, B))]]
START, COUNT = rows(ARM, B)
SACR = ARM == 'SACR'
PRED = {'FA': 'ptp-auto-paper1-fa-fulldev-b1-20261113-v1', 'GR': 'ptp-auto-paper1-gr-fulldev-b1-20261114-v1',
        'SACR': 'ptp-auto-native-sacr-fulldev-b1-20261114-v1'}[ARM]
JOB = JOBS + '/' + NAME; CODE = JOBS + '/ptp-auto-paper1-dev-fulldev-retrieval-20261115-v1/code/src'
FREEZE = json.loads((A/'paper1-freeze/freeze-manifest.json').read_bytes()); RT = FREEZE['generation_runtime']
TFREEZE = A/'paper1-freeze/test-freeze-manifest.json'
CONTROLLER_CPU = 900
DISK_PRIOR = max(x['disk_preexisting_upper_bound_bytes'] + x['additional_disk_bytes']
                 for x in (json.loads(p.read_bytes()) for p in A.rglob('declaration.json')) if 'disk_preexisting_upper_bound_bytes' in x)
SEG = 1 + max(int(re.fullmatch(r'segment(\d+)-booking\.json', p.name).group(1)) for p in A.rglob('segment*-booking.json'))
if SACR:
    FIX, FIXDIR = 'fixture-v8-result.json', 'native-fixture-v8'
    blobs, pins = package(['run_automatic_native.py', 'supervise_automatic_native.py', 'run_automatic_synthetic.py', 'supervise_automatic_synthetic.py'])
    WORKER, REVERT = 'scripts/healthtech/run_automatic_native.py', (b"('fidelity', 'full_dev', 'test')", b"('fidelity', 'full_dev')")
    EXACT = ('src/patent_to_pilot/research/sacr_automatic_runner.py', 'src/patent_to_pilot/research/paper1_rewrite_runner.py')
    SUPERVISOR = 'supervise_automatic_native.py'
else:
    FIX, FIXDIR = 'fixture-v3-result.json', 'paper1-fixture-v3'
    blobs, pins = package(['run_paper1_rewrite.py', 'supervise_paper1_rewrite.py'])
    WORKER, REVERT = 'scripts/healthtech/run_paper1_rewrite.py', (b", 'test': 10800}", b"}")
    EXACT = ('src/patent_to_pilot/research/paper1_rewrite_runner.py',)
    SUPERVISOR = 'supervise_paper1_rewrite.py'
    for f in ('src/patent_to_pilot/research/paper1_rewrite_arms.py', 'src/patent_to_pilot/research/r6_backend.py'):
        assert pins[f] == FREEZE['files_sha256'][f], 'frozen file changed: ' + f
FIXTURE = json.loads((A/FIXDIR/FIX).read_bytes()); assert FIXTURE['status'].startswith('PASS_AUTHORED'), FIXTURE['status']
FIXTURE_PINS = json.loads((A/FIXDIR/'fixture-declaration.json').read_bytes())['files_sha256']
package_sha = package_identity(pins)
worker_blob = blob(WORKER); assert worker_blob.count(REVERT[0]) == 1
assert sha(worker_blob.replace(REVERT[0], REVERT[1])) == FIXTURE_PINS[WORKER], 'worker differs from the fixture file beyond the test stage name'
for f in EXACT: assert pins[f] == FIXTURE_PINS[f], 'differs from the fixture-qualified file: ' + f
configs = {k: configuration(k) for k in ('FA', 'GR', 'SACR', 'RET')}
config = configs[ARM]; config_sha = document_hash(config)
ledger = json.loads(L.read_bytes()); lsha = document_hash(ledger)
h = journal(CODE, "h,at=head()\nscope=json.loads(h[3]);st=scope['automatic_study']\n"
                  "env=dict(st['authority'].get('stage_envelopes',{}))\nfor a in st.get('authority_amendments',[]):env.update(a.get('add_stage_envelopes',{}))\n"
                  "known=[c for a in st.get('authority_amendments',[]) for c in a['add_configuration_sha256']]+list(st['authority'].get('configuration_sha256',[]))\n"
                  "print(json.dumps({'generation':h[1],'ledger_sha256':document_hash(json.loads(h[2])),'active':h[4],'status':st['status'],"
                  "'authority_sha256':st['authority_sha256'],'pred':st['stage_costs'].get('" + PRED + "'),'envelope':env.get('test'),"
                  "'known':'" + config_sha + "' in known,'settled':sorted(st['stage_costs'])}))\n")
assert h['active'] is None and h['ledger_sha256'] == lsha and h['status'] == 'IDLE', h
assert h['pred'] and h['pred']['stage'] == 'full_dev' and h['pred']['calls_complete'] is True, h
assert all(e in h['settled'] for e in EARLIER), 'earlier batches must be settled first: %s' % [e for e in EARLIER if e not in h['settled']]
FIRST = h['envelope'] is None
assert FIRST == (not h['known']) == ((ARM, B) == ORDER[0]), h
if not FIRST: assert h['envelope'] == ENVELOPE['test'], h
S.mkdir()
seg = segment_booking(SEG, lsha)
after = copy.deepcopy(ledger); after['r6_phase0_cpu']['local_cpu_conservative_charged_seconds'] += seg['conservative_cpu_seconds']
(S/('segment%d-booking.json' % SEG)).write_text(json.dumps(seg, indent=2) + '\n')
out = book(CODE, [seg], h['generation']); assert document_hash(out['ledger']) == document_hash(after); write_ledger(out['ledger'])
ledger_sha = document_hash(after); gen = h['generation'] + 1
files = {'code/' + n: b for n, b in blobs.items()}
files.update({n: blobs['scripts/healthtech/' + n] for n in (SUPERVISOR, 'supervise_sacr_r5_engine.py', 'r3_engine_client.py')})
transport = stage(NAME, files)
built = ssh(f"""import json,hashlib
from pathlib import Path
raw=Path('{TEST_INPUT}').read_bytes();assert hashlib.sha256(raw).hexdigest()=='{TEST_SHA}'
rows=[json.loads(l) for l in raw.decode('utf-8').splitlines() if l.strip()];assert len(rows)=={TEST_N}
part=rows[{START}:{START}+{COUNT}];assert len(part)=={COUNT}
data=''.join(json.dumps({{'id':r['id'],'text':r['text']}},ensure_ascii=False)+'\\n' for r in part).encode()
d=Path('{JOB}')/'dispatch';d.mkdir()
(d/'queries.jsonl').write_bytes(data)
print(json.dumps({{'sha256':hashlib.sha256(data).hexdigest(),'queries':len(part)}}))
""")
assert built['queries'] == COUNT
operation = {'stage': 'test', 'arm': ARM, 'batch': B, 'test_rows': [START, START + COUNT], 'input_sha256': built['sha256'],
             'configuration_sha256': config_sha, 'package_sha256': package_sha}
results = {'s5': sha((A/'PAPER1-S5-SUMMARY.json').read_bytes()), 'fixture': sha((A/FIXDIR/FIX).read_bytes()),
           'test_freeze': sha(TFREEZE.read_bytes()), 'go': sha((A/'owner-paper1-test-go-approval.json').read_bytes())}
cpu = after['r6_phase0_cpu']
base = {'status': 'PASS', 'package_sha256': package_sha, 'configuration_sha256': config_sha}
gates = {'integrity': dict(base, gate='integrity', source_commit=git('rev-parse', 'HEAD').decode().strip(), files=len(pins), fixture_sha256=results['fixture'],
             test_freeze_manifest_sha256=results['test_freeze'],
             evidence='committed blobs; worker identical to the CPU-fixture-qualified file except the added test stage name (verified by reverting it); runner files identical; frozen arm files match'),
         'isolation': dict(base, gate='isolation', evidence='same supervisor/isolation as the S4 full-dev runs; re-validated before start'),
         'runtime': dict(base, gate='runtime', s5_summary_sha256=results['s5'], decoder_sha256=RT['decoder_sha256'],
             evidence='the same configuration ran the full dev set (S4) on this GPU; S5 C1 MOVEMENT_PRESENT for this arm'),
         'resources': dict(base, gate='resources', live_admission_required=True, gpu_remaining_seconds=after['gpu_remaining_seconds'],
             disk_preexisting_upper_bound_bytes=DISK_PRIOR),
         'accounting': dict(base, gate='accounting', ledger_sha256=ledger_sha, cpu_remaining_seconds=cpu_cap(cpu) - cpu_used(cpu),
             gpu_stage_host_cpu='TELEMETRY_NOT_CHARGED_TO_CPU_CAP')}
d = {'attempt_id': NAME, 'stage': 'test', 'retry': False, 'queries': COUNT, 'maximum_calls': (2 if SACR else 1) * COUNT, 'seconds': 10800,
     'input_token_cap': RT['input_token_cap'], 'max_consecutive_whitespaces': RT['max_consecutive_whitespaces'],
     'force_json_field_order': RT['force_json_field_order'], 'cpu_seconds': 10800 + CONTROLLER_CPU,
     'cpu_charge_basis': 'GPU_STAGE_SAFETY_BOUND_TELEMETRY_ONLY', 'additional_disk_bytes': 256*1024**2,
     'disk_preexisting_upper_bound_bytes': DISK_PRIOR, 'package_sha256': package_sha, 'files_sha256': pins,
     'configuration_sha256': config_sha, 'input_manifest_sha256': built['sha256'], 'km_sha256': pins[KM], 'model_sha256': pins[IDENT],
     'tokenizer_sha256': RT['tokenizer_sha256'], 'decoder_sha256': RT['decoder_sha256'], 'lmfe_source_sha256': RT['lmfe_source_sha256'],
     'predecessor_attempt_id': PRED, 'operation_sha256': document_hash(operation), 'batch': B,
     'gate_receipts': {k: document_hash(v) for k, v in gates.items()}}
if not SACR: d['arm'] = ARM
assert d['model_sha256'] == RT['model_sha256']
raw = json.dumps(d, indent=2).encode() + b'\n'
for n, v in (('configuration.json', config), ('gates.json', gates), ('operation.json', operation), ('input-check.json', built)):
    (S/n).write_text(json.dumps(v, indent=2) + '\n')
(S/'declaration.json').write_bytes(raw)
ssh(f"""import hashlib
from pathlib import Path
p=Path('{JOB}')/'dispatch'
(p/'declaration.json').write_bytes({raw!r});(p/'gates.json').write_bytes({(S/'gates.json').read_bytes()!r})
assert hashlib.sha256((p/'declaration.json').read_bytes()).hexdigest()=='{sha(raw)}'
print('{{}}')
""")
body = "from patent_to_pilot.research.automatic_dispatch_journal import AutomaticDispatchJournal\nd=json.loads(" + repr(json.dumps(d)) + ")\n"
body += "j=AutomaticDispatchJournal(path,'" + IDENTITY + "')\nh,at=head();assert h[1]==" + str(gen) + "\nam=None\n"
if FIRST:
    for k, c in configs.items(): (A/'paper1-freeze'/('test-configuration-%s.json' % k)).write_text(json.dumps(c, indent=2) + '\n')
    amendment = {'kind': 'AUTHORITY_AMENDMENT', 'owner_approval_sha256': results['go'], 'evidence_sha256': results['test_freeze'],
                 'add_configuration_sha256': [document_hash(configs[k]) for k in ('FA', 'GR', 'SACR', 'RET')],
                 'additional_synthetic_attempts': 0, 'add_stage_envelopes': ENVELOPE,
                 'round': 'paper1-s7-test', 'authority_sha256': h['authority_sha256'], 'ledger_sha256': ledger_sha, 'scope_sha256': None,
                 'reason': 'Paper 1 S7/S8 (owner go 2026-11-15, option a): test stage envelope + FA/GR/SACR/retrieval test configurations (full-dev configurations with stage test)'}
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
res = journal(JOB + '/code/src', body)
assert res['ledger_sha256'] == ledger_sha and res['qualified'], res
if res['amendment']: (S/'authority-amendment.json').write_text(json.dumps(res['amendment'], indent=2) + '\n')
(S/'qualification-receipt.json').write_text(json.dumps(res['qualification'], indent=2) + '\n')
summary = {'status': 'STAGED_QUALIFIED_NOT_LAUNCHED', 'job': NAME, 'arm': ARM, 'batch': B, 'queries': COUNT, 'test_rows': [START, START + COUNT],
           'supervisor': SUPERVISOR, 'declaration_sha256': sha(raw), 'package_sha256': package_sha,
           'configuration_sha256': config_sha, 'input_sha256': built['sha256'], 'transport': transport, 'journal_generation': res['generation'],
           'ledger_sha256': ledger_sha, 'study_status': res['status'], 'segment': SEG, 'segment_seconds': seg['conservative_cpu_seconds'],
           'disk_preexisting_upper_bound_bytes': DISK_PRIOR, 'cpu_remaining_seconds': gates['accounting']['cpu_remaining_seconds']}
(S/'freeze-summary.json').write_text(json.dumps(summary, indent=2) + '\n'); print(json.dumps(summary))
