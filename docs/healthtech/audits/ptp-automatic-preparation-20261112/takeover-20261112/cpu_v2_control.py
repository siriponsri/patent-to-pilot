"""cpu_v2_control.py <grammar|fixture> <start|observe>: launch ONCE or observe read-only.
Never restart on an observation timeout."""
from pathlib import Path
import json, subprocess, sys
kind, mode = sys.argv[1], sys.argv[2]
A = Path(__file__).resolve().parent/(sys.argv[3] if len(sys.argv) > 3 else 'cpu-v2'); assert kind in ('grammar', 'fixture', 'census') and mode in ('start', 'observe')
j = json.loads((A/'freeze-summary.json').read_bytes())['jobs'][kind]
base = f"from pathlib import Path\nimport json,sys\np=Path('/home/chaw/patent-to-pilot-jobs/{j['job']}')\n"
if mode == 'start':
    code = base + f"""import subprocess
assert not (p/'launch.json').exists() and not (p/'admission.json').exists()
with (p/'controller.log').open('xb') as log:
 child=subprocess.Popen(['python3',str(p/'{j['supervisor']}'),'{j['declaration_sha256']}'],cwd=p,stdout=log,stderr=log,start_new_session=True)
r={{'status':'CONTROLLER_LAUNCHED_NOT_COMPLETION','job':p.name,'pid':child.pid}}
with (p/'launch.json').open('x') as f:json.dump(r,f)
print(json.dumps(r))
"""
else:
    code = base + """sys.path.insert(0,str(p))
from r3_engine_client import Engine,EngineError
r={'job':p.name}
try:r['container_state']=Engine().inspect(p.name)['State']
except EngineError as error:
 if error.status!=404:raise
 r['container_state']='NOT_CREATED'
for key,loc in [('terminal','terminal.json'),('isolation_status','isolation.json'),('qualification','out/attempt/qualification.json'),('receipt','out/receipt.json'),('completion','out/attempt/completion.json'),('aggregate','out/attempt/aggregate.json'),('worker_failure','out/attempt/failure.json')]:
 if (p/loc).exists():
  v=json.loads((p/loc).read_bytes())
  r[key]=v.get('status') if key=='isolation_status' else v
if 'terminal' in r and r['terminal'].get('status')!='TERMINAL':r['controller_log']=(p/'controller.log').read_text()[-3000:]
print(json.dumps(r))
"""
r = subprocess.run(['ssh', '-o', 'BatchMode=yes', 'chaw@100.77.149.83', 'python3 -'], input=code.encode(), capture_output=True, timeout=45)
if r.returncode: print(r.stderr.decode()[-3000:]); r.check_returncode()
value = json.loads(r.stdout)
name = kind + ('-launch.json' if mode == 'start' else ('-terminal-observation.json' if 'terminal' in value else '-latest-observation.json'))
(A/name).write_text(json.dumps(value, indent=2) + '\n')
print(json.dumps(value)[:3000])
