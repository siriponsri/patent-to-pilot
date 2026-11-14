"""Native SACR fidelity controller (NATIVE-STAGES-20261112); journal must hold exact stage qualification."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import sqlite3
import subprocess
import sys
import time
from r3_engine_client import Engine, EngineError
from supervise_sacr_r5_engine import configuration as base_configuration, supervise, GPU


def configuration(job, stop, digest):
    config, mounts = base_configuration('smoke', job, stop, digest)
    mounts = [m for m in mounts if m[1] not in ('/declaration.json', '/resource-ledger.json')]
    mounts.append((job / 'dispatch', '/dispatch', True))
    host = config['HostConfig']
    host['Mounts'] = [{'Type': 'bind', 'Source': str(p), 'Target': t, 'ReadOnly': ro} for p,t,ro in mounts]
    host['NanoCpus'] = 1_000_000_000
    config['Env'] = [v.rsplit('=',1)[0]+'=1' if v.endswith('=8') else v for v in config['Env']]
    config['Cmd'] = ['-s', '/code/scripts/healthtech/run_automatic_native.py', str(stop), digest]
    return config, mounts


def main(pin):
    import resource
    job = Path(__file__).resolve().parent
    allowed = (tuple('ptp-auto-native-sacr-pilot20-20261112-v%d' % v for v in range(1, 6))
               + tuple('ptp-auto-native-sacr-fulldev-b%d-20261113-v1' % b for b in range(1, 7))  # b1 staged stale: never launch
               + tuple('ptp-auto-native-sacr-fulldev-b%d-20261114-v1' % b for b in range(1, 7)))
    if job.parent != Path('/home/chaw/patent-to-pilot-jobs') or job.name not in allowed:
        raise RuntimeError('fixed native job path required')
    resource.setrlimit(resource.RLIMIT_AS, (1024**3,1024**3))
    # Controller CPU grows with polls x output files (measured on Paper 1 S4: about 156 s for a 158-call batch);
    # a 79-query SACR batch writes about 2,200 files over about 2 h, so full-dev jobs get 900 s; pilot keeps 60 s.
    controller_cpu = 900 if '-fulldev-' in job.name else 60
    resource.setrlimit(resource.RLIMIT_CPU, (controller_cpu,controller_cpu))
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
        if d['attempt_id'] != job.name or d['stage'] not in ('fidelity', 'full_dev') or d['maximum_calls'] > 2 * d['queries']:
            raise RuntimeError('native declaration mismatch')
        sys.path.insert(0, str(job/'code/src'))
        from patent_to_pilot.research.automatic_dispatch_journal import AutomaticDispatchJournal
        from patent_to_pilot.research.r6_dispatch_journal import document_hash
        from patent_to_pilot.research.r7_dispatch_files import validate_worker_package
        validate_worker_package(job/'code', d['files_sha256'], d['package_sha256'])
        for name in ('supervise_automatic_native.py','supervise_sacr_r5_engine.py','r3_engine_client.py'):
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
        config, mounts = configuration(job, stop, pin)
        if any(not p.exists() for p,_,_ in mounts): raise RuntimeError('missing exact mount')
        live = {'observed_unix':time.time(), 'attempt_id':job.name, 'generation':generation,
            'ledger_sha256':document_hash(ledger), 'gpu_uuid':GPU, 'gpu_idle':True, 'owned_jobs_idle':True,
            'network_disabled':config['HostConfig']['NetworkMode']=='none',
            'protected_mounts_absent': all(t in ('/code','/out','/deps','/models/qwen3-8b','/models/.'+GPU+'.lock','/dispatch') for _,t,_ in mounts),
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
