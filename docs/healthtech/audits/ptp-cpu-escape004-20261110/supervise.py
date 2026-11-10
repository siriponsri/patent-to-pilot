"""Exclusive one-child CPU supervisor; preserve timeout and process termination."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import resource
import fcntl

job = Path(__file__).resolve().parent
code = job / 'code'
logs = job / 'logs'
declaration = code / 'docs/healthtech/audits/ptp-cpu-escape004-20261110'
started = time.monotonic()
transport = json.loads((job / 'transport.json').read_bytes())
slot = Path('/home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031/models/.GPU-277ccc57-c3e5-0731-cd49-f4f8695f7089.lock').open('a+b')
fcntl.flock(slot.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

def constrain_child():
    resource.setrlimit(resource.RLIMIT_AS, (32 * 1024**3, 32 * 1024**3))
    os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:8])



def status(message):
    with (logs / 'status.log').open('a') as handle:
        handle.write(datetime.now(timezone.utc).isoformat() + ' ' + message + '\n')
        handle.flush()
        os.fsync(handle.fileno())


def write(name, value):
    with (job / name).open('x') as handle:
        json.dump(value, handle, indent=2)
        handle.flush()
        os.fsync(handle.fileno())


env = dict(os.environ, PYTHONPATH=str(code / 'src'), CUDA_VISIBLE_DEVICES='', OMP_NUM_THREADS='8', MKL_NUM_THREADS='8', OPENBLAS_NUM_THREADS='8', NUMEXPR_NUM_THREADS='8', RAYON_NUM_THREADS='8', TOKENIZERS_PARALLELISM='false')
command = [sys.executable, str(code / 'scripts/healthtech/probe_sacr_escape_candidate.py'),
           '--tokenizer', '/home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031/models/qwen3-8b',
           '--payload', str(declaration / 'authored-fixtures.json'),
           '--declaration', str(declaration / 'declaration.json'), '--output', str(job / 'output')]
write('supervisor-reservation.json', {'pid': os.getpid(), 'wall_limit_seconds': 120,
                                     'supervisor_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                                     'code_commit': transport['commit']})
status('STARTED_CPU_ONLY')
with (logs / 'probe.stdout').open('xb') as out, (logs / 'probe.stderr').open('xb') as err:
    child = subprocess.Popen(command, cwd=code, env=env, stdout=out, stderr=err, start_new_session=True, preexec_fn=constrain_child)
    write('child.json', {'pid': child.pid, 'model_calls': 0})
    status('CHILD ' + str(child.pid))
    timed_out = False
    try:
        returncode = child.wait(timeout=120)
    except subprocess.TimeoutExpired:
        timed_out = True
        status('TIMEOUT_TERM_CHILD_GROUP')
        os.killpg(child.pid, signal.SIGTERM)
        try:
            returncode = child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            status('KILL_CHILD_GROUP')
            os.killpg(child.pid, signal.SIGKILL)
            returncode = child.wait(timeout=5)
result = job / 'output/result.json'
all_expected = json.loads(result.read_bytes())['all_expected'] if result.exists() else False
state = 'TIMEOUT' if timed_out else 'PASS' if returncode == 0 and all_expected else 'FAILED'
write('terminal.json', {'status': state, 'child_pid': child.pid, 'returncode': returncode,
                        'child_reaped': True, 'child_proc_exists': Path('/proc', str(child.pid)).exists(),
                        'child_peak_rss_bytes': resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss * 1024,
                        'cases_written': len(list((job / 'output').glob('case-*.json'))),
                        'result_exists': result.exists(), 'all_expected': all_expected,
                        'wall_seconds': time.monotonic() - started,
                        'finished_utc': datetime.now(timezone.utc).isoformat(), 'model_calls': 0})
status('TERMINAL ' + state)
