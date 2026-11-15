"""Paper 1 S5: freeze ONE full-dev retrieval job (journal stage 'full_dev') for FA, GR and SACR ONCE (no launch).

Encodes the 474 dev anchors, the A1 F-shuffle control and each arm's used texts with exactly the B0 encoder/prefix/
vectors; writes private top-200 rankings and label-free C1 statistics. No qrels, no evaluation (that is the CPU job).

Arm inputs = the settled S4 jobs in dev-row order. Jobs that stopped on one query (FA b2 at dev row 259, SACR b4 at
row 259, SACR b4c at row 280) wrote no decisions file: they are pinned as 'partial' (result.json manifest + failure
file); the hold query is the owner-approved original-query fallback (decisions 2026-11-14/15) and is not regenerated.
Appends authority amendment round 'paper1-s5' (the full_dev retrieval configuration). Predecessor: FA pilot retrieval.
"""
import copy, json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from takeover_lib import *
from patent_to_pilot.research.r6_dispatch_files import package_identity
from patent_to_pilot.research.automatic_cpu_booking import cpu_used, cpu_cap

NAME = 'ptp-auto-paper1-dev-fulldev-retrieval-20261115-v1'; S = A/'paper1-s5-retrieval'; S.mkdir(exist_ok=False)
PRED = 'ptp-auto-paper1-fa-pilot-retrieval-20261113-v1'
JOB = JOBS + '/' + NAME; CODE = JOBS + '/ptp-auto-paper1-gr-pilot-retrieval-20261113-v1/code/src'
QUERIES = JOBS + '/ptp-native-baseline-20261110-v1/runtime-dev/queries-ta.jsonl'
QSHA = '6fa09d71c96b0e18f5b7986add7011d17ba6826bad753d7a0cc52a2ce5859d2a'
B0_SHA = '26cfc1e0b9aa02477ca367cb07faee65d37f5e994e1625f29facbee2e007fb29'
FREEZE = json.loads((A/'paper1-freeze/freeze-manifest.json').read_bytes())
ARMS = {'FA': ('rewrite', ['ptp-auto-paper1-fa-fulldev-b1-20261113-v1', 'ptp-auto-paper1-fa-fulldev-b2-20261113-v1',
                           'ptp-auto-paper1-fa-fulldev-b2c-20261114-v1', 'ptp-auto-paper1-fa-fulldev-b3-20261114-v1']),
        'GR': ('rewrite', ['ptp-auto-paper1-gr-fulldev-b%d-20261114-v1' % b for b in (1, 2, 3)]),
        'SACR': ('sacr', ['ptp-auto-native-sacr-fulldev-b%d-20261114-v1' % b for b in (1, 2, 3, 4)]
                 + ['ptp-auto-native-sacr-fulldev-b4c-20261115-v1']
                 + ['ptp-auto-native-sacr-fulldev-b%s-20261115-v2' % b for b in ('4d', '5', '6')])}
PARTIAL = {'ptp-auto-paper1-fa-fulldev-b2-20261113-v1': 101, 'ptp-auto-native-sacr-fulldev-b4-20261114-v1': 22,
           'ptp-auto-native-sacr-fulldev-b4c-20261115-v1': 20}  # hold index = S4 records
DISK_PRIOR = max(x['disk_preexisting_upper_bound_bytes'] + x['additional_disk_bytes']
                 for x in (json.loads(p.read_bytes()) for p in A.rglob('declaration.json')) if 'disk_preexisting_upper_bound_bytes' in x)
SEG = 1 + max(int(re.fullmatch(r'segment(\d+)-booking\.json', p.name).group(1)) for p in A.rglob('segment*-booking.json'))
SECONDS = 3600


