"""Paper 1 retrieval controller (frozen protocol 2026-11-13 + A1); journal must hold exact stage qualification.

Derived from the SACR pilot retrieval controller. Arm job outputs are mounted read-only; no qrels/evaluator mounts.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import sqlite3
import subprocess
import sys
import time
from r3_engine_client import Engine, EngineError
from supervise_sacr_r5_engine import configuration as base_configuration, supervise, GPU, BASE


JOBS = Path('/home/chaw/patent-to-pilot-jobs')
JOB_NAME = re.compile(r'ptp-auto-paper1-(fa|gr|dev)-(pilot|fulldev)-retrieval-20261113-v[1-9]')
ARM_JOB = re.compile(r'ptp-auto-(paper1-(fa|gr)-(pilot20|fulldev-b[1-9])-20261113-v[1-9]|native-sacr-(pilot20-20261112-v5|fulldev-b[1-6]-20261113-v[1-9]))')
FIXED = ('/code', '/out', '/deps', '/models/patembed-large', '/models/.' + GPU + '.lock', '/dispatch',
         '/vectors/passage-vectors-f32.npy', '/runtime', '/b0/rankings-top200.jsonl')


def configuration(job, stop, digest, arms):
    config, mounts = base_configuration('smoke', job, stop, digest)
    mounts = [m for m in mounts if m[1] not in ('/declaration.json', '/resource-ledger.json', '/models/qwen3-8b')]
    mounts += [(job / 'dispatch', '/dispatch', True),
               (BASE / 'models/patembed-large', '/models/patembed-large', True),
               (JOBS / 'org-adaptive-20261105/outputs/dense-single/passage-vectors-f32.npy', '/vectors/passage-vectors-f32.npy', True),
               (JOBS / 'ptp-native-baseline-20261110-v1/runtime-dev', '/runtime', True),
               (JOBS / 'ptp-native-baseline-20261110-v1/out/attempt/rankings-top200.jsonl', '/b0/rankings-top200.jsonl', True)]
    for name in sorted(arms):
        if not re.fullmatch(r'[A-Z]{2,4}', name): raise RuntimeError('arm name')
        for k, pin in enumerate(arms[name]['jobs']):
            if not ARM_JOB.fullmatch(pin['job']): raise RuntimeError('arm job outside the Paper 1 allowlist')
            mounts += [(JOBS / pin['job'] / 'dispatch', '/arm/%s/%d/dispatch' % (name, k), True),
                       (JOBS / pin['job'] / 'out/attempt', '/arm/%s/%d/out' % (name, k), True)]
    host = config['HostConfig']
    host['Mounts'] = [{'Type': 'bind', 'Source': str(p), 'Target': t, 'ReadOnly': ro} for p, t, ro in mounts]
    config['Cmd'] = ['-s', '/code/scripts/healthtech/run_paper1_retrieval.py', str(stop), digest]
    return config, mounts


def main(pin):
    import resource
    job = Path(__file__).resolve().parent
    if job.parent != JOBS or not JOB_NAME.fullmatch(job.name):
        raise RuntimeError('fixed native job path required')
    resource.setrlimit(resource.RLIMIT_AS, (1024**3,1024**3))
    resource.setrlimit(resource.RLIMIT_CPU, (60,60))
    started = time.monotonic(); claimed = False; create_sent = False
    receipt = {'attempt_id': job.name, 'container_name': job.name, 'retry': False}
    with (job / 'admission.json').open('x') as f:
        json.dump({'declaration_sha256': pin, 'retry': False}, f); f.flush(); os.fsync(f.fileno())
    engine = Engine()
    def interrupted(*args): raise InterruptedError('controller interrupted')
    signal.signal(signal.SIGTERM, interrupted)
    try:
        raw = (job / 'dispatch/declaration.json').read_bytes()
        if hashlib.sha256(raw).hexdigest() != pin: raise RuntimeError('declaration changed')
        d = json.loads(raw)
        if (d['attempt_id'] != job.name or d['stage'] not in ('pilot', 'full_dev') or d['maximum_calls'] != 1
                or d.get('generation_calls') != 0 or type(d.get('arms')) is not dict):
            raise RuntimeError('Paper 1 retrieval declaration mismatch')
        sys.path.insert(0, str(job/'code/src'))
        from patent_to_pilot.research.automatic_dispatch_journal import AutomaticDispatchJournal
        from patent_to_pilot.research.r6_dispatch_journal import document_hash
        from patent_to_pilot.research.r7_dispatch_files import validate_worker_package
        validate_worker_package(job/'code', d['files_sha256'], d['package_sha256'])
        for name in ('supervise_paper1_retrieval.py','supervise_sacr_r5_engine.py','r3_engine_client.py'):
            if (job/name).read_bytes() != (job/'code/scripts/healthtech'/name).read_bytes():
                raise RuntimeError('controller code changed')
        receipt['declaration_sha256'] = document_hash(d)
        engine.check_version()
        for folder in job.parent.glob('ptp-*'):
            if not folder.is_dir(): continue
            try: state = engine.inspect(folder.name)['State']
            except EngineError as e:
                if e.status != 404: raise
                continue
            if state['Running'] or state['Pid'] != 0: raise RuntimeError('owned job active')
        try: engine.inspect(job.name)
        except EngineError as e:
            if e.status != 404: raise
        else: raise RuntimeError('existing container prevents replay')
        gpu = subprocess.run(['nvidia-smi','--query-compute-apps=pid,gpu_uuid','--format=csv,noheader'],
                             capture_output=True,text=True,check=True,timeout=10).stdout
        if GPU in gpu: raise RuntimeError('approved GPU busy')
        journal_path = job.parent/'ptp-r6-control/dispatch.sqlite'
        with sqlite3.connect('file:'+str(journal_path)+'?mode=ro',uri=True) as db:
            identity, generation, raw_ledger = db.execute('SELECT identity,generation,ledger FROM head').fetchone()
        ledger = json.loads(raw_ledger)
        stop = started + d['seconds'] - 240
        (job/'out').mkdir(exist_ok=False)
        config, mounts = configuration(job, stop, pin, d['arms'])
        if any(not p.exists() for p,_,_ in mounts): raise RuntimeError('missing exact mount')
        live = {'observed_unix':time.time(), 'attempt_id':job.name, 'generation':generation,
            'ledger_sha256':document_hash(ledger), 'gpu_uuid':GPU, 'gpu_idle':True, 'owned_jobs_idle':True,
            'network_disabled':config['HostConfig']['NetworkMode']=='none',
            'protected_mounts_absent': all(t in FIXED or re.fullmatch(r'/arm/[A-Z]{2,4}/\d+/(dispatch|out)', t) for _,t,_ in mounts),
            'cpu_threads':1, 'aggregate_ram_limit_bytes':32*1024**3,
            'incremental_disk_bytes':d['disk_preexisting_upper_bound_bytes'],
            'free_disk_bytes':shutil.disk_usage(job).free}
        gates = json.loads((job/'dispatch/gates.json').read_bytes())
        journal = AutomaticDispatchJournal(journal_path, identity)
        result = journal.claim(declaration=d,gates=gates,expected_generation=generation,live_receipt=live)
        claimed = True
        with (job/'global-dispatch.json').open('x') as f: json.dump(result,f)
        if time.monotonic()+30 >= stop: raise TimeoutError('preflight exhausted deadline')
        create_sent = True
        status, state = supervise(engine, job.name, config, mounts, stop, job/'out')
        receipt.update(status=status, container_state=state['State'])
    except BaseException as error:
        receipt.update(status='FAILED', exception_type=type(error).__name__)
        if create_sent:
            try: receipt['container_state'] = engine.terminate(job.name)['State']
            except BaseException: receipt['status'] = 'TERMINATION_UNKNOWN'
        else: receipt.update(container_outcome='NO_CONTAINER', create_request_sent=False)
        raise
    finally:
        receipt.update(whole_wall_seconds=time.monotonic()-started, controller_cpu_seconds=time.process_time(),
                       global_claim_consumed=claimed, settlement='REQUIRES_INDEPENDENT_TERMINAL_VERIFICATION')
        with (job/'terminal.json').open('x') as f: json.dump(receipt,f,indent=2)


if __name__ == '__main__': main(sys.argv[1])
