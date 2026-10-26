import copy, json, sqlite3
from pathlib import Path
import pytest
from patent_to_pilot.providers import MockHTTPResponse
from patent_to_pilot.providers.pilot import PilotError, dispatch, exclusive_run, plan_hash, request_for, validate_approval, validate_plan
PLAN = Path(__file__).parents[1] / 'configs/provider-pilot-plan.json'

@pytest.fixture
def plan():
    return json.loads(PLAN.read_text(encoding='utf-8'))

class Transport:
    is_mock = True

    def __init__(self, job, fn, calls):
        self.job = job
        self.fn = fn
        self.calls = calls

    def send(self, **kwargs):
        self.calls.append(self.job['id'])
        return self.fn(self.job, len(self.calls))

def reply(job, text=None, cost=0.0001):
    return MockHTTPResponse(200, {'model': job['model'], 'provider': {'google/gemini-2.5-flash-lite': 'Google AI Studio', 'openai/gpt-4.1-mini': 'OpenAI'}[job['model']], 'choices': [{'message': {'content': text if text is not None else json.dumps(dict(ack='ready', case_id=job['id']))}}], 'usage': dict(prompt_tokens=100, completion_tokens=12, total_tokens=112, cost=cost)})

def factory(calls, fn=reply):
    return lambda job: Transport(job, lambda j, n: fn(j), calls)

def test_durable_reservation_precedes_send_and_resume_skips_completed(plan, tmp_path):
    state = tmp_path / 'run.db'
    calls = []

    def observe(job):
        with sqlite3.connect(state) as db:
            a, finished = db.execute('SELECT reservation,finished FROM attempts ORDER BY seq DESC LIMIT 1').fetchone()
        assert json.loads(a)['reservation_status'] == 'pending' and (not finished)
        return reply(job)
    r = dispatch(plan, state, 'smoke', factory(calls, observe), max_new_attempts=1)
    assert r['status'] == 'PAUSED' and r['attempts'] == 1
    r = dispatch(plan, state, 'smoke', factory(calls, observe))
    assert r['status'] == 'PHASE_COMPLETE' and len(calls) == 2
    r = dispatch(plan, state, 'smoke', factory(calls))
    assert r['actual_debit_usd'] == pytest.approx(0.0002) and len(calls) == 2

def test_actual_schema_failures_retry_with_charges_and_total_ten_survive_resume(plan, tmp_path):
    state = tmp_path / 'run.db'
    calls = []
    dispatch(plan, state, 'smoke', factory(calls))
    seen = {}

    def sometimes(job):
        seen[job['id']] = seen.get(job['id'], 0) + 1
        return reply(job, '[]' if seen[job['id']] == 1 else None)
    r = dispatch(plan, state, 'pilot', factory(calls, sometimes))
    assert r['status'] == 'PHASE_COMPLETE' and r['attempts'] == len(calls) == 10 and (r['actual_debit_usd'] == pytest.approx(0.001))
    r = dispatch(plan, state, 'pilot', factory(calls))
    assert r['attempts'] == 10 and len(calls) == 10

def test_timeout_blocks_batch_and_resume_without_charging_zero(plan, tmp_path):
    calls = []

    def timeout(job):
        raise TimeoutError('synthetic opaque failure')
    state = tmp_path / 'run.db'
    r = dispatch(plan, state, 'smoke', factory(calls, timeout))
    assert r['status'] == 'BLOCKED_UNKNOWN_PENDING' and r['unknown_pending'] == [1]
    r = dispatch(plan, state, 'smoke', factory(calls))
    assert r['status'] == 'BLOCKED_UNKNOWN_PENDING' and len(calls) == 1
    with sqlite3.connect(state) as db:
        a = json.loads(db.execute('SELECT reservation FROM attempts').fetchone()[0])
    assert a['observed_cost_usd'] is None and a['reserved_cost_usd'] > 0

