"""Freeze SACR pilot retrieval ONCE (no launch): segment booking, configuration, gates, declaration,
stage, authority amendment (config) and qualify_stage('pilot', predecessor native v5)."""
import copy, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from takeover_lib import *
from patent_to_pilot.research.r6_dispatch_files import package_identity
from patent_to_pilot.research.automatic_cpu_booking import cpu_used, cpu_cap
NAME = 'ptp-auto-sacr-pilot-retrieval-20261113-v1'; S = A/'sacr-pilot-retrieval'; S.mkdir(exist_ok=False)
JOB = JOBS + '/' + NAME; CODE = JOBS + '/ptp-auto-native-sacr-pilot20-20261112-v5/code/src'
DISK_PRIOR = 31162801647 + 24*16*1024**2 + 5*256*1024**2 + 5*512*1024**2
PIN = {'b0': '26cfc1e0b9aa02477ca367cb07faee65d37f5e994e1625f29facbee2e007fb29',
       'decisions': 'ce7e68b5b2e2de24ad08dc641a88bcf5e41af1b52e5da69aca9cb5a620d964d4',
       'pilot': 'b5d837f47bf4fc497c9105cfa35b397979b15e46a9c093a0c9e9cf89e404262e'}
ledger = json.loads(L.read_bytes()); lsha = document_hash(ledger)
h = journal(CODE, "h,at=head()\nscope=json.loads(h[3])\nprint(json.dumps({'generation':h[1],'ledger_sha256':document_hash(json.loads(h[2])),'active':h[4],"
                  "'authority_sha256':scope['automatic_study']['authority_sha256'],'v5':scope['automatic_study']['stage_costs'].get('ptp-auto-native-sacr-pilot20-20261112-v5')}))\n")
assert h['active'] is None and h['ledger_sha256'] == lsha and h['v5']['calls_complete'] is True, h
blobs, pins = package(['run_sacr_pilot_retrieval.py', 'supervise_sacr_pilot_retrieval.py', 'run_dapfam_native_baseline.py', 'run_dapfam_dense_pool.py'])
package_sha = package_identity(pins)
seg = segment_booking(26, lsha)
after = copy.deepcopy(ledger); after['r6_phase0_cpu']['local_cpu_conservative_charged_seconds'] += seg['conservative_cpu_seconds']
(S/'segment26-booking.json').write_text(json.dumps(seg, indent=2) + '\n')
out = book(CODE, [seg], h['generation']); assert document_hash(out['ledger']) == document_hash(after); write_ledger(out['ledger'])
ledger_sha = document_hash(after); gen = h['generation'] + 1
configuration = {'stage': 'pilot', 'track': 'SACR', 'protocol': 'NATIVE-STAGES-20261112 addendum',
                 'encoder': 'B0 MeanPoolEncoder PatEmbed-large fp32, MODEL_PINS', 'query_prefix': 'DENSE_QUERY_PREFIX (B0)',
                 'vectors_sha256': '9a385bcfd0aab6c4c19f2a8715824922d42d328c53f0da58857b0106ed4f0137', 'ranking': 'rank_maxp depth 200',
                 'anchor_control': 'reencode 20 original TA; B0 reference only if all identical', 'labels_used': False}
config_sha = document_hash(configuration)
operation = {'stage': 'pilot', 'track': 'SACR', 'decisions_sha256': PIN['decisions'], 'configuration_sha256': config_sha, 'package_sha256': package_sha}
cpu = after['r6_phase0_cpu']
base = {'status': 'PASS', 'package_sha256': package_sha, 'configuration_sha256': config_sha}
gates = {'integrity': dict(base, gate='integrity', source_commit=git('rev-parse', 'HEAD').decode().strip(), files=len(pins),
             evidence='committed blobs; sacr_pilot_panel unit tests PASS; encode/rank path identical to B0 runner functions'),
         'isolation': dict(base, gate='isolation', evidence='supervisor config test PASS: read-only inputs, no qrels/evaluation mounts, network none'),
         'runtime': dict(base, gate='runtime', evidence='read-only remote preflight: all inputs present, B0 rankings and native decisions hashes pinned, 20 non-empty candidates'),
         'resources': dict(base, gate='resources', live_admission_required=True, gpu_remaining_seconds=after['gpu_remaining_seconds'],
             fidelity_remaining_seconds=after['fidelity_generation_remaining_seconds'], disk_preexisting_upper_bound_bytes=DISK_PRIOR),
         'accounting': dict(base, gate='accounting', ledger_sha256=ledger_sha, cpu_remaining_seconds=cpu_cap(cpu) - cpu_used(cpu),
             gpu_stage_host_cpu='TELEMETRY_NOT_CHARGED_TO_CPU_CAP')}
