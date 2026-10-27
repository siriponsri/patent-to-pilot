from concurrent.futures import ThreadPoolExecutor
import copy
import hashlib
import json
import sqlite3

import pytest
from pydantic import ValidationError
from patent_to_pilot.evaluation.synthetic_corpus import generate, validate, write_corpus
from patent_to_pilot.product.contracts import JobStatus, ProjectBrief, ReviewDecision
from patent_to_pilot.providers.project_budget import ProjectBudget, BudgetedTransport, money
from patent_to_pilot.providers.openrouter import BudgetExceededError, MockHTTPResponse, MockHTTPTransport, OpenRouterAdapter, ProviderConfig, ProviderCapabilities, ProviderRequest, ResponseValidationError, ModelDriftError
from patent_to_pilot.providers.paired import body_hash


def reserve(budget, aid="a", phase="calibration", amount="0.5", **overrides):
    args = dict(attempt_id=aid,phase=phase,model="openai/gpt-4.1-mini",provider="openai",payload_sha256="a"*64,upper_bound_usd=amount,bound_verified=True,data_class="synthetic")
    args.update(overrides)
    return budget.reserve(**args)


def test_reproducible_bounded_generation_and_split_components(tmp_path):
    first, second = write_corpus(tmp_path/'a'), write_corpus(tmp_path/'b')
    assert first == second
    assert first['coverage'] == {'cases':48,'families':24,'template_components':4,'event_types':['contradiction','partner_delay','policy_revision','withdrawal'],'split_counts':{'development':24,'demo':24},'independent_real_cases':0}
    data = json.loads((tmp_path/'a/corpus.json').read_text())
    assert generate(42) != generate(43)
    for name, sha in first['files'].items():
        assert hashlib.sha256((tmp_path/'a'/name).read_bytes()).hexdigest() == sha
        if name.startswith('current/'):
            current = json.loads((tmp_path/'a'/name).read_text())
            assert 'event' not in current and 'split' not in current and 'template_id' not in current
    assert len(list((tmp_path/'a/documents').glob('*.md'))) == 48
    assert validate(data)['independent_real_cases'] == 0
    with pytest.raises(FileExistsError): write_corpus(tmp_path/'a')


@pytest.mark.parametrize('mutation', ['hash','capacity','heldout','label','duplicate','event','split','nested_oracle'])
def test_synthetic_negative_controls(mutation):
    c = generate()
    r = c['cases'][0]
    if mutation=='hash': r['source']['content'] += 'tampered'
    elif mutation=='capacity': r['organization']['owned_capacity_units_per_day'] += 1
    elif mutation=='heldout': c['held_out_cases']=['SYN-000-0']
    elif mutation=='label': r['independent_validation']=True
    elif mutation=='duplicate': c['cases'].append(copy.deepcopy(r))
    elif mutation=='event': r['event']['preserved_route_ids']=['prototype']
    elif mutation=='split': c['cases'][1]['split']='demo'
    elif mutation=='nested_oracle': r['source']['gold_answer']='oracle'
    with pytest.raises(ValueError): validate(c)


def test_contracts_reject_oracle_and_inconsistent_status():
    with pytest.raises(ValidationError): ProjectBrief(project_id='p',version=1,objective='x',audience='investor',data_class='synthetic',gold_answer='x')
    with pytest.raises(ValidationError): JobStatus(job_id='j',project_id='p',state='blocked')
    with pytest.raises(ValidationError): JobStatus(job_id='j',project_id='p',state='running',provider_calls=1)
    with pytest.raises(ValidationError): JobStatus(job_id='j',project_id='p',state='running',affected_routes=['r'],preserved_routes=['r'])
    assert ReviewDecision(decision_id='d',project_id='p',expected_version=1,scope='critical_assumption',decision='confirm',evidence_ids=['e'],reason='reviewed').expected_version==1


def test_budget_reserve_reopen_replay_and_idempotent_settle(tmp_path):
    path=tmp_path/'b.sqlite'; b=ProjectBudget(path)
    reserve(b); b.close(); b=ProjectBudget(path)
    with pytest.raises(BudgetExceededError): reserve(b,'next')
    b.settle('a','0.1'); b.settle('a','0.1')
    assert b.snapshot()['actual_nano_usd']==100_000_000
    with pytest.raises(BudgetExceededError): reserve(b,'a')
    with pytest.raises(ValueError): b.settle('a','0.2')
    b.close()


def test_shared_phase_and_total_caps_and_release(tmp_path):
    b=ProjectBudget(tmp_path/'b.sqlite')
    reserve(b, amount='1'); b.settle('a','1')
    with pytest.raises(BudgetExceededError): reserve(b,'b',amount='0.000000001')
    with pytest.raises(BudgetExceededError): reserve(b,'b',phase='subsequent',amount='4')
    reserve(b,'b',phase='subsequent',amount='4',subsequent_released=True); b.settle('b','4')
    assert b.snapshot()['actual_nano_usd']==5_000_000_000
    with pytest.raises(BudgetExceededError): reserve(b,'c',phase='subsequent',amount='0.01',subsequent_released=True)
    b.close()


