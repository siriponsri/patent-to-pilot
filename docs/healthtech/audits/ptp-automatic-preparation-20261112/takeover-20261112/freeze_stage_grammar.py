"""Freeze + book + stage the CPU grammar job ONCE (does not launch it).

1. books takeover segment-1 local CPU (metered lines 1..N + 100 s conservative);
2. books the 600 s remote precharge for the grammar job (no refund);
3. freezes the declaration from committed Git blobs (canonical LF);
4. stages the exact archive in the fixed new job directory.
Refuses to run twice (exclusive declaration file).
"""
from pathlib import Path
import copy, hashlib, io, json, math, subprocess, sys, tarfile
R = Path('C:/Users/User/Desktop/myProject/patent-to-pilot'); sys.path.insert(0, str(R/'src'))
A = R/'docs/healthtech/audits/ptp-automatic-preparation-20261112/takeover-20261112'
G = A/'grammar-job'
L = R/'docs/healthtech/audits/ptp-mtm-dapfam-resume-20261110/resource-ledger.json'
from patent_to_pilot.research.r6_dispatch_journal import document_hash
from patent_to_pilot.research.r6_dispatch_files import package_identity
from patent_to_pilot.research.automatic_cpu_booking import cpu_used, cpu_cap

NAME = 'ptp-auto-grammar-20261112-v1'
HOST = 'chaw@100.77.149.83'; JOB = '/home/chaw/patent-to-pilot-jobs/' + NAME
LEDGER_SHA = 'f07dcc5fe7666d809f41a19d331d23812735dfb58653531a2889f755e937cbe5'
IDENTITY = '2b7c2aae40fafff474721b87ff1531569aeaa29990f8234bea32ac2d6b744db4'
TOKENIZER = {'tokenizer.json': 'aeb13307a71acd8fe81861d94ad54ab689df773318809eed3cbe794b4492dae4',
             'tokenizer_config.json': 'd5d09f07b48c3086c508b30d1c9114bd1189145b74e982a265350c923acd8101',
             'config.json': 'f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30'}
sha = lambda b: hashlib.sha256(b).hexdigest()
def git(*a): return subprocess.run(['git', *a], cwd=R, capture_output=True, check=True).stdout
def blob(path): return git('show', 'HEAD:' + path)
def ssh(code, timeout=60):
    r = subprocess.run(['ssh', '-o', 'BatchMode=yes', HOST, 'python3 -'], input=code.encode(),
                       capture_output=True, timeout=timeout)
    if r.returncode: print(r.stderr.decode()[-3000:]); r.check_returncode()
    return r.stdout

G.mkdir(exist_ok=False)
ledger = json.loads(L.read_bytes()); assert document_hash(ledger) == LEDGER_SHA
# Remote tokenizer-only files: hash vocab/merges now (read-only) and require the others unchanged.
remote = json.loads(ssh("""import hashlib,json
from pathlib import Path
m=Path('/home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031/models/qwen3-8b')
print(json.dumps({n:hashlib.sha256((m/n).read_bytes()).hexdigest() for n in
 ('tokenizer.json','tokenizer_config.json','config.json','vocab.json','merges.txt')}))
"""))
assert all(remote[k] == v for k, v in TOKENIZER.items()), 'tokenizer pin changed'
tokenizer_pins = remote

# Package from committed blobs only.
assert not git('status', '--porcelain', '--', 'src', 'scripts/healthtech').strip(), 'uncommitted package source'
names = [p for p in git('ls-files', 'src').decode().split() if p.endswith('.py')]
scripts = ['r3_engine_client.py', 'supervise_r3_engine_v2.py', 'supervise_sacr_r5_engine.py',
           'run_r6_calibration.py', 'supervise_r6_calibration.py', 'inspect_qwen_weight_identity.py',
           'run_r7_calibration.py', 'supervise_r7_calibration.py',
           'supervise_automatic_grammar.py', 'qualify_automatic_grammar.py']