def test_power_loss_leaves_durable_pending_and_no_automatic_replay(plan, tmp_path):

    class PowerLoss(BaseException):
        pass

    def crash(job):
        raise PowerLoss()
    state = tmp_path / 'run.db'
    calls = []
    with pytest.raises(PowerLoss):
        dispatch(plan, state, 'smoke', factory(calls, crash))
    r = dispatch(plan, state, 'smoke', factory(calls))
    assert r['unknown_pending'] == [1] and len(calls) == 1

def test_reconciliation_is_append_only_and_retry_keeps_prior_debit(plan, tmp_path):
    state = tmp_path / 'run.db'
    calls = []
    dispatch(plan, state, 'smoke', factory(calls))

    def timeout(job):
        raise TimeoutError()
    r = dispatch(plan, state, 'pilot', factory(calls, timeout))
    assert r['unknown_pending'] == [3]
    receipt = dict(approved_for_reconciliation=True, plan_sha256=plan_hash(plan), attempt_seq=3, evidence_reference='synthetic billing receipt', cost_usd=0.0003, input_tokens=100, output_tokens=0)
    r = dispatch(plan, state, 'pilot', factory(calls), reconcile=receipt)
    assert r['status'] == 'PHASE_COMPLETE' and r['attempts'] == 7 and (r['actual_debit_usd'] == pytest.approx(0.0009))
    with sqlite3.connect(state) as db:
        raw = json.loads(db.execute('SELECT reservation FROM attempts WHERE seq=3').fetchone()[0])
        assert raw['observed_cost_usd'] is None
        assert db.execute('SELECT COUNT(*) FROM reconciliations').fetchone()[0] == 1

def test_overrun_preserved_and_resume_cannot_dispatch(plan, tmp_path):
    calls = []
    state = tmp_path / 'run.db'
    r = dispatch(plan, state, 'smoke', factory(calls, lambda j: reply(j, cost=0.2)))
    assert r['status'] == 'BLOCKED_BUDGET' and r['actual_debit_usd'] == 0.2
    r = dispatch(plan, state, 'smoke', factory(calls))
    assert r['status'] == 'BLOCKED_BUDGET' and len(calls) == 1

def test_cap_rejects_next_reservation_without_dispatch(plan, tmp_path):
    plan['phases']['smoke']['cumulative_spend_cap_usd'] = 0.11
    state = tmp_path / 'run.db'
    calls = []
    r = dispatch(plan, state, 'smoke', factory(calls, lambda j: reply(j, cost=0.1)))
    assert r['status'] == 'BLOCKED_BUDGET' and r['attempts'] == 1 and (len(calls) == 1) and (r['actual_debit_usd'] == 0.1)

def test_concurrent_owner_is_rejected(plan, tmp_path):
    state = tmp_path / 'run.db'
    calls = []
    with exclusive_run(state):
        with pytest.raises(PilotError, match='another dispatcher'):
            dispatch(plan, state, 'smoke', factory(calls))
    assert not calls

def test_state_rejects_mutated_plan_and_mock_live_mix(plan, tmp_path):
    state = tmp_path / 'run.db'
    calls = []
    dispatch(plan, state, 'smoke', factory(calls))
    changed = copy.deepcopy(plan)
    changed['nominal_input_tokens'] += 1
    with pytest.raises(PilotError, match='state plan hash'):
        dispatch(changed, state, 'smoke', factory(calls))
    approval = dict(approved=True, funding_confirmed=True, plan_sha256=plan_hash(plan), phase='smoke', phase_spend_cap_usd=0.60, phase_attempts_max=2, owner_reference='synthetic authorization', state_path=str(state.resolve()))
    with pytest.raises(PilotError):
        dispatch(plan, state, 'smoke', factory(calls), live=True, approval=approval)
    assert len(calls) == 2

@pytest.mark.parametrize('changes', [{}, {'funding_confirmed': True}, {'approved': True}, {'plan_sha256': 'wrong'}])
def test_live_needs_funding_and_exact_plan_budget_before_factory(plan, tmp_path, changes):

    def forbidden(job):
        raise AssertionError('transport must not be constructed')
    with pytest.raises(PilotError, match='live blocked'):
        dispatch(plan, tmp_path / 'run.db', 'smoke', forbidden, live=True, approval=changes)

