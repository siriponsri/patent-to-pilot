from pathlib import Path
import os,socket,sys
root=Path(__file__).resolve().parent/'git-snapshot'
out=Path(__file__).resolve().parent/'checkout-subset'
out.mkdir(exist_ok=False)
for k in list(os.environ):
    if k.endswith(('API_KEY','ACCESS_TOKEN','SECRET_KEY')):del os.environ[k]
def deny(*a,**k):raise RuntimeError('offline audit network forbidden')
socket.socket.connect=deny;socket.create_connection=deny;socket.getaddrinfo=deny
os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1'
os.environ['PYTHONPATH']=str(root/'src')
sys.dont_write_bytecode=True
sys.path[:0]=[str(root/'src'),str(root)]
os.chdir(root)
import pytest
raise SystemExit(pytest.main(['-q','-p','no:cacheprovider','--basetemp',str(out/'tmp'),'--junitxml',str(out/'tests.xml'),
 'tests/test_healthtech_cross_cohort.py',
 'tests/test_healthtech_dapfam_bm25.py::test_manifest_code_provenance_binds_working_tree_source',
 'tests/test_healthtech_integration_contract.py::test_refresh_rebinds_backend_hashes_without_mutating_parent']))
