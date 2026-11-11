"""Proposed packaging revision; separate approval required before dispatch."""
import hashlib
import json
from pathlib import Path
import signal
import subprocess
import sys
import time
from r3_engine_client import Engine, EngineError

IMAGE='sha256:cb33f7f771ecec2ef1225cf39b159591a040391bd73e4c01f00fdfc4c47611d2'
GPU='GPU-277ccc57-c3e5-0731-cd49-f4f8695f7089'
BASE=Path('/home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031')
NAMES={'census':'ptp-sg-r3-census-20261111-v2','smoke':'ptp-sacr-r3-synthetic-smoke-20261111-v2'}


def configuration(kind, job, stop, declaration_sha):
    smoke=kind=='smoke'
    mounts=[(job/'code','/code',True),(job/'out','/out',False),
            (job/'declaration.json','/declaration.json',True)]
    if smoke:
        mounts += [(job/'resource-ledger.json','/resource-ledger.json',True),
                   (BASE/'venv/lib/python3.12/site-packages','/deps',True),
                   (BASE/'models/qwen3-8b','/models/qwen3-8b',True),
                   (BASE/('models/.'+GPU+'.lock'),'/models/.'+GPU+'.lock',False)]
    else:
        mounts += [(job/'corpus.jsonl','/input/corpus.jsonl',True)]
    env=['PYTHONDONTWRITEBYTECODE=1','CUDA_VISIBLE_DEVICES='+ (GPU if smoke else '')]
    if smoke:
        env += ['PYTHONPATH=/code/src:/deps','HF_HUB_OFFLINE=1','TRANSFORMERS_OFFLINE=1',
                'TOKENIZERS_PARALLELISM=false']
        env += [name+'=8' for name in ['OMP_NUM_THREADS','MKL_NUM_THREADS',
                'OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS','RAYON_NUM_THREADS']]
    host={'NetworkMode':'none','ReadonlyRootfs':True,'Privileged':False,
          'CapDrop':['ALL'],'SecurityOpt':['no-new-privileges'],
          'NanoCpus':8_000_000_000 if smoke else 1_000_000_000,
          'Memory':31*1024**3 if smoke else 1536*1024**2,
          'MemorySwap':31*1024**3 if smoke else 1536*1024**2,
          'PidsLimit':256 if smoke else 64,'LogConfig':{'Type':'none','Config':{}},
          'Ulimits':[{'Name':'fsize','Soft':(64 if smoke else 8)*1024**2,
                      'Hard':(64 if smoke else 8)*1024**2}],
          'Mounts':[{'Type':'bind','Source':str(source),'Target':target,'ReadOnly':ro}
                    for source,target,ro in mounts]}
    if smoke:
        host['DeviceRequests']=[{'Driver':'','Count':0,'DeviceIDs':[GPU],
                                'Capabilities':[['gpu']],'Options':{}}]
        host['Tmpfs']={'/tmp':'rw,nosuid,size=268435456'}
    script='run_sacr_r3_synthetic_smoke_v2.py' if smoke else 'run_sg_r3_census_v2.py'
    cmd=['-s','/code/scripts/healthtech/'+script]
    if smoke:cmd += [str(stop)]
    cmd += [declaration_sha]
    return {'Image':IMAGE,'User':'1000:1000','Entrypoint':['python'],'Cmd':cmd,
            'Env':env,'HostConfig':host},mounts


def validate_isolation(state, config, mounts):
    host=state['HostConfig'];expected=config['HostConfig']
    for key in ['NetworkMode','ReadonlyRootfs','Privileged','NanoCpus','Memory','MemorySwap',
                'PidsLimit','CapDrop','SecurityOpt','Ulimits']:
        if host[key]!=expected[key]:raise RuntimeError('isolation mismatch: '+key)
    if host['LogConfig']['Type']!='none' or (host.get('DeviceRequests') or []) != expected.get('DeviceRequests',[]):
        raise RuntimeError('logging/GPU mismatch')
    if (host.get('Tmpfs') or {})!=expected.get('Tmpfs',{}):
        raise RuntimeError('temporary filesystem mismatch')
    actual={(m['Source'],m['Destination'],not m['RW']) for m in state['Mounts'] if m['Type']=='bind'}
    if actual!={(str(s),t,ro) for s,t,ro in mounts}:
        raise RuntimeError('mount mismatch')
    if state['Config']['User']!='1000:1000' or state['Image']!=IMAGE:
        raise RuntimeError('identity mismatch')
    for key in ['Entrypoint','Cmd','Env']:
        # Images may append defaults to Env; all declared entries must match.
        if key=='Env':
            actual_env=dict(item.split('=',1) for item in state['Config']['Env'])
            if any(actual_env.get(k)!=v for k,v in (x.split('=',1) for x in config['Env'])):
                raise RuntimeError('environment mismatch')
        elif state['Config'][key]!=config[key]:raise RuntimeError('command mismatch')


