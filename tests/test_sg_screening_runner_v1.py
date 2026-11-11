import hashlib,json
import pytest
from patent_to_pilot.research.sg_screening_runner_v1 import run_screening,review_selection
from patent_to_pilot.research.sacr_generation import GenerationLimits
from patent_to_pilot.research.sacr_outcomes import METRICS
from patent_to_pilot.research.mtm_runtime import InputBoundaryError


def test_review_selection_fixed_strata_no_extra_cards_or_acceptance():
    rows=[{'index':i,'unit_type':'source' if i<100 else 'alias','stable_id':str(i),'status':'RISK' if i<20 else 'SCREENING_PASS'} for i in range(200)]
    a=review_selection(rows,'a'*64);b=review_selection(list(reversed(rows)),'a'*64)
    assert a['sentinel_indices']==b['sentinel_indices'] and len(a['sentinel_indices'])==10
    assert sum(i<100 for i in a['sentinel_indices'])==5
    assert a['card_count']==30 and a['cards_issued']==0 and not a['semantic_pass']
    rows[20]['status']='RISK';assert review_selection(rows,'a'*64)['status']=='STOP_REVIEW_CAP_EXCEEDED'


@pytest.mark.parametrize('fault',[None,'status','limits'])
def test_early_stop_at_21_completed_unusable_units_no_regeneration(tmp_path,fault):
    unit_list=[{'query_id':str(i),'source':'source','artifacts':{'record':'candidate'},'criteria':{},'scope':{},
                'unit_type':'source' if i<100 else 'alias','stable_id':str(i)} for i in range(200)]
    calls=[]
    def invoke(stage,dest,messages,schema):
        calls.append(stage);dest.mkdir()
        reservation={'messages_sha256':hashlib.sha256(json.dumps(messages,ensure_ascii=False,sort_keys=True).encode()).hexdigest(),
                     'status':'RESERVED','limits':GenerationLimits().__dict__,'retry':False}
        if fault=='status':reservation['status']='OTHER'
        if fault=='limits':reservation['limits']['output_tokens']=8192
        (dest/'reservation.json').write_text(json.dumps(reservation))
        record={'status':'INPUT_LIMIT','model_calls':0,'input_tokens':9000,'output_tokens':0,'text':None,'retry':False}
        (dest/'generation.json').write_text(json.dumps(record))
        return {**{k:0 for k in METRICS},'input_tokens':9000}
    if fault:
        with pytest.raises(InputBoundaryError,match='request binding mismatch'):
            run_screening(unit_list,tmp_path/'run',invoke=invoke,check_admission=lambda _:None,config_sha256='a'*64)
        assert len(calls)==1
        return
    result=run_screening(unit_list,tmp_path/'run',invoke=invoke,check_admission=lambda _:None,config_sha256='a'*64)
    assert len(calls)==21 and len(set(calls))==21
    assert result['risk_units']==21 and result['review_selection']['card_indices']==[]
    assert result['cards_issued']==0 and result['accepted_edges']==0
    with pytest.raises(FileExistsError):run_screening(unit_list,tmp_path/'run',invoke=invoke,check_admission=lambda _:None,config_sha256='a'*64)
