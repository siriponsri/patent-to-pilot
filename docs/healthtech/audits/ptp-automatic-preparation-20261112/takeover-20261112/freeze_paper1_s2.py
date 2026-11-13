"""Paper 1 S2: freeze ONE synthetic GPU smoke for an arm (FA|GR) ONCE (no launch).

FA run: segment booking, stage, append-only authority amendment (round 'paper1': both FA and GR configurations,
2 synthetic attempts; owner freeze approval), qualify_stage. GR run (after FA is settled): segment booking,
stage, qualify_stage only. The ledger must not change between this freeze and the claim.
"""
import copy, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from takeover_lib import *
from patent_to_pilot.research.r6_dispatch_files import package_identity
from patent_to_pilot.research.automatic_cpu_booking import cpu_used, cpu_cap
from patent_to_pilot.research import paper1_rewrite_arms as arms

ARM = sys.argv[1]; assert ARM in ('FA', 'GR')
SEG = {'FA': 32, 'GR': 33}[ARM]
NAME = 'ptp-auto-paper1-%s-synthetic-20261113-v1' % ARM.lower(); S = A/('paper1-s2-' + ARM.lower()); S.mkdir(exist_ok=False)
JOB = JOBS + '/' + NAME; CODE = JOBS + '/ptp-auto-native-sacr-fulldev-b1-20261113-v1/code/src'
FREEZE = json.loads((A/'paper1-freeze/freeze-manifest.json').read_bytes())
RT = FREEZE['generation_runtime']
# Prior upper bound (pilot retrieval declaration) + its 256 MiB + 8 CPU-sized jobs since (eval, fulldev-b1 staging, S1, fixtures).
DISK_PRIOR = 35591986671 + 256*1024**2 + 8*16*1024**2 + (512*1024**2 if ARM == 'GR' else 0)


def configuration(arm):
    return {'stage': 'synthetic', 'track': 'PAPER1_' + arm, 'protocol': 'PAPER1-ACQUISITION-PROTOCOL (frozen 2026-11-13)',
            'paper1_freeze_manifest_sha256': sha((A/'paper1-freeze/freeze-manifest.json').read_bytes()),
            'arm': FREEZE['arms'][arm], 'decoder_sha256': RT['decoder_sha256'], 'max_new_tokens': 4096, 'dtype': 'float16',
            'attention': 'eager', 'greedy': True, 'maximum_calls_per_query': 1, 'input_token_cap': RT['input_token_cap'],
            'max_consecutive_whitespaces': RT['max_consecutive_whitespaces'], 'force_json_field_order': RT['force_json_field_order'],
            'container': {'nano_cpus': 1, 'memory_bytes': 31*1024**3, 'network': 'none', 'gpu': 'single approved UUID'},
            'fallback': 'original query on input cap / output limit / schema or blank rejection; HOLD on unknown backend state',
            'semantic_certification': False}


ledger = json.loads(L.read_bytes()); lsha = document_hash(ledger)
h = journal(CODE, "h,at=head()\nscope=json.loads(h[3]);st=scope['automatic_study']\nprint(json.dumps({'generation':h[1],'ledger_sha256':document_hash(json.loads(h[2])),'active':h[4],"
                  "'status':st['status'],'authority_sha256':st['authority_sha256'],'fa':st['stage_costs'].get('ptp-auto-paper1-fa-synthetic-20261113-v1')}))\n")
assert h['active'] is None and h['ledger_sha256'] == lsha and h['status'] == 'IDLE', h
if ARM == 'GR': assert h['fa'] is not None, 'FA smoke must be settled before GR is frozen'
blobs, pins = package(['run_paper1_rewrite.py', 'supervise_paper1_rewrite.py'])
package_sha = package_identity(pins)
for f in ('src/patent_to_pilot/research/paper1_rewrite_arms.py', 'src/patent_to_pilot/research/r6_backend.py'):
    assert pins[f] == FREEZE['files_sha256'][f], 'frozen file changed: ' + f
