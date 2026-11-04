"""Exercise an installed wheel, without the live checkout or paid transport."""
from pathlib import Path
import sys, os, json, hashlib, datetime, socket, contextlib, importlib.metadata, argparse, xml.etree.ElementTree as ET

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--candidate-root',type=Path,required=True)
parser.add_argument('--output-dir',type=Path,required=True)
parser.add_argument('--forbid-root',type=Path,action='append',default=[])
args=parser.parse_args()
ROOT=args.candidate_root.resolve()
OUT=args.output_dir.resolve()
ENV=Path(sys.prefix).resolve()
OUT.mkdir(exist_ok=False)
os.chdir(ROOT)
os.environ['PYTHONDONTWRITEBYTECODE']='1'
os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1'
os.environ['LOCALAPPDATA']=str(OUT/'state')
os.environ['XDG_STATE_HOME']=str(OUT/'state')
os.environ.pop('PYTHONPATH',None)
os.environ.pop('OPENROUTER_API_KEY',None)
sys.dont_write_bytecode=True
sys.path.insert(0,str(ROOT/'tests'))
import patent_to_pilot
assert sys.prefix!=sys.base_prefix
assert Path(patent_to_pilot.__file__).resolve().is_relative_to(ENV), patent_to_pilot.__file__
network=[]; forbidden=[]
def guarded(original):
    def wrap(address,*args,**kwargs):
        host=address[0] if isinstance(address,tuple) else address
        if str(host).lower() not in {'localhost','127.0.0.1','::1'}:
            network.append('non_loopback')
            raise RuntimeError('offline wheel check forbids external network')
        return original(address,*args,**kwargs)
    return wrap
socket.create_connection=guarded(socket.create_connection)
socket.getaddrinfo=guarded(socket.getaddrinfo)
def method_guard(original):
    def wrap(sock,address,*args,**kwargs):
        host=address[0] if isinstance(address,tuple) else address
        if str(host).lower() not in {'localhost','127.0.0.1','::1'}:
            network.append('non_loopback')
            raise RuntimeError('offline wheel check forbids external network')
        return original(sock,address,*args,**kwargs)
    return wrap
for name in ('connect','connect_ex','bind'):
    setattr(socket.socket,name,method_guard(getattr(socket.socket,name)))
forbidden_roots=[p.resolve() for p in args.forbid_root]
def audit(event,args):
    if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
        p=Path(os.fsdecode(args[0])).resolve()
        if any(p.is_relative_to(root) for root in forbidden_roots):
            forbidden.append('live_workspace_read')
            raise RuntimeError('live checkout forbidden during installed reproduction')
sys.addaudithook(audit)
import pytest
targets=['test_healthtech','test_healthtech_case_journal','test_healthtech_api_generation',
         'test_healthtech_local_epoch','test_healthtech_local_execution','test_provider_adapter',
         'test_release_budget_process','test_healthtech_generation_payload']
targets=[f'tests/{n}.py' for n in targets if (ROOT/'tests'/f'{n}.py').exists()]
with (OUT/'pytest.log').open('w',encoding='utf-8') as log,contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
    code=pytest.main(['-q','-o','pythonpath=','-p','no:cacheprovider','--basetemp',str(OUT/'tmp'),
                     '--junitxml',str(OUT/'tests.xml'),*targets])

from patent_to_pilot.healthtech.engine import DossierInput, run_dossier, serialize_dossier, export_markdown
input_file=ROOT/'examples/healthtech/synthetic-device/input.json'
dossier,events,manifest=run_dossier(DossierInput.model_validate_json(input_file.read_text(encoding='utf-8')),
                                  run_id='installed-wheel-synthetic',code_commit='88dc404+dirty-snapshot')
outputs={
    'dossier.json':json.dumps(serialize_dossier(dossier,purpose='local_research'),ensure_ascii=False,indent=2)+'\n',
    'dossier.en.md':export_markdown(dossier,language='en',purpose='local_research'),
    'dossier.th.md':export_markdown(dossier,language='th',purpose='local_research'),
    'manifest.json':manifest.model_dump_json(indent=2)+'\n',
    'acquisition_events.jsonl':'\n'.join(e.model_dump_json() for e in events)+'\n',
}
for name,content in outputs.items():(OUT/name).write_text(content,encoding='utf-8')
modules={n:str(Path(m.__file__).resolve().relative_to(ENV)) for n,m in list(sys.modules.items())
         if n=='patent_to_pilot' or n.startswith('patent_to_pilot.') if getattr(m,'__file__',None)}
counts={k:sum(int(e.attrib.get(k,0)) for e in ET.parse(OUT/'tests.xml').getroot().iter('testsuite')) for k in ['tests','failures','errors','skipped']}
receipt={'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'status':'PASS' if code==0 and not network and not forbidden else 'FAIL',
 'pytest_exit_code':int(code),'tests':counts,'targets':targets,'installed_production_modules':modules,
 'workflow':'synthetic authored HealthTech dossier -> JSON, English/Thai Markdown, acquisition events, manifest',
 'input_sha256':hashlib.sha256(input_file.read_bytes()).hexdigest(),
 'output_hashes':{name:hashlib.sha256((OUT/name).read_bytes()).hexdigest() for name in outputs},
 'external_network_attempts':len(network),'live_workspace_read_attempts':len(forbidden),
 'provider_calls':0,'gpu_jobs':0,'new_paid_cost_usd':0,
 'dependencies':{n:importlib.metadata.version(n) for n in ('patent-to-pilot','pydantic','jsonschema','pytest')},
 'scope':'installed wheel in task venv with pre-existing system-site dependencies; Python socket/file guards, not an OS sandbox or pristine-machine install; synthetic engineering evidence, not new science'}
(OUT/'verification.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in receipt.items() if k!='installed_production_modules'},indent=2))
if code:print((OUT/'pytest.log').read_text(encoding='utf-8')[-7000:])
raise SystemExit(0 if receipt['status']=='PASS' else 1)
