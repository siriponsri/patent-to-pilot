"""Run a fixed offline test cohort with sockets denied and fresh evidence only."""
from pathlib import Path
import argparse,contextlib,datetime,hashlib,json,os,socket,sys,time

ROOT=Path(__file__).resolve().parents[1]
SUITES={
    'g10':['tests/test_g09_g10_integration.py','tests/test_g10_offline_comparison.py','tests/test_g11_adaptation.py'],
    'readiness':['tests/test_g10_offline_comparison.py','tests/test_g13_readiness.py'],
}
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--suite',choices=SUITES,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args()
    out=args.output_dir.resolve()
    if out.exists():raise FileExistsError('fresh output directory required')
    out.mkdir(parents=True)
    os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1'
    os.environ['PYTHONDONTWRITEBYTECODE']='1';sys.dont_write_bytecode=True
    sys.path.insert(0,str(ROOT/'src'));os.chdir(ROOT)
    files=list((ROOT/'src').rglob('*.py'))+[ROOT/x for x in SUITES[args.suite]]
    def snap():return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    before=snap();network=[]
    def denied(*a,**kw):network.append('blocked socket/DNS');raise RuntimeError('network disabled in offline verification')
    socket.socket.connect=denied;socket.socket.connect_ex=denied;socket.socket.bind=denied
    socket.create_connection=denied;socket.getaddrinfo=denied
    import pytest
    started=time.monotonic()
    command=['-q','-p','no:cacheprovider','--basetemp',str(out/'temp'),'--junitxml',str(out/'tests.xml'),*SUITES[args.suite]]
    recorded_args=list(command)
    with (out/'pytest.log').open('w',encoding='utf-8') as log,contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
        code=int(pytest.main(command))
    after=snap()
    result={'status':'PASS' if code==0 and before==after and not network else 'FAIL','test_exit_code':code,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'elapsed_seconds':time.monotonic()-started,'pytest_args':recorded_args,'source_before':before,'source_after':after,'source_unchanged':before==after,'socket_gate_attempts':len(network),'network_scope':'Python socket/DNS gate, not system-wide packet capture','provider_calls':'NOT_RUN'}
    (out/'verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ['source_before','source_after']},indent=2))
    print((out/'pytest.log').read_text(encoding='utf-8')[-2200:])
    return 0 if result['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
