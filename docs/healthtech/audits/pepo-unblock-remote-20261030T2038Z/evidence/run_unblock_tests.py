from pathlib import Path
import json
import os
import socket
import sys
import time


def main():
    workspace=Path(__file__).resolve().parent
    repair=Path(r'C:\Users\User\Desktop\myProject\_worktrees\patent-to-pilot-pepo-unblock-20261030')
    mode=sys.argv[1]
    source=Path(r'C:\Users\User\Desktop\myProject\patent-to-pilot') if mode=='baseline' else repair
    output=workspace/('unblock-'+mode)
    output.mkdir(exist_ok=True)
    sys.dont_write_bytecode=True
    os.environ['PYTHONDONTWRITEBYTECODE']='1'
    os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1'
    for key in list(os.environ):
        if key.endswith(('API_KEY','ACCESS_TOKEN','SECRET_KEY')):
            del os.environ[key]
    sys.path[:0]=[str(source/'src'),str(source),str(repair/'tests')]
    os.environ['PYTHONPATH']=os.pathsep.join([str(source/'src'),str(source),str(repair/'tests')])
    attempts=[]
    def deny(*args,**kwargs):
        attempts.append('network')
        raise RuntimeError('unblock verification is offline')
    socket.create_connection=deny
    socket.getaddrinfo=deny
    socket.socket.connect=deny
    socket.socket.connect_ex=deny
    def audit(event,args):
        if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
            path=Path(os.fsdecode(args[0])).resolve()
            if any(part in path.parts for part in ('.ssh','.aws')) or path.name.startswith('.env') and path.name!='.env.example' and not path.is_relative_to(output):
                raise RuntimeError('private configuration/credentials are outside offline test scope')
    sys.addaudithook(audit)
    os.chdir(repair)
    import pytest
    scope=['tests/test_healthtech_query_projection.py','tests/test_healthtech_vector_restart.py']
    if mode=='baseline':
        scope=['tests/test_healthtech_query_projection.py','tests/test_healthtech_vector_restart.py::test_resume_after_final_commit_before_checkpoint_cleanup']
    else:
        scope+=['tests/test_healthtech_boundary_matrix.py','tests/test_healthtech_vector_artifacts.py','tests/test_healthtech_vector_eval.py','tests/test_healthtech_runtime_export.py','tests/test_healthtech_repairs.py']
    start=time.monotonic()
    code=pytest.main(['-q','-rs','-p','no:cacheprovider','-o','pythonpath='+str(source/'src'),*scope,'--basetemp',str(output/'tmp'),'--junitxml',str(output/'tests.xml')])
    from patent_to_pilot.healthtech import engine
    from patent_to_pilot.evaluation.healthtech import vector_artifacts
    result={'mode':mode,'source':str(source),'scope':scope,'exit_code':int(code),'elapsed_seconds':time.monotonic()-start,'network_attempts':len(attempts),'provider_calls':0,'model_inference_calls':0,'engine_file':engine.__file__,'vector_artifacts_file':vector_artifacts.__file__}
    (output/'verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result))
    return code


if __name__=='__main__':
    raise SystemExit(main())
