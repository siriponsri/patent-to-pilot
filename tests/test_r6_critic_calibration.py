import json
from collections import Counter
import pytest
from patent_to_pilot.research.r6_critic_calibration import fixtures,assess,request
from patent_to_pilot.research.sacr_fidelity_screen import DIMENSIONS
from patent_to_pilot.research.mtm_runtime import InputBoundaryError


def reports(mode='correct'):
    rows=[]
    for f in fixtures():
        p=request(f);gold=f['expected'];flags=gold['required_flags']
        status='uncertain' if gold['kind']=='uncertain' else 'unsupported'
        if mode=='all_supported':flags=[]
        elif mode=='all_unsupported' or (mode=='blanket_on_nonidentical' and f['source']!=f['artifacts']['candidate']):
            flags=list(DIMENSIONS);status='unsupported'
        elif mode=='blanket_on_negative' and gold['kind']=='negative':flags=list(DIMENSIONS)
        dims={k:status if k in flags else 'supported' for k in DIMENSIONS}
        source_units=[u['id'] for u in p['payload']['source_units'] if any(u['start']<b and u['end']>a for a,b in gold['target_source_spans'])]
        if not source_units:source_units=[p['payload']['source_units'][0]['id']]
        candidate_units=[u['id'] for u in p['payload']['artifact_units']['candidate'] if any(u['start']<b and u['end']>a for a,b in gold['target_candidate_spans'])]
        findings=[{'dimension':k,'artifact':'candidate','source_units':source_units,
                   'candidate_units':candidate_units,'reason':'Authored software test response, not a model result.'} for k in flags]
        v={'binding_sha256':p['binding_sha256'],'dimensions':dims,'findings':findings}
        rows.append({'case_id':f['case_id'],'critic_text':json.dumps(v)})
    return rows


def test_distinct_varied_suite_and_explicit_uncertainty():
    f=fixtures()
    assert len(f)==24 and Counter(r['expected']['kind'] for r in f)=={'positive':10,'negative':10,'uncertain':4}
    assert len({(r['source'],r['artifacts']['candidate']) for r in f})==24
    assert all(r['source']!=r['artifacts']['candidate'] for r in f if r['expected']['kind']=='positive')
    assert {k for r in f for k in r['expected']['required_flags']}==set(DIMENSIONS)
    assert sum(len(request(r)['payload']['source_units'])>1 and len(r['artifacts'])>1 for r in f)>=2
    assert assess(reports())['status']=='AUTHORED_CALIBRATION_QUALIFIED'
    assert not assess(reports())['native_fidelity_proven']


@pytest.mark.parametrize('mode',['all_supported','all_unsupported','blanket_on_nonidentical','blanket_on_negative'])
def test_observed_blanket_and_equality_shortcuts_fail(mode):
    assert assess(reports(mode))['status']=='CALIBRATION_FAILED'


@pytest.mark.parametrize('mode',['missing','duplicate','self_reported'])
def test_missing_substituted_and_self_attested_rows_rejected(mode):
    rows=reports()
    if mode=='missing':rows.pop()
    elif mode=='duplicate':rows[0]=rows[1]
    else:rows[0]={'case_id':rows[0]['case_id'],'evaluator_contract':'VALID','dimensions':{}}
    with pytest.raises(InputBoundaryError):assess(rows)


def test_irrelevant_but_valid_source_ids_cannot_qualify():
    rows=reports();fixed={f['case_id']:f for f in fixtures()}
    changed=False
    for row in rows:
        f=fixed[row['case_id']];p=request(f)
        if f['expected']['kind']=='negative' and len(p['payload']['source_units'])>1:
            v=json.loads(row['critic_text'])
            for finding in v['findings']:finding['source_units']=['s:000']
            row['critic_text']=json.dumps(v);changed=True
    assert changed and assess(rows)['irrelevant_evidence_cases']>0


def test_branch_criteria_are_distinct_and_gold_not_in_prompt():
    branches={}
    for case in fixtures():
        p=request(case);payload=json.loads(p['messages'][1]['content'])
        assert 'expected' not in payload and 'required_flags' not in payload and 'target_source_spans' not in payload
        branches[case['branch']]=payload['criteria']
        assert not p['dispatch_authorized']
    assert len({json.dumps(c,sort_keys=True) for c in branches.values()})==3


@pytest.mark.parametrize('mode',['missing','irrelevant'])
def test_candidate_evidence_required_for_contradictions(mode):
    rows=reports();fixed={f['case_id']:f for f in fixtures()};changed=False
    for row in rows:
        f=fixed[row['case_id']];p=request(f)
        if f['expected']['target_candidate_spans'] and (mode=='missing' or len(p['payload']['artifact_units']['candidate'])>1):
            v=json.loads(row['critic_text'])
            for finding in v['findings']:
                finding['candidate_units']=[] if mode=='missing' else [p['payload']['artifact_units']['candidate'][0]['id']]
            row['critic_text']=json.dumps(v);changed=True
    assert changed and assess(rows)['irrelevant_evidence_cases']>0
