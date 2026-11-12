"""Freeze SACR full-dev batch b (1..6) ONCE (no launch). 474 dev queries in file order, 79 per batch.
Configuration identical to native v5 except stage=full_dev. Batch 1 also initializes full-dev accounting
and appends the full_dev envelope + configuration (owner: 'Proceed with both')."""
import copy, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from takeover_lib import *
from patent_to_pilot.research.r6_dispatch_files import package_identity
from patent_to_pilot.research.automatic_cpu_booking import cpu_used, cpu_cap
from patent_to_pilot.research.patent_structure_marking import VERSION
from patent_to_pilot.research.km_automatic_review import VERSION as REVIEW_VERSION, CHECKS
B = int(sys.argv[1]); assert 1 <= B <= 6
NAME = 'ptp-auto-native-sacr-fulldev-b%d-20261113-v1' % B; S = A/'fulldev'/('b%d' % B); S.mkdir(parents=True, exist_ok=False)
JOB = JOBS + '/' + NAME; CODE0 = JOBS + '/ptp-auto-sacr-pilot-retrieval-20261113-v1/code/src'
QUERIES = JOBS + '/ptp-native-baseline-20261110-v1/runtime-dev/queries-ta.jsonl'
QSHA = '6fa09d71c96b0e18f5b7986add7011d17ba6826bad753d7a0cc52a2ce5859d2a'
DECODER = '20232bca268d86c6e4bad73eb53be74c881ad06e004eb0aaa6ddb5af831368ae'
DISK_PRIOR = 31162801647 + 26*16*1024**2 + 5*256*1024**2 + 5*512*1024**2 + 256*1024**2 + (B - 1)*512*1024**2
assert VERSION == 'patent-structure-marking-v5' and REVIEW_VERSION == 'km-automatic-review-v3'
ledger = json.loads(L.read_bytes()); lsha = document_hash(ledger)
h = journal(CODE0, "h,at=head()\nscope=json.loads(h[3])\nprint(json.dumps({'generation':h[1],'ledger_sha256':document_hash(json.loads(h[2])),'active':h[4],"
                   "'authority_sha256':scope['automatic_study']['authority_sha256'],'pilot':scope['automatic_study']['stage_costs'].get('ptp-auto-sacr-pilot-retrieval-20261113-v1')}))\n")
assert h['active'] is None and h['ledger_sha256'] == lsha and h['pilot']['calls_complete'] is True, h
blobs, pins = package(['run_automatic_native.py', 'supervise_automatic_native.py', 'run_automatic_synthetic.py', 'supervise_automatic_synthetic.py'])
package_sha = package_identity(pins)
seg = segment_booking(27 + B, lsha)
after = copy.deepcopy(ledger); after['r6_phase0_cpu']['local_cpu_conservative_charged_seconds'] += seg['conservative_cpu_seconds']
(S/('segment%d-booking.json' % (27 + B))).write_text(json.dumps(seg, indent=2) + '\n')
out = book(CODE0, [seg], h['generation']); assert document_hash(out['ledger']) == document_hash(after); write_ledger(out['ledger'])
gen = h['generation'] + 1
files = {'code/' + n: b for n, b in blobs.items()}
files.update({n: blobs['scripts/healthtech/' + n] for n in ('supervise_automatic_native.py', 'supervise_sacr_r5_engine.py', 'r3_engine_client.py')})
transport = stage(NAME, files)
built = ssh(f"""import json,hashlib
from pathlib import Path
raw=Path('{QUERIES}').read_bytes();assert hashlib.sha256(raw).hexdigest()=='{QSHA}'
rows=[json.loads(l) for l in raw.decode('utf-8').splitlines() if l.strip()];assert len(rows)==474
part=rows[79*({B}-1):79*{B}];assert len(part)==79
d=Path('{JOB}')/'dispatch';d.mkdir()
data=''.join(json.dumps({{'id':r['id'],'text':r['text']}},ensure_ascii=False)+'\\n' for r in part).encode()
(d/'queries.jsonl').write_bytes(data)
print(json.dumps({{'sha256':hashlib.sha256(data).hexdigest(),'queries':len(part)}}))
""")
configuration = {'stage': 'full_dev', 'track': 'SACR', 'marking_version': VERSION, 'review_version': REVIEW_VERSION,
                 'review_checks': list(CHECKS), 'km_sha256': pins[KM], 'decoder_sha256': DECODER, 'max_new_tokens': 4096,
                 'dtype': 'float16', 'attention': 'eager', 'greedy': True, 'maximum_calls_per_query': 2,
                 'container': {'nano_cpus': 1, 'memory_bytes': 31*1024**3, 'network': 'none', 'gpu': 'single approved UUID'},
                 'fallback': 'original query on rejection/flag/uncertain/abstain; HOLD on unknown backend state',
                 'semantic_certification': False, 'human_review_required': False, 'protocol': 'NATIVE-STAGES-20261112',
                 'input_token_cap': 5800, 'max_consecutive_whitespaces': 48, 'force_json_field_order': True,
                 'batching': '474 dev queries in pinned file order, 6 batches x 79', 'identical_to': 'native v5 except stage'}
