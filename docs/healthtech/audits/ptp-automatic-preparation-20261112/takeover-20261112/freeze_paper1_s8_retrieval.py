"""Paper 1 S8: freeze ONE test retrieval job (journal stage 'test') for FA, GR and SACR ONCE (no launch).

Derived from freeze_paper1_s5_retrieval.py. Arm inputs = the settled S8 test generation batches; the configuration is
the S5 retrieval configuration with stage test (test_configs.configuration('RET'), already authorized in round
'paper1-s7-test'). There is no pinned B0 test ranking: the anchor check therefore selects the re-encoded anchors as the
reference (frozen rule), i.e. B0 on test = original TA queries encoded by this job with the same encoder/prefix.
No qrels, no evaluation. Predecessor: the S5 full-dev retrieval job.
"""
import copy, json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from takeover_lib import *
from test_configs import TEST_INPUT, TEST_SHA, TEST_N, ORDER, job as test_job, configuration as test_configuration
from patent_to_pilot.research.r6_dispatch_files import package_identity
from patent_to_pilot.research.automatic_cpu_booking import cpu_used, cpu_cap

NAME = 'ptp-auto-paper1-all-test-retrieval-20261115-v1'; S = A/'paper1-s8-retrieval'; S.mkdir(exist_ok=False)
PRED = 'ptp-auto-paper1-dev-fulldev-retrieval-20261115-v1'
JOB = JOBS + '/' + NAME; CODE = JOBS + '/ptp-auto-paper1-gr-pilot-retrieval-20261113-v1/code/src'
QUERIES = TEST_INPUT
QSHA = TEST_SHA
B0_SHA = '26cfc1e0b9aa02477ca367cb07faee65d37f5e994e1625f29facbee2e007fb29'
FREEZE = json.loads((A/'paper1-freeze/freeze-manifest.json').read_bytes())
ARMS = {arm: ('sacr' if arm == 'SACR' else 'rewrite', [test_job(a, b) for a, b in ORDER if a == arm]) for arm in ('FA', 'GR', 'SACR')}
PARTIAL = {}  # a stopped S8 batch would need an owner decision first
DISK_PRIOR = max(x['disk_preexisting_upper_bound_bytes'] + x['additional_disk_bytes']
                 for x in (json.loads(p.read_bytes()) for p in A.rglob('declaration.json')) if 'disk_preexisting_upper_bound_bytes' in x)
SEG = 1 + max(int(re.fullmatch(r'segment(\d+)-booking\.json', p.name).group(1)) for p in A.rglob('segment*-booking.json'))
SECONDS = 3600


def configuration():
    return test_configuration('RET')


ledger = json.loads(L.read_bytes()); lsha = document_hash(ledger)
h = journal(CODE, "h,at=head()\nscope=json.loads(h[3]);st=scope['automatic_study']\nprint(json.dumps({'generation':h[1],'ledger_sha256':document_hash(json.loads(h[2])),'active':h[4],"
                  "'status':st['status'],'authority_sha256':st['authority_sha256'],'pred':st['stage_costs'].get('" + PRED + "'),'settled':sorted(st['stage_costs'])}))\n")
