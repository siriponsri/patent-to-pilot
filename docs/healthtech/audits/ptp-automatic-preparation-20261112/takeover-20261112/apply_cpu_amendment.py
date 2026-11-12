"""Apply the owner CPU-cap amendment + preparation upper bound ONCE to the live journal.

Idempotent: transacts only at generation 5 (idle); otherwise verifies the
already-applied transition. Mirrors the resulting ledger to the local canonical
resource-ledger.json only after remote verification.
"""
from pathlib import Path
import copy, hashlib, json, subprocess, sys
R = Path('C:/Users/User/Desktop/myProject/patent-to-pilot'); sys.path.insert(0, str(R/'src'))
A = R/'docs/healthtech/audits/ptp-automatic-preparation-20261112/takeover-20261112'
L = R/'docs/healthtech/audits/ptp-mtm-dapfam-resume-20261110/resource-ledger.json'
from patent_to_pilot.research.r6_dispatch_journal import document_hash
from patent_to_pilot.research.automatic_cpu_booking import GPU_STAGE_HOST_CPU, cpu_used

IDENTITY = '2b7c2aae40fafff474721b87ff1531569aeaa29990f8234bea32ac2d6b744db4'
PRIOR_LEDGER_SHA = '2d0419778919614d48872f4d1f536edabb458881d6be18dbfb7d5542d402a927'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
old = json.loads(L.read_bytes())
evidence = json.loads((A/'preparation-window-evidence.json').read_bytes())
module_src = (R/'src/patent_to_pilot/research/automatic_cpu_booking.py').read_bytes().replace(b'\r\n', b'\n')
receipt = {'kind': 'CPU_CAP_AMENDMENT_AND_PREPARATION_UPPER_BOUND', 'from_seconds': 28800,
           'to_seconds': 57600, 'basis': 'UPPER_BOUND_NOT_MEASURED', 'gpu_stage_host_cpu': GPU_STAGE_HOST_CPU,
           'model_calls': 0, 'gpu_seconds': 0, 'location': 'local',
           'owner_approval_sha256': sha(A/'owner-cpu-amendment.json'),
           'evidence_sha256': sha(A/'preparation-window-evidence.json'),
           'window_start_unix': evidence['window_start_unix'], 'window_end_unix': evidence['window_end_unix'],
           'logical_cpus': evidence['logical_cpus'], 'upper_bound_seconds': evidence['upper_bound_seconds'],
           'booking_id': 'automatic-preparation-20261112T070041-073039',
           'prior_ledger_sha256': PRIOR_LEDGER_SHA, 'journal_identity': IDENTITY,
           'module_sha256_lf': hashlib.sha256(module_src).hexdigest()}
