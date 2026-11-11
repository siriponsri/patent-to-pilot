import hashlib
import json

import pytest

from test_r6_admission import fixture
from patent_to_pilot.research.r6_dispatch_files import load_dispatch
from patent_to_pilot.research.mtm_runtime import InputBoundaryError


def setup(tmp_path):
    d,l,s,g=fixture();items={'declaration':d,'ledger':l,'scope':s}
    items.update({'gate:'+name:value for name,value in g.items()})
    files={}
    for role,value in items.items():
        name=role.replace(':','-')+'.json'
        raw=json.dumps(value).encode();(tmp_path/name).write_bytes(raw)
        files[role]={'path':name,'sha256':hashlib.sha256(raw).hexdigest()}
    return {'version':'r6-dispatch-files-v1','files':files}


def load(tmp_path,manifest):
    raw=json.dumps(manifest).encode();(tmp_path/'manifest.json').write_bytes(raw)
    return load_dispatch(tmp_path,manifest_path='manifest.json',manifest_sha256=hashlib.sha256(raw).hexdigest())


def test_complete_file_bound_admission_still_requires_live_checks(tmp_path):
    value=load(tmp_path,setup(tmp_path))
    assert value['receipt']['status']=='PASS_STATIC_DISPATCH_CONTRACT'
    assert value['receipt']['live_admission']=='REQUIRED'


@pytest.mark.parametrize('fault',['changed','missing','traversal','absolute','duplicate','alias','gate','unbounded'])
def test_changed_incomplete_or_escaping_evidence_never_admitted(tmp_path,fault):
    manifest=setup(tmp_path)
    if fault=='changed':(tmp_path/'ledger.json').write_text('{}')
    if fault=='missing':(tmp_path/'ledger.json').unlink()
    if fault=='traversal':manifest['files']['ledger']['path']='../ledger.json'
    if fault=='absolute':manifest['files']['ledger']['path']=str(tmp_path/'ledger.json')
    if fault=='duplicate':manifest['files']['scope']=dict(manifest['files']['ledger'])
    if fault=='alias':manifest['files']['scope']=dict(manifest['files']['ledger'],path='./ledger.json')
    if fault=='gate':del manifest['files']['gate:grammar']
    if fault=='unbounded':(tmp_path/'ledger.json').write_bytes(b' '* (8*1024**2+1))
    with pytest.raises((InputBoundaryError,FileNotFoundError)):
        load(tmp_path,manifest)
