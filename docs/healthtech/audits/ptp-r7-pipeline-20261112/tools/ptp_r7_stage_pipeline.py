from pathlib import Path
import json,hashlib,subprocess,tarfile
R=Path('C:/Users/User/Desktop/myProject/patent-to-pilot');A=R/'docs/healthtech/audits/ptp-r7-pipeline-20261112'
L=R/'docs/healthtech/audits/ptp-mtm-dapfam-resume-20261110/resource-ledger.json'
ledger=json.loads(L.read_bytes());s=ledger['r6_phase0_cpu'];r7=ledger['r7_cpu']
assert 'r7-pipeline-fixture' not in s['jobs'] and s['remote_cpu_reserved_seconds']==s['local_cpu_reserved_seconds']==r7['reserved_seconds']==0
accounted=sum(s.get(k,0) for k in ['cpu_prior_upper_bound_seconds','local_cpu_conservative_charged_seconds','local_cpu_measured_seconds','remote_cpu_charged_seconds'])
assert accounted+1300<=s['cpu_cap_seconds']
assert r7['conservative_charged_seconds']+r7['measured_seconds']+1300<=3600
A.mkdir(exist_ok=False)
names=[p.relative_to(R).as_posix() for p in (R/'src').rglob('*.py')]
scripts=['r3_engine_client.py','supervise_r3_engine_v2.py','supervise_sacr_r5_engine.py',
 'supervise_r6_calibration.py','run_r6_calibration.py','supervise_r7_calibration.py','run_r7_calibration.py',
 'inspect_qwen_weight_identity.py','supervise_r7_backend_preflight.py','qualify_r7_calibration_pipeline.py']
names+=['scripts/healthtech/'+n for n in scripts]
identity='docs/healthtech/audits/ptp-method-first-r2-weights-20261110/identity.json'
prompt='docs/healthtech/research/prompts/sacr_generic_views_v0.txt';names.extend([identity,prompt])
pins={n:hashlib.sha256((R/n).read_bytes()).hexdigest() for n in names}
old=json.loads((R/'docs/healthtech/audits/ptp-r6-phase0-execution-20261111/critic-declaration.json').read_bytes())
name='ptp-r7-pipeline-fixture-preflight-20261112-v1'
d={'run_id':name,'kind':'pipeline-fixture','wall_seconds':600,'cpu_threads':2,'total_ram_bytes':2*1024**3,
   'real_model_calls':0,'gpu_seconds':0,'retry':False,'files_sha256':pins,'identity_sha256':pins[identity],
   'lmfe_source_sha256':old['lmfe_source_sha256'],'owner_approval_sha256':r7['approval_sha256'],
   'generic_prompt_sha256':pins[prompt],'artifact_scope':'SIMULATED_AUTHORED_CPU_ONLY',
   'expected_authored_backend_invocations':31,'no_pretrained_weight_loading':True,
   'qualification_scope':'R7 calibration exact compact path; additional R6 bundle regression only'}
declaration=A/'pipeline-fixture-declaration.json'
with declaration.open('x') as f:json.dump(d,f,indent=2)
ap=A/'pipeline-fixture-approval.json'
with ap.open('x') as f:json.dump({'status':'APPROVED','basis':'Owner-approved R7 exact pipeline qualification before GPU',
 'owner_approval_sha256':d['owner_approval_sha256'],'declarations_sha256':{declaration.name:hashlib.sha256(declaration.read_bytes()).hexdigest()}},f,indent=2)
t=Path('C:/Users/User/AppData/Local/Temp/ptp-r7-pipeline-fixture.tar')
with tarfile.open(t,'x') as tar:
 for n in names:tar.add(R/n,arcname='code/'+n)
 tar.add(declaration,arcname='declaration.json');tar.add(ap,arcname='owner-approval.json')
 for n in ['r3_engine_client.py','supervise_r3_engine_v2.py','supervise_r7_backend_preflight.py']:tar.add(R/'scripts/healthtech'/n,arcname=n)
transport={'bytes':t.stat().st_size,'sha256':hashlib.sha256(t.read_bytes()).hexdigest()}
(A/'pipeline-fixture-transport.json').write_text(json.dumps(transport,indent=2)+'\n')
s['remote_cpu_reserved_seconds']=1200;s['local_cpu_conservative_charged_seconds']+=100
r7['reserved_seconds']=1200;r7['conservative_charged_seconds']+=100
s['jobs']['r7-pipeline-fixture']={'status':'RESERVED_BEFORE_STAGING','declaration_sha256':hashlib.sha256(declaration.read_bytes()).hexdigest()}
L.write_text(json.dumps(ledger,indent=2)+'\n')
host='chaw@100.77.149.83';job='/home/chaw/patent-to-pilot-jobs/'+name
probe="""from pathlib import Path
import sys,json,sqlite3
b=Path('/home/chaw/patent-to-pilot-jobs');sys.path.insert(0,str(b/'ptp-r6-calibration-20261111-v1'))
from r3_engine_client import Engine
states={n:Engine().inspect(n)['State'] for n in ['ptp-r6-calibration-20261111-v1','ptp-sg-compact-input-preflight-20261111-v1']}
assert all(not s['Running'] and s['Pid']==0 for s in states.values())
with sqlite3.connect('file:'+str(b/'ptp-r6-control/dispatch.sqlite')+'?mode=ro',uri=True) as db:
 h=db.execute('SELECT generation,active FROM head').fetchone()
assert h==(1,None)
assert not (b/'ptp-r7-pipeline-fixture-preflight-20261112-v1').exists()
print(json.dumps({'states':states,'journal_generation':h[0],'active':h[1]}))
"""
result=subprocess.run(['ssh','-o','BatchMode=yes',host,'python3 -'],input=probe.encode(),capture_output=True,check=True,timeout=30)
(A/'pipeline-fixture-prior-idle.json').write_bytes(result.stdout)
subprocess.run(['ssh','-o','BatchMode=yes',host,'mkdir '+job],check=True,timeout=30)
subprocess.run(['scp','-q',str(t),host+':'+job+'/transport.tar'],check=True,timeout=60)
code=f"from pathlib import Path\nimport tarfile,hashlib\np=Path('{job}');t=p/'transport.tar'\nassert hashlib.sha256(t.read_bytes()).hexdigest()=='{transport['sha256']}'\nwith tarfile.open(t) as archive:\n assert all(not Path(m.name).is_absolute() and '..' not in Path(m.name).parts for m in archive.getmembers())\n archive.extractall(p,filter='data')\n"
subprocess.run(['ssh','-o','BatchMode=yes',host,'python3 -'],input=code.encode(),check=True,timeout=30)
s['jobs']['r7-pipeline-fixture']['status']='STAGED';L.write_text(json.dumps(ledger,indent=2)+'\n')
print(json.dumps({'status':'STAGED','cpu_reserved_seconds':1200,'local_conservative_additional_seconds':100,
 'prior_accounted_seconds':accounted,'transport_bytes':transport['bytes']}))