def configuration():
    return {'stage': 'full_dev', 'track': 'PAPER1_DEV_RETRIEVAL', 'arms': sorted(ARMS),
            'protocol': 'PAPER1-ACQUISITION-PROTOCOL (frozen 2026-11-13) S5 + amendment A1',
            'paper1_freeze_manifest_sha256': sha((A/'paper1-freeze/freeze-manifest.json').read_bytes()),
            'amendment_a1_sha256': sha((A/'paper1-freeze/amendment-a1.json').read_bytes()),
            'encoder': FREEZE['retrieval_runtime']['encoder'], 'query_prefix': FREEZE['retrieval_runtime']['query_prefix'],
            'vectors_sha256': FREEZE['retrieval_runtime']['passage_vectors_sha256'], 'ranking': 'rank_maxp depth 200',
            'texts': 'anchor (original TA), F-shuffle control, arm text where the arm decision is a use action; fallback keeps the reference ranking',
            'partial_jobs': 'hold query of a stopped S4 job = owner-approved ORIGINAL_QUERY_FALLBACK; later queries from the continuation job',
            'anchor_control': 'reencode anchors; B0 reference only if all identical', 'labels_used': False, 'evaluated': False}


ledger = json.loads(L.read_bytes()); lsha = document_hash(ledger)
h = journal(CODE, "h,at=head()\nscope=json.loads(h[3]);st=scope['automatic_study']\nprint(json.dumps({'generation':h[1],'ledger_sha256':document_hash(json.loads(h[2])),'active':h[4],"
                  "'status':st['status'],'authority_sha256':st['authority_sha256'],'pred':st['stage_costs'].get('" + PRED + "')}))\n")
assert h['active'] is None and h['ledger_sha256'] == lsha and h['status'] == 'IDLE', h
assert h['pred'] and h['pred']['stage'] == 'pilot' and h['pred']['calls_complete'] is True, h
# Read-only remote preflight: pins for every arm job and an exact coverage check of the 474 dev queries.
pre = ssh(f"""import json,hashlib
from pathlib import Path
sha=lambda b:hashlib.sha256(b).hexdigest()
J=Path('{JOBS}');raw=Path('{QUERIES}').read_bytes();assert sha(raw)=='{QSHA}'
rows=[json.loads(l) for l in raw.decode().splitlines() if l.strip()]
data=''.join(json.dumps({{'id':r['id'],'text':r['text']}},ensure_ascii=False)+'\\n' for r in rows).encode()
text={{r['id']:r['text'] for r in rows}};assert len(text)==474==len(rows)
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
    assert sorted(seen)==sorted(text) and len(seen)==474,(arm,len(seen))
    out[arm]={{'kind':kind,'jobs':pins,'used':used,'fallback':fb}}
b0=sha((J/'ptp-native-baseline-20261110-v1/out/attempt/rankings-top200.jsonl').read_bytes())
print(json.dumps({{'arms':out,'b0':b0,'input_sha256':sha(data)}}))
""", timeout=300)
assert pre['b0'] == B0_SHA, pre['b0']
counts = {a: {'used': v.pop('used'), 'fallback': v.pop('fallback')} for a, v in pre['arms'].items()}
assert counts['FA']['fallback'] == 1 and counts['GR']['fallback'] == 1 and counts['SACR']['fallback'] == 6, counts
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
operation = {'stage': 'full_dev', 'arms': arm_pins, 'configuration_sha256': config_sha, 'package_sha256': package_sha, 'input_sha256': INPUT_SHA}
results = {'pred': sha((A/'paper1-s3-fa-retrieval'/'settlement.json').read_bytes()), 'sacr_b6': sha((A/'sacr-fulldev-b6'/'settlement.json').read_bytes())}
cpu = after['r6_phase0_cpu']
base = {'status': 'PASS', 'package_sha256': package_sha, 'configuration_sha256': config_sha}
gates = {'integrity': dict(base, gate='integrity', source_commit=git('rev-parse', 'HEAD').decode().strip(), files=len(pins),
             evidence='committed blobs; paper1_retrieval_panel (incl. partial_job_decisions), paper1_controls unit tests and the worker partial-load test PASS; encode/rank path = B0 runner functions (frozen hashes match)'),
         'isolation': dict(base, gate='isolation', evidence='supervisor config tests PASS: read-only inputs and arm outputs (3 arms, continuation jobs), no qrels/evaluation mounts, network none'),
         'runtime': dict(base, gate='runtime', predecessor_settlement_sha256=results['pred'], s4_last_settlement_sha256=results['sacr_b6'],
             evidence='read-only remote preflight: dev query file, all 15 arm jobs (3 partial) and B0 rankings pinned; every arm covers the 474 dev queries exactly once with identical texts; same encode path ran in the S3 pilot retrievals'),
         'resources': dict(base, gate='resources', live_admission_required=True, gpu_remaining_seconds=after['gpu_remaining_seconds'],
             full_dev_charged_seconds=after['full_dev_charged_seconds'], disk_preexisting_upper_bound_bytes=DISK_PRIOR),
         'accounting': dict(base, gate='accounting', ledger_sha256=ledger_sha, cpu_remaining_seconds=cpu_cap(cpu) - cpu_used(cpu),
             gpu_stage_host_cpu='TELEMETRY_NOT_CHARGED_TO_CPU_CAP')}
