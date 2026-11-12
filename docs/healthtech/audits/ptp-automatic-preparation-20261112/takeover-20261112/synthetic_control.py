"""start: launch the staged CPU grammar controller ONCE. observe: read-only status.
Never restart on an observation timeout; inspect the same job instead."""
from pathlib import Path
import json, subprocess, sys
A = Path(__file__).resolve().parent/'synthetic-job'
s = json.loads((A/'freeze-summary.json').read_bytes()); mode = sys.argv[1]
assert mode in ('start', 'observe')
base = f"from pathlib import Path\nimport json,sys\np=Path('/home/chaw/patent-to-pilot-jobs/{s['job']}')\n"
if mode == 'start':
    code = base + f"""import subprocess
assert not (p/'launch.json').exists() and not (p/'admission.json').exists()
with (p/'controller.log').open('xb') as log:
 child=subprocess.Popen(['python3',str(p/'supervise_automatic_synthetic.py'),'{s['declaration_sha256']}'],cwd=p,stdout=log,stderr=log,start_new_session=True)
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
for key,loc in [('terminal','terminal.json'),('isolation_status','isolation.json'),('global_dispatch','global-dispatch.json'),('input_admission','out/attempt/before-model-input-admission.json'),('loaded_runtime','out/attempt/loaded-runtime.json'),('completion','out/attempt/completion.json'),('worker_failure','out/attempt/failure.json')]
r['call_markers']=sorted(x.name for x in (p/'out/attempt').glob('call-*.json')) if (p/'out/attempt').exists() else []:
 if (p/loc).exists():
  v=json.loads((p/loc).read_bytes())
  r[key]=v.get('status') if key=='isolation_status' else v
if 'terminal' in r and r['terminal'].get('status')!='TERMINAL':r['controller_log']=(p/'controller.log').read_text()[-3000:]
print(json.dumps(r))
"""
r = subprocess.run(['ssh', '-o', 'BatchMode=yes', 'chaw@100.77.149.83', 'python3 -'], input=code.encode(),
                   capture_output=True, timeout=45)
if r.returncode: print(r.stderr.decode()[-3000:]); r.check_returncode()
value = json.loads(r.stdout)
name = 'launch.json' if mode == 'start' else ('terminal-observation.json' if 'terminal' in value else 'latest-observation.json')
(A/name).write_text(json.dumps(value, indent=2) + '\n')
print(json.dumps(value)[:4000])
