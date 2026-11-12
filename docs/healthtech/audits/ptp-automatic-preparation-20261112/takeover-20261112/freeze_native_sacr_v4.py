"""Freeze native SACR fidelity on the frozen pilot-20 ONCE (no launch). NATIVE-STAGES-20261112.
Query texts never leave the remote: the pilot file is built there and only its hash returns."""
import copy, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from takeover_lib import *
from patent_to_pilot.research.r6_dispatch_files import package_identity
from patent_to_pilot.research.automatic_cpu_booking import cpu_used, cpu_cap
from patent_to_pilot.research.patent_structure_marking import VERSION
from patent_to_pilot.research.km_automatic_review import VERSION as REVIEW_VERSION, CHECKS
NAME = 'ptp-auto-native-sacr-pilot20-20261112-v4'; S = A/'native-sacr-pilot20-v4'; S.mkdir(exist_ok=False)
JOB = JOBS + '/' + NAME; CODE = JOBS + '/ptp-auto-native-fixture-20261112-v5/code/src'
DECODER = '20232bca268d86c6e4bad73eb53be74c881ad06e004eb0aaa6ddb5af831368ae'
DISK_PRIOR = 31162801647 + 20*16*1024**2 + 5*256*1024**2 + 3*512*1024**2  # + 2 CPU jobs + native v1-v3 declared
PILOT_SRC = JOBS + '/ptp-auto-graph-extractor-v3-20261112-v1/out/attempt/private.json'
PILOT_SHA = json.loads((A/'graph-extractor-v3'/'graph-extractor-v3-result.json').read_bytes())['pilot_ids_sha256']
QUERIES = JOBS + '/ptp-native-baseline-20261110-v1/runtime-dev/queries-ta.jsonl'
assert VERSION == 'patent-structure-marking-v5' and REVIEW_VERSION == 'km-automatic-review-v2'
ledger = json.loads(L.read_bytes()); lsha = document_hash(ledger)
h = journal(CODE, "h,at=head()\nscope=json.loads(h[3])\nprint(json.dumps({'generation':h[1],'ledger_sha256':document_hash(json.loads(h[2])),'active':h[4],"
                  "'scope_sha256':document_hash(scope),'authority_sha256':scope['automatic_study']['authority_sha256'],"
                  "'v5':scope['automatic_study']['stage_costs'].get('ptp-auto-synthetic-20261112-v5')}))\n")
assert h['active'] is None and h['ledger_sha256'] == lsha and h['v5']['calls_complete'] is True, h
# Private pilot file built remotely (job dir must not exist yet; built in a staging subdir after stage()).
blobs, pins = package(['run_automatic_native.py', 'supervise_automatic_native.py', 'run_automatic_synthetic.py', 'supervise_automatic_synthetic.py'])
package_sha = package_identity(pins)
seg = segment_booking(23, lsha)
after = copy.deepcopy(ledger); after['r6_phase0_cpu']['local_cpu_conservative_charged_seconds'] += seg['conservative_cpu_seconds']
(S/'segment23-booking.json').write_text(json.dumps(seg, indent=2) + '\n')
out = book(CODE, [seg], h['generation']); assert document_hash(out['ledger']) == document_hash(after); write_ledger(out['ledger'])
ledger_sha = document_hash(after); gen = h['generation'] + 1
files = {'code/' + n: b for n, b in blobs.items()}
files.update({n: blobs['scripts/healthtech/' + n] for n in ('supervise_automatic_native.py', 'supervise_sacr_r5_engine.py', 'r3_engine_client.py')})
transport = stage(NAME, files)
built = ssh(f"""import json,hashlib
from pathlib import Path
ids=json.loads(Path('{PILOT_SRC}').read_bytes())['pilot_ids']
assert hashlib.sha256(json.dumps(ids).encode()).hexdigest()=='{PILOT_SHA}' and len(ids)==20
rows={{}}
for line in Path('{QUERIES}').read_text(encoding='utf-8').splitlines():
    if line.strip():
        q=json.loads(line)
        if q['id'] in ids: rows[q['id']]=q['text']
assert len(rows)==20
d=Path('{JOB}')/'dispatch';d.mkdir()
raw=''.join(json.dumps({{'id':i,'text':rows[i]}},ensure_ascii=False)+'\\n' for i in ids).encode()
(d/'queries.jsonl').write_bytes(raw)
print(json.dumps({{'sha256':hashlib.sha256(raw).hexdigest(),'queries':len(ids)}}))
""")
configuration = {'stage': 'fidelity', 'track': 'SACR', 'marking_version': VERSION, 'review_version': REVIEW_VERSION,
                 'review_checks': list(CHECKS), 'km_sha256': pins[KM], 'decoder_sha256': DECODER, 'max_new_tokens': 4096,
                 'dtype': 'float16', 'attention': 'eager', 'greedy': True, 'maximum_calls_per_query': 2,
                 'container': {'nano_cpus': 1, 'memory_bytes': 31*1024**3, 'network': 'none', 'gpu': 'single approved UUID'},
                 'fallback': 'original query on rejection/flag/uncertain/abstain; HOLD on unknown backend state',
                 'semantic_certification': False, 'human_review_required': False, 'protocol': 'NATIVE-STAGES-20261112',
                 'input_token_cap': 5800, 'max_consecutive_whitespaces': 48, 'force_json_field_order': True,
                 'revision': 'native v4: declared JSON field order (v3 review guard refusal); whitespace cap 48, marking v5, cap 5800 unchanged'}
