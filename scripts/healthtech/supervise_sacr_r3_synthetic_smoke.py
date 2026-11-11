"""One-use 1800-second R3 synthetic smoke supervisor, no benchmark mounts."""
import hashlib
import json
from pathlib import Path
import signal
import subprocess
import time
import sys

NAME='ptp-sacr-r3-synthetic-smoke-20261111-v1'
JOB=Path('/home/chaw/patent-to-pilot-jobs')/NAME
BASE=JOB.parent/'research-product-o1-o4-20261031'
GPU='GPU-277ccc57-c3e5-0731-cd49-f4f8695f7089'
IMAGE='sha256:cb33f7f771ecec2ef1225cf39b159591a040391bd73e4c01f00fdfc4c47611d2'
WALL=1800
OUTPUT_CAP=64*1024**2


def output_bytes():
    # Include attach logs; Docker's own log driver is disabled below.
    return sum(p.stat().st_size for folder in ('out','logs')
               for p in (JOB/folder).rglob('*') if p.is_file())


def write(name,value):
    with (JOB/name).open('x') as f: json.dump(value,f,indent=2)


def inspect():
    return json.loads(subprocess.run(['docker','inspect',NAME],check=True,capture_output=True,
                                    text=True,timeout=10).stdout)[0]


def stop_owned():
    try:
        subprocess.run(['docker','stop','--time=5',NAME],capture_output=True,timeout=15)
    except (subprocess.SubprocessError,OSError):
        pass  # A lost stop response is not proof the container stopped.
    try: state=inspect()
    except (subprocess.SubprocessError,OSError,ValueError): state=None
    if state is None or state['State']['Running']:
        try: subprocess.run(['docker','kill',NAME],capture_output=True,timeout=10)
        except (subprocess.SubprocessError,OSError): pass
        state=inspect()  # Failure here remains UNKNOWN, never restart.
    if state['State']['Running']: raise RuntimeError('termination unverified')
    return state


def monitor(child,stop):
    reason='EXITED'
    while child.poll() is None:
        if time.monotonic()>=stop:
            reason='TIMEOUT'; stop_owned(); break
        if output_bytes()>OUTPUT_CAP:
            reason='OUTPUT_LIMIT'; stop_owned(); break
        time.sleep(1)
    rc=child.wait(timeout=15)
    state=inspect()
    if state['State']['Running']:
        reason='CLIENT_EXITED_CONTAINER_RUNNING'; state=stop_owned()
    return reason,rc,state


