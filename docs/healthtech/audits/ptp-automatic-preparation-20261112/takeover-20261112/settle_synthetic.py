"""Independently verify the synthetic GPU job terminal state and reconcile ONCE.

Refuses unless Docker reports exited/PID0 (or proven never-created). Whole wall
is charged once to GPU and fidelity; host CPU is telemetry only (unknown worker CPU -> physical bound
wall x (container CPUs + controller), fixed 2026-11-13). Idempotent:
at generation 14 it only verifies.
"""
from pathlib import Path
import hashlib, json, subprocess, sys
R = Path('C:/Users/User/Desktop/myProject/patent-to-pilot'); sys.path.insert(0, str(R/'src'))
A = R/'docs/healthtech/audits/ptp-automatic-preparation-20261112/takeover-20261112'
NAME, SUB = (sys.argv[1], sys.argv[2]) if len(sys.argv) == 3 else ('ptp-auto-synthetic-20261112-v1', 'synthetic-job')
S = A/SUB
L = R/'docs/healthtech/audits/ptp-mtm-dapfam-resume-20261110/resource-ledger.json'
from patent_to_pilot.research.r6_dispatch_journal import document_hash
JOBS = '/home/chaw/patent-to-pilot-jobs'; JOB = JOBS + '/' + NAME
IDENTITY = '2b7c2aae40fafff474721b87ff1531569aeaa29990f8234bea32ac2d6b744db4'
d = json.loads((S/'declaration.json').read_bytes())
code = """import json,sys,sqlite3,hashlib,subprocess
from pathlib import Path
p=Path('""" + JOB + """');sys.path[:0]=[str(p),str(p/'code/src'),'""" + JOBS + """/research-product-o1-o4-20261031/venv/lib/python3.12/site-packages']
from r3_engine_client import Engine,EngineError
from patent_to_pilot.research.r6_dispatch_journal import document_hash
from patent_to_pilot.research.automatic_dispatch_journal import AutomaticDispatchJournal
path=Path('""" + JOBS + """/ptp-r6-control/dispatch.sqlite')
def head():
 with sqlite3.connect('file:'+str(path)+'?mode=ro',uri=True) as db:return db.execute('SELECT generation,ledger,scope,active FROM head').fetchone()
def rd(rel):
 f=p/rel
 return json.loads(f.read_bytes()) if f.exists() else None
sup=rd('terminal.json');assert sup is not None,'supervisor terminal receipt missing'
try:
 info=Engine().inspect(p.name);state=info['State'];cpus=info['HostConfig']['NanoCpus']/1e9
except EngineError as e:
 if e.status!=404:raise
 state=None;cpus=None
out=p/'out/attempt'
markers=sorted(x.name for x in out.glob('call-*.json')) if out.exists() else []
gens=sorted(str(x.relative_to(out)) for x in out.glob('backend/**/generation.json')) if out.exists() else []
completion=rd('out/attempt/completion.json');failure=rd('out/attempt/failure.json')
worker_cpu=(completion or failure or {}).get('process_cpu_seconds')
files={}
for f in sorted(p.rglob('*')):
 if f.is_file() and 'code' not in f.relative_to(p).parts and f.name!='transport.tar':files[str(f.relative_to(p))]=hashlib.sha256(f.read_bytes()).hexdigest()
evidence={'supervisor_terminal':sup,'docker_state':state,'call_markers':markers,'normal_return_records':gens,
 'completion':completion,'failure':failure,'file_sha256':files}
ev_sha=document_hash(evidence)
d=json.loads((p/'dispatch/declaration.json').read_bytes())
if state is not None:
 assert state['Running'] is False and state['Pid']==0 and type(state['ExitCode']) is int,'not authoritatively terminal'
term={'attempt_id':p.name,'container_name':p.name,'declaration_sha256':document_hash(d),
 'whole_wall_seconds':sup['whole_wall_seconds'],'known_model_calls':len(gens),
 'calls_complete':len(gens)==len(markers),'cost_evidence_sha256':ev_sha,
 'aggregate_cpu_seconds':(worker_cpu+sup.get('controller_cpu_seconds',60)) if type(worker_cpu) in (int,float) else (sup['whole_wall_seconds']*(cpus+1) if cpus else d['cpu_seconds']+sup.get('controller_cpu_seconds',60)),
 'aggregate_cpu_basis':'worker process_cpu + controller' if type(worker_cpu) in (int,float) else ('worker CPU unknown: physical upper bound wall x (container CPUs + controller)' if cpus else 'worker CPU unknown: no container; declared safety bound recorded')}
if state is None:term.update(container_outcome='NO_CONTAINER',create_request_sent=False)
else:term['container_state']=state
h=head();applied=False
if h[3]==p.name:
 AutomaticDispatchJournal(path,'""" + IDENTITY + """').reconcile(attempt_id=p.name,terminal=term,terminal_sha256=document_hash(term),expected_generation=h[0])
 applied=True
h=head();assert h[3] is None and p.name in json.loads(h[2])['automatic_study']['stage_costs']
gpu=subprocess.run(['nvidia-smi','--query-compute-apps=pid,gpu_uuid','--format=csv,noheader'],capture_output=True,text=True,timeout=10,check=True).stdout
scope=json.loads(h[2])
print(json.dumps({'applied_now':applied,'generation':h[0],'terminal':term,'evidence':evidence,'ledger':json.loads(h[1]),
 'study':{k:scope['automatic_study'][k] for k in ('status','stage_costs')},
 'approved_gpu_occupied':'GPU-277ccc57-c3e5-0731-cd49-f4f8695f7089' in gpu}))
"""
r = subprocess.run(['ssh', '-o', 'BatchMode=yes', 'chaw@100.77.149.83', 'python3 -'], input=code.encode(), capture_output=True, timeout=120)
if r.returncode: print(r.stderr.decode()[-3000:]); r.check_returncode()
v = json.loads(r.stdout)
old = json.loads(L.read_bytes()); new = v.pop('ledger')
def order(ref, val):
    if isinstance(ref, dict) and isinstance(val, dict):
        o = {k: order(ref[k], val[k]) for k in ref if k in val}; o.update({k: x for k, x in val.items() if k not in ref}); return o
    if isinstance(ref, list) and isinstance(val, list) and len(ref) == len(val): return [order(a, b) for a, b in zip(ref, val)]
    return val
for k in old:
    if k not in ('gpu_conservative_charged_seconds', 'gpu_remaining_seconds', 'fidelity_generation_charged_seconds',
                 'fidelity_generation_remaining_seconds', 'model_calls', 'model_calls_count_is_lower_bound',
                 'gpu_stage_host_cpu_telemetry_seconds'):
        assert new[k] == old[k] or k == 'r6_phase0_cpu' and new[k] == old[k], k
L.write_text(json.dumps(order(old, new), indent=2) + '\n')
for n, x in (('terminal-evidence.json', v['evidence']), ('settlement-terminal.json', v['terminal']),
             ('settlement.json', {k: v[k] for k in ('applied_now', 'generation', 'study', 'approved_gpu_occupied')} | {'ledger_sha256': document_hash(new)})):
    (S/n).write_text(json.dumps(x, indent=2) + '\n')
print(json.dumps({'applied_now': v['applied_now'], 'generation': v['generation'], 'study': v['study'],
                  'gpu_charged': new['gpu_conservative_charged_seconds'], 'fidelity_remaining': new['fidelity_generation_remaining_seconds'],
                  'model_calls': new['model_calls'], 'telemetry_cpu': new.get('gpu_stage_host_cpu_telemetry_seconds'),
                  'approved_gpu_occupied': v['approved_gpu_occupied']}))