receipt_sha = document_hash(receipt)
payload = {'receipt': receipt, 'receipt_sha256': receipt_sha, 'module': module_src.decode()}
code = """import json,sys,sqlite3,subprocess,importlib.util,hashlib
from pathlib import Path
p=Path('/home/chaw/patent-to-pilot-jobs/ptp-r7-calibration-20261112-v1')
sys.path[:0]=[str(p/'code/src'),'/home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031/venv/lib/python3.12/site-packages']
import patent_to_pilot.research
from patent_to_pilot.research.r6_dispatch_journal import DispatchJournal,document_hash
""" + 'payload=json.loads(' + repr(json.dumps(payload)) + ')\n' + """
assert hashlib.sha256(payload['module'].encode()).hexdigest()==payload['receipt']['module_sha256_lf']
spec=importlib.util.spec_from_loader('patent_to_pilot.research.automatic_cpu_booking',loader=None)
m=importlib.util.module_from_spec(spec);m.__package__='patent_to_pilot.research'
exec(compile(payload['module'],'automatic_cpu_booking.py','exec'),m.__dict__)
path=p.parent/'ptp-r6-control/dispatch.sqlite'
def read():
 with sqlite3.connect('file:'+str(path)+'?mode=ro',uri=True) as db:
  head=db.execute('SELECT identity,generation,ledger,scope,active FROM head').fetchone()
  tables=[r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")]
  tr=db.execute('SELECT generation,kind,receipt FROM automatic_transitions ORDER BY generation').fetchall() if 'automatic_transitions' in tables else []
  bk=db.execute('SELECT id,receipt FROM automatic_cpu_bookings').fetchall() if 'automatic_cpu_bookings' in tables else []
  at=db.execute('SELECT id,terminal FROM attempts ORDER BY id').fetchall()
 return head,tr,bk,at
head,_,_,_=read()
applied=False
if head[1]==5:
 assert head[0]==payload['receipt']['journal_identity'] and head[4] is None
 assert document_hash(json.loads(head[2]))==payload['receipt']['prior_ledger_sha256']
 m.amend_cpu_cap_and_book_preparation(DispatchJournal(path,head[0]),expected_generation=5,
  receipt=payload['receipt'],receipt_sha256=payload['receipt_sha256'])
 applied=True
head,tr,bk,at=read()
assert head[1]==6 and head[4] is None
assert [(g,k) for g,k,_ in tr]==[(6,'CPU_CAP_AMENDMENT')] and json.loads(tr[0][2])==payload['receipt']
assert [i for i,_ in bk]==[payload['receipt']['booking_id']]
assert len(at)==2 and all(t is not None for _,t in at)
gpu=subprocess.run(['nvidia-smi','--query-compute-apps=pid,gpu_uuid','--format=csv,noheader'],capture_output=True,text=True,check=True,timeout=10).stdout
print(json.dumps({'applied_now':applied,'identity':head[0],'generation':head[1],'active':head[4],
 'ledger':json.loads(head[2]),'scope_sha256':document_hash(json.loads(head[3])),
 'approved_gpu_occupied':'GPU-277ccc57-c3e5-0731-cd49-f4f8695f7089' in gpu,'new_model_calls':0}))
"""
assert document_hash(old) == PRIOR_LEDGER_SHA or old.get('r6_phase0_cpu', {}).get('cpu_cap_seconds') == 57600
r = subprocess.run(['ssh', '-o', 'BatchMode=yes', 'chaw@100.77.149.83', 'python3 -'],
                   input=code.encode(), capture_output=True, timeout=60)
if r.returncode:
    print(r.stderr.decode()[-3000:]); r.check_returncode()
v = json.loads(r.stdout)
new = v.pop('ledger')
assert v['identity'] == IDENTITY and v['generation'] == 6
expected = copy.deepcopy(json.loads(L.read_bytes())) if document_hash(old) != PRIOR_LEDGER_SHA else None
cpu = new['r6_phase0_cpu']; prior = old['r6_phase0_cpu'] if expected is None else None
if prior is not None:  # verify no reset of any non-amended field
    for k, val in old.items():
        if k != 'r6_phase0_cpu': assert new[k] == val, k
    for k, val in prior.items():
        if k not in ('cpu_cap_seconds', 'local_cpu_conservative_charged_seconds'): assert cpu[k] == val, k
    assert cpu['local_cpu_conservative_charged_seconds'] == prior['local_cpu_conservative_charged_seconds'] + 21588
v.update(ledger_sha256=document_hash(new), receipt_sha256=receipt_sha,
         cpu_used_seconds=cpu_used(cpu), cpu_remaining_seconds=57600 - cpu_used(cpu))
for name, value in [('amendment-receipt.json', receipt), ('amendment-verification.json', v)]:
    target = A/name
    if target.exists():
        assert json.loads(target.read_bytes()) == value or name == 'amendment-verification.json'
    target.write_text(json.dumps(value, indent=2) + '\n')
L.write_text(json.dumps(new, indent=2) + '\n')
assert document_hash(json.loads(L.read_bytes())) == v['ledger_sha256']
print(json.dumps({k: v[k] for k in ('applied_now', 'generation', 'active', 'ledger_sha256', 'cpu_used_seconds',
                                     'cpu_remaining_seconds', 'approved_gpu_occupied')}))