names += ['scripts/healthtech/' + n for n in scripts]
km = 'docs/healthtech/research/plans/PATENT-STRUCTURE-KM.md'
identity = 'docs/healthtech/audits/ptp-method-first-r2-weights-20261110/identity.json'
names += [km, identity]
blobs = {n: blob(n) for n in names}
pins = {n: sha(b) for n, b in blobs.items()}
old = json.loads((R/'docs/healthtech/audits/ptp-r6-phase0-execution-20261111/critic-declaration.json').read_bytes())

# Bookings (computed locally, applied remotely, verified equal).
meas = (A/'local-cpu-measurements.jsonl').read_bytes()
lines = meas.decode().splitlines(); measured = sum(json.loads(x)['cpu_seconds'] for x in lines)
authority_sha = sha((A/'owner-long-run-authority.json').read_bytes())
amend_sha = sha((A/'owner-cpu-amendment.json').read_bytes())
segment = {'model_calls': 0, 'gpu_seconds': 0, 'owner_approval_sha256': amend_sha,
           'evidence_sha256': sha(meas), 'booking_id': 'takeover-20261112-segment1', 'location': 'local',
           'conservative_cpu_seconds': math.ceil(measured + 100),
           'basis': 'metered lines 1..%d (%.6f s) + 100 s conservative unmetered shell/inspection allowance' % (len(lines), measured),
           'prior_ledger_sha256': LEDGER_SHA}
after_segment = copy.deepcopy(ledger)
after_segment['r6_phase0_cpu']['local_cpu_conservative_charged_seconds'] += segment['conservative_cpu_seconds']
package_sha = package_identity(pins)
grammar = {'model_calls': 0, 'gpu_seconds': 0, 'owner_approval_sha256': authority_sha,
           'evidence_sha256': package_sha, 'booking_id': NAME, 'location': 'remote',
           'conservative_cpu_seconds': 600,
           'basis': 'upper bound: worker RLIMIT_CPU 480 s + controller RLIMIT_CPU 60 s on 1 core, wall stop 540 s; no refund',
           'prior_ledger_sha256': document_hash(after_segment)}
after_grammar = copy.deepcopy(after_segment)
after_grammar['r6_phase0_cpu']['remote_cpu_charged_seconds'] += 600
cpu = after_grammar['r6_phase0_cpu']; assert cpu_used(cpu) <= cpu_cap(cpu)

declaration = {'run_id': NAME, 'kind': 'automatic-grammar-only', 'model_calls': 0, 'gpu_seconds': 0,
               'retry': False, 'cpu_seconds': 480, 'wall_stop_seconds': 540, 'cpu_threads': 1,
               'container_memory_bytes': 1536*1024**2, 'controller_address_space_bytes': 512*1024**2,
               'files_sha256': pins, 'package_sha256': package_sha, 'source_commit': git('rev-parse', 'HEAD').decode().strip(),
               'tokenizer_files_sha256': tokenizer_pins, 'km_sha256': pins[km],
               'lmfe_source_sha256': old['lmfe_source_sha256'], 'cpu_booking_sha256': document_hash(grammar),
               'owner_authority_sha256': authority_sha, 'cases': 6,
               'qualification_scope': 'actual tokenizer + R6Backend grammar/EOS replay of 6 authored new-schema cases; no weights, corpus, GPU or model calls; not semantic evidence'}
raw = json.dumps(declaration, indent=2).encode() + b'\n'
with (G/'declaration.json').open('xb') as f: f.write(raw)
pin = sha(raw)
for n, v in (('segment1-booking.json', segment), ('grammar-booking.json', grammar)):
    (G/n).write_text(json.dumps(v, indent=2) + '\n')