config_sha = document_hash(configuration)
operation = {'stage': 'fidelity', 'track': 'SACR', 'input_sha256': built['sha256'], 'configuration_sha256': config_sha, 'package_sha256': package_sha}
cpu = after['r6_phase0_cpu']
base = {'status': 'PASS', 'package_sha256': package_sha, 'configuration_sha256': config_sha}
results = {'fixture': sha((A/'cpu-v8'/'fixture-terminal-observation.json').read_bytes()),
           'v5': sha((A/'synthetic-v5-job'/'synthetic-result.json').read_bytes())}
gates = {'integrity': dict(base, gate='integrity', source_commit=git('rev-parse', 'HEAD').decode().strip(), files=len(pins),
             evidence='committed blobs; CPU v8 PASS: grammar 11/11 incl. key-order violation and whitespace runaway rejected; native fixture v5 PASS', fixture_sha256=results['fixture']),
         'isolation': dict(base, gate='isolation', evidence='supervisor config tests PASS; supervisor re-validates isolation before start'),
         'runtime': dict(base, gate='runtime', synthetic_v5_sha256=results['v5'], decoder_sha256=DECODER,
             evidence='synthetic v5: marking v4 + review v2 valid end-to-end on this GPU'),
         'resources': dict(base, gate='resources', live_admission_required=True, gpu_remaining_seconds=after['gpu_remaining_seconds'],
             fidelity_remaining_seconds=after['fidelity_generation_remaining_seconds'], disk_preexisting_upper_bound_bytes=DISK_PRIOR),
         'accounting': dict(base, gate='accounting', ledger_sha256=ledger_sha, cpu_remaining_seconds=cpu_cap(cpu) - cpu_used(cpu),
             gpu_stage_host_cpu='TELEMETRY_NOT_CHARGED_TO_CPU_CAP')}
d = {'attempt_id': NAME, 'stage': 'fidelity', 'retry': False, 'queries': 20, 'maximum_calls': 40, 'seconds': 3600, 'input_token_cap': 5800, 'max_consecutive_whitespaces': 48, 'force_json_field_order': True,
     'cpu_seconds': 3660, 'cpu_charge_basis': 'GPU_STAGE_SAFETY_BOUND_TELEMETRY_ONLY', 'additional_disk_bytes': 512*1024**2,
     'disk_preexisting_upper_bound_bytes': DISK_PRIOR, 'package_sha256': package_sha, 'files_sha256': pins,
     'configuration_sha256': config_sha, 'input_manifest_sha256': built['sha256'], 'km_sha256': pins[KM], 'model_sha256': pins[IDENT],
     'tokenizer_sha256': 'aeb13307a71acd8fe81861d94ad54ab689df773318809eed3cbe794b4492dae4', 'decoder_sha256': DECODER,
     'lmfe_source_sha256': json.loads((R/'docs/healthtech/audits/ptp-r6-phase0-execution-20261111/critic-declaration.json').read_bytes())['lmfe_source_sha256'],
     'predecessor_attempt_id': 'ptp-auto-synthetic-20261112-v5', 'operation_sha256': document_hash(operation),
     'gate_receipts': {k: document_hash(v) for k, v in gates.items()}}
