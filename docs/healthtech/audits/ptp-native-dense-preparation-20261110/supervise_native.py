"""Create, inspect, then start exactly one offline native baseline container.

Run from the exclusive remote job directory after transport hash verification.
No restart, deletion, test mounts or daemon/socket mount.31GiB container plus
1GiB supervisor allowance. Wall cap includes5-second termination grace.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import time

JOB = Path(__file__).resolve().parent
BASE = Path('/home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031')
GPU = 'GPU-277ccc57-c3e5-0731-cd49-f4f8695f7089'
NAME = 'ptp-native-baseline-20261110-v1'
IMAGE = 'sha256:cb33f7f771ecec2ef1225cf39b159591a040391bd73e4c01f00fdfc4c47611d2'
VECTORS = Path('/home/chaw/patent-to-pilot-jobs/org-adaptive-20261105/outputs/dense-single/passage-vectors-f32.npy')


def write(name, value):
    with (JOB / name).open('x') as f:
        json.dump(value, f, indent=2)
        f.flush()


def inspect():
    p = subprocess.run(['docker', 'inspect', NAME], capture_output=True, text=True, timeout=10)
    if p.returncode:
        raise RuntimeError('container inspection failed; do not restart')
    return json.loads(p.stdout)[0]


def main():
    # Prevent supervisor replay before any Docker operation.
    write('reservation.json', {'gpu_reserved_seconds': 14400, 'retry': False,
                             'prior_charged_seconds': 141.9369698059745,
                             'total_limit_seconds': 259200, 'started_unix': time.time()})
    for folder in ('out', 'logs'):
        (JOB / folder).mkdir(exist_ok=False)
    free = subprocess.run(['nvidia-smi', '--query-compute-apps=pid,gpu_uuid', '--format=csv,noheader'],
                          check=True, capture_output=True, text=True, timeout=10)
    if GPU in free.stdout:
        raise RuntimeError('approved GPU already occupied')
    mounts = [(JOB / 'code', '/code', True), (JOB / 'runtime-dev', '/runtime', True),
              (BASE / 'venv/lib/python3.12/site-packages', '/deps', True),
              (BASE / 'models/patembed-large', '/models/patembed-large', True),
              (BASE / ('models/.' + GPU + '.lock'), '/models/.' + GPU + '.lock', False),
              (VECTORS, '/vectors.npy', True), (JOB / 'out', '/out', False)]
    command = ['docker', 'create', '--pull=never', '--name', NAME, '--network=none', '--read-only',
               '--cap-drop=ALL', '--security-opt=no-new-privileges', '--user=1000:1000',
               '--cpus=8', '--memory=31g', '--memory-swap=31g', '--pids-limit=256',
               '--tmpfs', '/tmp:rw,nosuid,size=268435456', '--gpus', 'device=' + GPU]
    for source, dest, ro in mounts:
        if not source.exists():
            raise RuntimeError('required mount missing')
        command += ['--mount', f'type=bind,src={source},dst={dest}' + (',readonly' if ro else '')]
    for env in ['PYTHONPATH=/code/src:/deps', 'OMP_NUM_THREADS=8', 'MKL_NUM_THREADS=8',
                'OPENBLAS_NUM_THREADS=8', 'NUMEXPR_NUM_THREADS=8', 'RAYON_NUM_THREADS=8',
                'TOKENIZERS_PARALLELISM=false', 'HF_HUB_OFFLINE=1', 'TRANSFORMERS_OFFLINE=1',
                'CUDA_VISIBLE_DEVICES=' + GPU]:
        command += ['--env', env]
    command += ['--entrypoint=python', IMAGE, '-s', '/code/scripts/healthtech/run_dapfam_native_baseline.py',
                '--runtime', '/runtime', '--model', '/models/patembed-large',
                '--vectors', '/vectors.npy', '--output', '/out/attempt']
    subprocess.run(command, check=True, capture_output=True, timeout=30)
    state = inspect()
    h = state['HostConfig']
    observed = {(m['Source'], m['Destination'], not m['RW']) for m in state['Mounts'] if m['Type'] == 'bind'}
    expected = {(str(s), d, ro) for s, d, ro in mounts}
    if (observed != expected or h['NetworkMode'] != 'none' or not h['ReadonlyRootfs']
            or h['Privileged'] or h['Memory'] != 31 * 1024**3 or h['MemorySwap'] != h['Memory']
            or h['NanoCpus'] != 8_000_000_000 or state['Config']['User'] != '1000:1000'
            or state['Image'] != IMAGE or h['PidsLimit'] != 256
            or h['CapDrop'] != ['ALL'] or 'no-new-privileges' not in h['SecurityOpt']
            or h['DeviceRequests'][0]['DeviceIDs'] != [GPU]):
        raise RuntimeError('container isolation readback mismatch; not started')
    write('isolation-readback.json', {'status': 'PASS_BEFORE_START', 'mounts': state['Mounts'],
                                     'host_config': h, 'image': state['Image']})
    started = time.monotonic()
    timeout = False
    peak = 0
    with (JOB / 'logs/stdout').open('xb') as out, (JOB / 'logs/stderr').open('xb') as err:
        child = subprocess.Popen(['docker', 'start', '-a', NAME], stdout=out, stderr=err)
        write('child.json', {'pid': child.pid, 'container_name': NAME})
        while child.poll() is None:
            if time.monotonic() - started >= 14395:
                timeout = True
                subprocess.run(['docker', 'stop', '--time=5', NAME], capture_output=True, timeout=15)
                break
            state = inspect()
            pid = state['State']['Pid']
            try:
                for line in Path(f'/proc/{pid}/cgroup').read_text().splitlines():
                    if line.startswith('0::'):
                        p = Path('/sys/fs/cgroup') / line.split('::', 1)[1].lstrip('/') / 'memory.peak'
                        peak = max(peak, int(p.read_text()))
            except (FileNotFoundError, ProcessLookupError):
                pass
            time.sleep(1)
        rc = child.wait(timeout=15)
    state = inspect()
    completion = JOB / 'out/attempt/completion.json'
    write('terminal.json', {'status': 'TIMEOUT' if timeout else 'COMPLETED_NOT_EVALUATED'
          if rc == 0 and completion.is_file() and state['State']['ExitCode'] == 0 else 'FAILED',
          'wall_seconds': time.monotonic() - started, 'returncode': rc,
          'container_state': state['State'], 'observed_cgroup_peak_bytes': peak,
          'completion_sha256': hashlib.sha256(completion.read_bytes()).hexdigest() if completion.is_file() else None,
          'retry': False})


if __name__ == '__main__':
    main()
