from pathlib import Path
import contextlib, datetime, hashlib, importlib.metadata, json, os, runpy, socket, subprocess, sys, traceback, xml.etree.ElementTree as E

import argparse
parser=argparse.ArgumentParser(description='Offline release reproduction with sockets and credential-file reads denied')
parser.add_argument('--output-dir',type=Path,required=True)
parser.add_argument('--source-commit',required=True,help='Commit verified separately with authorized Git; this script does not inspect .git')
parser.add_argument('--forbid-root',type=Path,help='Optional original workspace to deny during clean reproduction')
options=parser.parse_args()
ROOT=Path(__file__).resolve().parents[1]
ORIGINAL=options.forbid_root.resolve() if options.forbid_root else None
OUT=options.output_dir.resolve()
OUT.mkdir(exist_ok=False)
os.chdir(ROOT)
os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1'
os.environ['PYTHONDONTWRITEBYTECODE']='1'; sys.dont_write_bytecode=True
assert sys.prefix!=sys.base_prefix
assert not (ROOT/'.env').exists()
# Git metadata inspection is stopped after its ownership rejection. Ordinary
# source-file reads remain permitted; never read .git or change trust settings.
tracked=[]
for directory,subdirs,files in os.walk(ROOT):
    subdirs[:]=[d for d in subdirs if d not in {'.git','__pycache__','.pytest_cache'} and not d.endswith('.egg-info')]
    tracked.extend((Path(directory)/f).relative_to(ROOT).as_posix() for f in files if not f.endswith('.pyc'))
def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()
def snap():return {p:digest(ROOT/p) for p in tracked}
before=snap(); network=[]; forbidden=[]
def deny(*args,**kwargs):network.append('blocked socket/DNS');raise RuntimeError('network denied for offline reproduction')
socket.socket.connect=deny; socket.socket.connect_ex=deny; socket.socket.bind=deny; socket.create_connection=deny; socket.getaddrinfo=deny
def audit(event,args):
    if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
        p=Path(os.fsdecode(args[0])); absolute=os.path.abspath(p).casefold()
        if p.name.casefold()=='.env' or (ORIGINAL is not None and absolute.startswith(str(ORIGINAL).casefold()+os.sep)):
            forbidden.append(str(p)); raise RuntimeError('original workspace/credential reads denied')
sys.addaudithook(audit)
import patent_to_pilot,pytest
assert Path(patent_to_pilot.__file__).resolve().is_relative_to(ROOT)
tests=['tests/test_g10_offline_comparison.py','tests/test_g09_g10_integration.py','tests/test_g11_adaptation.py','tests/test_provider_adapter.py','tests/test_g13_readiness.py','tests/test_g13_stage_boundary.py','tests/test_longrun_offline_v2.py','tests/test_release_budget_process.py']
args=['-q','-p','no:cacheprovider','--basetemp',str(OUT/'tmp'),'--junitxml',str(OUT/'tests.xml'),*tests]
with (OUT/'pytest.log').open('w',encoding='utf-8') as log,contextlib.redirect_stdout(log),contextlib.redirect_stderr(log): code=int(pytest.main(args))
commands=[
 ('readme-workflow','scripts/run_g09_g10_workflow.py',['configs/g09-g10-example-input.json',str(OUT/'workflow')]),
 ('readme-comparison','scripts/run_g10_offline_comparison.py',['--output-dir',str(OUT/'comparison'),'--run-id','clean-release-'+options.source_commit[:7]]),
 ('readme-provider-dryrun','scripts/dispatch_provider_pilot.py',[]),
 ('goal-preflight-v2','scripts/prepare_long_run_offline.py',['--output-dir',str(OUT/'preflight-v2'),'--corpus-dir',str(OUT/'synthetic')]),
 ('g13-preflight-v1','scripts/run_g13_offline_preflight.py',['--output-dir',str(OUT/'preflight-v1')]),
 ('stage-boundary','scripts/verify_g13_stage_boundary.py',['--preflight',str(OUT/'preflight-v1/preflight.json'),'--output',str(OUT/'stage-boundary.json')]),
]
outcomes=[]
for name,script,argv in commands:
    sys.argv=[script,*argv]
    result={'name':name,'script':script,'arguments':argv,'exit_code':0}
    with (OUT/(name+'.log')).open('w',encoding='utf-8') as log,contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
        try:runpy.run_path(str(ROOT/script),run_name='__main__')
        except SystemExit as ex:result['exit_code']=ex.code or 0
        except Exception as ex:result.update(exit_code=1,error_class=type(ex).__name__);traceback.print_exc()
    outcomes.append(result)
schemas=json.loads((OUT/'preflight-v2/product-schemas.json').read_text()) if (OUT/'preflight-v2/product-schemas.json').exists() else {}
counts={k:sum(int(e.attrib.get(k,0)) for e in E.parse(OUT/'tests.xml').getroot().iter('testsuite')) for k in ['tests','failures','errors','skipped']}
after=snap()
report={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_commit_supplied':options.source_commit,'isolated_checkout':str(ROOT),'isolated_environment':sys.prefix,'installation':'environment creation and pip check recorded externally; versions below','dependency_versions':{d.metadata['Name']:d.version for d in importlib.metadata.distributions()},'pytest_exit_code':code,'tests':counts,'commands':outcomes,'schema_names':sorted(schemas),'source_files_before':before,'source_files_after':after,'source_files_unchanged':before==after,'snapshot_scope':'ordinary checkout files excluding .git, egg-info and caches; not a Git-index inventory','git_metadata_in_test_process':'NOT_INSPECTED; Git ref verified separately; no trust/ACL change','socket_gate_attempts':len(network),'forbidden_file_read_attempts':forbidden,'package_location':patent_to_pilot.__file__,'provider_calls':0,'api_cost_usd':0,'scope':'Python socket/DNS and file-open gate; no OS packet capture; dependency installation had PyPI network access','scientific_validation':False}
report['status']='PASS' if code==0 and all(x['exit_code']==0 for x in outcomes) and before==after and not network and not forbidden else 'FAIL'
(OUT/'verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k not in ('source_files_before','source_files_after','dependency_versions')},indent=2));print((OUT/'pytest.log').read_text()[-3500:])

raise SystemExit(0 if report["status"]=="PASS" else 1)
