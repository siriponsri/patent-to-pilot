"""Run repository regressions with Python network/real-env-file guards."""
from pathlib import Path
import argparse
import contextlib
import datetime
import hashlib
import json
import os
import socket
import sys
import xml.etree.ElementTree as ET


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path,help='fresh directory for logs, JUnit and receipt')
    parser.add_argument('--suite',choices=['public','all'],default='public',
        help='public: explicit published regression modules; all: discover tests in the local tests directory')
    args=parser.parse_args()
    repo=Path(__file__).resolve().parents[2]
    out=args.output.resolve()
    if out.exists():parser.error('output already exists; choose a fresh directory')
    out.mkdir(parents=True,exist_ok=False)
    os.chdir(repo)
    os.environ['PYTHONPATH']=str(repo/'src')
    os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1'
    os.environ['PYTHONDONTWRITEBYTECODE']='1'
    sys.dont_write_bytecode=True
    sys.path.insert(0,str(repo/'src'))
    code_files=sorted(p for folder in ['src','scripts','tests'] for p in (repo/folder).rglob('*.py'))
    before={p.relative_to(repo).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in code_files}
    for p in code_files:compile(p.read_text(encoding='utf-8-sig'),str(p),'exec')
    network=[];forbidden=[]
    def denied(*a,**kw):
        network.append('socket_or_dns_attempt')
        raise RuntimeError('network forbidden during offline verification')
    socket.socket.connect=denied;socket.socket.connect_ex=denied;socket.socket.bind=denied
    socket.create_connection=denied;socket.getaddrinfo=denied
    def audit(event,values):
        if event=='open' and isinstance(values[0],(str,bytes,os.PathLike)):
            if Path(os.fsdecode(values[0])).resolve()==repo/'.env':
                forbidden.append('real_repository_env_file')
                raise RuntimeError('real credential-file access forbidden')
    sys.addaudithook(audit)
    import pytest
    public_tests=['test_core','test_g04_profiles','test_g08_pipeline','test_g09_g10_integration',
        'test_g10_offline_comparison','test_g11_adaptation','test_g13_readiness',
        'test_g13_stage_boundary','test_longrun_offline_v2','test_provider_adapter',
        'test_release_budget_process','test_healthtech','test_provider_env_file',
        'test_healthtech_prelive','test_provider_identity','test_provider_paired','test_provider_pilot','test_provider_recovery']
    targets=['tests'] if args.suite=='all' else [f'tests/{name}.py' for name in public_tests]
    argv=['-q','-p','no:cacheprovider','--basetemp',str(out/'tmp'),'--junitxml',str(out/'tests.xml'),*targets]
    with (out/'pytest.log').open('w',encoding='utf-8') as log,contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
        code=int(pytest.main(argv))
    counts={k:sum(int(e.attrib.get(k,0)) for e in ET.parse(out/'tests.xml').getroot().iter('testsuite')) for k in ['tests','failures','errors','skipped']}
    after={p.relative_to(repo).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in code_files}
    result={'status':'PASS' if code==0 and before==after and not network and not forbidden else 'FAIL',
        'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'test_exit_code':code,'pytest':counts,
        'command':f'python -B scripts/healthtech/verify_offline.py <fresh-output> --suite {args.suite}',
        'suite':args.suite,'test_files':targets,
        'pythonpath_for_child_processes':'<repository>/src','compiled_python_files':len(code_files),
        'source_unchanged':before==after,'source_hashes':after,'network_attempts':len(network),
        'forbidden_credential_read_attempts':len(forbidden),'provider_calls':0,'paid_cost_usd':0,
        'scope':'Python socket/DNS and actual repository .env-file guards in test process; not OS-level packet capture. Child budget tests also deny sockets. Synthetic fixture checks are not scientific validation.'}
    (out/'verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='source_hashes'},indent=2))
    if result['status']!='PASS':print((out/'pytest.log').read_text(encoding='utf-8')[-5000:])
    return 0 if result['status']=='PASS' else 1


if __name__=='__main__':raise SystemExit(main())