d = {'attempt_id': NAME, 'stage': 'full_dev', 'retry': False, 'queries': 474, 'maximum_calls': 1, 'generation_calls': 0, 'seconds': SECONDS,
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
amendment = {'kind': 'AUTHORITY_AMENDMENT', 'owner_approval_sha256': sha((A/'owner-paper1-freeze-approval.json').read_bytes()),
             'evidence_sha256': results['sacr_b6'], 'add_configuration_sha256': [config_sha], 'additional_synthetic_attempts': 0,
             'round': 'paper1-s5', 'authority_sha256': h['authority_sha256'], 'ledger_sha256': ledger_sha, 'scope_sha256': None,
             'reason': 'Paper 1 frozen protocol S5: full-dev retrieval of FA, GR and SACR (one job; stage full_dev; not evaluated)'}
body = ("from patent_to_pilot.research.automatic_dispatch_journal import AutomaticDispatchJournal\nd=json.loads(" + repr(json.dumps(d)) + ")\n"
        "j=AutomaticDispatchJournal(path,'" + IDENTITY + "')\nh,at=head();assert h[1]==" + str(gen) + "\n"
        "am=json.loads(" + repr(json.dumps(amendment)) + ")\nam['scope_sha256']=document_hash(json.loads(h[3]))\n"
        "j.amend_authority(expected_generation=" + str(gen) + ",receipt=am,receipt_sha256=document_hash(am))\n"
        "h,at=head();scope=json.loads(h[3])\n"
        "q={'declaration':d,'authority_sha256':scope['automatic_study']['authority_sha256'],'ledger_sha256':document_hash(json.loads(h[2])),'scope_sha256':document_hash(scope)}\n"
        "j.qualify_stage(expected_generation=" + str(gen + 1) + ",receipt=q,receipt_sha256=document_hash(q))\n"
        "h,at=head();scope=json.loads(h[3])\nassert h[1]==" + str(gen + 2) + " and h[4] is None\n"
        "print(json.dumps({'generation':h[1],'ledger_sha256':document_hash(json.loads(h[2])),'amendment':am,'qualification':q,"
        "'qualified':'" + NAME + "' in scope['automatic_study']['qualified_dispatches'],'status':scope['automatic_study']['status']}))\n")
res = journal(code2, body)
assert res['ledger_sha256'] == ledger_sha and res['qualified'], res
(S/'authority-amendment.json').write_text(json.dumps(res['amendment'], indent=2) + '\n')
(S/'qualification-receipt.json').write_text(json.dumps(res['qualification'], indent=2) + '\n')
summary = {'status': 'STAGED_QUALIFIED_NOT_LAUNCHED', 'job': NAME, 'supervisor': 'supervise_paper1_retrieval.py',
           'declaration_sha256': sha(raw), 'package_sha256': package_sha, 'configuration_sha256': config_sha, 'input_sha256': INPUT_SHA,
           'arm_counts': counts, 'transport': transport, 'journal_generation': res['generation'], 'ledger_sha256': ledger_sha,
           'study_status': res['status'], 'segment': SEG, 'segment_seconds': seg['conservative_cpu_seconds'],
           'disk_preexisting_upper_bound_bytes': DISK_PRIOR, 'cpu_remaining_seconds': gates['accounting']['cpu_remaining_seconds']}
(S/'freeze-summary.json').write_text(json.dumps(summary, indent=2) + '\n'); print(json.dumps(summary))
