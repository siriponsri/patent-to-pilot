"""Terminal-only full24 R7 reconciliation. Never restarts or initializes live history."""
from pathlib import Path
from contextlib import closing
import copy,json,math,subprocess,sys,tempfile,hashlib,sqlite3
R=Path('C:/Users/User/Desktop/myProject/patent-to-pilot')
A=R/'docs/healthtech/audits/ptp-r7-calibration-20261112'
L=R/'docs/healthtech/audits/ptp-mtm-dapfam-resume-20261110/resource-ledger.json'
sys.path.insert(0,str(R/'src'))
from patent_to_pilot.research.r7_dispatch_files import load_dispatch
from patent_to_pilot.research.r6_dispatch_journal import initialize,DispatchJournal,document_hash,encoded

frozen=json.loads((A/'freeze-summary.json').read_bytes())
e=load_dispatch(A/'dispatch',manifest_path='manifest.json',manifest_sha256=frozen['manifest_sha256'])
v=json.loads((A/'terminal-verification.json').read_bytes())
assert v['raw24_reassessment']=='MATCHES_FROZEN_ASSESSOR'
assert v['generation_records']==v['backend_dispatch_markers']==v['backend_return_markers']==24
assert v['authoritative_state']['Running'] is False and v['authoritative_state']['Pid']==0
assert v['outcome'] in ('CALIBRATION_FAILED','AUTHORED_CALIBRATION_QUALIFIED')
assert v['costs']['metrics']['model_calls']['value']==24
current=json.loads(L.read_bytes());old=e['ledger'];scope=copy.deepcopy(e['scope']);d=e['declaration']
done=A/'reconciliation.json'
if done.exists():
 assert current==json.loads((A/'reconciled-ledger.json').read_bytes())
 print(done.read_text());sys.exit(0)
new=copy.deepcopy(old);wall=v['terminal']['whole_wall_seconds'];charge=math.ceil(wall)
assert math.isfinite(wall) and 0<wall and charge>=wall
for charged,remaining,cap in [
 ('gpu_conservative_charged_seconds','gpu_remaining_seconds','gpu_limit_seconds'),
 ('fidelity_generation_charged_seconds','fidelity_generation_remaining_seconds','fidelity_limit_seconds')]:
 new[charged]+=charge;new[remaining]=new[cap]-new[charged]
new['model_calls']+=24
assert 'r7_calibration' not in new
new['r7_calibration']={'status':v['outcome'],'assessment':v['assessment'],
 'whole_wall_seconds':wall,'charged_seconds':charge,
 'charge_basis':'Whole supervisor occupancy rounded up; per-call GPU seconds are not added again.',
 'model_calls':24,'costs':v['costs'],'terminal_sha256':v['terminal_file_sha256'],
 'raw24_reassessment':v['raw24_reassessment'],'retry':False,
 'owner_approval_sha256':d['candidate_owner_approval_sha256']}
assert current in (old,new),'Never discard an intervening accounting change'
scope['stage_costs']['calibration']['seconds']+=charge
scope['stage_costs']['calibration']['calls']+=24
assert scope['stage_costs']['calibration']['calls']==48
for reservation in scope['reservations']:
 if reservation['attempt_id']==d['attempt_id']:reservation['status']='SETTLED'
terminal=copy.deepcopy(v['terminal'])
terminal.update(costs_reconciled=True,charged_seconds=charge,
 failure_axis='EVALUATOR_CALIBRATION' if v['outcome']=='CALIBRATION_FAILED' else 'NONE',
 outcome=v['outcome'],verification_sha256=hashlib.sha256((A/'terminal-verification.json').read_bytes()).hexdigest())
