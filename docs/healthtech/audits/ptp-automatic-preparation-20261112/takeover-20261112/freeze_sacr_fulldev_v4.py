"""Paper 1 S4 SACR full-dev after the owner extended the fallback rule to grammar dead ends ('A: ขยายกติกา',
2026-11-15): freeze ONE batch ONCE (no launch).

Items: 4d (continuation of b4c: the 35 never-started queries, dev rows 281..315; dev row 280 stays an original-query
fallback and is NOT regenerated), 5 (rows 316..394), 6 (rows 395..473). Worker: verified EOS-guard refusal ->
GRAMMAR_REFUSED, verified grammar dead end ('grammar has no continuation') -> GRAMMAR_NO_CONTINUATION, both
ORIGINAL_QUERY_FALLBACK, batch continues. Configuration v3 (new sha); the first v4 freeze appends authority amendment
round 'sacr-full-dev-dead-end'. Owner authority: owner-sacr-s4-dead-end-approval.json. Requires native fixture v8 PASS.
The ledger must not change between this freeze and the claim.
"""
import copy, json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from takeover_lib import *
from patent_to_pilot.research.r6_dispatch_files import package_identity
from patent_to_pilot.research.automatic_cpu_booking import cpu_used, cpu_cap
from patent_to_pilot.research.patent_structure_marking import VERSION
from patent_to_pilot.research.km_automatic_review import VERSION as REVIEW_VERSION, CHECKS

ITEM = sys.argv[1]; assert ITEM in ('4d', '5', '6')
ORDER = ['4d', '5', '6']
job = lambda b: 'ptp-auto-native-sacr-fulldev-b%d-20261114-v1' % b
job3 = lambda item: 'ptp-auto-native-sacr-fulldev-b%s-20261115-v2' % item
B4C = 'ptp-auto-native-sacr-fulldev-b4c-20261115-v1'
NAME = job3(ITEM); S = A/('sacr-fulldev-b%s' % ITEM); assert not S.exists()
EARLIER = [job(b) for b in range(1, 5)] + [B4C] + [job3(i) for i in ORDER[:ORDER.index(ITEM)]]
START, COUNT = (79 * 3 + 23 + 21, 35) if ITEM == '4d' else (79 * (int(ITEM) - 1), 79)
FIXTURE = json.loads((A/'native-fixture-v8/fixture-v8-result.json').read_bytes())
assert FIXTURE['status'] == 'PASS_AUTHORED_NATIVE_PIPELINE', FIXTURE['status']
FIXTURE_PINS = json.loads((A/'native-fixture-v8/fixture-declaration.json').read_bytes())['files_sha256']
PRED = 'ptp-auto-sacr-pilot-retrieval-20261113-v1'
JOB = JOBS + '/' + NAME; CODE = JOBS + '/ptp-auto-paper1-gr-pilot-retrieval-20261113-v1/code/src'
QUERIES = JOBS + '/ptp-native-baseline-20261110-v1/runtime-dev/queries-ta.jsonl'
QSHA = '6fa09d71c96b0e18f5b7986add7011d17ba6826bad753d7a0cc52a2ce5859d2a'
DECODER = '20232bca268d86c6e4bad73eb53be74c881ad06e004eb0aaa6ddb5af831368ae'
CONTROLLER_CPU = 900
assert VERSION == 'patent-structure-marking-v5' and REVIEW_VERSION == 'km-automatic-review-v3'
DISK_PRIOR = max(x['disk_preexisting_upper_bound_bytes'] + x['additional_disk_bytes']
                 for x in (json.loads(p.read_bytes()) for p in A.rglob('declaration.json')) if 'disk_preexisting_upper_bound_bytes' in x)
SEG = 1 + max(int(re.fullmatch(r'segment(\d+)-booking\.json', p.name).group(1)) for p in A.rglob('segment*-booking.json'))

ledger = json.loads(L.read_bytes()); lsha = document_hash(ledger)
assert type(ledger.get('full_dev_charged_seconds')) in (int, float), 'full-dev accounting must be initialized'
blobs, pins = package(['run_automatic_native.py', 'supervise_automatic_native.py', 'run_automatic_synthetic.py', 'supervise_automatic_synthetic.py'])
package_sha = package_identity(pins)
for f in ('scripts/healthtech/run_automatic_native.py', 'src/patent_to_pilot/research/sacr_automatic_runner.py',
          'src/patent_to_pilot/research/paper1_rewrite_runner.py'):
    assert pins[f] == FIXTURE_PINS[f], 'worker differs from the fixture-v8-qualified file: ' + f
