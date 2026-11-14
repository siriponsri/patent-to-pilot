"""Paper 1 S4 (after owner decision A, 2026-11-14): freeze ONE full-dev generation job ONCE (no launch).

Items: FA:2c (continuation of FA b2: the 56 never-started queries, dev rows 260..315; dev row 259 stays an
original-query fallback and is NOT regenerated), FA:3, GR:1, GR:2, GR:3 (158 queries each, rows 158*(b-1)..).
Worker repaired: a verified grammar refusal -> ORIGINAL_QUERY_FALLBACK (GRAMMAR_REFUSED), batch continues.
Because the fallback behaviour changed, the configuration is v2 (new sha); the first v2 freeze appends authority
amendment round 'paper1-s4-refusal' adding the FA and GR v2 full_dev configurations (the full_dev envelope
{10800 s, 158 calls} already exists from round 'paper1-s4'). Owner authority: owner-paper1-s4-refusal-approval.json.
Requires fixture v3 PASS. The ledger must not change between this freeze and the claim.
"""
import copy, json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from takeover_lib import *
from patent_to_pilot.research.r6_dispatch_files import package_identity
from patent_to_pilot.research.automatic_cpu_booking import cpu_used, cpu_cap

ARM, ITEM = sys.argv[1], sys.argv[2]; assert (ARM, ITEM) in (('FA', '2c'), ('FA', '3'), ('GR', '1'), ('GR', '2'), ('GR', '3'))
low = ARM.lower(); N0 = 158
ORDER = {'FA': ['b1-20261113', 'b2-20261113', 'b2c-20261114', 'b3-20261114'], 'GR': ['b1-20261114', 'b2-20261114', 'b3-20261114']}
job = lambda arm, tag: 'ptp-auto-paper1-%s-fulldev-%s-v1' % (arm.lower(), tag)
TAG = 'b%s-20261114' % ITEM
NAME = job(ARM, TAG); S = A/('paper1-s4-%s-b%s' % (low, ITEM)); assert not S.exists()
EARLIER = [job(ARM, t) for t in ORDER[ARM][:ORDER[ARM].index(TAG)]]
if ARM == 'GR': EARLIER = [job('FA', t) for t in ORDER['FA']] + EARLIER  # one arm at a time: FA finished first
START, COUNT = (N0 + 102, 56) if ITEM == '2c' else (N0 * (int(ITEM) - 1), N0)
PRED = 'ptp-auto-paper1-%s-pilot-retrieval-20261113-v1' % low
JOB = JOBS + '/' + NAME; CODE = JOBS + '/ptp-auto-paper1-gr-pilot-retrieval-20261113-v1/code/src'
QUERIES = JOBS + '/ptp-native-baseline-20261110-v1/runtime-dev/queries-ta.jsonl'
FREEZE = json.loads((A/'paper1-freeze/freeze-manifest.json').read_bytes())
RT = FREEZE['generation_runtime']; QSHA = FREEZE['dev_inputs']['queries_sha256']
CONTROLLER_CPU = 900
FIXTURE = json.loads((A/'paper1-fixture-v3/fixture-v3-result.json').read_bytes())
assert FIXTURE['status'] == 'PASS_AUTHORED_PAPER1_REWRITE_PIPELINE', FIXTURE['status']
FIXTURE_PINS = json.loads((A/'paper1-fixture-v3/fixture-declaration.json').read_bytes())['files_sha256']
DISK_PRIOR = max(x['disk_preexisting_upper_bound_bytes'] + x['additional_disk_bytes']
                 for x in (json.loads(p.read_bytes()) for p in A.rglob('declaration.json')) if 'disk_preexisting_upper_bound_bytes' in x)
SEG = 1 + max(int(re.fullmatch(r'segment(\d+)-booking\.json', p.name).group(1)) for p in A.rglob('segment*-booking.json'))