identity=d['approval_sha256']
prior=json.loads((A/'current-resource-probe.json').read_bytes())['remote']['attempts']
# Reconstruct only an isolated test database with prior records and active R7.
# The actual live journal below is opened read/write; initialize is never called.
with tempfile.TemporaryDirectory(prefix='ptp-r7-accounting-') as temp:
 path=Path(temp)/'journal.sqlite';initialize(path,identity,old,e['scope'])
 with closing(sqlite3.connect(path)) as db,db:
  db.execute('UPDATE head SET generation=?,active=?',(3,d['attempt_id']))
  for row in prior:
   db.execute('INSERT INTO attempts VALUES (?,?,?)',(row['id'],encoded(row['declaration']),encoded(row['terminal'])))
  db.execute('INSERT INTO attempts VALUES (?,?,NULL)',(d['attempt_id'],encoded(d)))
 result=DispatchJournal(path,identity).reconcile(attempt_id=d['attempt_id'],terminal=terminal,new_ledger=new,new_scope=scope)
 assert result['status']=='RECONCILED' and result['generation']==4
files={'reconciled-ledger.json':new,'reconciled-scope.json':scope,'accounting-terminal.json':terminal}
for name,value in files.items():
 p=A/name
 if p.exists():assert json.loads(p.read_bytes())==value
 else:p.write_text(json.dumps(value,indent=2)+'\n')
payload={'identity':identity,'attempt_id':d['attempt_id'],'terminal':terminal,'ledger':new,'scope':scope}
code="""from pathlib import Path
import json,sys,sqlite3
p=Path('/home/chaw/patent-to-pilot-jobs/ptp-r7-calibration-20261112-v1')
sys.path[:0]=[str(p),str(p/'code/src'),'/home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031/venv/lib/python3.12/site-packages']
from patent_to_pilot.research.r6_dispatch_journal import DispatchJournal,document_hash
from r3_engine_client import Engine
state=Engine().inspect(p.name)['State']
assert state['Running'] is False and state['Pid']==0
"""+'payload=json.loads('+repr(json.dumps(payload))+')\n'+"""
receipt=p/'reconciliation.json'
if receipt.exists():
 value=json.loads(receipt.read_bytes())
 assert value['ledger_sha256']==document_hash(payload['ledger']) and value['scope_sha256']==document_hash(payload['scope'])
else:
 path=p.parent/'ptp-r6-control/dispatch.sqlite'
 with sqlite3.connect('file:'+str(path)+'?mode=ro',uri=True) as db:
  head=db.execute('SELECT identity,generation,ledger,scope,active FROM head').fetchone()
  attempt=db.execute('SELECT terminal FROM attempts WHERE id=?',(payload['attempt_id'],)).fetchone()
 if head[1]==4:
  assert head[0]==payload['identity'] and head[4] is None
  assert json.loads(head[2])==payload['ledger'] and json.loads(head[3])==payload['scope']
  assert attempt is not None and json.loads(attempt[0])==payload['terminal']
  value={'status':'RECONCILED','generation':4,'terminal_sha256':document_hash(payload['terminal'])}
 else:
  assert head[1]==3 and head[4]==payload['attempt_id']
  journal=DispatchJournal(path,payload['identity'])
  value=journal.reconcile(attempt_id=payload['attempt_id'],terminal=payload['terminal'],new_ledger=payload['ledger'],new_scope=payload['scope'])
 value.update(ledger_sha256=document_hash(payload['ledger']),scope_sha256=document_hash(payload['scope']))
 with receipt.open('x') as f:json.dump(value,f,indent=2)
print(json.dumps(value))
"""
r=subprocess.run(['ssh','-o','BatchMode=yes','chaw@100.77.149.83','python3 -'],input=code.encode(),capture_output=True,timeout=30)
if r.returncode:print(r.stderr.decode()[-3000:]);r.check_returncode()
receipt=json.loads(r.stdout)
assert receipt['status']=='RECONCILED' and receipt['generation']==4 and receipt['ledger_sha256']==document_hash(new)
assert json.loads(L.read_bytes()) in (old,new)
L.write_text(json.dumps(new,indent=2)+'\n')
done.write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'status':'RECONCILED','outcome':v['outcome'],'whole_wall_seconds':wall,
 'charged_seconds':charge,'model_calls':24,'GPU_remaining_seconds':new['gpu_remaining_seconds'],
 'fidelity_remaining_seconds':new['fidelity_generation_remaining_seconds'],'journal_generation':receipt['generation']}))
