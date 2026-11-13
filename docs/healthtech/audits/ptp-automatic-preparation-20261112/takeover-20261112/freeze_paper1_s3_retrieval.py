"""Paper 1 S3: freeze ONE pilot-20 retrieval job (journal stage 'pilot') for an arm (FA|GR) ONCE (no launch).

Encodes the 20 anchors, the A1 F-shuffle control and the arm's used rewrites with the B0 encoder/prefix/vectors;
writes private rankings and label-free C1 statistics. NOT evaluated (protocol section 7); it is the settled
'pilot' predecessor that the journal requires before full_dev, and the technical pilot of the S5 retrieval worker.
FA run also appends the authority amendment (round 'paper1-s3-pilot': FA and GR pilot configurations).
"""
import copy, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from takeover_lib import *
from patent_to_pilot.research.r6_dispatch_files import package_identity
from patent_to_pilot.research.automatic_cpu_booking import cpu_used, cpu_cap

ARM = sys.argv[1]; assert ARM in ('FA', 'GR')
SEG = {'FA': 36, 'GR': 37}[ARM]; low = ARM.lower()
NAME = 'ptp-auto-paper1-%s-pilot-retrieval-20261113-v1' % low; S = A/('paper1-s3-%s-retrieval' % low); S.mkdir(exist_ok=False)
PRED = 'ptp-auto-paper1-%s-pilot20-20261113-v1' % low
FA_JOB = 'ptp-auto-paper1-fa-pilot-retrieval-20261113-v1'
JOB = JOBS + '/' + NAME; CODE = JOBS + '/ptp-auto-paper1-gr-pilot20-20261113-v1/code/src'
PILOT_SHA = json.loads((A/'native-sacr-pilot20-v5/freeze-summary.json').read_bytes())['input_sha256']
B0_SHA = '26cfc1e0b9aa02477ca367cb07faee65d37f5e994e1625f29facbee2e007fb29'  # pinned in the SACR pilot retrieval declaration
FREEZE = json.loads((A/'paper1-freeze/freeze-manifest.json').read_bytes())
# GR pilot-20 declared upper bound + its 512 MiB (+ FA pilot retrieval's 256 MiB for the GR run).
DISK_PRIOR = 35591986671 + 256*1024**2 + 8*16*1024**2 + 4*512*1024**2 + (256*1024**2 if ARM == 'GR' else 0)


def configuration(arm):
    return {'stage': 'pilot', 'track': 'PAPER1_' + arm + '_RETRIEVAL', 'protocol': 'PAPER1-ACQUISITION-PROTOCOL (frozen 2026-11-13) S3 + amendment A1',
            'paper1_freeze_manifest_sha256': sha((A/'paper1-freeze/freeze-manifest.json').read_bytes()),
            'amendment_a1_sha256': sha((A/'paper1-freeze/amendment-a1.json').read_bytes()),
            'encoder': FREEZE['retrieval_runtime']['encoder'], 'query_prefix': FREEZE['retrieval_runtime']['query_prefix'],
            'vectors_sha256': FREEZE['retrieval_runtime']['passage_vectors_sha256'], 'ranking': 'rank_maxp depth 200',
            'texts': 'anchor (original TA), F-shuffle control, arm rewrite where USE_REWRITE; fallback keeps the reference ranking',
            'anchor_control': 'reencode anchors; B0 reference only if all identical', 'labels_used': False, 'evaluated': False}


ledger = json.loads(L.read_bytes()); lsha = document_hash(ledger)
h = journal(CODE, "h,at=head()\nscope=json.loads(h[3]);st=scope['automatic_study']\nprint(json.dumps({'generation':h[1],'ledger_sha256':document_hash(json.loads(h[2])),'active':h[4],"
                  "'status':st['status'],'authority_sha256':st['authority_sha256'],'pred':st['stage_costs'].get('" + PRED + "'),"
                  "'fa':st['stage_costs'].get('" + FA_JOB + "')}))\n")
