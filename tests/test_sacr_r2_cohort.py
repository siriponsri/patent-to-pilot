import json

import pytest

from patent_to_pilot.research.mtm_runtime import InputBoundaryError
from patent_to_pilot.research.sacr_native_fidelity import digest
from patent_to_pilot.research.sacr_r2_cohort import run_cohort
from test_sacr_native_fidelity import inputs


def harness(tmp_path, risks=0, fail_at=None):
    raw,sample = inputs(); sample_raw = json.dumps(sample).encode()
    calls=[]
    def query(q,source,path):
        calls.append(q)
        path.mkdir()
        if len(calls) == fail_at: raise RuntimeError('authored interruption')
        result={'query_id':q,'status':'ESCALATE' if len(calls)<=risks else
            'AUTOMATIC_UNFLAGGED_NOT_FIDELITY_PASS','semantic_pass':False,'retry':False}
        (path/'result.json').write_text(json.dumps(result))
        return result
    return dict(query_bytes=raw,sample_bytes=sample_raw,query_sha256=digest(raw),
        sample_sha256=digest(sample_raw),destination=tmp_path/'cohort',
        run_query=query,check_admission=lambda i:None),calls


@pytest.mark.parametrize('risks', [0,20,21])
def test_exact_risk_boundary_and_fixed_denominator(tmp_path,risks):
    args,calls=harness(tmp_path,risks=risks)
    result=run_cohort(**args)
    assert result['original_sample_size']==100 and result['semantic_pass'] is False
    assert result['human_cards_issued']==0
    if risks==21:
        assert len(calls)==21 and result['status']=='STOP_FROZEN_REVIEW_CAP'
        assert result['never_started_queries']==79
    else:
        assert len(calls)==100 and result['status']=='AUTOMATIC_SCREEN_COMPLETE_HUMAN_REVIEW_REQUIRED'
    with pytest.raises(FileExistsError): run_cohort(**args)


def test_inflight_failure_preserves_original_denominator_and_no_replay(tmp_path):
    args,calls=harness(tmp_path,fail_at=3)
    with pytest.raises(RuntimeError): run_cohort(**args)
    result=json.loads((args['destination']/'cohort.json').read_bytes())
    assert result['completed_queries']==2 and result['active_query_index']==2
    assert result['never_started_queries']==97 and result['not_completed_queries']==98
    assert len(calls)==3
    with pytest.raises(FileExistsError): run_cohort(**args)


def test_budget_stop_before_next_query_does_not_invent_inflight_work(tmp_path):
    args,calls=harness(tmp_path)
    def admission(index):
        if index==2: raise TimeoutError('budget unavailable')
    args['check_admission']=admission
    with pytest.raises(TimeoutError): run_cohort(**args)
    result=json.loads((args['destination']/'cohort.json').read_bytes())
    assert result['active_query_index'] is None and result['never_started_queries']==98
    assert result['incomplete_attempt_cost']=='NO_QUERY_DISPATCHED' and len(calls)==2


def test_changed_sample_is_rejected_before_any_output(tmp_path):
    args,calls=harness(tmp_path)
    sample=json.loads(args['sample_bytes']); sample['entries'].reverse()
    args['sample_bytes']=json.dumps(sample).encode(); args['sample_sha256']=digest(args['sample_bytes'])
    with pytest.raises(InputBoundaryError): run_cohort(**args)
    assert not args['destination'].exists() and calls==[]