configuration = {'stage': 'full_dev', 'track': 'SACR', 'marking_version': VERSION, 'review_version': REVIEW_VERSION,
                 'review_checks': list(CHECKS), 'km_sha256': pins[KM], 'decoder_sha256': DECODER, 'max_new_tokens': 4096,
                 'dtype': 'float16', 'attention': 'eager', 'greedy': True, 'maximum_calls_per_query': 2,
                 'container': {'nano_cpus': 1, 'memory_bytes': 31*1024**3, 'network': 'none', 'gpu': 'single approved UUID'},
                 'fallback': 'original query on rejection/flag/uncertain/abstain/verified grammar refusal or dead end; HOLD on any other backend exception',
                 'semantic_certification': False, 'human_review_required': False, 'protocol': 'NATIVE-STAGES-20261112',
                 'input_token_cap': 5800, 'max_consecutive_whitespaces': 48, 'force_json_field_order': True,
                 'batching': '474 dev queries in pinned file order, 6 batches x 79; b4 continued for rows 260..315 (row 259 = fallback), b4c continued for rows 281..315 (row 280 = fallback)',
                 'identical_to': 'v1 SACR full_dev configuration (native v5 except stage) except the grammar-refusal fallback',
                 'grammar_refusal': 'ORIGINAL_QUERY_FALLBACK reason GRAMMAR_REFUSED in marking or review; batch continues (owner decision A extended to SACR 2026-11-15; protocol section 3)',
                 'grammar_dead_end': 'ORIGINAL_QUERY_FALLBACK reason GRAMMAR_NO_CONTINUATION in marking or review; batch continues (owner decision 2026-11-15)',
                 'configuration_version': 3}
config_sha = document_hash(configuration)
h = journal(CODE, "h,at=head()\nscope=json.loads(h[3]);st=scope['automatic_study']\n"
                  "env=dict(st['authority'].get('stage_envelopes',{}))\nfor a in st.get('authority_amendments',[]):env.update(a.get('add_stage_envelopes',{}))\n"
                  "known=[c for a in st.get('authority_amendments',[]) for c in a['add_configuration_sha256']]+list(st['authority'].get('configuration_sha256',[]))\n"
                  "print(json.dumps({'generation':h[1],'ledger_sha256':document_hash(json.loads(h[2])),'active':h[4],'status':st['status'],"
                  "'authority_sha256':st['authority_sha256'],'pred':st['stage_costs'].get('" + PRED + "'),'envelope':env.get('full_dev'),"
                  "'known':'" + config_sha + "' in known,'settled':sorted(st['stage_costs'])}))\n")
assert h['active'] is None and h['ledger_sha256'] == lsha and h['status'] == 'IDLE', h
assert h['pred'] and h['pred']['stage'] == 'pilot' and h['pred']['calls_complete'] is True, h
assert h['envelope'] == {'seconds': 10800, 'maximum_calls': 158}, h
assert all(e in h['settled'] for e in EARLIER), 'earlier jobs must be settled first: %s' % [e for e in EARLIER if e not in h['settled']]
FIRST = not h['known']
S.mkdir()
seg = segment_booking(SEG, lsha)
after = copy.deepcopy(ledger); after['r6_phase0_cpu']['local_cpu_conservative_charged_seconds'] += seg['conservative_cpu_seconds']
(S/('segment%d-booking.json' % SEG)).write_text(json.dumps(seg, indent=2) + '\n')
out = book(CODE, [seg], h['generation']); assert document_hash(out['ledger']) == document_hash(after); write_ledger(out['ledger'])
ledger_sha = document_hash(after); gen = h['generation'] + 1
files = {'code/' + n: b for n, b in blobs.items()}
files.update({n: blobs['scripts/healthtech/' + n] for n in ('supervise_automatic_native.py', 'supervise_sacr_r5_engine.py', 'r3_engine_client.py')})
transport = stage(NAME, files)
built = ssh(f"""import json,hashlib
from pathlib import Path
raw=Path('{QUERIES}').read_bytes();assert hashlib.sha256(raw).hexdigest()=='{QSHA}'
rows=[json.loads(l) for l in raw.decode('utf-8').splitlines() if l.strip()];assert len(rows)==474
part=rows[{START}:{START}+{COUNT}];assert len(part)=={COUNT}
data=''.join(json.dumps({{'id':r['id'],'text':r['text']}},ensure_ascii=False)+'\\n' for r in part).encode()
check={{}}
if '{ITEM}'=='4d':
    b=Path('{JOBS}/{B4C}');lines=(b/'dispatch/queries.jsonl').read_bytes().decode().splitlines(keepends=True)
    assert ''.join(lines[21:]).encode()==data and len(lines)==56
    o=b/'out/attempt';done=sorted(p.parent.name for p in o.glob('queries/*/result.json'))
    assert done==['q%03d'%i for i in range(20)] and (o/'queries/q020/failure.json').exists() and not (o/'queries/q021').exists()
    check={{'b4c_results':len(done),'b4c_hold_index':20,'b4c_never_started':len(lines)-21}}
d=Path('{JOB}')/'dispatch';d.mkdir()
(d/'queries.jsonl').write_bytes(data)
print(json.dumps({{'sha256':hashlib.sha256(data).hexdigest(),'queries':len(part),'check':check}}))
""")
assert built['queries'] == COUNT
operation = {'stage': 'full_dev', 'track': 'SACR', 'batch': ITEM, 'dev_rows': [START, START + COUNT], 'input_sha256': built['sha256'], 'configuration_sha256': config_sha, 'package_sha256': package_sha}
results = {'v5': sha((A/'native-sacr-pilot20-v5'/'native-result.json').read_bytes()), 'pilot': sha((A/'sacr-pilot-eval'/'pilot-summary.json').read_bytes()),
           'pilot_retrieval': sha((A/'sacr-pilot-retrieval'/'settlement.json').read_bytes()),
           'fixture': sha((A/'native-fixture-v8'/'fixture-v8-result.json').read_bytes())}
