"""Single-controller durable ledger head; missing/unknown history never resets.

Initialize explicitly once at the fixed controller path. It is never mounted in
the model container. Reconciliation requires terminal evidence and full costs;
the controller remains responsible for observing those facts independently.
"""
from contextlib import closing,contextmanager
import hashlib
import json
import math
from pathlib import Path
import sqlite3

from .mtm_runtime import InputBoundaryError
from .r6_admission import validate_dispatch,STAGES,number,digest


def encoded(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def document_hash(value):return hashlib.sha256(encoded(value).encode()).hexdigest()


def initialize(path,identity,ledger,scope):
    if not digest(identity):raise InputBoundaryError('journal identity required')
    with Path(path).open('xb'):pass
    with closing(sqlite3.connect(path)) as db,db:
        db.execute('PRAGMA synchronous=FULL')
        db.execute('CREATE TABLE head (identity TEXT, generation INTEGER, ledger TEXT, scope TEXT, active TEXT)')
        db.execute('INSERT INTO head VALUES (?,0,?,?,NULL)',(identity,encoded(ledger),encoded(scope)))
        db.execute('CREATE TABLE attempts (id TEXT PRIMARY KEY, declaration TEXT, terminal TEXT)')


class DispatchJournal:
    def __init__(self,path,identity):
        self.path=Path(path).resolve(strict=True);self.identity=identity

    @contextmanager
    def transaction(self):
        with closing(sqlite3.connect(self.path.as_uri()+'?mode=rw',uri=True,timeout=5)) as db,db:
            db.execute('PRAGMA synchronous=FULL');db.execute('BEGIN IMMEDIATE')
            rows=db.execute('SELECT identity,generation,ledger,scope,active FROM head').fetchall()
            if len(rows)!=1 or rows[0][0]!=self.identity:raise InputBoundaryError('journal identity mismatch')
            yield db,rows[0]

    def claim(self,declaration,ledger,scope,gates,expected_generation):
        if type(expected_generation) is not int or expected_generation<0:
            raise InputBoundaryError('journal generation must be a nonnegative integer')
        validate_dispatch(declaration,ledger,scope,gates)
        with self.transaction() as (db,head):
            if (head[1]!=expected_generation or head[2]!=encoded(ledger)
                    or head[3]!=encoded(scope) or head[4] is not None):
                raise InputBoundaryError('stale ledger generation or unresolved global dispatch')
            attempt=declaration['attempt_id']
            versions=scope['stage_attempts'][declaration['stage']]
            if versions[-1]!=attempt:raise InputBoundaryError('dispatch is not latest declared version')
            if len(versions)>1:
                previous=versions[-2]
                prior=db.execute('SELECT terminal FROM attempts WHERE id=?',(previous,)).fetchone()
                revision=scope.get('revision_receipts',{}).get(attempt,{})
                if (prior is None or prior[0] is None or revision.get('previous_attempt_id')!=previous
                        or revision.get('status')!='APPROVED_BOUNDED_ENGINEERING_REVISION'
                        or revision.get('gold_or_threshold_changed') is not False
                        or not all(digest(revision.get(key)) for key in ('cause_evidence_sha256','tests_sha256','configuration_sha256'))
                        or json.loads(prior[0]).get('failure_axis')!='ENGINEERING'):
                    raise InputBoundaryError('revision requires reconciled engineering failure and frozen repair evidence')
            if db.execute('SELECT id FROM attempts WHERE id=?',(attempt,)).fetchone():
                raise InputBoundaryError('global dispatch replay forbidden')
            db.execute('INSERT INTO attempts VALUES (?,?,NULL)',(attempt,encoded(declaration)))
            db.execute('UPDATE head SET active=?',(attempt,))
        return {'status':'CONSUMED_UNRESOLVED','attempt_id':attempt,'generation':expected_generation,
                'ledger_sha256':document_hash(ledger),'scope_sha256':document_hash(scope),
                'journal_identity':self.identity,'retry':False}

    def reconcile(self,*,attempt_id,terminal,new_ledger,new_scope):
        state=terminal.get('container_state',{})
        wall=terminal.get('whole_wall_seconds')
        exited=(state.get('Running') is False and state.get('Pid')==0 and type(state.get('ExitCode')) is int)
        absent=(terminal.get('container_outcome')=='NO_CONTAINER' and
                (terminal.get('create_request_sent') is False or terminal.get('absence_observation')=='ENGINE_404'))
        if (not (exited or absent) or not number(wall) or terminal.get('costs_reconciled') is not True
                or terminal.get('attempt_id')!=attempt_id or terminal.get('container_name')!=attempt_id):
            raise InputBoundaryError('terminal and reconciled costs required')
        with self.transaction() as (db,head):
            if head[4]!=attempt_id:raise InputBoundaryError('no matching active dispatch')
            row=db.execute('SELECT declaration,terminal FROM attempts WHERE id=?',(attempt_id,)).fetchone()
            if row is None or row[1] is not None:raise InputBoundaryError('attempt already reconciled or missing')
            declaration=json.loads(row[0]);old=json.loads(head[2]);old_scope=json.loads(head[3])
            if terminal.get('declaration_sha256')!=document_hash(declaration):
                raise InputBoundaryError('terminal declaration identity mismatch')
            for charged,remaining,cap,required in [
                ('gpu_conservative_charged_seconds','gpu_remaining_seconds','gpu_limit_seconds',wall),
                ('fidelity_generation_charged_seconds','fidelity_generation_remaining_seconds','fidelity_limit_seconds',
                 wall if STAGES[declaration['stage']]['fidelity'] else 0)]:
                # A finite negative remainder records an overrun honestly; the next
                # validate_dispatch rejects it, so overrun never grants more work.
                left=new_ledger.get(remaining)
                if (not number(new_ledger.get(charged)) or type(left) not in (int,float) or not math.isfinite(left)
                        or new_ledger[charged]-old[charged]<required
                        or new_ledger.get(cap)!=old[cap]
                        or abs(new_ledger[charged]+new_ledger.get(remaining,float('inf'))-old[cap])>1e-6):
                    raise InputBoundaryError('reconciled whole-stage costs missing or reset')
            for key in ('initial_gpu_seconds','initial_fidelity_seconds','approval_sha256'):
                if new_scope.get(key)!=old_scope.get(key):raise InputBoundaryError('scope accounting floor changed')
            for name,history in old_scope['stage_attempts'].items():
                if new_scope.get('stage_attempts',{}).get(name,[])[:len(history)]!=history:
                    raise InputBoundaryError('historical stage attempts removed or reordered')
            for name in STAGES:
                before=old_scope['stage_costs'][name];after=new_scope.get('stage_costs',{}).get(name,{})
                if (not number(after.get('seconds')) or type(after.get('calls')) is not int
                        or after['seconds']<before['seconds'] or after['calls']<before['calls']
                        or (name!=declaration['stage'] and after!=before)):
                    raise InputBoundaryError('stage cost history reset or reassigned')
            delta=new_scope['stage_costs'][declaration['stage']]['seconds']-old_scope['stage_costs'][declaration['stage']]['seconds']
            if abs(delta-(new_ledger['gpu_conservative_charged_seconds']-old['gpu_conservative_charged_seconds']))>1e-6:
                raise InputBoundaryError('stage and global costs differ')
            reservations=new_scope.get('reservations',[])
            own=[r for r in reservations if r.get('attempt_id')==attempt_id]
            if len(own)!=1 or own[0].get('status')!='SETTLED' or own[0].get('declaration')!=declaration:
                raise InputBoundaryError('settled same-attempt reservation required')
            for original in old_scope['reservations']:
                retained=[r for r in reservations if r.get('attempt_id')==original.get('attempt_id')]
                expected=dict(original,status='SETTLED') if original.get('attempt_id')==attempt_id else original
                if retained!=[expected]:raise InputBoundaryError('historical reservation changed or removed')
            db.execute('UPDATE attempts SET terminal=? WHERE id=?',(encoded(terminal),attempt_id))
            db.execute('UPDATE head SET generation=?,ledger=?,scope=?,active=NULL',
                       (head[1]+1,encoded(new_ledger),encoded(new_scope)))
        return {'status':'RECONCILED','generation':head[1]+1,'terminal_sha256':document_hash(terminal)}