def configuration(arm):
    return {'stage': 'full_dev', 'track': 'PAPER1_' + arm, 'protocol': 'PAPER1-ACQUISITION-PROTOCOL (frozen 2026-11-13) S4 full-dev generation',
            'paper1_freeze_manifest_sha256': sha((A/'paper1-freeze/freeze-manifest.json').read_bytes()),
            'arm': FREEZE['arms'][arm], 'decoder_sha256': RT['decoder_sha256'], 'max_new_tokens': 4096, 'dtype': 'float16',
            'attention': 'eager', 'greedy': True, 'maximum_calls_per_query': 1, 'input_token_cap': RT['input_token_cap'],
            'max_consecutive_whitespaces': RT['max_consecutive_whitespaces'], 'force_json_field_order': RT['force_json_field_order'],
            'container': {'nano_cpus': 1, 'memory_bytes': 31*1024**3, 'network': 'none', 'gpu': 'single approved UUID'},
            'fallback': 'original query on input cap / output limit / schema or blank rejection / verified grammar refusal; HOLD on any other backend exception',
            'grammar_refusal': 'ORIGINAL_QUERY_FALLBACK reason GRAMMAR_REFUSED; batch continues (owner decision A 2026-11-14; protocol section 3)',
            'batching': '474 dev queries in pinned file order, 3 batches x 158; FA b2 continued for rows 260..315 (row 259 = fallback)',
            'identical_to': 'v1 full_dev configuration except the grammar-refusal fallback', 'configuration_version': 2,
            'semantic_certification': False}


ledger = json.loads(L.read_bytes()); lsha = document_hash(ledger)
v2 = [document_hash(configuration('FA')), document_hash(configuration('GR'))]
h = journal(CODE, "h,at=head()\nscope=json.loads(h[3]);st=scope['automatic_study']\n"
                  "known=[c for a in st.get('authority_amendments',[]) for c in a['add_configuration_sha256']]\n"
                  "print(json.dumps({'generation':h[1],'ledger_sha256':document_hash(json.loads(h[2])),'active':h[4],"
                  "'status':st['status'],'authority_sha256':st['authority_sha256'],'pred':st['stage_costs'].get('" + PRED + "'),"
                  "'known':[c for c in " + repr(v2) + " if c in known],'settled':sorted(st['stage_costs'])}))\n")
assert h['active'] is None and h['ledger_sha256'] == lsha and h['status'] == 'IDLE', h
assert h['pred'] and h['pred']['stage'] == 'pilot' and h['pred']['calls_complete'] is True, h
assert all(e in h['settled'] for e in EARLIER), 'earlier jobs must be settled first: %s' % [e for e in EARLIER if e not in h['settled']]
FIRST = not h['known']
if not FIRST: assert h['known'] == v2, h
assert type(ledger.get('full_dev_charged_seconds')) in (int, float), 'full-dev accounting must be initialized'
blobs, pins = package(['run_paper1_rewrite.py', 'supervise_paper1_rewrite.py'])
package_sha = package_identity(pins)
for f in ('src/patent_to_pilot/research/paper1_rewrite_arms.py', 'src/patent_to_pilot/research/r6_backend.py'):
    assert pins[f] == FREEZE['files_sha256'][f], 'frozen file changed: ' + f
for f in ('scripts/healthtech/run_paper1_rewrite.py', 'src/patent_to_pilot/research/paper1_rewrite_runner.py'):
    assert pins[f] == FIXTURE_PINS[f], 'worker differs from the fixture-v3-qualified file: ' + f
