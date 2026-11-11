"""One fixed CPU census job; approval must precede staging and execution."""
import hashlib
import json
from pathlib import Path
import subprocess
import time

NAME='ptp-sg-r3-census-20261111-v1'
JOB=Path('/home/chaw/patent-to-pilot-jobs')/NAME
IMAGE='sha256:cb33f7f771ecec2ef1225cf39b159591a040391bd73e4c01f00fdfc4c47611d2'


def inspect():
    return json.loads(subprocess.run(['docker','inspect',NAME],check=True,capture_output=True,text=True,timeout=10).stdout)[0]


def stop_owned():
    try:subprocess.run(['docker','stop','--time=5',NAME],capture_output=True,timeout=15)
    except (subprocess.SubprocessError,OSError):pass
    try:state=inspect()
    except (subprocess.SubprocessError,OSError,ValueError):state=None
    if state is None or state['State']['Running']:
        try:subprocess.run(['docker','kill',NAME],check=True,capture_output=True,timeout=10)
        except (subprocess.SubprocessError,OSError):pass
        state=inspect()
    if state['State']['Running']:raise RuntimeError('census termination unknown')
    return state


def validate_isolation(state,mounts):
    h=state['HostConfig']
    actual={(m['Source'],m['Destination'],not m['RW']) for m in state['Mounts']}
    if (actual!={(str(s),t,ro) for s,t,ro in mounts} or h['NetworkMode']!='none'
        or not h['ReadonlyRootfs'] or h['Privileged'] or h.get('DeviceRequests')
        or h['Memory']!=1536*1024**2 or h['MemorySwap']!=h['Memory']
        or h['NanoCpus']!=1_000_000_000 or state['Image']!=IMAGE
        or state['Config']['User']!='1000:1000' or h['CapDrop']!=['ALL']
        or 'no-new-privileges' not in h['SecurityOpt'] or h['LogConfig']['Type']!='none'
        or h['PidsLimit']!=64
        or not any(u['Name']=='fsize' and u['Soft']==8*1024**2 and u['Hard']==8*1024**2
                   for u in h.get('Ulimits',[]))):
        raise RuntimeError('census isolation mismatch')


def main():
    if Path(__file__).resolve().parent!=JOB:raise RuntimeError('fixed census job required')
    import resource
    resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2))
    raw=(JOB/'declaration.json').read_bytes();d=json.loads(raw)
    if d['run_id']!=NAME or d['wall_seconds']!=1800:raise RuntimeError('census declaration mismatch')
    root=JOB/'code'
    required={p.relative_to(root).as_posix() for p in (root/'src').rglob('*.py')}
    required|={'scripts/healthtech/run_sg_r3_census.py','scripts/healthtech/supervise_sg_r3_census.py'}
    if not required<=set(d['files_sha256']):raise RuntimeError('census pins incomplete')
    for name,expected in d['files_sha256'].items():
        p=(root/name).resolve()
        if not p.is_relative_to(root.resolve()) or hashlib.sha256(p.read_bytes()).hexdigest()!=expected:
            raise RuntimeError('census code changed')
    (JOB/'out').mkdir(exist_ok=False)
    start=time.monotonic()
    mounts=[(root,'/code',True),(JOB/'corpus.jsonl','/input/corpus.jsonl',True),
            (JOB/'declaration.json','/declaration.json',True),(JOB/'out','/out',False)]
    cmd=['docker','create','--pull=never','--name',NAME,'--network=none','--read-only',
         '--cap-drop=ALL','--security-opt=no-new-privileges','--user=1000:1000',
         '--cpus=1','--memory=1536m','--memory-swap=1536m','--pids-limit=64',
         '--log-driver=none','--ulimit','fsize=8388608:8388608',
         '--env','PYTHONDONTWRITEBYTECODE=1','--env','CUDA_VISIBLE_DEVICES=']
    for source,target,readonly in mounts:
        if not source.exists():raise RuntimeError('census mount missing')
        cmd+=['--mount',f'type=bind,src={source},dst={target}'+(',readonly' if readonly else '')]
    cmd+=['--entrypoint','python',IMAGE,'-s','/code/scripts/healthtech/run_sg_r3_census.py',hashlib.sha256(raw).hexdigest()]
    receipt={'status':'NOT_STARTED','gpu_seconds':0,'model_calls':0,'retry':False}
    try:
        subprocess.run(cmd,check=True,capture_output=True,timeout=30)
        state=inspect();validate_isolation(state,mounts)
        with (JOB/'isolation.json').open('x') as f:json.dump({'status':'PASS_BEFORE_START','mounts':state['Mounts'],'host_config':state['HostConfig']},f)
        receipt['status']='ATTACHING'
        try:
            result=subprocess.run(['docker','start','-a',NAME],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=1620)
            state=inspect()
            if state['State']['Running']:state=stop_owned()
            receipt.update(status='TERMINAL',attach_returncode=result.returncode,container_state=state['State'])
        except BaseException:
            try:receipt.update(status='INTERRUPTED_TERMINATED',container_state=stop_owned()['State'])
            except BaseException:receipt['status']='TERMINATION_UNKNOWN_NO_RETRY'
            raise
    finally:
        receipt['whole_wall_seconds']=time.monotonic()-start
        with (JOB/'terminal.json').open('x') as f:json.dump(receipt,f,indent=2)


if __name__=='__main__':main()
