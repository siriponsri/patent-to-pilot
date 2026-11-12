"""Freeze the synthetic GPU stage ONCE (does not launch).

a. book takeover segment 3 (metered lines 7..N + 100 s conservative) -> gen 11
b. freeze authored task, configuration, five gate receipts, declaration
c. stage the exact archive in the fixed job dir
d. adopt automatic scope (gen 12) and qualify the synthetic stage (gen 13);
   ledger is unchanged after (a), so the accounting gate stays current until claim.
"""
from pathlib import Path
import copy, hashlib, io, json, math, subprocess, sys, tarfile
R = Path('C:/Users/User/Desktop/myProject/patent-to-pilot'); sys.path.insert(0, str(R/'src'))
A = R/'docs/healthtech/audits/ptp-automatic-preparation-20261112/takeover-20261112'
S = A/'synthetic-job'
L = R/'docs/healthtech/audits/ptp-mtm-dapfam-resume-20261110/resource-ledger.json'
from patent_to_pilot.research.r6_dispatch_journal import document_hash
from patent_to_pilot.research.r6_dispatch_files import package_identity
from patent_to_pilot.research.automatic_cpu_booking import cpu_used, cpu_cap
from patent_to_pilot.research.patent_structure_marking import VERSION
from patent_to_pilot.research.km_automatic_review import CHECKS

NAME = 'ptp-auto-synthetic-20261112-v1'; HOST = 'chaw@100.77.149.83'
JOBS = '/home/chaw/patent-to-pilot-jobs'; JOB = JOBS + '/' + NAME
LEDGER_SHA = '0dd87fe91a3d6456e1a480444ca882ad1f092296b4dc3d7a84faf83efb35619f'
IDENTITY = '2b7c2aae40fafff474721b87ff1531569aeaa29990f8234bea32ac2d6b744db4'
DECODER = '20232bca268d86c6e4bad73eb53be74c881ad06e004eb0aaa6ddb5af831368ae'  # = R7 frozen pin = fixture observation
DISK_PRIOR = 31162801647 + 2*16*1024**2  # R7 conservative bound + grammar job + fixture job
sha = lambda b: hashlib.sha256(b).hexdigest()
def git(*a): return subprocess.run(['git', *a], cwd=R, capture_output=True, check=True).stdout
def blob(p): return git('show', 'HEAD:' + p)
def ssh(code, timeout=90):
    r = subprocess.run(['ssh', '-o', 'BatchMode=yes', HOST, 'python3 -'], input=code.encode(), capture_output=True, timeout=timeout)
    if r.returncode: print(r.stderr.decode()[-3000:]); r.check_returncode()
    return json.loads(r.stdout)
def remote_journal(code_dir, body):
    return ssh("import json,sys,sqlite3\nfrom pathlib import Path\nsys.path[:0]=['" + code_dir + "/src','" + JOBS +
               "/research-product-o1-o4-20261031/venv/lib/python3.12/site-packages']\n"
               "from patent_to_pilot.research.r6_dispatch_journal import document_hash\n"
               "path=Path('" + JOBS + "/ptp-r6-control/dispatch.sqlite')\n"
               "def head():\n with sqlite3.connect('file:'+str(path)+'?mode=ro',uri=True) as db:\n"
               "  h=db.execute('SELECT identity,generation,ledger,scope,active FROM head').fetchone()\n"
               "  at=db.execute('SELECT id,declaration,terminal FROM attempts ORDER BY id').fetchall()\n"
               " return h,at\n" + body)

S.mkdir(exist_ok=False)
ledger = json.loads(L.read_bytes()); assert document_hash(ledger) == LEDGER_SHA
assert not git('status', '--porcelain', '--', 'src', 'scripts/healthtech').strip(), 'uncommitted package source'

# (a) segment 3 booking, applied with the fixture job's staged (identical-commit) booking module.
meas = (A/'local-cpu-measurements.jsonl').read_bytes(); lines = meas.decode().splitlines(); FIRST = 7
measured = sum(json.loads(x)['cpu_seconds'] for x in lines[FIRST-1:])
amend_sha = sha((A/'owner-cpu-amendment.json').read_bytes())
segment = {'model_calls': 0, 'gpu_seconds': 0, 'owner_approval_sha256': amend_sha, 'evidence_sha256': sha(meas),
           'booking_id': 'takeover-20261112-segment3', 'location': 'local', 'conservative_cpu_seconds': math.ceil(measured + 100),
           'basis': 'metered lines %d..%d (%.6f s) + 100 s conservative unmetered shell/inspection allowance' % (FIRST, len(lines), measured),
           'prior_ledger_sha256': LEDGER_SHA}