def supervise(engine,name,config,mounts,stop,output,clock=time.monotonic,sleep=time.sleep):
    engine.request('POST','/v1.47/containers/create?name='+name,config)
    state=engine.inspect(name);validate_isolation(state,config,mounts)
    with (output.parent/'isolation.json').open('x') as f:
        json.dump({'status':'PASS_BEFORE_START','mounts':state['Mounts'],
                   'host_config':state['HostConfig']},f,indent=2)
    engine.request('POST','/v1.47/containers/'+name+'/start')
    while True:
        state=engine.inspect(name)
        if not state['State']['Running']:return 'TERMINAL',state
        size=sum(p.stat().st_size for p in output.rglob('*') if p.is_file())
        if clock()>=stop or size>64*1024**2:
            reason='TIMEOUT' if clock()>=stop else 'OUTPUT_LIMIT'
            return reason,engine.terminate(name)
        sleep(1)


def main(kind):
    if kind not in NAMES:raise ValueError('unknown job kind')
    name=NAMES[kind];job=Path('/home/chaw/patent-to-pilot-jobs')/name
    if Path(__file__).resolve().parent!=job:raise RuntimeError('fixed path required')
    import resource
    cap=(1024 if kind=='smoke' else 512)*1024**2
    resource.setrlimit(resource.RLIMIT_AS,(cap,cap))
    resource.setrlimit(resource.RLIMIT_FSIZE,(64*1024**2,64*1024**2))
    # Exclusive receipt guards the whole attempt, including pre-create failures.
    with (job/'admission.json').open('x') as f:json.dump({'retry':False,'kind':kind},f)
    start=time.monotonic();receipt={'status':'PREFLIGHT','retry':False,'started_unix':time.time()}
    engine=Engine();may_have_created=False
    try:
        raw=(job/'declaration.json').read_bytes();digest=hashlib.sha256(raw).hexdigest();d=json.loads(raw)
        approval=json.loads((job/'owner-approval.json').read_bytes())
        if approval.get('status')!='APPROVED' or digest not in approval['declarations_sha256'].values():
            raise RuntimeError('exact declaration approval missing')
        if d['run_id']!=name or d['wall_seconds']!=1800:raise RuntimeError('scope mismatch')
        root=job/'code'
        required={p.relative_to(root).as_posix() for p in (root/'src').rglob('*.py')}
        required|={'scripts/healthtech/r3_engine_client.py','scripts/healthtech/supervise_r3_engine_v2.py'}
        required.add('scripts/healthtech/'+('run_sacr_r3_synthetic_smoke_v2.py' if kind=='smoke' else 'run_sg_r3_census_v2.py'))
        if not required<=set(d['files_sha256']):raise RuntimeError('source pins incomplete')
        for path,h in d['files_sha256'].items():
            p=(root/path).resolve()
            if not p.is_relative_to(root.resolve()) or hashlib.sha256(p.read_bytes()).hexdigest()!=h:
                raise RuntimeError('source pin mismatch')
        for file in ['r3_engine_client.py','supervise_r3_engine_v2.py']:
            if (job/file).read_bytes()!=(root/'scripts/healthtech'/file).read_bytes():
                raise RuntimeError('controller copy differs')
        receipt['engine']=engine.check_version()
        try:engine.inspect(name)
        except EngineError as e:
            if e.status!=404:raise
        else:raise RuntimeError('owned name exists; no replay')
        if kind=='smoke':
            sys.path.insert(0,str(root/'src'))
            from patent_to_pilot.research.sacr_r3_runtime_guards import validate_sources,validate_budget
            validate_sources(root,d['files_sha256'])
            ledger_raw=(job/'resource-ledger.json').read_bytes()
            if hashlib.sha256(ledger_raw).hexdigest()!=d['resource_ledger_sha256']:raise RuntimeError('ledger mismatch')
            validate_budget(json.loads(ledger_raw),1800)
            used=subprocess.run(['nvidia-smi','--query-compute-apps=pid,gpu_uuid','--format=csv,noheader'],
                                check=True,capture_output=True,text=True,timeout=10).stdout
            if GPU in used:raise RuntimeError('approved GPU occupied')
        (job/'out').mkdir(exist_ok=False)
        config,mounts=configuration(kind,job,start+1560,digest)
        if any(not p.exists() for p,_,_ in mounts):raise RuntimeError('mount missing')
        signal.signal(signal.SIGTERM,lambda *_:(_ for _ in ()).throw(InterruptedError('interrupted')))
        may_have_created=True
        reason,state=supervise(engine,name,config,mounts,start+1560,job/'out')
        receipt.update(status=reason,container_state=state['State'])
    except BaseException as error:
        receipt.update(status='FAILED_PREFLIGHT',exception_type=type(error).__name__)
        if may_have_created:
            try:receipt.update(status='FAILED_TERMINATED',container_state=engine.terminate(name)['State'])
            except EngineError as missing:
                receipt['status']='FAILED_NO_CONTAINER' if missing.status==404 else 'TERMINATION_UNKNOWN'
            except BaseException:receipt['status']='TERMINATION_UNKNOWN'
        raise
    finally:
        receipt['whole_wall_seconds']=time.monotonic()-start
        receipt['controller_peak_rss_bytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
        with (job/'terminal.json').open('x') as f:json.dump(receipt,f,indent=2)


if __name__=='__main__':main(sys.argv[1])
