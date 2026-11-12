"""CPU-only authored pipeline fixture for the automatic synthetic worker.

Reuses the qualified CPU grammar container configuration (CPU1, 1536MiB,
network off, read-only rootfs, tokenizer files only, no weights/GPU), plus a
writable /dispatch for the fixture declaration and generation_config.json.
Requires a precharged 600 s durable CPU booking named after the job.
"""
import hashlib, json, signal, sqlite3, sys, time
from pathlib import Path
from r3_engine_client import Engine, EngineError
from supervise_r3_engine_v2 import supervise, BASE
from supervise_automatic_grammar import configuration as grammar_configuration

NAME = 'ptp-auto-native-fixture-20261112-v3'  # v1 collision; v2 PASS (marking v4)


def configuration(job, stop, pin, tokenizer_files):
    config, mounts = grammar_configuration(job, stop, pin, [n for n in tokenizer_files if n != 'generation_config.json'])
    if 'generation_config.json' in tokenizer_files:
        mounts.append((BASE/'models/qwen3-8b/generation_config.json', '/models/qwen3-8b/generation_config.json', True))
    mounts.append((job/'dispatch', '/dispatch', False))
    config['HostConfig']['Mounts'] = [{'Type': 'bind', 'Source': str(s), 'Target': t, 'ReadOnly': ro} for s, t, ro in mounts]
    config['Cmd'] = ['-s', '/code/scripts/healthtech/qualify_automatic_native_pipeline.py', pin]
    return config, mounts


def main(pin):
    import resource
    job = Path(__file__).resolve().parent
    if job != Path('/home/chaw/patent-to-pilot-jobs')/NAME: raise RuntimeError('fixed CPU job path required')
    resource.setrlimit(resource.RLIMIT_AS, (512*1024**2, 512*1024**2))
    resource.setrlimit(resource.RLIMIT_CPU, (30, 30))
    start = time.monotonic(); created = False; engine = Engine()
    receipt = {'model_calls': 0, 'gpu_seconds': 0, 'retry': False, 'attempt_id': NAME}
    with (job/'admission.json').open('x') as f: json.dump({'declaration_sha256': pin, 'retry': False}, f)
    def interrupted(*args): raise InterruptedError('CPU controller interrupted')
    signal.signal(signal.SIGTERM, interrupted)
    try:
        raw = (job/'declaration.json').read_bytes()
        if hashlib.sha256(raw).hexdigest() != pin: raise RuntimeError('declaration pin changed')
        d = json.loads(raw)
        if d['kind'] != 'automatic-native-pipeline-fixture' or d['cpu_seconds'] > 90: raise RuntimeError('CPU scope mismatch')
        sys.path.insert(0, str(job/'code/src'))
        from patent_to_pilot.research.r7_dispatch_files import validate_worker_package
        from patent_to_pilot.research.r6_dispatch_journal import document_hash
        validate_worker_package(job/'code', d['files_sha256'], d['package_sha256'])
        for name in ('supervise_automatic_native_fixture.py', 'supervise_automatic_pipeline_fixture.py', 'supervise_automatic_grammar.py',
                     'supervise_r3_engine_v2.py', 'r3_engine_client.py'):
            if (job/name).read_bytes() != (job/'code/scripts/healthtech'/name).read_bytes(): raise RuntimeError('controller pin changed')
        with sqlite3.connect('file:'+str(job.parent/'ptp-r6-control/dispatch.sqlite')+'?mode=ro', uri=True) as db:
            active = db.execute('SELECT active FROM head').fetchone()[0]
            row = db.execute('SELECT receipt FROM automatic_cpu_bookings WHERE id=?', (NAME,)).fetchone()
        if active is not None or row is None: raise RuntimeError('active global job or missing CPU booking')
        booking = json.loads(row[0])
        if (document_hash(booking) != d['cpu_booking_sha256'] or booking['conservative_cpu_seconds'] != 120
                or booking['location'] != 'remote'): raise RuntimeError('CPU booking mismatch')
        engine.check_version()
        try: engine.inspect(NAME)
        except EngineError as error:
            if error.status != 404: raise
        else: raise RuntimeError('existing CPU container prevents replay')
        (job/'out').mkdir(exist_ok=False); (job/'dispatch').mkdir(exist_ok=False)
        config, mounts = configuration(job, start+110, pin, d['tokenizer_files_sha256'])
        if any(not p.exists() for p, _, _ in mounts): raise RuntimeError('missing exact mount')
        created = True
        reason, state = supervise(engine, NAME, config, mounts, start+110, job/'out')
        receipt.update(status=reason, container_state=state['State'])
    except BaseException as error:
        receipt.update(status='FAILED', exception_type=type(error).__name__)
        if created:
            try: receipt['container_state'] = engine.terminate(NAME)['State']
            except BaseException: receipt['status'] = 'TERMINATION_UNKNOWN'
        else: receipt.update(container_outcome='NO_CONTAINER', create_request_sent=False)
        raise
    finally:
        receipt.update(whole_wall_seconds=time.monotonic()-start, controller_cpu_seconds=time.process_time())
        with (job/'terminal.json').open('x') as f: json.dump(receipt, f, indent=2)


if __name__ == '__main__': main(sys.argv[1])