config_sha = document_hash(configuration)
operation = {'stage': 'full_dev', 'track': 'SACR', 'batch': B, 'input_sha256': built['sha256'], 'configuration_sha256': config_sha, 'package_sha256': package_sha}
results = {'v5': sha((A/'native-sacr-pilot20-v5'/'native-result.json').read_bytes()), 'pilot': sha((A/'sacr-pilot-eval'/'pilot-summary.json').read_bytes())}
d = {'attempt_id': NAME, 'stage': 'full_dev', 'retry': False, 'queries': 79, 'maximum_calls': 158, 'seconds': 10800,
     'input_token_cap': 5800, 'max_consecutive_whitespaces': 48, 'force_json_field_order': True,
     'cpu_seconds': 10860, 'cpu_charge_basis': 'GPU_STAGE_SAFETY_BOUND_TELEMETRY_ONLY', 'additional_disk_bytes': 512*1024**2,
     'disk_preexisting_upper_bound_bytes': DISK_PRIOR, 'package_sha256': package_sha, 'files_sha256': pins,
     'configuration_sha256': config_sha, 'input_manifest_sha256': built['sha256'], 'km_sha256': pins[KM], 'model_sha256': pins[IDENT],
     'tokenizer_sha256': 'aeb13307a71acd8fe81861d94ad54ab689df773318809eed3cbe794b4492dae4', 'decoder_sha256': DECODER,
     'lmfe_source_sha256': json.loads((R/'docs/healthtech/audits/ptp-r6-phase0-execution-20261111/critic-declaration.json').read_bytes())['lmfe_source_sha256'],
     'predecessor_attempt_id': 'ptp-auto-sacr-pilot-retrieval-20261113-v1', 'operation_sha256': document_hash(operation), 'batch': B}
init = {'kind': 'FULL_DEV_ACCOUNTING_INIT', 'owner_approval_sha256': sha((A/'owner-fulldev-graph-approval.json').read_bytes()),
        'evidence_sha256': results['pilot'], 'prior_ledger_sha256': None,
        'basis': 'ledger full_dev_started=false and no full_dev_charged_seconds: no full-dev stage ever ran (R5-R7 full dev NOT_RUN)'}
amendment = {'kind': 'AUTHORITY_AMENDMENT', 'owner_approval_sha256': sha((A/'owner-fulldev-graph-approval.json').read_bytes()),
             'evidence_sha256': results['pilot'], 'add_configuration_sha256': [config_sha], 'additional_synthetic_attempts': 0,
             'round': 'full-dev', 'add_stage_envelopes': {'full_dev': {'seconds': 10800, 'maximum_calls': 158}},
             'authority_sha256': h['authority_sha256'], 'ledger_sha256': None, 'scope_sha256': None,
             'reason': "owner 'Proceed with both': SACR full-dev, 6 batches x 79 queries"}
body = ("from patent_to_pilot.research.automatic_dispatch_journal import AutomaticDispatchJournal\n"
        "import copy\nd=json.loads(" + repr(json.dumps(d)) + ")\nj=AutomaticDispatchJournal(path,'" + IDENTITY + "')\n"
        "init=json.loads(" + repr(json.dumps(init)) + ")\nam=json.loads(" + repr(json.dumps(amendment)) + ")\ng=" + str(gen) + "\n")
if B == 1:
    body += ("h,at=head();assert h[1]==g\ninit['prior_ledger_sha256']=document_hash(json.loads(h[2]))\n"
             "j.initialize_full_dev_accounting(expected_generation=g,receipt=init,receipt_sha256=document_hash(init));g+=1\n"
             "h,at=head();am['ledger_sha256']=document_hash(json.loads(h[2]));am['scope_sha256']=document_hash(json.loads(h[3]))\n"
             "j.amend_authority(expected_generation=g,receipt=am,receipt_sha256=document_hash(am));g+=1\n")
