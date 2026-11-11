"""One CPU-only aggregate read of a sealed dev evaluator artifact."""
import json
from pathlib import Path
import subprocess
import time

NAME='ptp-native-exposure-20261111-v1'
JOB=Path('/home/chaw/patent-to-pilot-jobs')/NAME
INPUT=JOB.parent/'ptp-native-evaluator-20261110-v2/out/attempt/private-per-query.json'
IMAGE='sha256:cb33f7f771ecec2ef1225cf39b159591a040391bd73e4c01f00fdfc4c47611d2'


def inspect():
    return json.loads(subprocess.run(['docker','inspect',NAME],check=True,capture_output=True,text=True,timeout=10).stdout)[0]


def main():
    if Path(__file__).resolve().parent!=JOB: raise RuntimeError('fixed job path required')
    (JOB/'out').mkdir(exist_ok=False)
    mounts=[(JOB/'summarize.py','/code/summarize.py',True),(INPUT,'/input/private-per-query.json',True),(JOB/'out','/out',False)]
    cmd=['docker','create','--pull=never','--name',NAME,'--network=none','--read-only',
         '--cap-drop=ALL','--security-opt=no-new-privileges','--user=1000:1000',
         '--cpus=1','--memory=512m','--memory-swap=512m','--pids-limit=64']
    for src,dest,ro in mounts:
        if not src.exists(): raise RuntimeError('explicit mount missing')
        cmd+=['--mount',f'type=bind,src={src},dst={dest}'+(',readonly' if ro else '')]
    cmd+=['--env','PYTHONDONTWRITEBYTECODE=1','--env','CUDA_VISIBLE_DEVICES=',
          '--entrypoint=python',IMAGE,'-s','/code/summarize.py']
    started=time.monotonic()
    subprocess.run(cmd,check=True,capture_output=True,timeout=30)
    state=inspect(); h=state['HostConfig']
    actual={(m['Source'],m['Destination'],not m['RW']) for m in state['Mounts'] if m['Type']=='bind'}
    if (actual!={(str(s),dest,ro) for s,dest,ro in mounts} or h['NetworkMode']!='none'
            or not h['ReadonlyRootfs'] or h['Privileged'] or h.get('DeviceRequests')
            or h['Memory']!=512*1024**2 or h['MemorySwap']!=h['Memory']
            or h['NanoCpus']!=1_000_000_000 or state['Image']!=IMAGE):
        raise RuntimeError('isolation mismatch; not started')
    with (JOB/'isolation.json').open('x') as f:
        json.dump({'status':'PASS_BEFORE_START','mounts':state['Mounts'],'host_config':h},f,indent=2)
    try:
        result=subprocess.run(['docker','start','-a',NAME],capture_output=True,text=True,timeout=60)
    except BaseException:
        try: subprocess.run(['docker','stop','--time=5',NAME],capture_output=True,timeout=15)
        except subprocess.SubprocessError: pass
        if inspect()['State']['Running']:
            subprocess.run(['docker','kill',NAME],capture_output=True,timeout=10)
        raise
    state=inspect()
    if state['State']['Running']: raise RuntimeError('termination unverified')
    with (JOB/'terminal.json').open('x') as f:
        json.dump({'wall_seconds':time.monotonic()-started,'container_state':state['State'],
                   'returncode':result.returncode,'model_calls':0,'gpu_seconds':0},f,indent=2)
    if result.returncode: raise RuntimeError('aggregate failed: '+result.stderr[-1000:])
    print(result.stdout)


if __name__=='__main__': main()
