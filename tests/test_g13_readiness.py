import copy
import json
from pathlib import Path

import pytest

from patent_to_pilot.evaluation.pilot_readiness import (
    CASE_IDS, ROOT, build_preflight, calibrate, current_stage, split_violations, validate_output_contract,
)


def plan():
    return json.loads((ROOT/'configs/g13-offline-plan-v1.json').read_text(encoding='utf-8'))


def test_exposed_cases_cannot_be_relabelled_held_out():
    rows=plan()['split_rows']
    rows[0]['split']='final_test'
    assert any('exposed case' in f for f in split_violations(rows))


@pytest.mark.parametrize('field',['case_id','family_id','source_publication','template_cluster','component_id'])
def test_group_identity_overlap_is_rejected(field):
    rows=[{'case_id':'A','family_id':'FA','source_publication':'PA','template_cluster':'TA','component_id':'CA','split':'development'},
          {'case_id':'B','family_id':'FB','source_publication':'PB','template_cluster':'TB','component_id':'CB','split':'final_test'}]
    rows[1][field]=rows[0][field]
    assert any(f.startswith(field+' crosses splits') for f in split_violations(rows))


def test_cross_org_claim_requires_org_disjointness_only_when_claimed():
    rows=[{'case_id':'A','family_id':'FA','split':'development','organization_id':'ORG'},
          {'case_id':'B','family_id':'FB','split':'final_test','organization_id':'ORG'}]
    assert not split_violations(rows)
    assert any('organization_id' in f for f in split_violations(rows,cross_org_claim=True))


def test_unknown_family_cannot_support_disjoint_final_claim():
    assert split_violations([{'case_id':'FUTURE','split':'final_test','family_id':None}])


def test_current_stage_reads_only_current_packet_and_declared_profile(monkeypatch):
    allowed={
        (ROOT/'methodology/evaluation/cases/PTP-0001/public-input/S0.json').resolve(),
        (ROOT/'methodology/organizations/fictional-profile-a/v1/profile.json').resolve(),
    }
    original=Path.read_text
    reads=[]
    def guarded(path,*args,**kwargs):
        path=path.resolve(); reads.append(path)
        assert path in allowed, f'unexpected file read: {path}'
        return original(path,*args,**kwargs)
    monkeypatch.setattr(Path,'read_text',guarded)
    payload,_=current_stage('PTP-0001','S0')
    assert set(reads)==allowed
    assert set(payload)=={'packet','profile'}
    assert payload['packet']['state_id']=='S0'


def test_nested_oracle_and_future_keys_are_rejected():
    from patent_to_pilot.evaluation.comparison import validate_public_packet,validate_public_profile
    payload,_=current_stage('PTP-0001','S0')
    for key in ['expected_doc_ids','gold_answer','future_events','oracle_output']:
        packet=copy.deepcopy(payload['packet'])
        packet['unexpected_container']=[{'nested':{key:'hidden'}}]
        with pytest.raises(ValueError,match='evaluator-only'):validate_public_packet(packet)
        profile=copy.deepcopy(payload['profile']);profile['unexpected_container']=[{key:'hidden'}]
        with pytest.raises(ValueError,match='evaluator-only'):validate_public_profile(profile)


def test_calibration_has_supported_positives_and_rejects_actual_wrong_outputs():
    controls=calibrate()
    assert all(c['passed'] for c in controls)
    assert len([c for c in controls if c['expected'] is True])==3
    assert len([c for c in controls if c['expected'] is False])==7
    assert all(c['observed'] is False for c in controls if not c['expected'])


def test_schema_cannot_carry_future_answers_into_staged_inputs(tmp_path,monkeypatch):
    for key in ['oracle','future_events','expected_doc_ids']:
        with pytest.raises(ValueError,match='evaluator-only schema'):
            validate_output_contract({'nested':[{'extra':{key:'hidden'}}]})
    original=Path.read_text
    def injected(path,*a,**kw):
        text=original(path,*a,**kw)
        if path.name=='output-schema.json':
            value=json.loads(text);value['nested']={'gold_answer':'injected'}
            return json.dumps(value)
        return text
    p=plan()
    monkeypatch.setattr(Path,'read_text',injected)
    with pytest.raises(ValueError,match='evaluator-only schema'):
        build_preflight(p,tmp_path/'leak')
    assert not (tmp_path/'leak').exists()


def test_preflight_runs_offline_but_never_claims_scientific_readiness(tmp_path):
    result=build_preflight(plan(),tmp_path/'new-run')
    assert result['status']=='PASS'
    assert result['scientific_live_ready'] is False
    assert result['public_case_count']==3 and result['public_state_count']==15
    assert result['held_out_case_count']==0
    assert result['provider_calls']==0 and result['api_cost_usd']==0
    assert result['mock_call_records']==9
    for path in (tmp_path/'new-run/curator-staged-current-inputs').glob('*/*'):
        assert {p.name for p in path.iterdir()}=={'runtime-input.json','output-contract.json'}
        payload=json.loads((path/'runtime-input.json').read_text())
        assert set(payload)=={'packet','profile'}
    assert len(result['scientific_blockers'])>=1


def test_preflight_never_overwrites_retained_results(tmp_path):
    out=tmp_path/'retained';out.mkdir();(out/'marker').write_text('preserve')
    with pytest.raises(FileExistsError):build_preflight(plan(),out)
    assert (out/'marker').read_text()=='preserve'


def test_live_or_false_split_config_is_rejected_before_writes(tmp_path):
    p=plan();p['live_enabled']=True
    with pytest.raises(ValueError,match='offline-only'):build_preflight(p,tmp_path/'live')
    assert not (tmp_path/'live').exists()
    p=plan();p['split_rows'][0]['already_exposed']=False
    with pytest.raises(ValueError,match='exposed development'):build_preflight(p,tmp_path/'fake')
    assert not (tmp_path/'fake').exists()


def test_plan_cannot_invent_family_provenance_or_a_heldout_panel(tmp_path):
    p=plan();p['split_rows'][0]['family_id']='INVENTED'
    with pytest.raises(ValueError,match='split provenance'):
        build_preflight(p,tmp_path/'invented')
    p=plan();p['final_test']=['PTP-0001']
    with pytest.raises(ValueError,match='no held-out panel'):
        build_preflight(p,tmp_path/'heldout')
    assert not (tmp_path/'invented').exists()
    assert not (tmp_path/'heldout').exists()