body += ("h,at=head();scope=json.loads(h[3]);d['gate_receipts']={}\n"
         "led=json.loads(h[2])\n"
         "print(json.dumps({'generation':h[1],'ledger':led,'scope_sha256':document_hash(scope),'init':init,'amendment':am}))\n")
pre = journal(JOB + '/code/src', body)
ledger_now = pre['ledger']; ledger_sha = document_hash(ledger_now); write_ledger(ledger_now)
cpu = ledger_now['r6_phase0_cpu']
base = {'status': 'PASS', 'package_sha256': package_sha, 'configuration_sha256': config_sha}
gates = {'integrity': dict(base, gate='integrity', source_commit=git('rev-parse', 'HEAD').decode().strip(), files=len(pins),
             evidence='committed blobs; worker identical to native v5 except stage/caps check; native v5 complete 20/20', v5_sha256=results['v5']),
         'isolation': dict(base, gate='isolation', evidence='same supervisor/isolation as native v5; re-validated before start'),
         'runtime': dict(base, gate='runtime', evidence='native v5 + pilot retrieval technically valid', pilot_summary_sha256=results['pilot'], decoder_sha256=DECODER),
         'resources': dict(base, gate='resources', live_admission_required=True, gpu_remaining_seconds=ledger_now['gpu_remaining_seconds'],
             full_dev_charged_seconds=ledger_now['full_dev_charged_seconds'], disk_preexisting_upper_bound_bytes=DISK_PRIOR),
         'accounting': dict(base, gate='accounting', ledger_sha256=ledger_sha, cpu_remaining_seconds=cpu_cap(cpu) - cpu_used(cpu),
             gpu_stage_host_cpu='TELEMETRY_NOT_CHARGED_TO_CPU_CAP')}
d['gate_receipts'] = {k: document_hash(v) for k, v in gates.items()}
raw = json.dumps(d, indent=2).encode() + b'\n'
for n, v in (('configuration.json', configuration), ('gates.json', gates), ('operation.json', operation), ('full-dev-init.json', pre['init']),
             ('authority-amendment.json', pre['amendment'])):
    (S/n).write_text(json.dumps(v, indent=2) + '\n')
(S/'declaration.json').write_bytes(raw)
ssh(f"""from pathlib import Path
import hashlib
p=Path('{JOB}')/'dispatch'
(p/'declaration.json').write_bytes({raw!r});(p/'gates.json').write_bytes({(S/'gates.json').read_bytes()!r})
assert hashlib.sha256((p/'declaration.json').read_bytes()).hexdigest()=='{sha(raw)}'
print('{{}}')
""")
res = journal(JOB + '/code/src', "from patent_to_pilot.research.automatic_dispatch_journal import AutomaticDispatchJournal\n"
    "d=json.loads(" + repr(json.dumps(d)) + ")\nh,at=head();scope=json.loads(h[3])\nassert document_hash(json.loads(h[2]))=='" + ledger_sha + "'\n"
    "q={'declaration':d,'authority_sha256':scope['automatic_study']['authority_sha256'],'ledger_sha256':document_hash(json.loads(h[2])),'scope_sha256':document_hash(scope)}\n"
    "AutomaticDispatchJournal(path,'" + IDENTITY + "').qualify_stage(expected_generation=h[1],receipt=q,receipt_sha256=document_hash(q))\n"
    "h2,at=head();assert h2[4] is None\nprint(json.dumps({'generation':h2[1],'ledger_sha256':document_hash(json.loads(h2[2])),'qualification':q}))\n")
assert res['ledger_sha256'] == ledger_sha
(S/'qualification-receipt.json').write_text(json.dumps(res['qualification'], indent=2) + '\n')
summary = {'status': 'STAGED_QUALIFIED_NOT_LAUNCHED', 'job': NAME, 'batch': B, 'declaration_sha256': sha(raw), 'package_sha256': package_sha,
           'configuration_sha256': config_sha, 'input_sha256': built['sha256'], 'transport': transport, 'journal_generation': res['generation'],
           'ledger_sha256': ledger_sha, 'cpu_remaining_seconds': gates['accounting']['cpu_remaining_seconds']}
(S/'freeze-summary.json').write_text(json.dumps(summary, indent=2) + '\n'); print(json.dumps(summary))
