from pathlib import Path
import subprocess,json,sys
A=Path('C:/Users/User/Desktop/myProject/patent-to-pilot/docs/healthtech/audits/ptp-r7-calibration-20261112')
s=json.loads((A/'freeze-summary.json').read_bytes());mode=sys.argv[1]
assert mode in ('start','observe')
base=f"from pathlib import Path\nimport json,sys\np=Path('/home/chaw/patent-to-pilot-jobs/{s['attempt_id']}')\n"
if mode=='start':
 code=base+f"""import subprocess
assert not (p/'launch.json').exists() and not (p/'admission.json').exists()
with (p/'controller.log').open('xb') as log:
 child=subprocess.Popen(['python3',str(p/'supervise_r7_calibration.py'),'{s['manifest_sha256']}'],cwd=p,stdout=log,stderr=log,start_new_session=True)
r={{'status':'CONTROLLER_LAUNCHED_NOT_COMPLETION','job':p.name,'pid':child.pid}}
with (p/'launch.json').open('x') as f:json.dump(r,f)
print(json.dumps(r))
"""
else:
 code=base+"""sys.path.insert(0,str(p))
from r3_engine_client import Engine,EngineError
r={'job':p.name}
try:r['container_state']=Engine().inspect(p.name)['State']
except EngineError as error:
 if error.status!=404:raise
 r['container_state']='NOT_CREATED'
for key,location in [('terminal','terminal.json'),('loaded_runtime','out/attempt/loaded-runtime.json'),('completion','out/attempt/completion.json'),('assessment','out/attempt/calibration/calibration-assessment.json'),('worker_failure','out/attempt/failure.json')]:
 if (p/location).exists():
  value=json.loads((p/location).read_bytes())
  if key=='assessment':value={k:v for k,v in value.items() if k not in ('events','costs')}
  r[key]=value
r['completed_generation_records']=len(list((p/'out/attempt/calibration').glob('unit-*/generation.json')))
r['dispatch_markers']=len(list((p/'out/attempt/calibration').glob('unit-*-diagnostics-private/backend-dispatch.json')))
if r.get('terminal',{}).get('status','').startswith('FAILED'):r['controller_log']=(p/'controller.log').read_text()[-3000:]
print(json.dumps(r))
"""
r=subprocess.run(['ssh','-o','BatchMode=yes','chaw@100.77.149.83','python3 -'],input=code.encode(),capture_output=True,timeout=30)
if r.returncode:print(r.stderr.decode()[-3000:]);r.check_returncode()
value=json.loads(r.stdout)
if mode=='start' or 'terminal' in value:(A/('launch.json' if mode=='start' else 'terminal-observation.json')).write_text(json.dumps(value,indent=2)+'\n')
else:(A/'latest-live-observation.json').write_text(json.dumps(value,indent=2)+'\n')
brief={k:v for k,v in value.items() if k not in ('completion',)}
if 'completion' in value:brief['completion']={k:v for k,v in value['completion'].items() if k!='events'}
print(json.dumps(brief))
