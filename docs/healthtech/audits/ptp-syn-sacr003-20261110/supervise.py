"""One container attempt with an external wall bound; no restart or fallback."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import time

job = Path(__file__).resolve().parent
transport = json.loads((job / 'transport.json').read_bytes())
declaration_path = 'docs/healthtech/audits/ptp-syn-sacr003-20261110/declaration.json'
declaration = json.loads((job / 'code' / declaration_path).read_bytes())
name = 'ptp-syn-sacr003-20261110-v1'
base = Path('/home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031')
slot = base / 'models/.GPU-277ccc57-c3e5-0731-cd49-f4f8695f7089.lock'
assert slot.is_file()


def write(filename, value):
    with (job / filename).open('x') as handle:
        json.dump(value, handle, indent=2)
        handle.flush()


def inspect():
    try:
        result = subprocess.run(['docker', 'inspect', name], capture_output=True, text=True, timeout=5)
        return json.loads(result.stdout)[0] if result.returncode == 0 else None
    except (subprocess.TimeoutExpired, ValueError, IndexError):
        return None


command = ['docker', 'run', '--pull=never', '--name', name, '--network=none', '--read-only',
           '--cap-drop=ALL', '--security-opt=no-new-privileges', '--user=1000:1000',
           '--cpus=8', '--memory=32g', '--memory-swap=32g', '--pids-limit=256',
           '--tmpfs', '/tmp:rw,nosuid,size=268435456',
           '--gpus', 'device=GPU-277ccc57-c3e5-0731-cd49-f4f8695f7089']
for source, destination, readonly in [
    (job / 'code', '/code', True),
    (base / 'venv/lib/python3.12/site-packages', '/deps', True),
    (base / 'models/qwen3-8b', '/models/qwen3-8b', True),
    (slot, '/models/' + slot.name, False),
    (job / 'out', '/out', False),
]:
    command += ['--mount', f'type=bind,src={source},dst={destination}' + (',readonly' if readonly else '')]
for value in ['PYTHONPATH=/code/src:/deps', 'OMP_NUM_THREADS=8', 'MKL_NUM_THREADS=8',
              'OPENBLAS_NUM_THREADS=8', 'NUMEXPR_NUM_THREADS=8', 'RAYON_NUM_THREADS=8',
              'TOKENIZERS_PARALLELISM=false', 'HF_HUB_OFFLINE=1', 'TRANSFORMERS_OFFLINE=1',
              'CUDA_VISIBLE_DEVICES=GPU-277ccc57-c3e5-0731-cd49-f4f8695f7089']:
    command += ['--env', value]
identity = 'docs/healthtech/audits/ptp-method-first-r2-weights-20261110/identity.json'
grammar = '/code/docs/healthtech/audits/ptp-cpu-escape004-20261110/'
command += ['--entrypoint=python', declaration['container_image'], '-s',
            '/code/scripts/healthtech/smoke_sacr_qwen_guarded_v3.py',
            '--model-root', '/models/qwen3-8b', '--identity', '/code/' + identity,
            '--identity-sha256', declaration['files_sha256'][identity],
            '--grammar-payload', grammar + 'authored-fixtures.json',
            '--grammar-declaration', grammar + 'declaration.json', '--output', '/out/attempt']
write('supervisor-reservation.json', {'container_name': name, 'commit': transport['commit'],
      'started_utc': datetime.now(timezone.utc).isoformat(), 'wall_seconds': 1800,
      'maximum_model_calls': 1, 'retry': False})
started = time.monotonic()
observed_peak = 0
timed_out = False
captured = False
with (job / 'logs/stdout').open('xb') as stdout, (job / 'logs/stderr').open('xb') as stderr:
    child = subprocess.Popen(command, stdout=stdout, stderr=stderr, start_new_session=True)
    write('child.json', {'pid': child.pid, 'container_name': name})
    while child.poll() is None:
        if time.monotonic() - started >= 1800:
            timed_out = True
            subprocess.run(['docker', 'stop', '--time=5', name], capture_output=True, timeout=15)
            break
        state = inspect()
        if state and not captured:
            write('container-config.json', {'id': state['Id'], 'image': state['Image'],
                  'user': state['Config']['User'], 'mounts': state['Mounts'],
                  'limits': {k: state['HostConfig'][k] for k in
                             ['NetworkMode', 'ReadonlyRootfs', 'Memory', 'MemorySwap',
                              'NanoCpus', 'PidsLimit', 'CapDrop', 'SecurityOpt', 'Privileged', 'DeviceRequests']}})
            captured = True
        if state and state['State']['Pid']:
            proc = Path('/proc', str(state['State']['Pid']), 'cgroup')
            try:
                for line in proc.read_text().splitlines():
                    if line.startswith('0::'):
                        peak = Path('/sys/fs/cgroup') / line.split('::', 1)[1].lstrip('/') / 'memory.peak'
                        if peak.is_file():
                            observed_peak = max(observed_peak, int(peak.read_text()))
            except (FileNotFoundError, ProcessLookupError):
                pass
        time.sleep(1)
    returncode = child.wait(timeout=15)
state = inspect()
summary_path = job / 'out/attempt/summary.json'
summary = json.loads(summary_path.read_bytes()) if summary_path.exists() else {}
write('terminal.json', {'status': 'TIMEOUT' if timed_out else
      'PASS' if returncode == 0 and summary.get('engineering_pass') and state and
      not state['State']['Running'] and state['State']['ExitCode'] == 0 else 'FAILED',
      'returncode': returncode, 'container_state': state['State'] if state else None,
      'container_name': name, 'wall_seconds': time.monotonic() - started,
      'observed_cgroup_peak_bytes': observed_peak,
      'memory_observation_limit': 'sampled memory.peak while alive; final unobserved interval may be higher',
      'finished_utc': datetime.now(timezone.utc).isoformat(),
      'summary_sha256': hashlib.sha256(summary_path.read_bytes()).hexdigest() if summary_path.exists() else None,
      'maximum_model_calls': 1, 'retry': False})