seg = segment_booking(SEG, lsha)
after = copy.deepcopy(ledger); after['r6_phase0_cpu']['local_cpu_conservative_charged_seconds'] += seg['conservative_cpu_seconds']
(S/('segment%d-booking.json' % SEG)).write_text(json.dumps(seg, indent=2) + '\n')
out = book(CODE, [seg], h['generation']); assert document_hash(out['ledger']) == document_hash(after); write_ledger(out['ledger'])
ledger_sha = document_hash(after); gen = h['generation'] + 1
task_obj = json.loads((A/'synthetic-job/task.json').read_bytes())
task = (json.dumps({'id': 'synthetic-paper1-%s-001' % ARM.lower(), 'text': task_obj['source']}, ensure_ascii=False) + '\n').encode()
config = configuration(ARM); config_sha = document_hash(config)
operation = {'stage': 'synthetic', 'arm': ARM, 'task_sha256': sha(task), 'configuration_sha256': config_sha, 'package_sha256': package_sha}
results = {'s1': sha((A/'paper1-s1/s1-result.json').read_bytes()), 'fixture': sha((A/'paper1-fixture-v2/fixture-v2-result.json').read_bytes())}
cpu = after['r6_phase0_cpu']
base = {'status': 'PASS', 'package_sha256': package_sha, 'configuration_sha256': config_sha}
gates = {'integrity': dict(base, gate='integrity', source_commit=git('rev-parse', 'HEAD').decode().strip(), files=len(pins),
             evidence='committed blobs; frozen FA/GR files match the Paper 1 freeze manifest; fixture v2 PASS', fixture_sha256=results['fixture']),
         'isolation': dict(base, gate='isolation', evidence='supervisor derived from native controller; re-validates isolation before start'),
         'runtime': dict(base, gate='runtime', s1_sha256=results['s1'], decoder_sha256=RT['decoder_sha256'],
             evidence='S1 FA/GR grammar 13/13 PASS on the real tokenizer; same model/decoder as native SACR v5 on this GPU'),
         'resources': dict(base, gate='resources', live_admission_required=True, gpu_remaining_seconds=after['gpu_remaining_seconds'],
             fidelity_remaining_seconds=after['fidelity_generation_remaining_seconds'], disk_preexisting_upper_bound_bytes=DISK_PRIOR),
         'accounting': dict(base, gate='accounting', ledger_sha256=ledger_sha, cpu_remaining_seconds=cpu_cap(cpu) - cpu_used(cpu),
             gpu_stage_host_cpu='TELEMETRY_NOT_CHARGED_TO_CPU_CAP')}
d = {'attempt_id': NAME, 'arm': ARM, 'stage': 'synthetic', 'retry': False, 'queries': 1, 'maximum_calls': 1, 'seconds': 1800,
     'input_token_cap': RT['input_token_cap'], 'max_consecutive_whitespaces': RT['max_consecutive_whitespaces'],
     'force_json_field_order': RT['force_json_field_order'], 'cpu_seconds': 1860, 'cpu_charge_basis': 'GPU_STAGE_SAFETY_BOUND_TELEMETRY_ONLY',
     'additional_disk_bytes': 512*1024**2, 'disk_preexisting_upper_bound_bytes': DISK_PRIOR, 'package_sha256': package_sha,
     'files_sha256': pins, 'configuration_sha256': config_sha, 'input_manifest_sha256': sha(task), 'km_sha256': pins[KM],
     'model_sha256': pins[IDENT], 'tokenizer_sha256': RT['tokenizer_sha256'], 'decoder_sha256': RT['decoder_sha256'],
     'lmfe_source_sha256': RT['lmfe_source_sha256'], 'operation_sha256': document_hash(operation),
     'gate_receipts': {k: document_hash(v) for k, v in gates.items()}}
assert d['model_sha256'] == RT['model_sha256']
raw = json.dumps(d, indent=2).encode() + b'\n'
for n, v in (('configuration.json', config), ('gates.json', gates), ('operation.json', operation)): (S/n).write_text(json.dumps(v, indent=2) + '\n')
(S/'declaration.json').write_bytes(raw); (S/'queries.jsonl').write_bytes(task)
files = {'code/' + n: b for n, b in blobs.items()}
files.update({n: blobs['scripts/healthtech/' + n] for n in ('supervise_paper1_rewrite.py', 'supervise_sacr_r5_engine.py', 'r3_engine_client.py')})
files.update({'dispatch/declaration.json': raw, 'dispatch/queries.jsonl': task, 'dispatch/gates.json': (S/'gates.json').read_bytes()})
transport = stage(NAME, files)
code2 = JOB + '/code/src'
body = "from patent_to_pilot.research.automatic_dispatch_journal import AutomaticDispatchJournal\nd=json.loads(" + repr(json.dumps(d)) + ")\n"
body += "j=AutomaticDispatchJournal(path,'" + IDENTITY + "')\nh,at=head();assert h[1]==" + str(gen) + "\nam=None\n"
if ARM == 'FA':
    amendment = {'kind': 'AUTHORITY_AMENDMENT', 'owner_approval_sha256': sha((A/'owner-paper1-freeze-approval.json').read_bytes()),
                 'evidence_sha256': results['fixture'], 'add_configuration_sha256': [document_hash(configuration('FA')), document_hash(configuration('GR'))],
                 'additional_synthetic_attempts': 2, 'round': 'paper1', 'authority_sha256': h['authority_sha256'], 'ledger_sha256': ledger_sha,
                 'scope_sha256': None, 'reason': 'Paper 1 frozen protocol S2: one synthetic smoke each for FA and GR'}
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
summary = {'status': 'STAGED_QUALIFIED_NOT_LAUNCHED', 'job': NAME, 'arm': ARM, 'supervisor': 'supervise_paper1_rewrite.py',
           'declaration_sha256': sha(raw), 'package_sha256': package_sha, 'configuration_sha256': config_sha, 'transport': transport,
           'journal_generation': res['generation'], 'ledger_sha256': ledger_sha, 'study_status': res['status'],
           'segment_seconds': seg['conservative_cpu_seconds'], 'cpu_remaining_seconds': gates['accounting']['cpu_remaining_seconds']}
(S/'freeze-summary.json').write_text(json.dumps(summary, indent=2) + '\n'); print(json.dumps(summary))