raw = json.dumps(d, indent=2).encode() + b'\n'
for n, v in (('configuration.json', configuration), ('gates.json', gates), ('operation.json', operation)): (S/n).write_text(json.dumps(v, indent=2) + '\n')
(S/'declaration.json').write_bytes(raw)
ssh(f"""import hashlib
from pathlib import Path
d=Path('{JOB}')/'dispatch'
(d/'declaration.json').write_bytes({raw!r});(d/'gates.json').write_bytes({(S/'gates.json').read_bytes()!r})
assert hashlib.sha256((d/'declaration.json').read_bytes()).hexdigest()=='{sha(raw)}'
print('{{}}')
""")
amendment = {'kind': 'AUTHORITY_AMENDMENT', 'owner_approval_sha256': sha((A/'owner-native-v3-approval.json').read_bytes()),
             'evidence_sha256': sha((A/'native-sacr-pilot20-v3'/'native-result.json').read_bytes()), 'add_configuration_sha256': [config_sha], 'additional_synthetic_attempts': 0,
             'round': 'native-v4',
             'authority_sha256': h['authority_sha256'], 'ledger_sha256': ledger_sha, 'scope_sha256': None,
             'reason': 'standing owner allowance revision 1 of 2: declared JSON field order after v3 review guard refusal'}
code2 = JOB + '/code/src'
res = journal(code2, "from patent_to_pilot.research.automatic_dispatch_journal import AutomaticDispatchJournal\n"
    "am=json.loads(" + repr(json.dumps(amendment)) + ")\nd=json.loads(" + repr(json.dumps(d)) + ")\n"
    "h,at=head();am['scope_sha256']=document_hash(json.loads(h[3]))\nassert h[1]==" + str(gen) + "\n"
    "j=AutomaticDispatchJournal(path,'" + IDENTITY + "')\n"
    "j.amend_authority(expected_generation=" + str(gen) + ",receipt=am,receipt_sha256=document_hash(am))\n"
    "h,at=head();scope=json.loads(h[3])\n"
    "q={'declaration':d,'authority_sha256':am['authority_sha256'],'ledger_sha256':document_hash(json.loads(h[2])),'scope_sha256':document_hash(scope)}\n"
    "j.qualify_stage(expected_generation=" + str(gen + 1) + ",receipt=q,receipt_sha256=document_hash(q))\n"
    "h,at=head();scope=json.loads(h[3])\nassert h[1]==" + str(gen + 2) + " and h[4] is None\n"
    "print(json.dumps({'generation':h[1],'ledger_sha256':document_hash(json.loads(h[2])),'amendment':am,'qualification':q}))\n")
assert res['ledger_sha256'] == ledger_sha
(S/'authority-amendment.json').write_text(json.dumps(res['amendment'], indent=2) + '\n')
(S/'qualification-receipt.json').write_text(json.dumps(res['qualification'], indent=2) + '\n')
summary = {'status': 'STAGED_QUALIFIED_NOT_LAUNCHED', 'job': NAME, 'declaration_sha256': sha(raw), 'package_sha256': package_sha,
           'configuration_sha256': config_sha, 'input_sha256': built['sha256'], 'transport': transport, 'journal_generation': res['generation'],
           'ledger_sha256': ledger_sha, 'segment23_seconds': seg['conservative_cpu_seconds'], 'cpu_remaining_seconds': gates['accounting']['cpu_remaining_seconds']}
(S/'freeze-summary.json').write_text(json.dumps(summary, indent=2) + '\n'); print(json.dumps(summary))
