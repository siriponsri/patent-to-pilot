"""Single CPU-only isolated dev evaluation; no model or protected mounts."""
import json
from pathlib import Path
import subprocess
import time

JOB = Path(__file__).resolve().parent
BASELINE = JOB.parent / 'ptp-native-baseline-20261110-v1'
NAME = 'ptp-native-evaluator-20261110-v1'
IMAGE = 'sha256:cb33f7f771ecec2ef1225cf39b159591a040391bd73e4c01f00fdfc4c47611d2'


def write(name, value):
    with (JOB / name).open('x') as f:
        json.dump(value, f, indent=2)


def inspect():
    return json.loads(subprocess.run(['docker', 'inspect', NAME], check=True,
                     capture_output=True, text=True, timeout=10).stdout)[0]


def main():
    write('reservation.json', {'cpu_seconds_wall_cap': 120, 'gpu_calls': 0, 'retry': False})
    (JOB / 'out').mkdir(exist_ok=False)
    mounts = [(JOB / 'code', '/code', True),
              (BASELINE / 'runtime-dev', '/inputs/runtime', True),
              (BASELINE / 'out/attempt', '/inputs/rankings', True),
              (JOB / 'dev-evaluation', '/inputs/evaluation', True), (JOB / 'out', '/out', False)]
    cmd = ['docker', 'create', '--pull=never', '--name', NAME, '--network=none', '--read-only',
           '--user=1000:1000', '--cap-drop=ALL', '--security-opt=no-new-privileges',
           '--cpus=2', '--memory=4g', '--memory-swap=4g', '--pids-limit=32',
           '--tmpfs', '/tmp:rw,nosuid,size=67108864', '--env', 'PYTHONPATH=/code/src',
           '--env', 'PYTHONDONTWRITEBYTECODE=1']
    for source, dest, ro in mounts:
        if not source.exists():
            raise RuntimeError('missing evaluator mount')
        cmd += ['--mount', f'type=bind,src={source},dst={dest}' + (',readonly' if ro else '')]
    cmd += ['--entrypoint=python', IMAGE, '-s', '/code/scripts/healthtech/evaluate_dapfam_native_baseline.py',
            '--inputs', '/inputs', '--output', '/out/attempt']
    subprocess.run(cmd, check=True, capture_output=True, timeout=30)
    s = inspect()
    h = s['HostConfig']
    if ({(m['Source'], m['Destination'], not m['RW']) for m in s['Mounts'] if m['Type'] == 'bind'}
            != {(str(p), d, ro) for p, d, ro in mounts}
            or h['NetworkMode'] != 'none' or not h['ReadonlyRootfs'] or h['Privileged']
            or h['DeviceRequests'] or h['Memory'] != 4 * 1024**3
            or h['MemorySwap'] != h['Memory'] or h['NanoCpus'] != 2_000_000_000
            or s['Config']['User'] != '1000:1000' or s['Image'] != IMAGE):
        raise RuntimeError('evaluator isolation readback failed before start')
    write('isolation.json', {'status': 'PASS_BEFORE_START', 'mounts': s['Mounts'], 'limits': h})
    started = time.monotonic()
    reason = 'EXITED'
    with (JOB / 'stdout').open('xb') as out, (JOB / 'stderr').open('xb') as err:
        child = subprocess.Popen(['docker', 'start', '-a', NAME], stdout=out, stderr=err)
        try:
            rc = child.wait(timeout=115)
        except BaseException:
            subprocess.run(['docker', 'stop', '--time=5', NAME], capture_output=True, timeout=15)
            reason = 'INTERRUPTED_OR_TIMEOUT'
            rc = child.wait(timeout=15)
    s = inspect()
    write('terminal.json', {'status': 'COMPLETED_DEV_ONLY' if reason == 'EXITED' and rc == 0
          and not s['State']['Running'] and (JOB / 'out/attempt/summary.json').is_file() else 'FAILED',
          'returncode': rc, 'reason': reason, 'wall_seconds': time.monotonic() - started,
          'state': s['State'], 'gpu_calls': 0, 'retry': False})


if __name__ == '__main__':
    main()
