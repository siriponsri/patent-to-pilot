"""Single CPU-only preflight under owner-approved600second limit."""
from pathlib import Path
import json,hashlib,time
from r3_engine_client import Engine,EngineError
from supervise_r3_engine_v2 import configuration,supervise,BASE
NAME='ptp-sacr-r5-token-preflight-20261111-v1'
JOB=Path('/home/chaw/patent-to-pilot-jobs')/NAME
def add_temporary_workspace(config):
    from copy import deepcopy
    result=deepcopy(config);host=result['HostConfig']
    if host['Memory']!=1536*1024**2 or not host['ReadonlyRootfs'] or host['NetworkMode']!='none':
        raise RuntimeError('temporary workspace requires unchanged CPU isolation')
    host['Tmpfs']={'/tmp':'rw,nosuid,size=67108864'}
    return result
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
        for name in ['r3_engine_client.py','supervise_r3_engine_v2.py','supervise_r5_token_preflight.py']:
            if (JOB/name).read_bytes()!=(JOB/'code/scripts/healthtech'/name).read_bytes():raise RuntimeError('controller copy differs')
        receipt['engine']=engine.check_version()
        try:engine.inspect(NAME)
        except EngineError as e:
            if e.status!=404:raise
        else:raise RuntimeError('existing preflight; no replay')
        (JOB/'out').mkdir(exist_ok=False)
        config,mounts=configuration('census',JOB,start+540,digest)
        mounts=[m for m in mounts if m[1]!='/input/corpus.jsonl']
        mounts += [(BASE/'venv/lib/python3.12/site-packages','/deps',True),(BASE/'models/qwen3-8b','/models/qwen3-8b',True)]
        config['HostConfig']['NanoCpus']=2_000_000_000
        # Tmpfs is accounted within the unchanged1536MiB cgroup RAM ceiling.
        config=add_temporary_workspace(config)
        config['HostConfig']['Mounts']=[{'Type':'bind','Source':str(s),'Target':t,'ReadOnly':ro} for s,t,ro in mounts]
        config['Env']+=['PYTHONPATH=/code/src:/deps','HF_HUB_OFFLINE=1','TRANSFORMERS_OFFLINE=1','TOKENIZERS_PARALLELISM=false']
        config['Env'] += [n+'=2' for n in ['OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS','RAYON_NUM_THREADS']]
        config['Cmd']=['-s','/code/scripts/healthtech/preflight_sacr_r5_tokens.py',digest]
        if any(not s.exists() for s,_,_ in mounts):raise RuntimeError('missing input mount')
        created=True
        reason,state=supervise(engine,NAME,config,mounts,start+540,JOB/'out')
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
