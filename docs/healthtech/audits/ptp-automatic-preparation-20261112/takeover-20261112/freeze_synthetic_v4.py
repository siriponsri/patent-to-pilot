"""Freeze synthetic GPU smoke v2 ONCE (no launch): segment-5 booking, v2 configuration
(marking schema v2), stage, append-only authority amendment (owner: max 2 revisions),
qualify_stage. Ledger is unchanged after the booking until the claim."""
import copy, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from takeover_lib import *
from patent_to_pilot.research.r6_dispatch_files import package_identity
from patent_to_pilot.research.automatic_cpu_booking import cpu_used, cpu_cap
from patent_to_pilot.research.patent_structure_marking import VERSION
from patent_to_pilot.research.km_automatic_review import CHECKS
assert VERSION == 'patent-structure-marking-v4'
NAME = 'ptp-auto-synthetic-20261112-v4'; S = A/'synthetic-v4-job'; S.mkdir(exist_ok=False)
V1 = A/'synthetic-job'
DECODER = '20232bca268d86c6e4bad73eb53be74c881ad06e004eb0aaa6ddb5af831368ae'
DISK_PRIOR = 31162801647 + 8*16*1024**2 + 3*256*1024**2  # R7 bound + 8 CPU jobs + synthetic v1-v3 declared
ledger = json.loads(L.read_bytes()); ledger_sha = document_hash(ledger)
v1code = JOBS + '/ptp-auto-synthetic-20261112-v3/code/src'
h = journal(v1code, "h,at=head()\nprint(json.dumps({'generation':h[1],'ledger_sha256':document_hash(json.loads(h[2])),'active':h[4]}))\n")
assert h['active'] is None and h['ledger_sha256'] == ledger_sha, h
seg = segment_booking(10, ledger_sha)
after = copy.deepcopy(ledger); after['r6_phase0_cpu']['local_cpu_conservative_charged_seconds'] += seg['conservative_cpu_seconds']
(S/'segment10-booking.json').write_text(json.dumps(seg, indent=2) + '\n')
out = book(v1code, [seg], h['generation']); assert document_hash(out['ledger']) == document_hash(after)
write_ledger(out['ledger']); ledger_sha = document_hash(after); gen = h['generation'] + 1

blobs, pins = package(['run_automatic_synthetic.py', 'supervise_automatic_synthetic.py'])
package_sha = package_identity(pins)
task = (V1/'task.json').read_bytes().replace(b'synthetic-auto-gpu-001', b'synthetic-auto-gpu-004')
assert json.loads(task)['query_id'] == 'synthetic-auto-gpu-004'
v1cfg = json.loads((V1/'configuration.json').read_bytes())
configuration = dict(v1cfg, marking_version=VERSION, km_sha256=pins[KM],
    revision='v4 (SACR round 2): v3 bounded labels + two authored worked examples (not the test sentence) + labelling guideline; v3 abstained on every token')
assert configuration['review_checks'] == list(CHECKS)
config_sha = document_hash(configuration)
operation = {'stage': 'synthetic', 'task_sha256': sha(task), 'configuration_sha256': config_sha, 'package_sha256': package_sha}
cpu2 = A/'cpu-v4'
results = {'grammar': sha((cpu2/'grammar-result.json').read_bytes()), 'fixture': sha((cpu2/'fixture-result.json').read_bytes())}
base = {'status': 'PASS', 'package_sha256': package_sha, 'configuration_sha256': config_sha}
gates = {
 'integrity': dict(base, gate='integrity', source_commit=git('rev-parse', 'HEAD').decode().strip(), files=len(pins),
     evidence='package from committed blobs; 137 tests PASS; actual worker main PASS in CPU fixture v4 (marking schema v4)',
     fixture_result_sha256=results['fixture']),
 'isolation': dict(base, gate='isolation', evidence='supervisor config test PASS; supervisor re-validates actual isolation before start; v1 isolation PASS_BEFORE_START'),
 'runtime': dict(base, gate='runtime', grammar_result_sha256=results['grammar'], fixture_result_sha256=results['fixture'], decoder_sha256=DECODER,
     evidence='grammar v4 rejects too-short/too-long label arrays; v2/v3 completed normal GPU marking calls on this GPU'),
 'resources': dict(base, gate='resources', live_admission_required=True, gpu_remaining_seconds=after['gpu_remaining_seconds'],
     fidelity_remaining_seconds=after['fidelity_generation_remaining_seconds'], disk_preexisting_upper_bound_bytes=DISK_PRIOR),
 'accounting': dict(base, gate='accounting', ledger_sha256=ledger_sha,
     cpu_remaining_seconds=cpu_cap(after['r6_phase0_cpu']) - cpu_used(after['r6_phase0_cpu']), gpu_stage_host_cpu='TELEMETRY_NOT_CHARGED_TO_CPU_CAP')}
