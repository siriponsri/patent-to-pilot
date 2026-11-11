"""Single CPU-only preflight, fixed paths, offline mounts and 240-second attach cap."""
import json
from pathlib import Path
import subprocess
import time

NAME = 'ptp-sacr-r2-tokenizer-preflight-20261111-v1'
JOB = Path('/home/chaw/patent-to-pilot-jobs') / NAME
BASE = JOB.parent / 'research-product-o1-o4-20261031'
PRIOR = JOB.parent / 'ptp-native-sacr-fidelity-20261110-v1'
IMAGE = 'sha256:cb33f7f771ecec2ef1225cf39b159591a040391bd73e4c01f00fdfc4c47611d2'


def write(name, value):
    with (JOB/name).open('x') as f:
        json.dump(value, f, indent=2)


def inspect():
    return json.loads(subprocess.run(['docker', 'inspect', NAME], check=True,
        capture_output=True, text=True, timeout=10).stdout)[0]


def main():
    if Path(__file__).resolve().parent != JOB:
        raise RuntimeError('fixed job path required')
    started = time.monotonic()
    (JOB/'out').mkdir(exist_ok=False)
    mounts = [(JOB/'code', '/code', True), (JOB/'out', '/out', False),
              (BASE/'venv/lib/python3.12/site-packages', '/deps', True),
              (BASE/'models/qwen3-8b', '/model', True),
              (PRIOR/'inputs/queries-ta.jsonl', '/inputs/queries-ta.jsonl', True),
              (PRIOR/'inputs/sample.json', '/inputs/sample.json', True)]
    cmd = ['docker', 'create', '--pull=never', '--name', NAME, '--network=none', '--read-only',
           '--cap-drop=ALL', '--security-opt=no-new-privileges', '--user=1000:1000',
           '--cpus=2', '--memory=4g', '--memory-swap=4g', '--pids-limit=128',
           '--tmpfs', '/tmp:rw,nosuid,size=134217728']
    for src, dest, ro in mounts:
        if not src.exists(): raise RuntimeError('required mount missing')
        cmd += ['--mount', f'type=bind,src={src},dst={dest}'+(',readonly' if ro else '')]
    for env in ['PYTHONPATH=/code/src:/deps', 'PYTHONDONTWRITEBYTECODE=1', 'CUDA_VISIBLE_DEVICES=',
                'HF_HUB_OFFLINE=1', 'TRANSFORMERS_OFFLINE=1', 'TOKENIZERS_PARALLELISM=false',
                'OMP_NUM_THREADS=2', 'MKL_NUM_THREADS=2', 'OPENBLAS_NUM_THREADS=2', 'RAYON_NUM_THREADS=2']:
        cmd += ['--env', env]
    cmd += ['--entrypoint=python', IMAGE, '-s', '/code/scripts/healthtech/preflight_sacr_r2_tokenizer.py']
    subprocess.run(cmd, check=True, capture_output=True, timeout=30)
    state = inspect(); h = state['HostConfig']
    actual = {(m['Source'], m['Destination'], not m['RW']) for m in state['Mounts'] if m['Type']=='bind'}
    if (actual != {(str(s), d, ro) for s,d,ro in mounts} or h['NetworkMode'] != 'none'
            or not h['ReadonlyRootfs'] or h['Privileged'] or h.get('DeviceRequests')
            or h['Memory'] != 4*1024**3 or h['MemorySwap'] != h['Memory']
            or h['NanoCpus'] != 2_000_000_000 or state['Config']['User'] != '1000:1000'
            or state['Image'] != IMAGE or h['CapDrop'] != ['ALL']
            or 'no-new-privileges' not in h['SecurityOpt']):
        raise RuntimeError('isolation mismatch; not started')
    write('isolation.json', {'status':'PASS_BEFORE_START', 'mounts':state['Mounts'], 'host_config':h})
    reason = 'EXITED'
    with (JOB/'stdout').open('xb') as out, (JOB/'stderr').open('xb') as err:
        try:
            result = subprocess.run(['docker', 'start', '-a', NAME], stdout=out, stderr=err, timeout=240)
            rc = result.returncode
        except BaseException:
            reason = 'INTERRUPTED_OR_TIMEOUT'
            subprocess.run(['docker','stop','--time=5',NAME],capture_output=True,timeout=15)
            if inspect()['State']['Running']:
                subprocess.run(['docker','kill',NAME],check=True,capture_output=True,timeout=10)
            rc = None
    state = inspect()
    if state['State']['Running']: raise RuntimeError('termination unverified; do not restart')
    write('terminal.json', {'status': reason, 'exit_code':state['State']['ExitCode'],
        'attach_returncode':rc, 'wall_seconds':time.monotonic()-started,
        'gpu_seconds':0, 'model_calls':0, 'container_state':state['State'], 'retry':False})
    print(json.dumps({'status':reason, 'exit_code':state['State']['ExitCode']}))


if __name__ == '__main__': main()
