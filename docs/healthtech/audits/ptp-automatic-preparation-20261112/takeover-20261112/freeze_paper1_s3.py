"""Paper 1 S3: freeze ONE pilot-20 technical run (journal stage 'fidelity') for an arm (FA|GR) ONCE (no launch).

Throughput/failure only; not evaluated separately (frozen protocol section 7). The pilot-20 file is copied on the
remote from the settled native SACR v5 job (sha b5d837f4...); query texts never leave the remote.
FA run: segment booking, stage, append-only authority amendment (round 'paper1-s3': FA and GR fidelity
configurations, 0 synthetic attempts; owner freeze approval), qualify_stage. GR run (after FA is settled):
segment booking, stage, qualify_stage only. The ledger must not change between this freeze and the claim.
"""
import copy, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from takeover_lib import *
from patent_to_pilot.research.r6_dispatch_files import package_identity
from patent_to_pilot.research.automatic_cpu_booking import cpu_used, cpu_cap

ARM = sys.argv[1]; assert ARM in ('FA', 'GR')
SEG = {'FA': 34, 'GR': 35}[ARM]
NAME = 'ptp-auto-paper1-%s-pilot20-20261113-v1' % ARM.lower(); S = A/('paper1-s3-' + ARM.lower()); S.mkdir(exist_ok=False)
PRED = 'ptp-auto-paper1-%s-synthetic-20261113-v1' % ARM.lower()
FA_JOB = 'ptp-auto-paper1-fa-pilot20-20261113-v1'
JOB = JOBS + '/' + NAME; CODE = JOBS + '/ptp-auto-paper1-gr-synthetic-20261113-v1/code/src'
PILOT = JOBS + '/ptp-auto-native-sacr-pilot20-20261112-v5/dispatch/queries.jsonl'
PILOT_SHA = json.loads((A/'native-sacr-pilot20-v5/freeze-summary.json').read_bytes())['input_sha256']
assert PILOT_SHA.startswith('b5d837f4')
FREEZE = json.loads((A/'paper1-freeze/freeze-manifest.json').read_bytes())
RT = FREEZE['generation_runtime']
# S2 GR declared upper bound + its 512 MiB (+ FA pilot-20's 512 MiB for the GR run).
DISK_PRIOR = 35591986671 + 256*1024**2 + 8*16*1024**2 + 2*512*1024**2 + (512*1024**2 if ARM == 'GR' else 0)


def configuration(arm):
    return {'stage': 'fidelity', 'track': 'PAPER1_' + arm, 'protocol': 'PAPER1-ACQUISITION-PROTOCOL (frozen 2026-11-13) S3 technical pilot',
            'paper1_freeze_manifest_sha256': sha((A/'paper1-freeze/freeze-manifest.json').read_bytes()),
            'arm': FREEZE['arms'][arm], 'decoder_sha256': RT['decoder_sha256'], 'max_new_tokens': 4096, 'dtype': 'float16',
            'attention': 'eager', 'greedy': True, 'maximum_calls_per_query': 1, 'input_token_cap': RT['input_token_cap'],
            'max_consecutive_whitespaces': RT['max_consecutive_whitespaces'], 'force_json_field_order': RT['force_json_field_order'],
            'container': {'nano_cpus': 1, 'memory_bytes': 31*1024**3, 'network': 'none', 'gpu': 'single approved UUID'},
            'fallback': 'original query on input cap / output limit / schema or blank rejection; HOLD on unknown backend state',
            'semantic_certification': False}


ledger = json.loads(L.read_bytes()); lsha = document_hash(ledger)
h = journal(CODE, "h,at=head()\nscope=json.loads(h[3]);st=scope['automatic_study']\nprint(json.dumps({'generation':h[1],'ledger_sha256':document_hash(json.loads(h[2])),'active':h[4],"
                  "'status':st['status'],'authority_sha256':st['authority_sha256'],'pred':st['stage_costs'].get('" + PRED + "'),"
                  "'fa':st['stage_costs'].get('" + FA_JOB + "')}))\n")
