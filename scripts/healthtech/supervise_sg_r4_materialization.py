"""Single bounded corpus materialization; no inference or database access."""
from pathlib import Path
import json,hashlib,time
from r3_engine_client import Engine,EngineError
from supervise_r3_engine_v2 import configuration,validate_isolation
NAME='ptp-sg-r4-materialization-20261111-v1'
JOB=Path('/home/chaw/patent-to-pilot-jobs')/NAME
def job_configuration(job,digest):
    config,mounts=configuration('census',job,0,digest)
    mounts=[(s,('/corpus.jsonl' if t=='/input/corpus.jsonl' else t),ro) for s,t,ro in mounts]
    mounts.append((job/'source-sample.json','/source-sample.json',True))
    config['HostConfig']['Mounts']=[{'Type':'bind','Source':str(s),'Target':t,'ReadOnly':ro} for s,t,ro in mounts]
    config['HostConfig']['Ulimits']=[{'Name':'fsize','Soft':128*1024**2,'Hard':128*1024**2}]
    config['Cmd']=['-s','/code/scripts/healthtech/run_sg_r4_materialization.py',digest]
    return config,mounts
def main():
    import resource
    if Path(__file__).resolve().parent!=JOB:raise RuntimeError('fixed job required')
    resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2))
    resource.setrlimit(resource.RLIMIT_FSIZE,(16*1024**2,16*1024**2))
    with (JOB/'admission.json').open('x') as f:json.dump({'retry':False},f)
    started=time.monotonic();receipt={'status':'PREFLIGHT','model_calls':0,'gpu_seconds':0,'retry':False}
    engine=Engine();created=False
    try:
        raw=(JOB/'declaration.json').read_bytes();d=json.loads(raw);digest=hashlib.sha256(raw).hexdigest()
        approval=json.loads((JOB/'owner-approval.json').read_bytes())
        if approval.get('status')!='APPROVED' or digest not in approval['declarations_sha256'].values():raise RuntimeError('approval mismatch')
        if d['run_id']!=NAME or d['wall_seconds']!=1800:raise RuntimeError('job scope mismatch')
        root=JOB/'code'
        required={p.relative_to(root).as_posix() for p in (root/'src').rglob('*.py')}
        required|={'scripts/healthtech/run_sg_r4_materialization.py','scripts/healthtech/supervise_sg_r4_materialization.py','scripts/healthtech/r3_engine_client.py','scripts/healthtech/supervise_r3_engine_v2.py'}
        if not required<=set(d['files_sha256']):raise RuntimeError('incomplete pins')
        for name,expected in d['files_sha256'].items():
            p=(root/name).resolve()
            if not p.is_relative_to(root.resolve()) or hashlib.sha256(p.read_bytes()).hexdigest()!=expected:raise RuntimeError('code changed')
        for name in ['r3_engine_client.py','supervise_r3_engine_v2.py','supervise_sg_r4_materialization.py']:
            if (JOB/name).read_bytes()!=(root/'scripts/healthtech'/name).read_bytes():raise RuntimeError('controller copy differs')
        receipt['engine']=engine.check_version()
        try:engine.inspect(NAME)
        except EngineError as e:
            if e.status!=404:raise
        else:raise RuntimeError('existing job no replay')
        (JOB/'out').mkdir(exist_ok=False);config,mounts=job_configuration(JOB,digest)
        if any(not s.exists() for s,_,_ in mounts):raise RuntimeError('missing mount')
        created=True;engine.request('POST','/v1.47/containers/create?name='+NAME,config)
        state=engine.inspect(NAME);validate_isolation(state,config,mounts)
        with (JOB/'isolation.json').open('x') as f:json.dump({'status':'PASS_BEFORE_START','mounts':state['Mounts'],'host_config':state['HostConfig']},f,indent=2)
        engine.request('POST','/v1.47/containers/'+NAME+'/start')
        reason='TERMINAL'
        while True:
            state=engine.inspect(NAME)
            if not state['State']['Running']:break
            if time.monotonic()-started>=1560 or sum(p.stat().st_size for p in (JOB/'out').rglob('*') if p.is_file())>128*1024**2:
                reason='RESOURCE_STOP';state=engine.terminate(NAME);break
            time.sleep(1)
        receipt.update(status=reason,container_state=state['State'])
    except BaseException as error:
        receipt.update(status='FAILED',exception_type=type(error).__name__)
        if created:
            try:receipt['container_state']=engine.terminate(NAME)['State']
            except EngineError as e:receipt['status']='FAILED_NO_CONTAINER' if e.status==404 else 'TERMINATION_UNKNOWN'
            except BaseException:receipt['status']='TERMINATION_UNKNOWN'
        raise
    finally:
        receipt.update(whole_wall_seconds=time.monotonic()-started,controller_peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024)
        with (JOB/'terminal.json').open('x') as f:json.dump(receipt,f,indent=2)
if __name__=='__main__':main()