def test_pilot_requires_smoke_and_conservative_request_bound(plan, tmp_path):
    calls = []
    r = dispatch(plan, tmp_path / 'run.db', 'pilot', factory(calls))
    assert r['status'] == 'BLOCKED_SMOKE_NOT_COMPLETE' and (not calls)
    bounds = []
    for j in plan['phases']['smoke']['jobs']:
        q = request_for(plan, j)
        row = plan['models'][j['model']]
        assert q.input_tokens_estimate == row['context_length'] and q.schema_framing_tokens == 0 and (q.max_output_tokens == 1500)
        bounds.append(q.cost_upper_bound_usd)
    assert bounds == pytest.approx([0.1054576, 0.4214304])

def test_cli_default_and_unapproved_live_read_no_key_or_state(plan, tmp_path, monkeypatch, capsys):
    import os, runpy, sys
    script = Path(__file__).parents[1] / 'scripts/dispatch_provider_pilot.py'
    state = tmp_path / 'not-created.db'

    class NoKey(dict):

        def get(self, k, default=None):
            if k == 'OPENROUTER_API_KEY':
                raise AssertionError('key read forbidden before approval')
            return default
    for args, expected in [([], 0), (['--live'], 2)]:
        with monkeypatch.context() as m:
            m.setattr(os, 'environ', NoKey())
            m.setattr(sys, 'argv', [str(script), '--state', str(state), *args])
            with pytest.raises(SystemExit) as stopped:
                runpy.run_path(str(script), run_name='__main__')
            assert stopped.value.code == expected
        assert not state.exists()
    output = capsys.readouterr()
    assert 'READY_AWAITING_FUNDING_AND_BUDGET_APPROVAL' in output.out and 'BLOCKED' in output.err

def test_cli_mock_is_executable_and_resume_stable(tmp_path, monkeypatch, capsys):
    import runpy, sys
    script = Path(__file__).parents[1] / 'scripts/dispatch_provider_pilot.py'
    state = tmp_path / 'mock.db'
    for _ in range(2):
        monkeypatch.setattr(sys, 'argv', [str(script), '--mock', '--state', str(state), '--phase', 'smoke'])
        with pytest.raises(SystemExit) as stopped:
            runpy.run_path(str(script), run_name='__main__')
        assert stopped.value.code == 0
        out = json.loads(capsys.readouterr().out)
        assert out['attempts'] == 2 and out['status'] == 'PHASE_COMPLETE'


def test_smoke_approval_cannot_authorize_pilot(plan, tmp_path):
    a=dict(approved=True,funding_confirmed=True,plan_sha256=plan_hash(plan),phase='smoke',phase_spend_cap_usd=.60,phase_attempts_max=2,owner_reference='synthetic approval', state_path=str((tmp_path/'live.db').resolve()))
    validate_approval(plan,'smoke',a,tmp_path/'live.db')
    with pytest.raises(PilotError,match='live blocked'):
        validate_approval(plan,'pilot',a,tmp_path/'live.db')


def test_live_approval_binds_state_and_lost_state_cannot_reset(plan,tmp_path):
    state=tmp_path/'live.db';calls=[]
    a=dict(approved=True,funding_confirmed=True,plan_sha256=plan_hash(plan),phase='smoke',phase_spend_cap_usd=.60,phase_attempts_max=2,owner_reference='synthetic',state_path=str(state.resolve()))
    result=dispatch(plan,state,'smoke',factory(calls),live=True,approval=a)
    assert result['attempts']==len(calls)==2
    with pytest.raises(PilotError,match='live blocked'):
        dispatch(plan,tmp_path/'other.db','smoke',factory(calls),live=True,approval=a)
    assert len(calls)==2
    state.unlink()
    with pytest.raises(PilotError,match='refuse reset'):
        dispatch(plan,state,'smoke',factory(calls),live=True,approval=a)
    assert len(calls)==2
