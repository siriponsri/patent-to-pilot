"""Sequential, journaled engineering pilot, separate from research evaluation."""
from __future__ import annotations
import os
import hashlib, json, math, sqlite3
from contextlib import contextmanager
from pathlib import Path
from .openrouter import AttemptLedger, BudgetExceededError, OpenRouterAdapter, ProviderAttempt, ProviderCapabilities, ProviderConfig, ProviderRequest

class PilotError(RuntimeError):
    pass

def canonical(x):
    return json.dumps(x, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False)

def plan_hash(plan):
    return hashlib.sha256(canonical(plan).encode()).hexdigest()

def validate_plan(p):
    if p.get('version') != 'ptp-prefund-1' or p.get('endpoint') != 'https://openrouter.ai/api/v1/chat/completions':
        raise PilotError('unsupported plan or endpoint')
    if not 0 < p['project_spend_cap_usd'] <= 1 or p['max_attempts_total'] != 10:
        raise PilotError('project limit must be at most USD 1 and ten total attempts')
    if p['output_tokens'] != 1500 or sum((x['attempts_max'] for x in p['phases'].values())) != 10:
        raise PilotError('invalid phase/token limits')
    ids = []
    for phase in p['phases'].values():
        if not 0 < phase['cumulative_spend_cap_usd'] <= p['project_spend_cap_usd']:
            raise PilotError('invalid phase cap')
        for j in phase['jobs']:
            ids.append(j['id'])
            if j['model'] not in p['models'] or not 1 <= j['attempts_max'] <= 2:
                raise PilotError('invalid job')
    if len(ids) != len(set(ids)):
        raise PilotError('duplicate job')
    for row in p['models'].values():
        if not row['routing_only'] or not {'max_tokens', 'structured_outputs', 'response_format'} <= set(row['supported_parameters']):
            raise PilotError('missing routing/capabilities')
        if type(row['context_length']) is not int or row['context_length'] < 1:
            raise PilotError('invalid context bound')
        for name in ('prompt_usd_per_million', 'completion_usd_per_million'):
            if not math.isfinite(row[name]) or row[name] <= 0:
                raise PilotError('invalid price')

def validate_approval(p, phase, a, state):
    required = dict(approved=True, funding_confirmed=True, plan_sha256=plan_hash(p),
        phase=phase, phase_spend_cap_usd=p['phases'][phase]['cumulative_spend_cap_usd'],
        phase_attempts_max=p['phases'][phase]['attempts_max'])
    if not a or any(a.get(k) != v for k, v in required.items()) or not a.get('owner_reference') or not Path(a.get('state_path', '')).is_absolute() or str(Path(a['state_path']).resolve()).casefold() != str(Path(state).resolve()).casefold():
        raise PilotError('live blocked: exact phase/plan/budget approval and funding confirmation required')


def request_for(p, j):
    """Reserve advertised full input context including schema; 4128 is nominal only."""
    row = p['models'][j['model']]
    schema = {'type': 'object', 'properties': {'ack': {'type': 'string', 'enum': ['ready']}, 'case_id': {'type': 'string', 'enum': [j['id']]}}, 'required': ['ack', 'case_id'], 'additionalProperties': False}
    prompt = 'Public synthetic engineering echo only. Return JSON ack=ready and case_id=' + j['id'] + '. ' + j['instruction']
    if len(canonical({'prompt': prompt, 'schema': schema}).encode()) > 2048:
        raise PilotError('fixed packet exceeds reviewed byte allowance')
    bound = (row['context_length'] * row['prompt_usd_per_million'] + p['output_tokens'] * row['completion_usd_per_million']) / 1000000.0
    return ProviderRequest(prompt=prompt, response_schema=schema, input_tokens_estimate=row['context_length'], max_output_tokens=p['output_tokens'], cost_upper_bound_usd=bound, request_id='ptp-' + j['id'])

def config_for(p, phase, j, live):
    r = p['models'][j['model']]
    return ProviderConfig(model=j['model'], routing_only=r['routing_only'], max_price={'prompt': r['prompt_usd_per_million'], 'completion': r['completion_usd_per_million']}, live_enabled=live, max_input_tokens=r['context_length'], max_output_tokens=p['output_tokens'], max_total_tokens=p['max_attempts_total'] * (max((x['context_length'] for x in p['models'].values())) + p['output_tokens']), max_spend_usd=p['phases'][phase]['cumulative_spend_cap_usd'], retries=0, prompt_version=p['version'], config_version=plan_hash(p))

