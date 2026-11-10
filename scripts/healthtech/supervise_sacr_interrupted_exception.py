"""Candidate for the one explicitly approved interrupted-query exception. NOT_DISPATCHED.

Create, inspect, then start exactly one offline native SACR fidelity profile container.

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
NAME = 'ptp-native-sacr-exception-20261111-v1'
PRIOR = JOB.parent / 'ptp-native-sacr-fidelity-20261110-v1'
CANONICAL = 'exception-index045-v1'
OUTPUT = PRIOR / 'out' / CANONICAL
WALL_SECONDS = 1200
STOP_SECONDS = WALL_SECONDS - 240
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
            # Reserve 240 seconds inside the declared envelope for a slow
            # in-flight inspect and nested bounded stop/reobserve cleanup.
            if time.monotonic() - started >= STOP_SECONDS:
                stop_owned()
                return 'TIMEOUT', peak
            size = sum(p.stat().st_size for folder in (OUTPUT, JOB / 'logs')
                       for p in folder.rglob('*') if p.is_file())
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
    # This host path is permanent across dispatch directories. Never remap it.
    if JOB.name != NAME or JOB.parent != Path('/home/chaw/patent-to-pilot-jobs'):
        raise RuntimeError('fixed job location required')
    if OUTPUT.exists() or OUTPUT.is_symlink():
        raise RuntimeError('canonical output exists; no replay')
    declaration_raw = (JOB / 'declaration.json').read_bytes()
    declaration = json.loads(declaration_raw)
    if declaration['wall_seconds'] != WALL_SECONDS or declaration['maximum_calls'] != 1:
        raise RuntimeError('fixed continuation allocation mismatch')
    for name, expected in declaration['files_sha256'].items():
        target = (JOB / 'runtime-code' / name).resolve()
        if not target.is_relative_to((JOB / 'runtime-code').resolve()) or hashlib.sha256(target.read_bytes()).hexdigest() != expected:
            raise RuntimeError('declared code/prompt hash mismatch before reservation')
    ledger_raw = (JOB / 'resource-ledger.json').read_bytes()
    ledger = json.loads(ledger_raw)
    if hashlib.sha256(ledger_raw).hexdigest() != declaration['resource_ledger_sha256']:
        raise RuntimeError('resource ledger mismatch')
    if WALL_SECONDS > min(ledger['gpu_remaining_seconds'], ledger['fidelity_generation_remaining_seconds']):
        raise RuntimeError('remaining budget insufficient')
    if hashlib.sha256((JOB / 'private-plan/continuation.json').read_bytes()).hexdigest() != declaration['continuation_manifest_sha256']:
        raise RuntimeError('sealed history manifest mismatch')
    prior_state = json.loads(subprocess.run(['docker','inspect',PRIOR.name],check=True,capture_output=True,text=True,timeout=10).stdout)[0]['State']
    terminal_raw = (PRIOR / 'terminal.json').read_bytes()
    terminal = json.loads(terminal_raw)
    if hashlib.sha256(terminal_raw).hexdigest() != declaration['prior_terminal_sha256']:
        raise RuntimeError('prior terminal hash mismatch')
    if prior_state['Running'] or any(prior_state[k] != terminal['container_state'][k] for k in ('ExitCode','StartedAt','FinishedAt')):
        raise RuntimeError('prior terminal changed')
    continuation_state = json.loads(subprocess.run(['docker','inspect','ptp-native-sacr-continuation-20261111-v1'],check=True,capture_output=True,text=True,timeout=10).stdout)[0]['State']
    if continuation_state['Running'] or continuation_state['Status'] not in ('exited','dead'):
        raise RuntimeError('existing continuation must be terminal before exception')
    continuation_terminal_path = JOB.parent / 'ptp-native-sacr-continuation-20261111-v1/terminal.json'
    continuation_raw = continuation_terminal_path.read_bytes()
    continuation_terminal = json.loads(continuation_raw)
    closure = ledger['native_unstarted_continuation_reservation']
    if (hashlib.sha256(continuation_raw).hexdigest() != declaration['continuation_terminal_sha256'] or
            closure['terminal_sha256'] != declaration['continuation_terminal_sha256'] or
            closure['actual_supervisor_seconds'] != continuation_terminal['wall_seconds'] or
            any(continuation_state[k] != continuation_terminal['container_state'][k] for k in ('ExitCode','StartedAt','FinishedAt'))):
        raise RuntimeError('actual continuation receipt/state/charge mismatch')
    grant_raw = (JOB / 'retry-authorization.json').read_bytes()
    if hashlib.sha256(grant_raw).hexdigest() != declaration['retry_authorization_sha256']:
        raise RuntimeError('owner exception hash mismatch')
    write('observed-continuation-state.json', continuation_state)
    write('observed-prior-state.json', prior_state)
    write('reservation.json', {'gpu_reserved_seconds': WALL_SECONDS, 'retry': False,
                             'prior_charged_seconds': ledger['gpu_conservative_charged_seconds'],
                             'prior_fidelity_seconds': ledger['fidelity_generation_charged_seconds'],
                             'total_limit_seconds': 259200, 'started_unix': time.time()})
    OUTPUT.mkdir(exist_ok=False)
    (JOB / 'logs').mkdir(exist_ok=False)
    free = subprocess.run(['nvidia-smi', '--query-compute-apps=pid,gpu_uuid', '--format=csv,noheader'],
                          check=True, capture_output=True, text=True, timeout=10)
    if GPU in free.stdout:
        raise RuntimeError('approved GPU already occupied')
    mounts = [(JOB / 'runtime-code', '/code', True),
              (BASE / 'venv/lib/python3.12/site-packages', '/deps', True),
              (BASE / 'models/qwen3-8b', '/models/qwen3-8b', True),
              (BASE / ('models/.' + GPU + '.lock'), '/models/.' + GPU + '.lock', False),
              (OUTPUT, '/history/' + CANONICAL, False),
              (PRIOR / 'out/attempt', '/history/attempt', True),
              (PRIOR / 'inputs', '/inputs', True),
              (PRIOR / 'terminal.json', '/prior-terminal.json', True),
              (JOB / 'observed-prior-state.json', '/observed-prior-state.json', True),
              (JOB / 'private-plan/continuation.json', '/continuation.json', True),
              (JOB / 'resource-ledger.json', '/resource-ledger.json', True),
              (JOB / 'declaration.json', '/declaration.json', True),
              (JOB / 'retry-authorization.json', '/retry-authorization.json', True),
              (continuation_terminal_path, '/continuation-terminal.json', True)]
    started = time.monotonic()
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
    declaration_path = '/declaration.json'
    command += ['--entrypoint=python', IMAGE, '-s', '/code/scripts/healthtech/run_sacr_native_fidelity.py',
                '--model-root', '/models/qwen3-8b',
                '--identity', '/code/docs/healthtech/audits/ptp-method-first-r2-weights-20261110/identity.json',
                '--queries', '/inputs/queries-ta.jsonl', '--sample', '/inputs/sample.json',
                '--declaration', declaration_path,
                '--declaration-sha256', hashlib.sha256(declaration_raw).hexdigest(),
                '--output', '/history/' + CANONICAL + '/attempt',
                '--prior-output', '/history/attempt', '--prior-terminal', '/prior-terminal.json',
                '--observed-state', '/observed-prior-state.json', '--continuation-manifest', '/continuation.json',
                '--resource-ledger', '/resource-ledger.json',
                '--supervisor-stop-monotonic', str(started + STOP_SECONDS),
                '--retry-authorization', '/retry-authorization.json',
                '--continuation-terminal', '/continuation-terminal.json']
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
    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(InterruptedError('supervisor interrupted')))
    with (JOB / 'logs/stdout').open('xb') as out, (JOB / 'logs/stderr').open('xb') as err:
        reason, peak, rc, state = start_and_monitor(started, out, err)
    completion = OUTPUT / 'attempt/terminal.json'
    summary = json.loads(completion.read_bytes()) if completion.is_file() else {}
    write('terminal.json', {'status': reason if reason != 'EXITED' else 'EXCEPTION_CLOSED_FIDELITY_PENDING'
          if rc == 0 and summary.get('status') == 'EXCEPTION_STRUCTURAL_RESULT_FIDELITY_PENDING' and state['State']['ExitCode'] == 0 else 'FAILED',
          'wall_seconds': time.monotonic() - started, 'returncode': rc,
          'container_state': state['State'], 'observed_cgroup_peak_bytes': peak,
          'completion_sha256': hashlib.sha256(completion.read_bytes()).hexdigest() if completion.is_file() else None,
          'retry': False})


if __name__ == '__main__':
    main()
