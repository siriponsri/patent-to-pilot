"""One conservative closeout CPU charge, exact journal synchronization, live audit."""
from pathlib import Path
import json,copy,subprocess,sys,hashlib
R=Path('C:/Users/User/Desktop/myProject/patent-to-pilot');sys.path.insert(0,str(R/'src'))
A=R/'docs/healthtech/audits/ptp-r7-calibration-20261112'
L=R/'docs/healthtech/audits/ptp-mtm-dapfam-resume-20261110/resource-ledger.json'
from patent_to_pilot.research.r6_dispatch_journal import document_hash
from patent_to_pilot.research.r7_dispatch_journal import validate_cpu_change,CPU_CHARGES,CPU_RESERVES
old=json.loads((A/'reconciled-ledger.json').read_bytes());new=copy.deepcopy(old)
new['r6_phase0_cpu']['local_cpu_conservative_charged_seconds']+=100
new['r7_cpu']['conservative_charged_seconds']+=100
assert json.loads(L.read_bytes()) in (old,new)
d=json.loads((A/'dispatch/declaration.json').read_bytes())
receipt={'status':'VERIFIED_CPU_ONLY_RECONCILIATION','journal_identity':d['approval_sha256'],
 'owner_approval_sha256':d['candidate_owner_approval_sha256'],'model_calls':0,'gpu_seconds':0,
 'old_ledger_sha256':document_hash(old),'new_ledger_sha256':document_hash(new),
 'cpu_deltas':{k:new['r6_phase0_cpu'].get(k,0)-old['r6_phase0_cpu'].get(k,0) for k in CPU_CHARGES+CPU_RESERVES},
 'evidence_sha256':[hashlib.sha256((A/n).read_bytes()).hexdigest() for n in
 ['terminal-verification.json','reconciliation.json','calibration-diagnosis.json']],
 'charge_basis':'100 conservative CPU seconds for terminal verification, diagnosis, bookkeeping, report/audit/publication closeout; no further model work.'}
validate_cpu_change(old,new,receipt)
payload={'ledger':new,'receipt':receipt,'receipt_sha256':document_hash(receipt),
         'scope':json.loads((A/'reconciled-scope.json').read_bytes())}
code="""from pathlib import Path
import json,sys,sqlite3,subprocess
p=Path('/home/chaw/patent-to-pilot-jobs/ptp-r7-calibration-20261112-v1')
sys.path[:0]=[str(p),str(p/'code/src'),'/home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031/venv/lib/python3.12/site-packages']
from patent_to_pilot.research.r7_dispatch_journal import R7DispatchJournal
from patent_to_pilot.research.r6_dispatch_journal import document_hash
from r3_engine_client import Engine,EngineError
"""+'payload=json.loads('+repr(json.dumps(payload))+')\n'+"""
path=p.parent/'ptp-r6-control/dispatch.sqlite'
with sqlite3.connect('file:'+str(path)+'?mode=ro',uri=True) as db:
 head=db.execute('SELECT identity,generation,ledger,scope,active FROM head').fetchone()
if head[1]==4:
 R7DispatchJournal(path,payload['receipt']['journal_identity']).sync_cpu_ledger(expected_generation=4,
  new_ledger=payload['ledger'],receipt=payload['receipt'],receipt_sha256=payload['receipt_sha256'])
with sqlite3.connect('file:'+str(path)+'?mode=ro',uri=True) as db:
 head=db.execute('SELECT identity,generation,ledger,scope,active FROM head').fetchone()
 attempts=db.execute('SELECT id,terminal FROM attempts ORDER BY id').fetchall()
 transitions=db.execute('SELECT generation,kind,receipt FROM r7_transitions ORDER BY generation').fetchall()
assert head[0]==payload['receipt']['journal_identity'] and head[1]==5 and head[4] is None
assert json.loads(head[2])==payload['ledger'] and json.loads(head[3])==payload['scope']
assert json.loads(transitions[-1][2])==payload['receipt']
assert len(attempts)==2 and all(row[1] is not None for row in attempts)
states=[];engine=Engine()
for job in p.parent.glob('ptp-*'):
 if not job.is_dir():continue
 try:state=engine.inspect(job.name)['State']
 except EngineError as error:
  if error.status!=404:raise
  continue
 assert not state['Running'] and state['Pid']==0,(job.name,state)
 states.append({'job':job.name,'status':state['Status'],'pid':state['Pid']})
gpu=subprocess.run(['nvidia-smi','--query-compute-apps=pid,gpu_uuid','--format=csv,noheader'],capture_output=True,text=True,check=True,timeout=10).stdout
assert 'GPU-277ccc57-c3e5-0731-cd49-f4f8695f7089' not in gpu
print(json.dumps({'status':'TERMINAL_ACCOUNTING_AND_IDLE_VERIFIED','generation':5,'active':None,
 'ledger_sha256':document_hash(payload['ledger']),'scope_sha256':document_hash(payload['scope']),
 'cpu_receipt_sha256':payload['receipt_sha256'],'attempts':[{'id':i,'terminal_sha256':document_hash(json.loads(t)),
 'failure_axis':json.loads(t)['failure_axis']} for i,t in attempts],
 'transitions':[{'generation':g,'kind':k,'receipt_sha256':document_hash(json.loads(r))} for g,k,r in transitions],
 'terminal_containers':states,'approved_gpu_occupied':False,'new_model_calls':0}))
"""
r=subprocess.run(['ssh','-o','BatchMode=yes','chaw@100.77.149.83','python3 -'],input=code.encode(),capture_output=True,timeout=45)
if r.returncode:print(r.stderr.decode()[-3000:]);r.check_returncode()
verification=json.loads(r.stdout)
for name,value in [('closeout-cpu-receipt.json',receipt),('final-ledger.json',new),('final-state-verification.json',verification)]:
 p=A/name
 if p.exists():assert json.loads(p.read_bytes())==value
 else:p.write_text(json.dumps(value,indent=2)+'\n')
assert json.loads(L.read_bytes()) in (old,new)
L.write_text(json.dumps(new,indent=2)+'\n')
print(json.dumps({'status':verification['status'],'generation':5,'terminal_containers':len(verification['terminal_containers']),
 'R7_CPU_seconds':new['r7_cpu']['conservative_charged_seconds']+new['r7_cpu']['measured_seconds'],
 'GPU_charged_seconds':new['gpu_conservative_charged_seconds'],'fidelity_charged_seconds':new['fidelity_generation_charged_seconds']}))
