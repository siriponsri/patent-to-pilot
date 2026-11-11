from pathlib import Path
import subprocess,json
R=Path('C:/Users/User/Desktop/myProject/patent-to-pilot');A=R/'docs/healthtech/audits/ptp-r7-calibration-20261112'
A.mkdir(exist_ok=True)
code="""from pathlib import Path
import json,sys,subprocess,shutil
b=Path('/home/chaw/patent-to-pilot-jobs');sys.path.insert(0,str(b/'ptp-r6-pipeline-fixture-preflight-20261111-v1'))
from r3_engine_client import Engine,EngineError
e=Engine();states=[];total=0
for p in b.glob('ptp-*'):
 if not p.is_dir():continue
 total+=sum(f.stat().st_size for f in p.rglob('*') if f.is_file() and not f.is_symlink())
 try:s=e.inspect(p.name)['State']
 except EngineError as error:
  if error.status!=404:raise
  continue
 assert not s['Running'] and s['Pid']==0,(p.name,s['Status'])
 states.append({'job':p.name,'status':s['Status'],'pid':s['Pid']})
gpu=subprocess.run(['nvidia-smi','--query-compute-apps=pid,gpu_uuid','--format=csv,noheader'],capture_output=True,text=True,check=True,timeout=10).stdout
assert 'GPU-277ccc57-c3e5-0731-cd49-f4f8695f7089' not in gpu
assert not (b/'ptp-r7-calibration-20261112-v1').exists()
import sqlite3
with sqlite3.connect('file:'+str(b/'ptp-r6-control/dispatch.sqlite')+'?mode=ro',uri=True) as db:
 head=db.execute('SELECT identity,generation,ledger,scope,active FROM head').fetchone()
 attempts=db.execute('SELECT id,declaration,terminal FROM attempts').fetchall()
assert head[1]==1 and head[4] is None
mem=dict((line.split(':')[0],line.split(':')[1].strip()) for line in Path('/proc/meminfo').read_text().splitlines())
print(json.dumps({'project_job_logical_bytes':total,'free_bytes':shutil.disk_usage(b).free,'terminal_states':states,
 'approved_gpu_occupied':False,'journal_head':{'identity':head[0],'generation':head[1],'ledger':json.loads(head[2]),'scope':json.loads(head[3]),'active':head[4]},'attempts':[{'id':a[0],'declaration':json.loads(a[1]),'terminal':json.loads(a[2]) if a[2] else None} for a in attempts],'calibration_job_absent':True,'memory_available':mem['MemAvailable']}))
"""
r=subprocess.run(['ssh','-o','BatchMode=yes','chaw@100.77.149.83','python3 -'],input=code.encode(),capture_output=True,check=True,timeout=60)
remote=json.loads(r.stdout)
local=sum(p.stat().st_size for p in R.rglob('*') if p.is_file() and not p.is_symlink())
old=json.loads((R/'docs/healthtech/audits/ptp-r6-phase0-execution-20261111/admission.json').read_bytes())
bound=old['prior_disk_bound_including_R5_reservation']+remote['project_job_logical_bytes']+local+old['r6_disk_reserved_bytes']
assert bound<=40*1024**3 and remote['free_bytes']>4*1024**3
receipt={'status':'PASS_CURRENT_IDLE_AND_CONSERVATIVE_DISK','remote':remote,'local_logical_bytes':local,
 'retained_prior_disk_bound':old['prior_disk_bound_including_R5_reservation'],'R6_reserve_bytes':old['r6_disk_reserved_bytes'],
 'combined_conservative_bound_bytes':bound,'disk_cap_bytes':40*1024**3,'no_model_or_GPU_dispatch':True}
(A/'current-resource-probe.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'status':receipt['status'],'disk_bound_GiB':bound/1024**3,'terminal_project_containers':len(remote['terminal_states']),
 'GPU_busy':False,'memory_available':remote['memory_available']}))