cpu = after['r6_phase0_cpu']
base = {'status': 'PASS', 'package_sha256': package_sha, 'configuration_sha256': config_sha}
gates = {'integrity': dict(base, gate='integrity', source_commit=git('rev-parse', 'HEAD').decode().strip(), files=len(pins), v5_sha256=results['v5'],
             fixture_sha256=results['fixture'],
             evidence='committed blobs; worker/runner identical to the fixture-v8-qualified files (authored refusal in marking -> GRAMMAR_REFUSED, authored dead end in review -> GRAMMAR_NO_CONTINUATION, batch continues); otherwise as SACR full-dev b1-b4c'),
         'isolation': dict(base, gate='isolation', evidence='same supervisor/isolation as native v5; re-validated before start'),
         'runtime': dict(base, gate='runtime', evidence='native v5 + SACR pilot retrieval technically valid', pilot_summary_sha256=results['pilot'],
             pilot_retrieval_settlement_sha256=results['pilot_retrieval'], decoder_sha256=DECODER),
         'resources': dict(base, gate='resources', live_admission_required=True, gpu_remaining_seconds=after['gpu_remaining_seconds'],
             full_dev_charged_seconds=after['full_dev_charged_seconds'], disk_preexisting_upper_bound_bytes=DISK_PRIOR),
         'accounting': dict(base, gate='accounting', ledger_sha256=ledger_sha, cpu_remaining_seconds=cpu_cap(cpu) - cpu_used(cpu),
             gpu_stage_host_cpu='TELEMETRY_NOT_CHARGED_TO_CPU_CAP')}
d = {'attempt_id': NAME, 'stage': 'full_dev', 'retry': False, 'queries': COUNT, 'maximum_calls': 2 * COUNT, 'seconds': 10800,
     'input_token_cap': 5800, 'max_consecutive_whitespaces': 48, 'force_json_field_order': True,
     'cpu_seconds': 10800 + CONTROLLER_CPU, 'cpu_charge_basis': 'GPU_STAGE_SAFETY_BOUND_TELEMETRY_ONLY', 'additional_disk_bytes': 256*1024**2,
     'disk_preexisting_upper_bound_bytes': DISK_PRIOR, 'package_sha256': package_sha, 'files_sha256': pins,
     'configuration_sha256': config_sha, 'input_manifest_sha256': built['sha256'], 'km_sha256': pins[KM], 'model_sha256': pins[IDENT],
     'tokenizer_sha256': 'aeb13307a71acd8fe81861d94ad54ab689df773318809eed3cbe794b4492dae4', 'decoder_sha256': DECODER,
     'lmfe_source_sha256': json.loads((R/'docs/healthtech/audits/ptp-r6-phase0-execution-20261111/critic-declaration.json').read_bytes())['lmfe_source_sha256'],
     'predecessor_attempt_id': PRED, 'operation_sha256': document_hash(operation), 'batch': ITEM,
     'gate_receipts': {k: document_hash(v) for k, v in gates.items()}}
raw = json.dumps(d, indent=2).encode() + b'\n'
for n, v in (('configuration.json', configuration), ('gates.json', gates), ('operation.json', operation), ('input-check.json', built)): (S/n).write_text(json.dumps(v, indent=2) + '\n')
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
    amendment = {'kind': 'AUTHORITY_AMENDMENT', 'owner_approval_sha256': sha((A/'owner-sacr-s4-dead-end-approval.json').read_bytes()),
                 'evidence_sha256': results['fixture'], 'add_configuration_sha256': [config_sha], 'additional_synthetic_attempts': 0,
                 'round': 'sacr-full-dev-dead-end', 'authority_sha256': h['authority_sha256'], 'ledger_sha256': ledger_sha, 'scope_sha256': None,
                 'reason': "owner 'A: ขยายกติกา' (2026-11-15): verified grammar dead end -> original-query fallback; SACR full-dev v3 configuration for b4d/b5/b6"}
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
summary = {'status': 'STAGED_QUALIFIED_NOT_LAUNCHED', 'job': NAME, 'batch': ITEM, 'queries': COUNT, 'dev_rows': [START, START + COUNT],
           'supervisor': 'supervise_automatic_native.py', 'declaration_sha256': sha(raw), 'package_sha256': package_sha,
           'configuration_sha256': config_sha, 'input_sha256': built['sha256'], 'transport': transport, 'journal_generation': res['generation'],
           'ledger_sha256': ledger_sha, 'study_status': res['status'], 'segment': SEG, 'segment_seconds': seg['conservative_cpu_seconds'],
           'disk_preexisting_upper_bound_bytes': DISK_PRIOR, 'cpu_remaining_seconds': gates['accounting']['cpu_remaining_seconds']}
(S/'freeze-summary.json').write_text(json.dumps(summary, indent=2) + '\n'); print(json.dumps(summary))