@contextmanager
def exclusive_run(path):
    """Separate OS-held SQLite lock remains held across journal commits and releases on crash."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lock = sqlite3.connect(str(path) + '.lock.sqlite3', timeout=0)
    try:
        try:
            lock.execute('BEGIN EXCLUSIVE')
        except sqlite3.OperationalError:
            raise PilotError('another dispatcher owns this state') from None
        yield
    finally:
        lock.close()

class Journal:

    def __init__(self, path, p, live):
        self.db = sqlite3.connect(path)
        self.db.executescript('CREATE TABLE IF NOT EXISTS meta(id INTEGER PRIMARY KEY CHECK(id=1),digest TEXT,mode TEXT); CREATE TABLE IF NOT EXISTS attempts(seq INTEGER PRIMARY KEY,phase TEXT,job TEXT,config TEXT,request TEXT,reservation TEXT,finished INTEGER DEFAULT 0,response TEXT); CREATE TABLE IF NOT EXISTS reconciliations(seq INTEGER PRIMARY KEY,receipt TEXT);')
        row = self.db.execute('SELECT digest,mode FROM meta WHERE id=1').fetchone()
        identity = (plan_hash(p), 'live' if live else 'mock')
        if row and row != identity:
            self.db.close()
            raise PilotError('state plan hash or mock/live mode differs')
        if not row:
            self.db.execute('INSERT INTO meta VALUES(1,?,?)', identity)
            self.db.commit()

    def rows(self):
        out = []
        for seq, phase, job, config, request, reservation, finished, response in self.db.execute('SELECT * FROM attempts ORDER BY seq'):
            a = ProviderAttempt.model_validate_json(reservation)
            receipt = self.db.execute('SELECT receipt FROM reconciliations WHERE seq=?', (seq,)).fetchone()
            if receipt:
                r = json.loads(receipt[0])
                a.observed_cost_usd = r['cost_usd']
                a.observed_input_tokens = r['input_tokens']
                a.observed_output_tokens = r['output_tokens']
                a.observed_total_tokens = r['input_tokens'] + r['output_tokens']
                a.reservation_status = 'settled'
                a.status = 'reconciled_failed'
                finished = 1
            out.append(dict(seq=seq, phase=phase, job=job, config=json.loads(config), request=json.loads(request), attempt=a, finished=bool(finished), response=response))
        return out

    def summary(self, status, reason=None):
        rows = self.rows()
        return dict(status=status, reason=reason, attempts=len(rows), actual_debit_usd=sum((r['attempt'].observed_cost_usd or 0 for r in rows)), reserved_cost_usd=sum((r['attempt'].reserved_cost_usd or 0) for r in rows if r['attempt'].observed_cost_usd is None), unknown_pending=[r['seq'] for r in rows if not r['finished'] or r['attempt'].reservation_status != 'settled'], completed_jobs=[r['job'] for r in rows if r['finished'] and r['attempt'].status == 'success'])

    def reconcile(self, p, r):
        if r.get('approved_for_reconciliation') is not True or r.get('plan_sha256') != plan_hash(p) or (not r.get('evidence_reference')):
            raise PilotError('approved plan-bound billing evidence required')
        row = next((x for x in self.rows() if x['seq'] == r.get('attempt_seq')), None)
        if not row or (row['finished'] and row['attempt'].reservation_status == 'settled'):
            raise PilotError('only unresolved attempts may be reconciled')
        if type(r.get('cost_usd')) not in (int, float) or not math.isfinite(r['cost_usd']) or r['cost_usd'] < 0:
            raise PilotError('invalid reconciled cost')
        if any((type(r.get(k)) is not int or r[k] < 0 for k in ('input_tokens', 'output_tokens'))):
            raise PilotError('invalid reconciled tokens')
        self.db.execute('INSERT INTO reconciliations VALUES(?,?)', (row['seq'], canonical(r)))
        self.db.commit()

class DurableLedger(AttemptLedger):
    """Durable pre-dispatch reservations; replay through the accepted ledger on resume."""

    def __init__(self, journal, p):
        super().__init__()
        self.journal = journal
        self.plan = p
        self.context = None
        for row in journal.rows():
            c = ProviderConfig.model_validate(row['config'])
            self.configure_cap(c.max_spend_usd)
            a = super().reserve(config=c, request=ProviderRequest.model_validate(row['request']), attempt=1)
            old = row['attempt']
            a.reservation_id = old.reservation_id
            usage = dict(input_tokens=old.observed_input_tokens, output_tokens=old.observed_output_tokens, total_tokens=old.observed_total_tokens)
            super().settle(a, usage=usage, cost=old.observed_cost_usd, outcome_known=True)
            a.status = old.status

    def reserve(self, *, config, request, attempt):
        phase, job = self.context
        rows = self.journal.rows()
        if len(rows) >= self.plan['max_attempts_total'] or sum((r['phase'] == phase for r in rows)) >= self.plan['phases'][phase]['attempts_max'] or sum((r['job'] == job['id'] for r in rows)) >= job['attempts_max']:
            raise BudgetExceededError('total/phase/job attempt limit reached')
        a = super().reserve(config=config, request=request, attempt=attempt)
        self.journal.db.execute('INSERT INTO attempts(phase,job,config,request,reservation) VALUES(?,?,?,?,?)', (phase, job['id'], config.model_dump_json(), request.model_dump_json(), a.model_dump_json()))
        self.journal.db.commit()
        return a

    def save(self, a, finished=False, response=None):
        if a.reservation_id:
            self.journal.db.execute('UPDATE attempts SET reservation=?,finished=?,response=? WHERE seq=(SELECT MAX(seq) FROM attempts)', (a.model_dump_json(), int(finished), response))
            self.journal.db.commit()

    def settle(self, a, **kwargs):
        result = super().settle(a, **kwargs)
        self.save(a)
        return result

def dispatch(p, state, phase, transport_factory, *, live=False, approval=None, reconcile=None, max_new_attempts=None):
    validate_plan(p)
    if phase not in p['phases']:
        raise PilotError('unknown phase')
    if live:
        validate_approval(p, phase, approval, state)
    with exclusive_run(state):
        if live:
            state = Path(state).resolve()
            marker = Path(str(state) + '.started.json')
            activation = dict(plan_sha256=plan_hash(p), state_path=str(state).casefold())
            if marker.exists():
                if not state.exists() or json.loads(marker.read_text(encoding='utf-8')) != activation:
                    raise PilotError('live activation exists but state is missing or differs; refuse reset')
            elif state.exists():
                raise PilotError('existing live state has no activation marker; refuse reset')
            else:
                with marker.open('x', encoding='utf-8') as f:
                    f.write(canonical(activation));f.flush();os.fsync(f.fileno())
        journal = Journal(state, p, live)
        try:
            if reconcile:
                journal.reconcile(p, reconcile)
            if journal.summary('')['unknown_pending']:
                return journal.summary('BLOCKED_UNKNOWN_PENDING', 'billing/outcome evidence required; no automatic replay')
            if phase == 'pilot' and (not {j['id'] for j in p['phases']['smoke']['jobs']} <= set(journal.summary('')['completed_jobs'])):
                return journal.summary('BLOCKED_SMOKE_NOT_COMPLETE')
            ledger = DurableLedger(journal, p)
            new_count = 0
            for job in p['phases'][phase]['jobs']:
                while True:
                    rows = [r for r in journal.rows() if r['job'] == job['id']]
                    if any((r['attempt'].status == 'success' for r in rows)) or len(rows) >= job['attempts_max']:
                        break
                    if max_new_attempts is not None and new_count >= max_new_attempts:
                        return journal.summary('PAUSED')
                    ledger.context = (phase, job)
                    adapter = OpenRouterAdapter(config_for(p, phase, job, live), transport_factory(job), ProviderCapabilities(provider='openrouter', model=job['model'], structured_outputs=True), ledger)
                    response = None
                    error = None
                    before = len(ledger.attempts)
                    try:
                        response = adapter.complete(request_for(p, job))
                    except Exception as exc:
                        error = type(exc).__name__
                    finally:
                        if len(ledger.attempts) > before and (response is not None or error is not None):
                            ledger.save(ledger.attempts[-1], finished=True, response=response.model_dump_json() if response else None)
                    new_count += 1
                    if journal.summary('')['unknown_pending']:
                        return journal.summary('BLOCKED_UNKNOWN_PENDING', error)
                    if ledger.budget_breach or error == 'BudgetExceededError':
                        return journal.summary('BLOCKED_BUDGET', error)
                    if error and error != 'ResponseValidationError':
                        return journal.summary('STOPPED_ERROR', error)
            done = set(journal.summary('')['completed_jobs'])
            return journal.summary('PHASE_COMPLETE' if all((j['id'] in done for j in p['phases'][phase]['jobs'])) else 'PHASE_FAILED')
        finally:
            journal.db.close()