assert h['active'] is None and h['ledger_sha256'] == lsha and h['status'] == 'IDLE', h
assert h['pred'] and h['pred']['stage'] == 'full_dev' and h['pred']['calls_complete'] is True, h
assert all(test_job(a, b) in h['settled'] for a, b in ORDER), 'all S8 generation batches must be settled first'
# Read-only remote preflight: pins for every arm job and an exact coverage check of the 773 test queries.
pre = ssh(f"""import json,hashlib
from pathlib import Path
sha=lambda b:hashlib.sha256(b).hexdigest()
J=Path('{JOBS}');raw=Path('{QUERIES}').read_bytes();assert sha(raw)=='{QSHA}'
rows=[json.loads(l) for l in raw.decode().splitlines() if l.strip()]
data=''.join(json.dumps({{'id':r['id'],'text':r['text']}},ensure_ascii=False)+'\\n' for r in rows).encode()
text={{r['id']:r['text'] for r in rows}};assert len(text)=={TEST_N}==len(rows)
arms=json.loads({json.dumps(json.dumps(ARMS))});partial=json.loads({json.dumps(json.dumps(PARTIAL))});out={{}}
for arm,(kind,jobs) in arms.items():
    pins=[];seen=[];used=fb=0
    for j in jobs:
        p=J/j;qraw=(p/'dispatch/queries.jsonl').read_bytes();qs=[json.loads(l) for l in qraw.decode().splitlines() if l.strip()]
        assert all(text[q['id']]==q['text'] for q in qs)
        o=p/'out/attempt';pin={{'job':j,'queries_sha256':sha(qraw)}}
        if j in partial:
            n=partial[j];raws=[(o/'queries'/('q%03d'%i)/'result.json').read_bytes() for i in range(n)]
            f=(o/'queries'/('q%03d'%n)/'failure.json').read_bytes()
            assert not (o/'queries'/('q%03d'%(n+1))).exists() and not (o/'decisions-private.json').exists()
            pin['partial']={{'hold_index':n,'results_manifest_sha256':sha(json.dumps([sha(r) for r in raws]).encode()),'failure_sha256':sha(f)}}
            acts=[(json.loads(r).get('action') if kind=='rewrite' else json.loads(r)['decision']['action']) for r in raws]+['ORIGINAL_QUERY_FALLBACK']
            seen+=[q['id'] for q in qs[:n+1]]
        else:
            d=(o/'decisions-private.json').read_bytes();pin['decisions_sha256']=sha(d);v=json.loads(d)
            assert set(v)=={{q['id'] for q in qs}};acts=[x['action'] for x in v.values()];seen+=[q['id'] for q in qs]
        used+=sum(a!='ORIGINAL_QUERY_FALLBACK' for a in acts);fb+=sum(a=='ORIGINAL_QUERY_FALLBACK' for a in acts)
        pins.append(pin)
    assert sorted(seen)==sorted(text) and len(seen)=={TEST_N},(arm,len(seen))
    out[arm]={{'kind':kind,'jobs':pins,'used':used,'fallback':fb}}
b0=sha((J/'ptp-native-baseline-20261110-v1/out/attempt/rankings-top200.jsonl').read_bytes())
print(json.dumps({{'arms':out,'b0':b0,'input_sha256':sha(data)}}))
""", timeout=300)
assert pre['b0'] == B0_SHA, pre['b0']
counts = {a: {'used': v.pop('used'), 'fallback': v.pop('fallback')} for a, v in pre['arms'].items()}
arm_pins = pre['arms']; INPUT_SHA = pre['input_sha256']
blobs, pins = package(['run_paper1_retrieval.py', 'supervise_paper1_retrieval.py', 'run_dapfam_native_baseline.py', 'run_dapfam_dense_pool.py'])
package_sha = package_identity(pins)
for f in ('src/patent_to_pilot/research/native_dense_ranking.py', 'scripts/healthtech/run_dapfam_native_baseline.py'):
    assert pins[f] == FREEZE['files_sha256'][f], 'frozen file changed: ' + f
seg = segment_booking(SEG, lsha)
after = copy.deepcopy(ledger); after['r6_phase0_cpu']['local_cpu_conservative_charged_seconds'] += seg['conservative_cpu_seconds']
(S/('segment%d-booking.json' % SEG)).write_text(json.dumps(seg, indent=2) + '\n')
out = book(CODE, [seg], h['generation']); assert document_hash(out['ledger']) == document_hash(after); write_ledger(out['ledger'])
ledger_sha = document_hash(after); gen = h['generation'] + 1
config = configuration(); config_sha = document_hash(config)
operation = {'stage': 'test', 'arms': arm_pins, 'configuration_sha256': config_sha, 'package_sha256': package_sha, 'input_sha256': INPUT_SHA}
results = {'pred': sha((A/'paper1-s5-retrieval'/'settlement.json').read_bytes()), 'sacr_b6': sha((A/'paper1-s8-sacr-b10'/'settlement.json').read_bytes())}
cpu = after['r6_phase0_cpu']
base = {'status': 'PASS', 'package_sha256': package_sha, 'configuration_sha256': config_sha}
gates = {'integrity': dict(base, gate='integrity', source_commit=git('rev-parse', 'HEAD').decode().strip(), files=len(pins),
             evidence='committed blobs; paper1_retrieval_panel (incl. partial_job_decisions), paper1_controls unit tests and the worker partial-load test PASS; encode/rank path = B0 runner functions (frozen hashes match)'),
         'isolation': dict(base, gate='isolation', evidence='supervisor config tests PASS: read-only inputs and arm outputs (3 arms, continuation jobs), no qrels/evaluation mounts, network none'),
         'runtime': dict(base, gate='runtime', predecessor_settlement_sha256=results['pred'], s4_last_settlement_sha256=results['sacr_b6'],
             evidence='read-only remote preflight: test query file and all 20 S8 arm batches pinned; every arm covers the 773 test queries exactly once with identical texts; same encode path ran the S5 full-dev retrieval'),
         'resources': dict(base, gate='resources', live_admission_required=True, gpu_remaining_seconds=after['gpu_remaining_seconds'],
             disk_preexisting_upper_bound_bytes=DISK_PRIOR),
         'accounting': dict(base, gate='accounting', ledger_sha256=ledger_sha, cpu_remaining_seconds=cpu_cap(cpu) - cpu_used(cpu),
             gpu_stage_host_cpu='TELEMETRY_NOT_CHARGED_TO_CPU_CAP')}
