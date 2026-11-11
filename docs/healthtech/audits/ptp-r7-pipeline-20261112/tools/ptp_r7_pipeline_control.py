from pathlib import Path
import subprocess,json,sys
action=sys.argv[1];assert action in ('start','observe')
name='ptp-r7-pipeline-fixture-preflight-20261112-v1'
prefix=f"from pathlib import Path\nimport subprocess,json,sys\np=Path('/home/chaw/patent-to-pilot-jobs/{name}')\n"
if action=='start':
 code=prefix+"""assert not (p/'launch.json').exists() and not (p/'admission.json').exists()
with (p/'controller.log').open('xb') as log:
 child=subprocess.Popen(['python3',str(p/'supervise_r7_backend_preflight.py')],cwd=p,stdout=log,stderr=log,start_new_session=True)
receipt={'job':p.name,'pid':child.pid,'status':'CONTROLLER_LAUNCHED_NOT_COMPLETION'}
with (p/'launch.json').open('x') as f:json.dump(receipt,f)
print(json.dumps(receipt))
"""
else:
 code=prefix+"""sys.path.insert(0,str(p))
from r3_engine_client import Engine,EngineError
result={'job':p.name,'authored_calibration_records':len(list((p/'out/attempt/calibration').glob('unit-*/generation.json')))}
try:result['container_state']=Engine().inspect(p.name)['State']
except EngineError as error:
 if error.status!=404:raise
 result['container_state']='NOT_CREATED'
for key,location in [('terminal','terminal.json'),('receipt','out/receipt.json')]:
 if (p/location).exists():result[key]=json.loads((p/location).read_bytes())
if 'terminal' in result and result.get('receipt',{}).get('status')!='PASS_AUTHORED_FULL_CALIBRATION_PIPELINE':
 result['controller_log']=(p/'controller.log').read_text()[-5000:]
 if (p/'out/worker.log').exists():result['worker_log']=(p/'out/worker.log').read_text()[-5000:]
print(json.dumps(result))
"""
r=subprocess.run(['ssh','-o','BatchMode=yes','chaw@100.77.149.83','python3 -'],input=code.encode(),capture_output=True,timeout=30)
r.check_returncode();v=json.loads(r.stdout)
a=Path('C:/Users/User/Desktop/myProject/patent-to-pilot/docs/healthtech/audits/ptp-r7-pipeline-20261112')
if action=='start':
 with (a/'launch.json').open('x') as f:json.dump(v,f,indent=2)
elif 'terminal' in v:
 (a/'terminal-observation.json').write_text(json.dumps(v,indent=2)+'\n')
print(json.dumps(v))
