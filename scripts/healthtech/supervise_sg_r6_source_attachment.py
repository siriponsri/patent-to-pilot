"""Approved1800second CPU1 fixed-source attachment; no model or evaluator."""
from pathlib import Path
import json,hashlib,time
from r3_engine_client import Engine,EngineError
from supervise_r3_engine_v2 import configuration,supervise,BASE
NAME='ptp-sg-r6-source-attachment-20261111-v1'
JOB=Path('/home/chaw/patent-to-pilot-jobs')/NAME
def add_temporary_workspace(config):
    from copy import deepcopy
    result=deepcopy(config);host=result['HostConfig']
    if host['Memory']!=1536*1024**2 or not host['ReadonlyRootfs'] or host['NetworkMode']!='none':
        raise RuntimeError('temporary workspace requires unchanged CPU isolation')
    host['Tmpfs']={'/tmp':'rw,nosuid,size=67108864'}
    return result

def source_configuration(job,stop,digest):
    config,mounts=configuration('census',job,stop,digest)
    mounts += [(job/'source-sample.json','/input/source-sample.json',True), (job/'alias-sample.json','/input/alias-sample.json',True)]
    config=add_temporary_workspace(config)
    config['HostConfig']['Ulimits']=[{'Name':'fsize','Soft':64*1024**2,'Hard':64*1024**2}]
    config['HostConfig']['Mounts']=[{'Type':'bind','Source':str(s),'Target':t,'ReadOnly':ro} for s,t,ro in mounts]
    config['Env']+=['PYTHONPATH=/code/src']
    config['Env'] += [n+'=1' for n in ['OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS','RAYON_NUM_THREADS']]
    config['Cmd']=['-s','/code/scripts/healthtech/run_sg_r6_source_attachment.py',digest]
    return config,mounts
def main():
    import resource
    if Path(__file__).resolve().parent!=JOB:raise RuntimeError('fixed job required')
    resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2))
    resource.setrlimit(resource.RLIMIT_FSIZE,(16*1024**2,16*1024**2))
    with (JOB/'admission.json').open('x') as f:json.dump({'retry':False},f)
    start=time.monotonic();receipt={'status':'PREFLIGHT','model_calls':0,'gpu_seconds':0};engine=Engine();created=False
    try:
        raw=(JOB/'declaration.json').read_bytes();d=json.loads(raw);digest=hashlib.sha256(raw).hexdigest()
        approval=json.loads((JOB/'owner-approval.json').read_bytes())
        if approval.get('status')!='APPROVED' or digest not in approval['declarations_sha256'].values():raise RuntimeError('approval binding missing')
        for path,expected in d['files_sha256'].items():
            p=(JOB/'code'/path).resolve()
            if not p.is_relative_to((JOB/'code').resolve()) or hashlib.sha256(p.read_bytes()).hexdigest()!=expected:raise RuntimeError('code pin mismatch')
        for name in ['r3_engine_client.py','supervise_r3_engine_v2.py','supervise_sg_r6_source_attachment.py']:
            if (JOB/name).read_bytes()!=(JOB/'code/scripts/healthtech'/name).read_bytes():raise RuntimeError('controller copy differs')
        receipt['engine']=engine.check_version()
        try:engine.inspect(NAME)
        except EngineError as e:
            if e.status!=404:raise
        else:raise RuntimeError('existing preflight; no replay')
        (JOB/'out').mkdir(exist_ok=False)
        config,mounts=source_configuration(JOB,start+1560,digest)
        if any(not s.exists() for s,_,_ in mounts):raise RuntimeError('missing input mount')
        created=True
        reason,state=supervise(engine,NAME,config,mounts,start+1560,JOB/'out')
        receipt.update(status=reason,container_state=state['State'])
    except BaseException as error:
        receipt.update(status='FAILED',exception_type=type(error).__name__)
        if created:
            try:receipt['container_state']=engine.terminate(NAME)['State']
            except EngineError as e:receipt['status']='FAILED_NO_CONTAINER' if e.status==404 else 'TERMINATION_UNKNOWN'
            except BaseException:receipt['status']='TERMINATION_UNKNOWN'
        raise
    finally:
        receipt['whole_wall_seconds']=time.monotonic()-start
        with (JOB/'terminal.json').open('x') as f:json.dump(receipt,f,indent=2)
if __name__=='__main__':main()