assert h['active'] is None and h['ledger_sha256'] == lsha and h['status'] == 'IDLE', h
assert h['pred'] and h['pred']['stage'] == 'synthetic' and h['pred']['calls_complete'] is True, h
if ARM == 'GR': assert h['fa'] is not None, 'FA pilot-20 must be settled before GR is frozen'
blobs, pins = package(['run_paper1_rewrite.py', 'supervise_paper1_rewrite.py'])
package_sha = package_identity(pins)
for f in ('src/patent_to_pilot/research/paper1_rewrite_arms.py', 'src/patent_to_pilot/research/r6_backend.py'):
    assert pins[f] == FREEZE['files_sha256'][f], 'frozen file changed: ' + f
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
raw=Path('{PILOT}').read_bytes()
assert hashlib.sha256(raw).hexdigest()=='{PILOT_SHA}'
rows=[json.loads(x) for x in raw.decode().splitlines() if x.strip()]
assert len(rows)==20 and all(set(r)=={{'id','text'}} for r in rows) and len({{r['id'] for r in rows}})==20
d=Path('{JOB}')/'dispatch';d.mkdir()
(d/'queries.jsonl').write_bytes(raw)
print(json.dumps({{'sha256':hashlib.sha256((d/'queries.jsonl').read_bytes()).hexdigest(),'queries':len(rows)}}))
""")
assert built == {'sha256': PILOT_SHA, 'queries': 20}, built
config = configuration(ARM); config_sha = document_hash(config)
operation = {'stage': 'fidelity', 'arm': ARM, 'input_sha256': PILOT_SHA, 'configuration_sha256': config_sha, 'package_sha256': package_sha}
results = {'s2': sha((A/'PAPER1-S2-SUMMARY.json').read_bytes()), 'fixture': sha((A/'paper1-fixture-v2/fixture-v2-result.json').read_bytes()),
           'pred': sha((A/('paper1-s2-' + ARM.lower())/'settlement.json').read_bytes())}
cpu = after['r6_phase0_cpu']
base = {'status': 'PASS', 'package_sha256': package_sha, 'configuration_sha256': config_sha}
gates = {'integrity': dict(base, gate='integrity', source_commit=git('rev-parse', 'HEAD').decode().strip(), files=len(pins),
             evidence='committed blobs; frozen FA/GR files match the Paper 1 freeze manifest; fixture v2 PASS; supervisor change = job-name allowlist only',
             fixture_sha256=results['fixture']),
         'isolation': dict(base, gate='isolation', evidence='supervisor derived from native controller; re-validates isolation before start'),
         'runtime': dict(base, gate='runtime', s2_summary_sha256=results['s2'], predecessor_settlement_sha256=results['pred'],
             decoder_sha256=RT['decoder_sha256'], evidence='S2 synthetic smoke of this arm: exit 0, 1 call, REWRITE_VALIDATED on this GPU'),
         'resources': dict(base, gate='resources', live_admission_required=True, gpu_remaining_seconds=after['gpu_remaining_seconds'],
             fidelity_remaining_seconds=after['fidelity_generation_remaining_seconds'], disk_preexisting_upper_bound_bytes=DISK_PRIOR),
         'accounting': dict(base, gate='accounting', ledger_sha256=ledger_sha, cpu_remaining_seconds=cpu_cap(cpu) - cpu_used(cpu),
             gpu_stage_host_cpu='TELEMETRY_NOT_CHARGED_TO_CPU_CAP')}
d = {'attempt_id': NAME, 'arm': ARM, 'stage': 'fidelity', 'retry': False, 'queries': 20, 'maximum_calls': 20, 'seconds': 3600,
     'input_token_cap': RT['input_token_cap'], 'max_consecutive_whitespaces': RT['max_consecutive_whitespaces'],
     'force_json_field_order': RT['force_json_field_order'], 'cpu_seconds': 3660, 'cpu_charge_basis': 'GPU_STAGE_SAFETY_BOUND_TELEMETRY_ONLY',
     'additional_disk_bytes': 512*1024**2, 'disk_preexisting_upper_bound_bytes': DISK_PRIOR, 'package_sha256': package_sha,
     'files_sha256': pins, 'configuration_sha256': config_sha, 'input_manifest_sha256': PILOT_SHA, 'km_sha256': pins[KM],
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
if ARM == 'FA':
    amendment = {'kind': 'AUTHORITY_AMENDMENT', 'owner_approval_sha256': sha((A/'owner-paper1-freeze-approval.json').read_bytes()),
                 'evidence_sha256': results['s2'], 'add_configuration_sha256': [document_hash(configuration('FA')), document_hash(configuration('GR'))],
                 'additional_synthetic_attempts': 0, 'round': 'paper1-s3', 'authority_sha256': h['authority_sha256'], 'ledger_sha256': ledger_sha,
                 'scope_sha256': None, 'reason': 'Paper 1 frozen protocol S3: pilot-20 technical run (stage fidelity) for FA and GR'}
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
           'declaration_sha256': sha(raw), 'package_sha256': package_sha, 'configuration_sha256': config_sha, 'input_sha256': PILOT_SHA,
           'transport': transport, 'journal_generation': res['generation'], 'ledger_sha256': ledger_sha, 'study_status': res['status'],
           'segment_seconds': seg['conservative_cpu_seconds'], 'cpu_remaining_seconds': gates['accounting']['cpu_remaining_seconds']}
(S/'freeze-summary.json').write_text(json.dumps(summary, indent=2) + '\n'); print(json.dumps(summary))