S.mkdir()
seg = segment_booking(SEG, lsha)
after = copy.deepcopy(ledger); after['r6_phase0_cpu']['local_cpu_conservative_charged_seconds'] += seg['conservative_cpu_seconds']
(S/('segment%d-booking.json' % SEG)).write_text(json.dumps(seg, indent=2) + '\n')
out = book(CODE, [seg], h['generation']); assert document_hash(out['ledger']) == document_hash(after); write_ledger(out['ledger'])
ledger_sha = document_hash(after); gen = h['generation'] + 1
files = {'code/' + n: b for n, b in blobs.items()}
files.update({n: blobs['scripts/healthtech/' + n] for n in ('supervise_paper1_rewrite.py', 'supervise_sacr_r5_engine.py', 'r3_engine_client.py')})
transport = stage(NAME, files)
b2 = JOBS + '/' + job('FA', 'b2-20261113')
built = ssh(f"""import json,hashlib
from pathlib import Path
raw=Path('{QUERIES}').read_bytes();assert hashlib.sha256(raw).hexdigest()=='{QSHA}'
rows=[json.loads(l) for l in raw.decode('utf-8').splitlines() if l.strip()];assert len(rows)==474
part=rows[{START}:{START}+{COUNT}];assert len(part)=={COUNT}
data=''.join(json.dumps({{'id':r['id'],'text':r['text']}},ensure_ascii=False)+'\\n' for r in part).encode()
check={{}}
if '{ITEM}'=='2c':
    b=Path('{b2}');lines=(b/'dispatch/queries.jsonl').read_bytes().decode().splitlines(keepends=True)
    assert ''.join(lines[102:]).encode()==data and len(lines)==158
    o=b/'out/attempt';done=sorted(p.parent.name for p in o.glob('queries/*/result.json'))
    assert done==['q%03d'%i for i in range(101)] and (o/'queries/q101/failure.json').exists() and not (o/'queries/q102').exists()
    check={{'b2_results':len(done),'b2_hold_index':101,'b2_never_started':len(lines)-102}}
d=Path('{JOB}')/'dispatch';d.mkdir()
(d/'queries.jsonl').write_bytes(data)
print(json.dumps({{'sha256':hashlib.sha256(data).hexdigest(),'queries':len(part),'check':check}}))
""")
assert built['queries'] == COUNT
config = configuration(ARM); config_sha = document_hash(config)
operation = {'stage': 'full_dev', 'arm': ARM, 'item': ITEM, 'dev_rows': [START, START + COUNT], 'input_sha256': built['sha256'],
             'configuration_sha256': config_sha, 'package_sha256': package_sha}
results = {'s3': sha((A/'PAPER1-S3-SUMMARY.json').read_bytes()), 'pred': sha((A/('paper1-s3-%s-retrieval' % low)/'settlement.json').read_bytes()),
           'fixture': sha((A/'paper1-fixture-v3/fixture-v3-result.json').read_bytes())}
cpu = after['r6_phase0_cpu']
base = {'status': 'PASS', 'package_sha256': package_sha, 'configuration_sha256': config_sha}
gates = {'integrity': dict(base, gate='integrity', source_commit=git('rev-parse', 'HEAD').decode().strip(), files=len(pins), fixture_sha256=results['fixture'],
             evidence='committed blobs; frozen FA/GR files match the Paper 1 freeze manifest; worker/runner identical to the fixture-v3-qualified files (authored grammar refusal -> fallback, batch continues)'),
         'isolation': dict(base, gate='isolation', evidence='same supervisor/isolation as the S3/S4 runs; re-validated before start'),
         'runtime': dict(base, gate='runtime', s3_summary_sha256=results['s3'], predecessor_settlement_sha256=results['pred'], decoder_sha256=RT['decoder_sha256'],
             evidence='S3 pilot-20 20/20 for this arm; FA full-dev b1 158/158 on this GPU'),
         'resources': dict(base, gate='resources', live_admission_required=True, gpu_remaining_seconds=after['gpu_remaining_seconds'],
             full_dev_charged_seconds=after['full_dev_charged_seconds'], disk_preexisting_upper_bound_bytes=DISK_PRIOR),
         'accounting': dict(base, gate='accounting', ledger_sha256=ledger_sha, cpu_remaining_seconds=cpu_cap(cpu) - cpu_used(cpu),
             gpu_stage_host_cpu='TELEMETRY_NOT_CHARGED_TO_CPU_CAP')}