def test_unknown_and_overrun_retain_charges_and_block(tmp_path):
    b=ProjectBudget(tmp_path/'b.sqlite'); reserve(b)
    b.settle('a',None)
    assert b.snapshot()['committed_nano_usd']==500_000_000
    with pytest.raises(BudgetExceededError): reserve(b,'b')
    with pytest.raises(BudgetExceededError): b.settle('a','1.2')
    assert b.snapshot()['actual_nano_usd']==1_200_000_000
    assert b.snapshot()['breach'] is True
    with pytest.raises(BudgetExceededError): reserve(b,'b')
    b.close()


@pytest.mark.parametrize('changes',[{'bound_verified':False},{'model':'unapproved'},{'provider':'azure'},{'data_class':'private'}])
def test_budget_failclosed_permissions(tmp_path,changes):
    b=ProjectBudget(tmp_path/'b.sqlite')
    with pytest.raises((ValueError,BudgetExceededError)): reserve(b,**changes)
    assert b.snapshot()['attempts']==0
    b.close()


def test_two_connections_cannot_race_reservations(tmp_path):
    path=tmp_path/'b.sqlite'; ProjectBudget(path).close()
    def run(i):
        b=ProjectBudget(path)
        try:
            reserve(b,str(i),amount='0.75'); return 'reserved'
        except BudgetExceededError: return 'blocked'
        finally: b.close()
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(run,range(2)))==['blocked','reserved']
    b=ProjectBudget(path); assert b.snapshot()['attempts']==1; b.close()


def adapter_fixture(tmp_path,content='{"answer":"ok"}',reported_model=None,cost='0.1'):
    config=ProviderConfig(model='openai/gpt-4.1-mini',routing_only=['openai'],max_spend_usd=1)
    request=ProviderRequest(prompt='SYNTHETIC echo',input_tokens_estimate=10,max_output_tokens=20,cost_upper_bound_usd=.5,response_schema={'type':'object','properties':{'answer':{'const':'ok'}},'required':['answer'],'additionalProperties':False})
    payload={'model':reported_model or config.model,'provider':'OpenAI','choices':[{'message':{'content':content}}],'usage':{'prompt_tokens':10,'completion_tokens':5,'cost':cost}}
    mock=MockHTTPTransport(MockHTTPResponse(200,payload)); budget=ProjectBudget(tmp_path/'b.sqlite')
    binding=dict(attempt_id='attempt1',phase='calibration',payload_sha256=body_hash(config,request),upper_bound_usd=.5,bound_verified=True,data_class='synthetic')
    wrapper=BudgetedTransport(mock,budget,binding)
    caps=ProviderCapabilities(provider='openrouter',model=config.model,structured_outputs=True)
    return OpenRouterAdapter(config,wrapper,caps),request,budget,mock


@pytest.mark.parametrize('failure',['schema','model','none'])
def test_adapter_integration_bills_before_validation(tmp_path,failure):
    a,r,b,m=adapter_fixture(tmp_path,content='{}' if failure=='schema' else '{"answer":"ok"}',reported_model='wrong' if failure=='model' else None,cost=.1)
    if failure=='schema':
        with pytest.raises(ResponseValidationError): a.complete(r)
    elif failure=='model':
        with pytest.raises(ModelDriftError): a.complete(r)
    else: assert a.complete(r).response_schema_valid is True
    assert len(m.calls)==1 and b.snapshot()['actual_nano_usd']==100_000_000
    with pytest.raises(BudgetExceededError): a.complete(r)
    assert len(m.calls)==1
    b.close()


def test_invalid_accounting_and_failure_redaction(tmp_path):
    a,r,b,m=adapter_fixture(tmp_path,cost='not money')
    with pytest.raises(RuntimeError,match='accounting invalid'): a.complete(r)
    assert b.snapshot()['unknown_or_pending']==['attempt1']; b.close()


def test_missing_usage_cost_stops_and_transport_error_is_sanitized(tmp_path):
    import traceback
    a,r,b,m=adapter_fixture(tmp_path,cost=None)
    with pytest.raises(BudgetExceededError,match='unknown_pending'): a.complete(r)
    assert b.snapshot()['unknown_or_pending']==['attempt1']; b.close()
    other=tmp_path/'other'; other.mkdir()
    a,r,b,m=adapter_fixture(other)
    m.response=RuntimeError('FAKE_SECRET_MUST_NOT_LEAK')
    try:
        a.complete(r)
    except RuntimeError:
        assert 'FAKE_SECRET_MUST_NOT_LEAK' not in traceback.format_exc()
    else: pytest.fail('transport failure must propagate')
    assert b.snapshot()['unknown_or_pending']==['attempt1']; b.close()


def test_money_rejects_nonfinite_and_rounds_reservation_up():
    assert money('0.0000000001')==1
    for value in ['nan','inf',-1,True]:
        with pytest.raises(ValueError): money(value)