after = copy.deepcopy(ledger); after['r6_phase0_cpu']['local_cpu_conservative_charged_seconds'] += segment['conservative_cpu_seconds']
(S/'segment3-booking.json').write_text(json.dumps(segment, indent=2) + '\n')
fixture_code = JOBS + '/ptp-auto-pipeline-fixture-20261112-v1/code'
out = remote_journal(fixture_code, "from patent_to_pilot.research.automatic_cpu_booking import book_cpu\nfrom patent_to_pilot.research.r6_dispatch_journal import DispatchJournal\n"
    "b=json.loads(" + repr(json.dumps(segment)) + ")\nbook_cpu(DispatchJournal(path,'" + IDENTITY + "'),expected_generation=10,receipt=b,receipt_sha256=document_hash(b))\n"
    "h,at=head()\nassert h[1]==11 and h[4] is None\nprint(json.dumps({'ledger':json.loads(h[2]),'scope_sha256':document_hash(json.loads(h[3])),'attempts_sha256':document_hash(at),'scope_has_auto':'automatic_study' in json.loads(h[3])}))\n")
assert document_hash(out['ledger']) == document_hash(after) and not out['scope_has_auto']
L.write_text(json.dumps(after, indent=2) + '\n'); ledger_sha = document_hash(after)

# (b) frozen package, task, configuration, gates, declaration.
names = [p for p in git('ls-files', 'src').decode().split() if p.endswith('.py')]
scripts = ['r3_engine_client.py', 'supervise_r3_engine_v2.py', 'supervise_sacr_r5_engine.py', 'run_r6_calibration.py',
           'supervise_r6_calibration.py', 'inspect_qwen_weight_identity.py', 'run_r7_calibration.py', 'supervise_r7_calibration.py',
           'run_automatic_synthetic.py', 'supervise_automatic_synthetic.py']
names += ['scripts/healthtech/' + n for n in scripts]
km = 'docs/healthtech/research/plans/PATENT-STRUCTURE-KM.md'; ident = 'docs/healthtech/audits/ptp-method-first-r2-weights-20261110/identity.json'
plan = 'docs/healthtech/research/plans/PAPER1-DUAL-TRACK-LONG-RUN-20261112.md'
names += [km, ident]; blobs = {n: blob(n) for n in names}; pins = {n: sha(b) for n, b in blobs.items()}
package_sha = package_identity(pins)
task = json.dumps({'query_id': 'synthetic-auto-gpu-001', 'authored_synthetic': True,
    'source': 'An infusion pump comprising a reservoir and a controller, wherein the controller stops delivery when the '
              'measured line pressure exceeds 40 kPa, except during a priming cycle shorter than 10 seconds, and the '
              'reservoir is not refilled while delivery is active.'}, ensure_ascii=False).encode()
old = json.loads((R/'docs/healthtech/audits/ptp-r6-phase0-execution-20261111/critic-declaration.json').read_bytes())
tokenizer_sha = 'aeb13307a71acd8fe81861d94ad54ab689df773318809eed3cbe794b4492dae4'
configuration = {'stage': 'synthetic', 'marking_version': VERSION, 'review_checks': list(CHECKS), 'km_sha256': pins[km],
    'decoder_sha256': DECODER, 'max_new_tokens': 4096, 'dtype': 'float16', 'attention': 'eager', 'greedy': True,
    'container': {'nano_cpus': 1, 'memory_bytes': 31*1024**3, 'network': 'none', 'gpu': 'single approved UUID'},
    'maximum_calls': 2, 'seconds': 1800, 'fallback': 'original query on rejection; HOLD on unknown backend state',
    'semantic_certification': False, 'human_review_required': False}