assert h['active'] is None and h['ledger_sha256'] == lsha and h['status'] == 'IDLE', h
assert h['pred'] and h['pred']['stage'] == 'fidelity' and h['pred']['calls_complete'] is True, h
if ARM == 'GR': assert h['fa'] is not None, 'FA pilot retrieval must be settled before GR is frozen'
pre = ssh(f"""import json,hashlib
from pathlib import Path
p=Path('{JOBS}/{PRED}')
q=(p/'dispatch/queries.jsonl').read_bytes();dec=(p/'out/attempt/decisions-private.json').read_bytes()
assert hashlib.sha256(q).hexdigest()=='{PILOT_SHA}'
v=json.loads(dec)
print(json.dumps({{'decisions_sha256':hashlib.sha256(dec).hexdigest(),'queries':len(v),'used':sum(x['action']=='USE_REWRITE' for x in v.values()),
 'b0':hashlib.sha256(Path('{JOBS}/ptp-native-baseline-20261110-v1/out/attempt/rankings-top200.jsonl').read_bytes()).hexdigest()}}))
""")
assert pre['queries'] == 20 and pre['b0'] == B0_SHA, pre
blobs, pins = package(['run_paper1_retrieval.py', 'supervise_paper1_retrieval.py', 'run_dapfam_native_baseline.py', 'run_dapfam_dense_pool.py'])
package_sha = package_identity(pins)
for f in ('src/patent_to_pilot/research/native_dense_ranking.py', 'scripts/healthtech/run_dapfam_native_baseline.py'):
    assert pins[f] == FREEZE['files_sha256'][f], 'frozen file changed: ' + f
seg = segment_booking(SEG, lsha)
after = copy.deepcopy(ledger); after['r6_phase0_cpu']['local_cpu_conservative_charged_seconds'] += seg['conservative_cpu_seconds']
(S/('segment%d-booking.json' % SEG)).write_text(json.dumps(seg, indent=2) + '\n')
out = book(CODE, [seg], h['generation']); assert document_hash(out['ledger']) == document_hash(after); write_ledger(out['ledger'])
ledger_sha = document_hash(after); gen = h['generation'] + 1
config = configuration(ARM); config_sha = document_hash(config)
arm_pins = {ARM: {'kind': 'rewrite', 'jobs': [{'job': PRED, 'queries_sha256': PILOT_SHA, 'decisions_sha256': pre['decisions_sha256']}]}}
operation = {'stage': 'pilot', 'arm': ARM, 'arms': arm_pins, 'configuration_sha256': config_sha, 'package_sha256': package_sha}
results = {'pred': sha((A/('paper1-s3-' + low)/'settlement.json').read_bytes()), 'sacr_pilot': sha((A/'sacr-pilot-retrieval/freeze-summary.json').read_bytes())}
cpu = after['r6_phase0_cpu']
base = {'status': 'PASS', 'package_sha256': package_sha, 'configuration_sha256': config_sha}
gates = {'integrity': dict(base, gate='integrity', source_commit=git('rev-parse', 'HEAD').decode().strip(), files=len(pins),
             evidence='committed blobs; paper1_retrieval_panel, paper1_controls and sacr_pilot_panel unit tests PASS; encode/rank path = B0 runner functions (frozen hashes match)'),
         'isolation': dict(base, gate='isolation', evidence='supervisor config test PASS: read-only inputs and arm outputs, no qrels/evaluation mounts, network none'),
         'runtime': dict(base, gate='runtime', predecessor_settlement_sha256=results['pred'], sacr_pilot_retrieval_sha256=results['sacr_pilot'],
             evidence='read-only remote preflight: pilot file, arm decisions and B0 rankings hashes pinned; same encode path ran in the SACR pilot retrieval'),
         'resources': dict(base, gate='resources', live_admission_required=True, gpu_remaining_seconds=after['gpu_remaining_seconds'],
             fidelity_remaining_seconds=after['fidelity_generation_remaining_seconds'], disk_preexisting_upper_bound_bytes=DISK_PRIOR),
         'accounting': dict(base, gate='accounting', ledger_sha256=ledger_sha, cpu_remaining_seconds=cpu_cap(cpu) - cpu_used(cpu),
             gpu_stage_host_cpu='TELEMETRY_NOT_CHARGED_TO_CPU_CAP')}