v1d = json.loads((V1/'declaration.json').read_bytes())
d = dict(v1d, attempt_id=NAME, files_sha256=pins, package_sha256=package_sha, configuration_sha256=config_sha,
         input_manifest_sha256=sha(task), km_sha256=pins[KM], model_sha256=pins[IDENT], disk_preexisting_upper_bound_bytes=DISK_PRIOR,
         operation_sha256=document_hash(operation), gate_receipts={k: document_hash(v) for k, v in gates.items()})
raw = json.dumps(d, indent=2).encode() + b'\n'
for n, v in (('task.json', None), ('configuration.json', configuration), ('gates.json', gates), ('operation.json', operation)):
    (S/n).write_bytes(task if v is None else json.dumps(v, indent=2).encode() + b'\n')
(S/'declaration.json').write_bytes(raw)
files = {'code/' + n: b for n, b in blobs.items()}
files.update({n: blobs['scripts/healthtech/' + n] for n in ('supervise_automatic_synthetic.py', 'supervise_sacr_r5_engine.py', 'r3_engine_client.py')})
files.update({'dispatch/declaration.json': raw, 'dispatch/task.json': task, 'dispatch/gates.json': (S/'gates.json').read_bytes()})
transport = stage(NAME, files)
v2code = JOBS + '/' + NAME + '/code/src'
pre = journal(v2code, "h,at=head()\nscope=json.loads(h[3])\nprint(json.dumps({'generation':h[1],'scope_sha256':document_hash(scope),'authority_sha256':scope['automatic_study']['authority_sha256']}))\n")
assert pre['generation'] == gen
amendment = {'kind': 'AUTHORITY_AMENDMENT', 'owner_approval_sha256': sha((A/'owner-parallel-round2-approval.json').read_bytes()),
             'evidence_sha256': sha((A/'synthetic-v3-job'/'synthetic-result.json').read_bytes()), 'add_configuration_sha256': [config_sha],
             'additional_synthetic_attempts': 2, 'round': 'round-2', 'authority_sha256': pre['authority_sha256'], 'ledger_sha256': ledger_sha,
             'scope_sha256': pre['scope_sha256'], 'reason': 'owner approved a new SACR round (round-2) in parallel with Graph; agent default cap 2 synthetic attempts'}
(S/'authority-amendment.json').write_text(json.dumps(amendment, indent=2) + '\n')
res = journal(v2code, "from patent_to_pilot.research.automatic_dispatch_journal import AutomaticDispatchJournal\n"
    "am=json.loads(" + repr(json.dumps(amendment)) + ")\nd=json.loads(" + repr(json.dumps(d)) + ")\n"
    "j=AutomaticDispatchJournal(path,'" + IDENTITY + "')\n"
    "j.amend_authority(expected_generation=" + str(gen) + ",receipt=am,receipt_sha256=document_hash(am))\n"
    "h,at=head();scope=json.loads(h[3])\n"
    "q={'declaration':d,'authority_sha256':am['authority_sha256'],'ledger_sha256':document_hash(json.loads(h[2])),'scope_sha256':document_hash(scope)}\n"
    "j.qualify_stage(expected_generation=" + str(gen + 1) + ",receipt=q,receipt_sha256=document_hash(q))\n"
    "h,at=head();scope=json.loads(h[3])\nassert h[1]==" + str(gen + 2) + " and h[4] is None\n"
    "print(json.dumps({'generation':h[1],'ledger_sha256':document_hash(json.loads(h[2])),'qualification':q,'qualified':sorted(scope['automatic_study']['qualified_dispatches']),'status':scope['automatic_study']['status']}))\n")
assert res['ledger_sha256'] == ledger_sha and NAME in res['qualified']
(S/'qualification-receipt.json').write_text(json.dumps(res['qualification'], indent=2) + '\n')
summary = {'status': 'STAGED_QUALIFIED_NOT_LAUNCHED', 'job': NAME, 'declaration_sha256': sha(raw), 'package_sha256': package_sha,
           'configuration_sha256': config_sha, 'transport': transport, 'journal_generation': res['generation'], 'ledger_sha256': ledger_sha,
           'study_status': res['status'], 'segment10_seconds': seg['conservative_cpu_seconds'],
           'cpu_remaining_seconds': gates['accounting']['cpu_remaining_seconds']}
(S/'freeze-summary.json').write_text(json.dumps(summary, indent=2) + '\n'); print(json.dumps(summary))