config_sha = document_hash(configuration)
operation = {'stage': 'synthetic', 'task_sha256': sha(task), 'configuration_sha256': config_sha, 'package_sha256': package_sha}
results = {n: sha((A/p).read_bytes()) for n, p in (('grammar', 'grammar-job/grammar-result.json'), ('fixture', 'pipeline-fixture-job/fixture-result.json'))}
base = {'status': 'PASS', 'package_sha256': package_sha, 'configuration_sha256': config_sha}
gates = {
 'integrity': dict(base, gate='integrity', source_commit=git('rev-parse', 'HEAD').decode().strip(), files=len(pins),
     evidence='package built from committed blobs; 135 automatic/journal/SACR/Graph/KM tests PASS; actual worker main PASS in CPU fixture',
     fixture_result_sha256=results['fixture']),
 'isolation': dict(base, gate='isolation', evidence='supervise_automatic_synthetic config test PASS (network none, read-only, 31GiB, CPU1, single GPU, no corpus/evaluator mounts); supervisor re-validates actual container isolation before start'),
 'runtime': dict(base, gate='runtime', grammar_result_sha256=results['grammar'], fixture_result_sha256=results['fixture'],
     decoder_sha256=DECODER, evidence='real tokenizer grammar PASS; decoder pin identical to R7 (Qwen3 fp16 eager loaded on this GPU in R7)'),
 'resources': dict(base, gate='resources', live_admission_required=True, gpu_remaining_seconds=after['gpu_remaining_seconds'],
     fidelity_remaining_seconds=after['fidelity_generation_remaining_seconds'], disk_preexisting_upper_bound_bytes=DISK_PRIOR),
 'accounting': dict(base, gate='accounting', ledger_sha256=ledger_sha, cpu_remaining_seconds=cpu_cap(after['r6_phase0_cpu'])-cpu_used(after['r6_phase0_cpu']),
     gpu_stage_host_cpu='TELEMETRY_NOT_CHARGED_TO_CPU_CAP')}
d = {'attempt_id': NAME, 'stage': 'synthetic', 'retry': False, 'maximum_calls': 2, 'seconds': 1800,
     'cpu_seconds': 1860, 'cpu_charge_basis': 'GPU_STAGE_SAFETY_BOUND_TELEMETRY_ONLY', 'additional_disk_bytes': 256*1024**2,
     'disk_preexisting_upper_bound_bytes': DISK_PRIOR, 'package_sha256': package_sha, 'files_sha256': pins,
     'configuration_sha256': config_sha, 'input_manifest_sha256': sha(task), 'model_sha256': pins[ident],
     'tokenizer_sha256': tokenizer_sha, 'decoder_sha256': DECODER, 'km_sha256': pins[km],
     'lmfe_source_sha256': old['lmfe_source_sha256'], 'operation_sha256': document_hash(operation),
     'gate_receipts': {k: document_hash(v) for k, v in gates.items()}}
raw = json.dumps(d, indent=2).encode() + b'\n'; pin = sha(raw)
for n, v in (('task.json', None), ('configuration.json', configuration), ('gates.json', gates), ('operation.json', operation)):
    (S/n).write_bytes(task if v is None else json.dumps(v, indent=2).encode() + b'\n')
(S/'declaration.json').write_bytes(raw)

# (c) stage archive (no launch).
buf = io.BytesIO()
with tarfile.open(fileobj=buf, mode='w') as tar:
    def add(arc, data):
        i = tarfile.TarInfo(arc); i.size = len(data); i.mode = 0o644; i.mtime = 0; tar.addfile(i, io.BytesIO(data))
    for n, b in blobs.items(): add('code/' + n, b)
    for n in ('supervise_automatic_synthetic.py', 'supervise_sacr_r5_engine.py', 'r3_engine_client.py'): add(n, blobs['scripts/healthtech/' + n])
    add('dispatch/declaration.json', raw); add('dispatch/task.json', task); add('dispatch/gates.json', (S/'gates.json').read_bytes())