d = {'attempt_id': NAME, 'stage': 'test', 'retry': False, 'queries': TEST_N, 'maximum_calls': 1, 'generation_calls': 0, 'seconds': SECONDS,
     'cpu_seconds': SECONDS + 900, 'cpu_charge_basis': 'GPU_STAGE_SAFETY_BOUND_TELEMETRY_ONLY', 'additional_disk_bytes': 256*1024**2,
     'disk_preexisting_upper_bound_bytes': DISK_PRIOR, 'package_sha256': package_sha, 'files_sha256': pins,
     'configuration_sha256': config_sha, 'input_manifest_sha256': INPUT_SHA, 'arms': arm_pins, 'b0_rankings_sha256': B0_SHA,
     'model_sha256': pins[IDENT], 'predecessor_attempt_id': PRED, 'operation_sha256': document_hash(operation),
     'gate_receipts': {k: document_hash(v) for k, v in gates.items()}}
raw = json.dumps(d, indent=2).encode() + b'\n'
for n, v in (('configuration.json', config), ('gates.json', gates), ('operation.json', operation), ('arm-counts.json', counts)):
    (S/n).write_text(json.dumps(v, indent=2) + '\n')
(S/'declaration.json').write_bytes(raw)
files = {'code/' + n: b for n, b in blobs.items()}
files.update({n: blobs['scripts/healthtech/' + n] for n in ('supervise_paper1_retrieval.py', 'supervise_sacr_r5_engine.py', 'r3_engine_client.py')})
files.update({'dispatch/declaration.json': raw, 'dispatch/gates.json': (S/'gates.json').read_bytes()})
transport = stage(NAME, files)
ssh(f"""import hashlib,json
from pathlib import Path
rows=[json.loads(l) for l in Path('{QUERIES}').read_bytes().decode().splitlines() if l.strip()]
data=''.join(json.dumps({{'id':r['id'],'text':r['text']}},ensure_ascii=False)+'\\n' for r in rows).encode()
assert hashlib.sha256(data).hexdigest()=='{INPUT_SHA}'
(Path('{JOB}')/'dispatch/queries.jsonl').write_bytes(data)
print('{{}}')
""")
code2 = JOB + '/code/src'
body = ("from patent_to_pilot.research.automatic_dispatch_journal import AutomaticDispatchJournal\nd=json.loads(" + repr(json.dumps(d)) + ")\n"
        "j=AutomaticDispatchJournal(path,'" + IDENTITY + "')\nh,at=head();assert h[1]==" + str(gen) + "\n"
        "am=None\n"
        "h,at=head();scope=json.loads(h[3])\n"
        "q={'declaration':d,'authority_sha256':scope['automatic_study']['authority_sha256'],'ledger_sha256':document_hash(json.loads(h[2])),'scope_sha256':document_hash(scope)}\n"
        "j.qualify_stage(expected_generation=" + str(gen) + ",receipt=q,receipt_sha256=document_hash(q))\n"
        "h,at=head();scope=json.loads(h[3])\nassert h[1]==" + str(gen + 1) + " and h[4] is None\n"
        "print(json.dumps({'generation':h[1],'ledger_sha256':document_hash(json.loads(h[2])),'amendment':am,'qualification':q,"
        "'qualified':'" + NAME + "' in scope['automatic_study']['qualified_dispatches'],'status':scope['automatic_study']['status']}))\n")
res = journal(code2, body)
assert res['ledger_sha256'] == ledger_sha and res['qualified'], res
(S/'qualification-receipt.json').write_text(json.dumps(res['qualification'], indent=2) + '\n')
summary = {'status': 'STAGED_QUALIFIED_NOT_LAUNCHED', 'job': NAME, 'supervisor': 'supervise_paper1_retrieval.py',
           'declaration_sha256': sha(raw), 'package_sha256': package_sha, 'configuration_sha256': config_sha, 'input_sha256': INPUT_SHA,
           'arm_counts': counts, 'transport': transport, 'journal_generation': res['generation'], 'ledger_sha256': ledger_sha,
           'study_status': res['status'], 'segment': SEG, 'segment_seconds': seg['conservative_cpu_seconds'],
           'disk_preexisting_upper_bound_bytes': DISK_PRIOR, 'cpu_remaining_seconds': gates['accounting']['cpu_remaining_seconds']}
(S/'freeze-summary.json').write_text(json.dumps(summary, indent=2) + '\n'); print(json.dumps(summary))
