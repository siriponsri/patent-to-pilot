"""Fixed R6 calibration controller; exact evidence and one exclusive admission."""
import json
from pathlib import Path
import signal
import subprocess
import sys
import time

from r3_engine_client import Engine,EngineError
from supervise_sacr_r5_engine import configuration as prior_configuration,supervise,GPU


def configuration(job,stop,manifest_sha256):
    config,mounts=prior_configuration('smoke',job,stop,manifest_sha256)
    mounts=[m for m in mounts if m[1] not in ('/declaration.json','/resource-ledger.json')]
    mounts.append((job/'dispatch','/dispatch',True))
    config['HostConfig']['Mounts']=[{'Type':'bind','Source':str(p),'Target':target,'ReadOnly':readonly}
                                  for p,target,readonly in mounts]
    config['Cmd']=['-s','/code/scripts/healthtech/run_r6_calibration.py',str(stop),manifest_sha256]
    return config,mounts


def main(manifest_sha256):
    import resource
    job=Path(__file__).resolve().parent;name=job.name
    if (job.parent!=Path('/home/chaw/patent-to-pilot-jobs')
            or name not in ('ptp-r6-calibration-20261111-v1','ptp-r6-calibration-20261111-v2')):
        raise RuntimeError('fixed calibration job required')
    resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
    resource.setrlimit(resource.RLIMIT_FSIZE,(64*1024**2,64*1024**2))
    start=time.monotonic()
    # Never remove this receipt after any failure. A new destination cannot reuse
    # a qualified attempt because its exact fixed name is checked below.
    with (job/'admission.json').open('x') as f:
        json.dump({'status':'CONSUMED_UNRESOLVED','manifest_sha256':manifest_sha256,'retry':False},f)
        f.flush()
        import os
        os.fsync(f.fileno())
    receipt={'status':'PREFLIGHT','retry':False,'started_unix':time.time()}
    engine=Engine();created=False
    def interrupted(*_):raise InterruptedError('calibration controller interrupted')
    signal.signal(signal.SIGTERM,interrupted)
    try:
        root=job/'code';sys.path.insert(0,str(root/'src'))
        from patent_to_pilot.research.r6_dispatch_files import load_dispatch,validate_worker_package
        evidence=load_dispatch(job/'dispatch',manifest_path='manifest.json',manifest_sha256=manifest_sha256)
        d=evidence['declaration']
        if d['attempt_id']!=name or d['stage']!='calibration' or d['maximum_calls']!=24:
            raise RuntimeError('fixed calibration declaration mismatch')
        validate_worker_package(root,d['files_sha256'],d['package_sha256'])
        for file in ['r3_engine_client.py','supervise_sacr_r5_engine.py','supervise_r6_calibration.py']:
            if (job/file).read_bytes()!=(root/'scripts/healthtech'/file).read_bytes():
                raise RuntimeError('controller executable differs from pinned source')
        receipt['engine']=engine.check_version()
        try:engine.inspect(name)
        except EngineError as error:
            if error.status!=404:raise
        else:raise RuntimeError('existing container prevents replay')
        used=subprocess.run(['nvidia-smi','--query-compute-apps=pid,gpu_uuid','--format=csv,noheader'],
            check=True,capture_output=True,text=True,timeout=10).stdout
        if GPU in used:raise RuntimeError('approved GPU occupied')
        stop=start+d['seconds']-240
        if time.monotonic()+30>=stop:raise TimeoutError('setup exhausted stage allowance')
        (job/'out').mkdir(exist_ok=False)
        config,mounts=configuration(job,stop,manifest_sha256)
        if any(not p.exists() for p,_,_ in mounts):raise RuntimeError('required mount missing')
        # Container creation failures remain unknown until authoritative inspect.
        created=True
        reason,state=supervise(engine,name,config,mounts,stop,job/'out')
        receipt.update(status=reason,container_state=state['State'])
    except BaseException as error:
        receipt.update(status='FAILED_PREFLIGHT',exception_type=type(error).__name__)
        if created:
            try:receipt.update(status='FAILED_TERMINATED',container_state=engine.terminate(name)['State'])
            except EngineError as missing:
                receipt['status']='FAILED_NO_CONTAINER' if missing.status==404 else 'TERMINATION_UNKNOWN'
            except BaseException:receipt['status']='TERMINATION_UNKNOWN'
        raise
    finally:
        receipt.update(whole_wall_seconds=time.monotonic()-start,controller_cpu_seconds=time.process_time(),
            controller_peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024)
        with (job/'terminal.json').open('x') as f:json.dump(receipt,f,indent=2)


if __name__=='__main__':main(sys.argv[1])