data = buf.getvalue(); transport = {'bytes': len(data), 'sha256': sha(data)}
tmp = Path('C:/Users/User/AppData/Local/Temp/' + NAME + '.tar'); tmp.write_bytes(data)
ssh("from pathlib import Path\nimport json\np=Path('" + JOB + "')\nassert not p.exists()\np.mkdir()\nprint('{}')\n")
subprocess.run(['scp', '-q', str(tmp), HOST + ':' + JOB + '/transport.tar'], check=True, timeout=120)
ssh(f"""from pathlib import Path
import tarfile,hashlib,json
p=Path('{JOB}');t=p/'transport.tar'
assert hashlib.sha256(t.read_bytes()).hexdigest()=='{transport['sha256']}'
with tarfile.open(t) as a:
 assert all(not Path(m.name).is_absolute() and '..' not in Path(m.name).parts for m in a.getmembers())
 a.extractall(p,filter='data')
assert hashlib.sha256((p/'dispatch/declaration.json').read_bytes()).hexdigest()=='{pin}'
print('{{}}')
""")

# (d) adopt automatic scope + qualify synthetic stage using the staged code.
authority = {'status': 'OWNER_APPROVED_AUTOMATIC_DUAL_TRACK', 'journal_identity': IDENTITY,
    'human_review_required': False, 'semantic_certification': False,
    'owner_approval_sha256': sha((A/'owner-long-run-authority.json').read_bytes()),
    'protocol_sha256': sha(blob(plan)), 'policy_sha256': pins[km],
    'prior_ledger_sha256': ledger_sha, 'prior_scope_sha256': out['scope_sha256'], 'prior_attempts_sha256': out['attempts_sha256'],
    'unchanged_ledger_caps': {k: after[k] for k in ('gpu_limit_seconds', 'fidelity_limit_seconds', 'full_dev_limit_seconds',
        'disk_limit_bytes_combined_incremental', 'human_cards_total_limit_all_benchmarks_all_configurations')},
    'stage_envelopes': {'synthetic': {'seconds': 1800, 'maximum_calls': 2}},
    'configuration_sha256': [config_sha],
    'package_gpu_ceiling_seconds': 160*3600,
    'later_stages': 'fidelity/pilot/full_dev envelopes and call caps require a separate append-only authority amendment after synthetic throughput is measured'}
(S/'authority.json').write_text(json.dumps(authority, indent=2) + '\n')
auth_sha = document_hash(authority)
code_dir = JOB + '/code'
res = remote_journal(code_dir, "from patent_to_pilot.research.automatic_dispatch_journal import AutomaticDispatchJournal\n"
    "a=json.loads(" + repr(json.dumps(authority)) + ")\nd=json.loads(" + repr(json.dumps(d)) + ")\n"
    "j=AutomaticDispatchJournal(path,'" + IDENTITY + "')\n"
    "j.adopt_scope(expected_generation=11,authority=a,authority_sha256='" + auth_sha + "')\n"
    "h,at=head();ledger=json.loads(h[2]);scope=json.loads(h[3])\n"
    "q={'declaration':d,'authority_sha256':'" + auth_sha + "','ledger_sha256':document_hash(ledger),'scope_sha256':document_hash(scope)}\n"
    "j.qualify_stage(expected_generation=12,receipt=q,receipt_sha256=document_hash(q))\n"
    "h,at=head();scope=json.loads(h[3])\nassert h[1]==13 and h[4] is None\n"
    "print(json.dumps({'generation':h[1],'ledger_sha256':document_hash(json.loads(h[2])),'scope_sha256':document_hash(scope),'qualification':q,"
    "'qualified':list(scope['automatic_study']['qualified_dispatches']),'status':scope['automatic_study']['status']}))\n")
assert res['ledger_sha256'] == ledger_sha and res['qualified'] == [NAME]
(S/'qualification-receipt.json').write_text(json.dumps(res['qualification'], indent=2) + '\n')
summary = {'status': 'STAGED_QUALIFIED_NOT_LAUNCHED', 'job': NAME, 'declaration_sha256': pin, 'package_sha256': package_sha,
           'configuration_sha256': config_sha, 'authority_sha256': auth_sha, 'transport': transport,
           'journal_generation': res['generation'], 'ledger_sha256': ledger_sha, 'scope_sha256': res['scope_sha256'],
           'study_status': res['status'], 'segment3_seconds': segment['conservative_cpu_seconds'],
           'cpu_remaining_seconds': gates['accounting']['cpu_remaining_seconds']}
(S/'freeze-summary.json').write_text(json.dumps(summary, indent=2) + '\n'); print(json.dumps(summary))
