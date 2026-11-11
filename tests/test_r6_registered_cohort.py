import json
import hashlib

import pytest

from patent_to_pilot.research.r6_attempt_registry import initialize,AttemptRegistry
from patent_to_pilot.research.r6_cohort import run_registered_native_section,digest
from patent_to_pilot.research.mtm_runtime import InputBoundaryError


def setup(tmp_path,monkeypatch):
    from patent_to_pilot.research import sacr_r6_bundle_runner
    path=tmp_path/'registry.sqlite';initialize(path,'e'*64)
    rows=[{'query_id':f'q{i:03}','source':f'Authored source {i}'} for i in range(100)]
    calls=[]
    def authored(**args):
        calls.append(args['query_id'])
        out=args['destination'];out.mkdir()
        record={'query_id':args['query_id'],'source_sha256':hashlib.sha256(args['source'].encode()).hexdigest(),
                'execution':args['execution'],'retry':False}
        result={'query_id':args['query_id'],'status':'AUTOMATIC_UNFLAGGED_NOT_FIDELITY_PASS',
                'events':[],'retry':False}
        (out/'input.json').write_text(json.dumps(record))
        (out/'result.json').write_text(json.dumps(result))
        return result
    monkeypatch.setattr(sacr_r6_bundle_runner,'run_bundle',authored)
    return dict(registry=AttemptRegistry(path,'e'*64),namespace='R6',execution={'run_id':'fixed'},
        bundle_arguments={},rows=rows,manifest_sha256=digest(rows),configuration_sha256='a'*64,
        check_admission=lambda index:None),calls


def test_native_bridge_reuses_original_files_and_never_regenerates(tmp_path,monkeypatch):
    args,calls=setup(tmp_path,monkeypatch)
    bridge=run_registered_native_section(destination=tmp_path/'bridge',section='native5',**args)
    remaining=run_registered_native_section(destination=tmp_path/'remaining',section='native95',
        bridge=bridge,bridge_sha256=digest(bridge),**args)
    assert calls==[row['query_id'] for row in args['rows']]
    assert remaining['reused_units']==5 and remaining['status']=='SECTION_COMPLETE'
    with pytest.raises(InputBoundaryError,match='replay forbidden'):
        run_registered_native_section(destination=tmp_path/'other',section='native5',**args)
    assert len(calls)==100


@pytest.mark.parametrize('fault',['bytes','deleted','namespace','execution','source'])
def test_changed_bridge_artifacts_or_identity_stop_before_new_calls(tmp_path,monkeypatch,fault):
    args,calls=setup(tmp_path,monkeypatch)
    bridge=run_registered_native_section(destination=tmp_path/'bridge',section='native5',**args)
    result=tmp_path/'bridge'/'unit-000'/'result.json'
    if fault=='bytes':result.write_text(result.read_text()+'\n')
    if fault=='deleted':result.unlink()
    if fault=='namespace':args['namespace']='unapproved'
    if fault=='execution':args['execution']={'run_id':'changed'}
    if fault=='source':
        args['rows'][0]['source']='changed';args['manifest_sha256']=digest(args['rows'])
    with pytest.raises((InputBoundaryError,FileNotFoundError)):
        run_registered_native_section(destination=tmp_path/'remaining',section='native95',
            bridge=bridge,bridge_sha256=digest(bridge),**args)
    assert len(calls)==5 and not (tmp_path/'remaining').exists()