d = {'attempt_id': NAME, 'arm': ARM, 'stage': 'pilot', 'retry': False, 'queries': 20, 'maximum_calls': 1, 'generation_calls': 0, 'seconds': 1800,
     'cpu_seconds': 1860, 'cpu_charge_basis': 'GPU_STAGE_SAFETY_BOUND_TELEMETRY_ONLY', 'additional_disk_bytes': 256*1024**2,
     'disk_preexisting_upper_bound_bytes': DISK_PRIOR, 'package_sha256': package_sha, 'files_sha256': pins,
     'configuration_sha256': config_sha, 'input_manifest_sha256': PILOT_SHA, 'arms': arm_pins, 'b0_rankings_sha256': B0_SHA,
     'model_sha256': pins[IDENT], 'predecessor_attempt_id': PRED, 'operation_sha256': document_hash(operation),
     'gate_receipts': {k: document_hash(v) for k, v in gates.items()}}
raw = json.dumps(d, indent=2).encode() + b'\n'
for n, v in (('configuration.json', config), ('gates.json', gates), ('operation.json', operation)): (S/n).write_text(json.dumps(v, indent=2) + '\n')
(S/'declaration.json').write_bytes(raw)
files = {'code/' + n: b for n, b in blobs.items()}
files.update({n: blobs['scripts/healthtech/' + n] for n in ('supervise_paper1_retrieval.py', 'supervise_sacr_r5_engine.py', 'r3_engine_client.py')})
files.update({'dispatch/declaration.json': raw, 'dispatch/gates.json': (S/'gates.json').read_bytes()})
transport = stage(NAME, files)
built = ssh(f"""import hashlib
from pathlib import Path
raw=Path('{JOBS}/{PRED}/dispatch/queries.jsonl').read_bytes()
assert hashlib.sha256(raw).hexdigest()=='{PILOT_SHA}'
(Path('{JOB}')/'dispatch/queries.jsonl').write_bytes(raw)
print('{{}}')
""")
code2 = JOB + '/code/src'
body = "from patent_to_pilot.research.automatic_dispatch_journal import AutomaticDispatchJournal\nd=json.loads(" + repr(json.dumps(d)) + ")\n"
body += "j=AutomaticDispatchJournal(path,'" + IDENTITY + "')\nh,at=head();assert h[1]==" + str(gen) + "\nam=None\n"
if ARM == 'FA':
    amendment = {'kind': 'AUTHORITY_AMENDMENT', 'owner_approval_sha256': sha((A/'owner-paper1-freeze-approval.json').read_bytes()),
                 'evidence_sha256': results['pred'], 'add_configuration_sha256': [document_hash(configuration('FA')), document_hash(configuration('GR'))],
                 'additional_synthetic_attempts': 0, 'round': 'paper1-s3-pilot', 'authority_sha256': h['authority_sha256'], 'ledger_sha256': ledger_sha,
                 'scope_sha256': None, 'reason': 'Paper 1 frozen protocol S3: pilot-20 retrieval (stage pilot, not evaluated) for FA and GR; journal predecessor for full_dev'}
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
summary = {'status': 'STAGED_QUALIFIED_NOT_LAUNCHED', 'job': NAME, 'arm': ARM, 'supervisor': 'supervise_paper1_retrieval.py',
           'declaration_sha256': sha(raw), 'package_sha256': package_sha, 'configuration_sha256': config_sha, 'input_sha256': PILOT_SHA,
           'arm_used_rewrites': pre['used'], 'transport': transport, 'journal_generation': res['generation'], 'ledger_sha256': ledger_sha,
           'study_status': res['status'], 'segment_seconds': seg['conservative_cpu_seconds'],
           'cpu_remaining_seconds': gates['accounting']['cpu_remaining_seconds']}
(S/'freeze-summary.json').write_text(json.dumps(summary, indent=2) + '\n'); print(json.dumps(summary))