def main():
    if Path(__file__).resolve().parent != JOB: raise RuntimeError('fixed job path required')
    import resource  # Linux host only; fail before dispatch if unavailable.
    resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
    resource.setrlimit(resource.RLIMIT_FSIZE,(OUTPUT_CAP,OUTPUT_CAP))
    raw=(JOB/'declaration.json').read_bytes(); d=json.loads(raw)
    if d['run_id']!=NAME or d['wall_seconds']!=WALL or d['maximum_calls']!=3:
        raise RuntimeError('declaration scope mismatch')
    sys.path.insert(0,str(JOB/'code/src'))
    from patent_to_pilot.research.sacr_r3_runtime_guards import validate_sources,validate_budget
    validate_sources(JOB/'code',d['files_sha256'])
    ledger_raw=(JOB/'resource-ledger.json').read_bytes(); ledger=json.loads(ledger_raw)
    if hashlib.sha256(ledger_raw).hexdigest()!=d['resource_ledger_sha256']:
        raise RuntimeError('ledger hash mismatch')
    validate_budget(ledger,WALL)
    used=subprocess.run(['nvidia-smi','--query-compute-apps=pid,gpu_uuid','--format=csv,noheader'],
        check=True,capture_output=True,text=True,timeout=10).stdout
    if GPU in used: raise RuntimeError('approved GPU occupied')
    (JOB/'out').mkdir(exist_ok=False)
    (JOB/'logs').mkdir(exist_ok=False)
    write('reservation.json',{'seconds':WALL,'maximum_calls':3,'retry':False,'started_unix':time.time()})
    started=time.monotonic(); stop=started+WALL-240
    mounts=[(JOB/'code','/code',True),(JOB/'out','/out',False),
        (JOB/'declaration.json','/declaration.json',True),(JOB/'resource-ledger.json','/resource-ledger.json',True),
        (BASE/'venv/lib/python3.12/site-packages','/deps',True),(BASE/'models/qwen3-8b','/models/qwen3-8b',True),
        (BASE/('models/.'+GPU+'.lock'),'/models/.'+GPU+'.lock',False)]
    cmd=['docker','create','--pull=never','--name',NAME,'--network=none','--read-only',
         '--cap-drop=ALL','--security-opt=no-new-privileges','--user=1000:1000','--cpus=8',
         '--memory=31g','--memory-swap=31g','--pids-limit=256','--tmpfs','/tmp:rw,nosuid,size=268435456',
         '--log-driver=none','--ulimit','fsize=67108864:67108864',
         '--gpus','device='+GPU]
    for src,dest,ro in mounts:
        if not src.exists(): raise RuntimeError('mount missing')
        cmd+=['--mount',f'type=bind,src={src},dst={dest}'+(',readonly' if ro else '')]
    for env in ['PYTHONPATH=/code/src:/deps','PYTHONDONTWRITEBYTECODE=1','CUDA_VISIBLE_DEVICES='+GPU,
                'HF_HUB_OFFLINE=1','TRANSFORMERS_OFFLINE=1','TOKENIZERS_PARALLELISM=false',
                'OMP_NUM_THREADS=8','MKL_NUM_THREADS=8','OPENBLAS_NUM_THREADS=8','NUMEXPR_NUM_THREADS=8','RAYON_NUM_THREADS=8']:
        cmd+=['--env',env]
    cmd+=['--entrypoint=python',IMAGE,'-s','/code/scripts/healthtech/run_sacr_r3_synthetic_smoke.py',
          str(stop),hashlib.sha256(raw).hexdigest()]
    subprocess.run(cmd,check=True,capture_output=True,timeout=30)
    state=inspect(); h=state['HostConfig']
    actual={(m['Source'],m['Destination'],not m['RW']) for m in state['Mounts'] if m['Type']=='bind'}
    if (actual!={(str(s),dest,ro) for s,dest,ro in mounts} or h['NetworkMode']!='none'
            or not h['ReadonlyRootfs'] or h['Privileged'] or h['Memory']!=31*1024**3
            or h['MemorySwap']!=h['Memory'] or h['NanoCpus']!=8_000_000_000
            or h['PidsLimit']!=256
            or h['LogConfig']['Type']!='none'
            or not any(u['Name']=='fsize' and u['Soft']==OUTPUT_CAP and u['Hard']==OUTPUT_CAP
                       for u in h.get('Ulimits',[]))
            or state['Config']['User']!='1000:1000' or state['Image']!=IMAGE
            or h['DeviceRequests'][0]['DeviceIDs']!=[GPU] or h['CapDrop']!=['ALL']
            or 'no-new-privileges' not in h['SecurityOpt']):
        raise RuntimeError('isolation mismatch; not started')
    write('isolation.json',{'status':'PASS_BEFORE_START','mounts':state['Mounts'],'host_config':h})
    signal.signal(signal.SIGTERM,lambda *_:(_ for _ in ()).throw(InterruptedError('supervisor interrupted')))
    with (JOB/'logs/stdout').open('xb') as out,(JOB/'logs/stderr').open('xb') as err:
        child=subprocess.Popen(['docker','start','-a',NAME],stdout=out,stderr=err)
        try:
            write('child.json',{'pid':child.pid,'container':NAME})
            reason,rc,state=monitor(child,stop)
        except BaseException as original_error:
            try:
                state=stop_owned()
                cleanup={'status':'TERMINATED','container_state':state['State']}
            except BaseException as cleanup_error:
                cleanup={'status':'OWNED_TERMINATION_UNKNOWN','cleanup_exception':type(cleanup_error).__name__}
            write('interrupted.json',{**cleanup,'original_exception':type(original_error).__name__,
                'wall_seconds':time.monotonic()-started,'declaration_sha256':hashlib.sha256(raw).hexdigest(),
                'retry':False,'costs':'WHOLE_SUPERVISOR_ELAPSED_REQUIRES_LEDGER_CHARGE'})
            raise
    write('terminal.json',{'status':reason,'wall_seconds':time.monotonic()-started,
        'attach_returncode':rc,'container_state':state['State'],'retry':False})
    print(json.dumps({'status':reason,'exit_code':state['State']['ExitCode']}))


if __name__=='__main__': main()