d = {'attempt_id': NAME, 'arm': ARM, 'stage': 'full_dev', 'batch': ITEM, 'retry': False, 'queries': COUNT, 'maximum_calls': COUNT, 'seconds': 10800,
     'input_token_cap': RT['input_token_cap'], 'max_consecutive_whitespaces': RT['max_consecutive_whitespaces'],
     'force_json_field_order': RT['force_json_field_order'], 'cpu_seconds': 10800 + CONTROLLER_CPU, 'cpu_charge_basis': 'GPU_STAGE_SAFETY_BOUND_TELEMETRY_ONLY',
     'additional_disk_bytes': 256*1024**2, 'disk_preexisting_upper_bound_bytes': DISK_PRIOR, 'package_sha256': package_sha,
     'files_sha256': pins, 'configuration_sha256': config_sha, 'input_manifest_sha256': built['sha256'], 'km_sha256': pins[KM],
     'model_sha256': pins[IDENT], 'tokenizer_sha256': RT['tokenizer_sha256'], 'decoder_sha256': RT['decoder_sha256'],
     'lmfe_source_sha256': RT['lmfe_source_sha256'], 'predecessor_attempt_id': PRED, 'operation_sha256': document_hash(operation),
     'gate_receipts': {k: document_hash(v) for k, v in gates.items()}}
assert d['model_sha256'] == RT['model_sha256']
raw = json.dumps(d, indent=2).encode() + b'\n'
for n, v in (('configuration.json', config), ('gates.json', gates), ('operation.json', operation), ('input-check.json', built)):
    (S/n).write_text(json.dumps(v, indent=2) + '\n')
(S/'declaration.json').write_bytes(raw)
ssh(f"""import hashlib
from pathlib import Path
d=Path('{JOB}')/'dispatch'
(d/'declaration.json').write_bytes({raw!r});(d/'gates.json').write_bytes({(S/'gates.json').read_bytes()!r})
assert hashlib.sha256((d/'declaration.json').read_bytes()).hexdigest()=='{sha(raw)}'
print('{{}}')
""")
body = "from patent_to_pilot.research.automatic_dispatch_journal import AutomaticDispatchJournal\nd=json.loads(" + repr(json.dumps(d)) + ")\n"
body += "j=AutomaticDispatchJournal(path,'" + IDENTITY + "')\nh,at=head();assert h[1]==" + str(gen) + "\nam=None\n"
if FIRST:
    amendment = {'kind': 'AUTHORITY_AMENDMENT', 'owner_approval_sha256': sha((A/'owner-paper1-s4-refusal-approval.json').read_bytes()),
                 'evidence_sha256': results['fixture'], 'add_configuration_sha256': v2, 'additional_synthetic_attempts': 0,
                 'round': 'paper1-s4-refusal', 'authority_sha256': h['authority_sha256'], 'ledger_sha256': ledger_sha, 'scope_sha256': None,
                 'reason': 'owner decision A: verified grammar refusal -> per-query fallback (protocol section 3); FA/GR full_dev configuration v2'}
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
summary = {'status': 'STAGED_QUALIFIED_NOT_LAUNCHED', 'job': NAME, 'arm': ARM, 'item': ITEM, 'queries': COUNT, 'dev_rows': [START, START + COUNT],
           'supervisor': 'supervise_paper1_rewrite.py', 'declaration_sha256': sha(raw), 'package_sha256': package_sha,
           'configuration_sha256': config_sha, 'input_sha256': built['sha256'], 'transport': transport, 'journal_generation': res['generation'],
           'ledger_sha256': ledger_sha, 'study_status': res['status'], 'segment': SEG, 'segment_seconds': seg['conservative_cpu_seconds'],
           'disk_preexisting_upper_bound_bytes': DISK_PRIOR, 'cpu_remaining_seconds': gates['accounting']['cpu_remaining_seconds']}
(S/'freeze-summary.json').write_text(json.dumps(summary, indent=2) + '\n'); print(json.dumps(summary))
