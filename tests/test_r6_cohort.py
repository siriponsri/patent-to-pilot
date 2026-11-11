import json
import pytest
from patent_to_pilot.research.r6_cohort import run_native_section,digest
from patent_to_pilot.research.mtm_runtime import InputBoundaryError
from patent_to_pilot.research.sacr_outcomes import METRICS


def setup(tmp_path,risks=False):
    rows=[{'query_id':f'q{i:03}','source':f'Authored source {i}.'} for i in range(100)];seen=[]
    def run(index,row,path):
        seen.append(index);path.mkdir()
        result={'query_id':row['query_id'],'status':'UNASSESSABLE' if risks else 'AUTOMATIC_UNFLAGGED_NOT_FIDELITY_PASS',
            'events':[{'event_id':f'authored-{index}','query_id':row['query_id'],'stage':'profile','status':'COMPLETED',
                'metrics':{k:0 for k in METRICS}}]}
        (path/'result.json').write_text(json.dumps(result));return result
    return {'rows':rows,'manifest_sha256':digest(rows),'configuration_sha256':'a'*64,
        'run_bundle':run,'check_admission':lambda index:None},seen


def test_bridge_then95_reuses_exact_firstfive_without_calls_or_costs(tmp_path):
    args,seen=setup(tmp_path)
    bridge=run_native_section(destination=tmp_path/'bridge',section='native5',**args)
    assert seen==list(range(5))
    result=run_native_section(destination=tmp_path/'remaining',section='native95',bridge=bridge,bridge_sha256=digest(bridge),**args)
    assert seen==list(range(100)) and result['reused_units']==5 and len(result['results'])==100
    assert result['status']=='SECTION_COMPLETE' and not result['semantic_pass']
    with pytest.raises(FileExistsError):run_native_section(destination=tmp_path/'bridge',section='native5',**args)


def test_risk21_stops_fixed_cohort_without_substitutions(tmp_path):
    args,seen=setup(tmp_path,risks=True)
    bridge=run_native_section(destination=tmp_path/'bridge',section='native5',**args)
    r=run_native_section(destination=tmp_path/'remaining',section='native95',bridge=bridge,bridge_sha256=digest(bridge),**args)
    assert seen==list(range(21)) and r['risk_units']==21 and r['status']=='STOPPED_RISK_CAP'
    assert r['fixed_denominator']==100


@pytest.mark.parametrize('fault',['manifest','bridge','source','duplicate'])
def test_changed_cohort_or_missing_bridge_fails_before_invocation(tmp_path,fault):
    args,seen=setup(tmp_path)
    if fault=='manifest':args['manifest_sha256']='0'*64
    if fault=='source':args['rows'][0]['source']='changed'
    if fault=='duplicate':
        args['rows'][1]=dict(args['rows'][0]);args['manifest_sha256']=digest(args['rows'])
    with pytest.raises(InputBoundaryError):run_native_section(destination=tmp_path/'out',section='native95' if fault=='bridge' else 'native5',**args)
    assert not seen and not (tmp_path/'out').exists()


def test_unknown_bundle_stops_no_replay(tmp_path):
    args,seen=setup(tmp_path);original=args['run_bundle']
    def broken(index,row,path):
        if index==2:raise RuntimeError('unknown backend')
        return original(index,row,path)
    args['run_bundle']=broken
    with pytest.raises(RuntimeError):run_native_section(destination=tmp_path/'out',section='native5',**args)
    failure=json.loads((tmp_path/'out'/'failure.json').read_text())
    assert failure['active_index']==2 and seen==[0,1]


@pytest.mark.parametrize('fault',['risk','query_id','event_duplicate','mutated_row'])
def test_reviewed_identity_and_accounting_boundaries(tmp_path,fault):
    args,seen=setup(tmp_path)
    bridge=run_native_section(destination=tmp_path/'bridge',section='native5',**args)
    if fault=='risk':bridge['results'][0]['risk']=True;bridge['risk_units']=1
    if fault=='query_id':
        item=bridge['results'][0];item['result']['query_id']='wrong';item['result_sha256']=digest(item['result'])
    if fault in ('event_duplicate','mutated_row'):
        original=args['run_bundle']
        def changed(index,row,path):
            if fault=='mutated_row':row['source']='changed'
            r=original(index,row,path)
            if fault=='event_duplicate':
                r['events'][0]['event_id']='authored-0';(path/'result.json').write_text(json.dumps(r))
            return r
        args['run_bundle']=changed
    with pytest.raises(InputBoundaryError):run_native_section(destination=tmp_path/'remaining',section='native95',
        bridge=bridge,bridge_sha256=digest(bridge),**args)