d = {'attempt_id': NAME, 'stage': 'pilot', 'retry': False, 'maximum_calls': 1, 'generation_calls': 0, 'seconds': 1800,
     'cpu_seconds': 1860, 'cpu_charge_basis': 'GPU_STAGE_SAFETY_BOUND_TELEMETRY_ONLY', 'additional_disk_bytes': 256*1024**2,
     'disk_preexisting_upper_bound_bytes': DISK_PRIOR, 'package_sha256': package_sha, 'files_sha256': pins,
     'configuration_sha256': config_sha, 'input_manifest_sha256': PIN['pilot'], 'decisions_sha256': PIN['decisions'],
     'b0_rankings_sha256': PIN['b0'], 'model_sha256': pins[IDENT], 'predecessor_attempt_id': 'ptp-auto-native-sacr-pilot20-20261112-v5',
     'operation_sha256': document_hash(operation), 'gate_receipts': {k: document_hash(v) for k, v in gates.items()}}
raw = json.dumps(d, indent=2).encode() + b'\n'
for n, v in (('configuration.json', configuration), ('gates.json', gates), ('operation.json', operation)): (S/n).write_text(json.dumps(v, indent=2) + '\n')
(S/'declaration.json').write_bytes(raw)
files = {'code/' + n: b for n, b in blobs.items()}
files.update({n: blobs['scripts/healthtech/' + n] for n in ('supervise_sacr_pilot_retrieval.py', 'supervise_sacr_r5_engine.py', 'r3_engine_client.py')})
files.update({'dispatch/declaration.json': raw, 'dispatch/gates.json': (S/'gates.json').read_bytes()})
transport = stage(NAME, files)
amendment = {'kind': 'AUTHORITY_AMENDMENT', 'owner_approval_sha256': sha((A/'owner-cpu-amendment-2.json').read_bytes()),
             'evidence_sha256': sha((A/'native-sacr-pilot20-v5'/'native-result.json').read_bytes()), 'add_configuration_sha256': [config_sha],
             'additional_synthetic_attempts': 0, 'round': 'pilot', 'authority_sha256': h['authority_sha256'], 'ledger_sha256': ledger_sha,
             'scope_sha256': None, 'reason': 'owner: continue native SACR; pilot retrieval per NATIVE-STAGES addendum (frozen before scores)'}
res = journal(JOB + '/code/src', "from patent_to_pilot.research.automatic_dispatch_journal import AutomaticDispatchJournal\n"
    "am=json.loads(" + repr(json.dumps(amendment)) + ")\nd=json.loads(" + repr(json.dumps(d)) + ")\n"
    "h,at=head();am['scope_sha256']=document_hash(json.loads(h[3]))\nassert h[1]==" + str(gen) + "\n"
    "j=AutomaticDispatchJournal(path,'" + IDENTITY + "')\n"
    "j.amend_authority(expected_generation=" + str(gen) + ",receipt=am,receipt_sha256=document_hash(am))\n"
    "h,at=head();scope=json.loads(h[3])\n"
    "q={'declaration':d,'authority_sha256':am['authority_sha256'],'ledger_sha256':document_hash(json.loads(h[2])),'scope_sha256':document_hash(scope)}\n"
    "j.qualify_stage(expected_generation=" + str(gen + 1) + ",receipt=q,receipt_sha256=document_hash(q))\n"
    "h,at=head()\nassert h[1]==" + str(gen + 2) + " and h[4] is None\n"
    "print(json.dumps({'generation':h[1],'ledger_sha256':document_hash(json.loads(h[2])),'amendment':am,'qualification':q}))\n")
assert res['ledger_sha256'] == ledger_sha
(S/'authority-amendment.json').write_text(json.dumps(res['amendment'], indent=2) + '\n')
(S/'qualification-receipt.json').write_text(json.dumps(res['qualification'], indent=2) + '\n')
summary = {'status': 'STAGED_QUALIFIED_NOT_LAUNCHED', 'job': NAME, 'declaration_sha256': sha(raw), 'package_sha256': package_sha,
           'configuration_sha256': config_sha, 'transport': transport, 'journal_generation': res['generation'], 'ledger_sha256': ledger_sha,
           'segment26_seconds': seg['conservative_cpu_seconds'], 'cpu_remaining_seconds': gates['accounting']['cpu_remaining_seconds']}
(S/'freeze-summary.json').write_text(json.dumps(summary, indent=2) + '\n'); print(json.dumps(summary))