# Apply both bookings remotely (gen 6 -> 8), verify against local expectation.
module = (blob('src/patent_to_pilot/research/automatic_cpu_booking.py')).decode()
payload = {'module': module, 'bookings': [segment, grammar], 'expected': document_hash(after_grammar)}
out = json.loads(ssh("""import json,sys,sqlite3,importlib.util
from pathlib import Path
p=Path('/home/chaw/patent-to-pilot-jobs/ptp-r7-calibration-20261112-v1')
sys.path[:0]=[str(p/'code/src'),'/home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031/venv/lib/python3.12/site-packages']
import patent_to_pilot.research
from patent_to_pilot.research.r6_dispatch_journal import DispatchJournal,document_hash
""" + 'payload=json.loads(' + repr(json.dumps(payload)) + ')\n' + """
spec=importlib.util.spec_from_loader('patent_to_pilot.research.automatic_cpu_booking',loader=None)
m=importlib.util.module_from_spec(spec);m.__package__='patent_to_pilot.research'
exec(compile(payload['module'],'automatic_cpu_booking.py','exec'),m.__dict__)
path=p.parent/'ptp-r6-control/dispatch.sqlite'
j=DispatchJournal(path,'""" + IDENTITY + """')
for i,b in enumerate(payload['bookings']):
 m.book_cpu(j,expected_generation=6+i,receipt=b,receipt_sha256=document_hash(b))
with sqlite3.connect('file:'+str(path)+'?mode=ro',uri=True) as db:
 head=db.execute('SELECT generation,ledger,active FROM head').fetchone()
 ids=[r[0] for r in db.execute('SELECT id FROM automatic_cpu_bookings ORDER BY id')]
assert head[0]==8 and head[2] is None and document_hash(json.loads(head[1]))==payload['expected']
print(json.dumps({'generation':head[0],'ledger':json.loads(head[1]),'booking_ids':ids}))
"""))
assert document_hash(out['ledger']) == document_hash(after_grammar)
L.write_text(json.dumps(after_grammar, indent=2) + '\n')  # same key order as the local file

# Archive from blobs + root controller copies + declaration.
buf = io.BytesIO()
with tarfile.open(fileobj=buf, mode='w') as tar:
    def add(arc, data):
        info = tarfile.TarInfo(arc); info.size = len(data); info.mode = 0o644; info.mtime = 0
        tar.addfile(info, io.BytesIO(data))
    for n, b in blobs.items(): add('code/' + n, b)
    for n in ('supervise_automatic_grammar.py', 'supervise_r3_engine_v2.py', 'r3_engine_client.py'):
        add(n, blobs['scripts/healthtech/' + n])
    add('declaration.json', raw)
data = buf.getvalue(); transport = {'bytes': len(data), 'sha256': sha(data), 'files': len(blobs) + 4}
tmp = Path('C:/Users/User/AppData/Local/Temp/' + NAME + '.tar'); tmp.write_bytes(data)
ssh("from pathlib import Path\np=Path('" + JOB + "')\nassert not p.exists()\np.mkdir()\n")
subprocess.run(['scp', '-q', str(tmp), HOST + ':' + JOB + '/transport.tar'], check=True, timeout=120)
ssh(f"""from pathlib import Path
import tarfile,hashlib
p=Path('{JOB}');t=p/'transport.tar'
assert hashlib.sha256(t.read_bytes()).hexdigest()=='{transport['sha256']}'
with tarfile.open(t) as a:
 assert all(not Path(m.name).is_absolute() and '..' not in Path(m.name).parts for m in a.getmembers())
 a.extractall(p,filter='data')
assert hashlib.sha256((p/'declaration.json').read_bytes()).hexdigest()=='{pin}'
""")
summary = {'status': 'STAGED_NOT_LAUNCHED', 'job': NAME, 'declaration_sha256': pin,
           'package_sha256': package_sha, 'transport': transport, 'journal_generation': 8,
           'ledger_sha256': document_hash(after_grammar), 'booking_ids': out['booking_ids'],
           'cpu_used_seconds': cpu_used(cpu), 'cpu_remaining_seconds': cpu_cap(cpu) - cpu_used(cpu),
           'segment1_seconds': segment['conservative_cpu_seconds']}
(G/'freeze-summary.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps(summary))
