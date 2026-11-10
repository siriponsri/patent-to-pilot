"""Create, inspect, then start exactly one offline native SACR fidelity profile container.

Run from the exclusive remote job directory after transport hash verification.
No restart, deletion, test mounts or daemon/socket mount.31GiB container plus
1GiB supervisor allowance. Wall cap includes5-second termination grace.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import time
import signal

JOB = Path(__file__).resolve().parent
BASE = Path('/home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031')
GPU = 'GPU-277ccc57-c3e5-0731-cd49-f4f8695f7089'
NAME = 'ptp-native-sacr-fidelity-20261110-v1'
IMAGE = 'sha256:cb33f7f771ecec2ef1225cf39b159591a040391bd73e4c01f00fdfc4c47611d2'


def write(name, value):
    with (JOB / name).open('x') as f:
        json.dump(value, f, indent=2)
        f.flush()


def inspect():
    p = subprocess.run(['docker', 'inspect', NAME], capture_output=True, text=True, timeout=10)
    if p.returncode:
        raise RuntimeError('container inspection failed; do not restart')
    return json.loads(p.stdout)[0]


def stop_owned():
    """Only stop this attempt; failures remain unknown, never restart it."""
    subprocess.run(['docker', 'stop', '--time=5', NAME], capture_output=True, timeout=15)
    state = inspect()
    if state['State']['Running']:
        subprocess.run(['docker', 'kill', NAME], check=True, capture_output=True, timeout=10)
        state = inspect()
    if state['State']['Running']:
        raise RuntimeError('owned container termination unverified')
    return state


def monitor(child, started):
    peak, observation_errors = 0, 0
    try:
        while child.poll() is None:
            # Reserve 240 seconds inside the 7200-second envelope for a slow
            # in-flight inspect and nested bounded stop/reobserve cleanup.
            if time.monotonic() - started >= 6960:
                stop_owned()
                return 'TIMEOUT', peak
            size = sum(p.stat().st_size for folder in ('out', 'logs')
                       for p in (JOB / folder).rglob('*') if p.is_file())
            if size > 128 * 1024**2:
                stop_owned()
                return 'OUTPUT_LIMIT', peak
            try:
                state = inspect()
                observation_errors = 0
            except (subprocess.TimeoutExpired, RuntimeError, ValueError):
                observation_errors += 1
                if observation_errors >= 3:
                    stop_owned()
                    return 'OBSERVATION_FAILED_STOPPED', peak
                time.sleep(1)
                continue  # Reobserve the same child, never start another.
            pid = state['State']['Pid']
            try:
                for line in Path(f'/proc/{pid}/cgroup').read_text().splitlines():
                    if line.startswith('0::'):
                        p = Path('/sys/fs/cgroup') / line.split('::', 1)[1].lstrip('/') / 'memory.peak'
                        peak = max(peak, int(p.read_text()))
            except (FileNotFoundError, ProcessLookupError):
                pass
            time.sleep(1)
        return 'EXITED', peak
    except BaseException:
        stop_owned()
        raise


def start_and_monitor(started, out, err):
    try:
        child = subprocess.Popen(['docker', 'start', '-a', NAME], stdout=out, stderr=err)
        write('child.json', {'pid': child.pid, 'container_name': NAME})
        reason, peak = monitor(child, started)
        rc = child.wait(timeout=15)
        state = inspect()
        if state['State']['Running']:
            raise RuntimeError('attached client exited while owned container remains running')
        return reason, peak, rc, state
    except BaseException:
        try:
            stop_owned()
        except BaseException as stop_error:
            try:
                write('cleanup-failure.json', {'status': 'OWNED_TERMINATION_UNKNOWN',
                    'exception_type': type(stop_error).__name__, 'container': NAME, 'retry': False})
            except BaseException:
                pass
        raise


def main():
    # Prevent supervisor replay before any Docker operation.
    declaration = json.loads((JOB / 'code/docs/healthtech/audits/ptp-native-sacr-fidelity-20261110/declaration.json').read_text())
    for name, expected in declaration['files_sha256'].items():
        if hashlib.sha256((JOB / 'code' / name).read_bytes()).hexdigest() != expected:
            raise RuntimeError('declared code/prompt hash mismatch before reservation')
    write('reservation.json', {'gpu_reserved_seconds': 7200, 'retry': False,
                             'prior_charged_seconds': 278.886824848596,
                             'total_limit_seconds': 259200, 'started_unix': time.time()})
    for folder in ('out', 'logs'):
        (JOB / folder).mkdir(exist_ok=False)
    free = subprocess.run(['nvidia-smi', '--query-compute-apps=pid,gpu_uuid', '--format=csv,noheader'],
                          check=True, capture_output=True, text=True, timeout=10)
    if GPU in free.stdout:
        raise RuntimeError('approved GPU already occupied')
    mounts = [(JOB / 'code', '/code', True),
              (BASE / 'venv/lib/python3.12/site-packages', '/deps', True),
              (BASE / 'models/qwen3-8b', '/models/qwen3-8b', True),
              (BASE / ('models/.' + GPU + '.lock'), '/models/.' + GPU + '.lock', False),
              (JOB / 'out', '/out', False), (JOB / 'inputs', '/inputs', True)]
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
    declaration_path = '/code/docs/healthtech/audits/ptp-native-sacr-fidelity-20261110/declaration.json'
    command += ['--entrypoint=python', IMAGE, '-s', '/code/scripts/healthtech/run_sacr_native_fidelity.py',
                '--model-root', '/models/qwen3-8b',
                '--identity', '/code/docs/healthtech/audits/ptp-method-first-r2-weights-20261110/identity.json',
                '--queries', '/inputs/queries-ta.jsonl', '--sample', '/inputs/sample.json',
                '--declaration', declaration_path,
                '--declaration-sha256', hashlib.sha256((JOB / 'code' / declaration_path.removeprefix('/code/')).read_bytes()).hexdigest(),
                '--output', '/out/attempt']
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
    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(InterruptedError('supervisor interrupted')))
    with (JOB / 'logs/stdout').open('xb') as out, (JOB / 'logs/stderr').open('xb') as err:
        reason, peak, rc, state = start_and_monitor(started, out, err)
    completion = JOB / 'out/attempt/terminal.json'
    summary = json.loads(completion.read_bytes()) if completion.is_file() else {}
    write('terminal.json', {'status': reason if reason != 'EXITED' else 'PROFILE_BATCH_COMPLETE_FIDELITY_PENDING'
          if rc == 0 and summary.get('status') == 'PROFILE_BATCH_COMPLETED_FIDELITY_PENDING' and state['State']['ExitCode'] == 0 else 'FAILED',
          'wall_seconds': time.monotonic() - started, 'returncode': rc,
          'container_state': state['State'], 'observed_cgroup_peak_bytes': peak,
          'completion_sha256': hashlib.sha256(completion.read_bytes()).hexdigest() if completion.is_file() else None,
          'retry': False})


if __name__ == '__main__':
    main()
