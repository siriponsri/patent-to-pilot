"""Versioned, receipt-bound CPU reconciliation; never resets the R6 journal.

This transition grants no model authority. Its receipt hash must be pinned by
the controller after independently verifying the referenced CPU evidence.
"""
import json
from copy import deepcopy

from .mtm_runtime import InputBoundaryError
from .r6_admission import digest, number, validate_dispatch, STAGES
from .r6_dispatch_journal import DispatchJournal, document_hash, encoded


CPU_CHARGES = ('local_cpu_conservative_charged_seconds',
               'local_cpu_measured_seconds', 'remote_cpu_charged_seconds')
CPU_RESERVES = ('local_cpu_reserved_seconds', 'remote_cpu_reserved_seconds')
CPU_ANNOTATIONS = ('compact_preparation_pending_cpu_settled_seconds',
                   'compact_v2_local_CPU_charged_seconds')


def require(condition, message):
    if not condition:
        raise InputBoundaryError(message)


def cpu_total(cpu):
    keys = ('cpu_prior_upper_bound_seconds',) + CPU_CHARGES + CPU_RESERVES
    require(all(number(cpu.get(k, 0)) for k in keys), 'invalid CPU accounting')
    return sum(cpu.get(k, 0) for k in keys)


def validate_cpu_change(old, new, receipt):
    """Only allow append-only zero-model CPU evidence and monotonic charges."""
    before = deepcopy(old); after = deepcopy(new)
    old_cpu = before.pop('r6_phase0_cpu'); new_cpu = after.pop('r6_phase0_cpu')
    for key in ('r7_cpu', 'graph_compact_v2_input'):
        previous = before.pop(key, None); current = after.pop(key, None)
        if key == 'graph_compact_v2_input':
            require(previous is None or current == previous, 'historical Graph receipt changed')
            if current is not None:
                require(current.get('model_calls') == 0 and current.get('GPU_seconds') == 0
                        and current.get('cards_issued') == 0, 'CPU transition contains model work')
        elif current is not None:
            require(current.get('cap_seconds') == 3600
                    and current.get('approval_sha256') == receipt.get('owner_approval_sha256'),
                    'R7 CPU approval changed')
            fields = ('conservative_charged_seconds', 'measured_seconds', 'reserved_seconds')
            require(all(number(current.get(k)) for k in fields), 'invalid R7 CPU accounting')
            require(sum(current[k] for k in fields) <= 3600, 'R7 CPU allowance exhausted')
            require(current['reserved_seconds'] == 0, 'R7 CPU work remains unresolved')
            for r7_key, global_key in [('conservative_charged_seconds', CPU_CHARGES[0]),
                                       ('measured_seconds', CPU_CHARGES[1])]:
                delta = current[r7_key] - (previous[r7_key] if previous else 0)
                global_delta = new_cpu.get(global_key,0)-old_cpu.get(global_key,0)
                if r7_key == 'measured_seconds':
                    global_delta += new_cpu.get(CPU_CHARGES[2],0)-old_cpu.get(CPU_CHARGES[2],0)
                require(delta <= global_delta,
                        'R7 CPU charge not included in global accounting')
            if previous is not None:
                for k in fields[:2]:
                    require(current[k] >= previous[k], 'R7 CPU charges reset')
                require(previous['approval_sha256'] == current['approval_sha256']
                        and previous['cap_seconds'] == current['cap_seconds'], 'R7 CPU identity changed')
        else:
            require(previous is None, 'R7 CPU history removed')
    require(before == after, 'non-CPU ledger mutation prohibited')
    require(cpu_total(new_cpu) <= 28800 and new_cpu.get('cpu_cap_seconds') == 28800,
            'global CPU allowance exhausted')
    old_fixed = deepcopy(old_cpu); new_fixed = deepcopy(new_cpu)
    deltas = {}
    for key in CPU_CHARGES:
        a = old_fixed.pop(key, 0); b = new_fixed.pop(key, 0)
        require(number(a) and number(b) and b >= a, 'CPU charge reset')
        deltas[key] = b-a
    for key in CPU_RESERVES:
        a = old_fixed.pop(key, 0); b = new_fixed.pop(key, 0)
        require(number(a) and b == 0, 'CPU work remains unresolved')
        deltas[key] = b-a
    require(deltas == receipt.get('cpu_deltas'), 'CPU settlement deltas lack evidence binding')
    for key in CPU_ANNOTATIONS:
        a = old_fixed.pop(key, None); b = new_fixed.pop(key, None)
        require(a == b or (a is None and number(b)), 'historical CPU annotation changed')
    old_jobs = old_fixed.pop('jobs', {}); new_jobs = new_fixed.pop('jobs', {})
    require(all(new_jobs.get(k) == v for k,v in old_jobs.items()), 'CPU job history changed')
    for key in new_jobs.keys()-old_jobs.keys():
        job = new_jobs[key]
        require(job.get('model_calls') == 0 and number(job.get('cpu_seconds'))
                and type(job.get('model_calls')) is int
                and type(job.get('gpu_seconds')) is int and job['gpu_seconds'] == 0
                and digest(job.get('declaration_sha256')), 'new CPU job lacks zero-model evidence')
    require(old_fixed == new_fixed, 'CPU limits or historical metadata changed')


class R7DispatchJournal(DispatchJournal):
    def authorize_calibration(self, *, expected_generation, ledger, declaration, gates,
                              authority, authority_sha256):
        """Append one owner-approved candidate, preserving the failed prior run.

        The controller pins the reviewed authority document, including the exact
        terminal, declaration, frozen gold, transport and accounting baseline.
        This is deliberately distinct from an engineering retry.
        """
        require(type(expected_generation) is int and expected_generation >= 0, 'invalid generation')
        require(type(declaration.get('ledger_generation')) is int
                and declaration['ledger_generation'] == expected_generation+1,
                'candidate must bind post-authorization generation')
        require(digest(authority_sha256) and document_hash(authority) == authority_sha256,
                'candidate authority differs from controller pin')
        require(authority.get('status') == 'OWNER_APPROVED_R7_SINGLE_CANDIDATE'
                and authority.get('journal_identity') == self.identity
                and authority.get('gold_or_threshold_changed') is False,
                'explicit new candidate authority required')
        for key in ('owner_approval_sha256','plan_sha256','previous_terminal_sha256',
                    'declaration_sha256','gold_sha256','criteria_sha256','transport_sha256'):
            require(digest(authority.get(key)), 'candidate identity missing: '+key)
        require(authority['declaration_sha256'] == document_hash(declaration)
                and declaration.get('stage') == 'calibration'
                and declaration.get('maximum_calls') == 24
                and number(declaration.get('seconds')) and 0 < declaration['seconds'] <= 7200,
                'candidate must be the exact bounded calibration')
        require(declaration.get('candidate_owner_approval_sha256') == authority['owner_approval_sha256']
                and declaration.get('transport_version') == 'sg-compact-transport-v2'
                and all(declaration.get(k) == authority[k] for k in
                        ('gold_sha256','criteria_sha256','transport_sha256')),
                'candidate transport or scientific identity changed')
        require(authority.get('gpu_seconds') == 637200 and authority.get('fidelity_seconds') == 169200
                and authority.get('full_dev_seconds') == 460800 and authority.get('cpu_seconds') == 3600,
                'R7 ceilings changed')
        with self.transaction() as (db, head):
            require(head[1] == expected_generation and head[4] is None and head[2] == encoded(ledger),
                    'stale candidate ledger or unresolved dispatch')
            scope = json.loads(head[3]); prior = authority.get('previous_attempt_id')
            require('r7_authority' not in scope and scope['stage_attempts']['calibration'] == [prior],
                    'candidate already authorized or historical calibration differs')
            row = db.execute('SELECT terminal FROM attempts WHERE id=?',(prior,)).fetchone()
            require(row is not None and row[0] is not None, 'prior calibration unresolved')
            terminal = json.loads(row[0])
            require(document_hash(terminal) == authority['previous_terminal_sha256']
                    and terminal.get('failure_axis') == 'EVALUATOR_CALIBRATION',
                    'prior scientific outcome changed')
            for floor_key, charged in [('initial_gpu_seconds','gpu_conservative_charged_seconds'),
                                       ('initial_fidelity_seconds','fidelity_generation_charged_seconds')]:
                baseline = authority.get(floor_key)
                require(number(baseline) and scope[floor_key] <= baseline <= ledger[charged],
                        'invalid R7 baseline')
            attempt = declaration['attempt_id']
            require(not db.execute('SELECT id FROM attempts WHERE id=?',(attempt,)).fetchone(),
                    'candidate dispatch replay')
            scope['stage_attempts']['calibration'].append(attempt)
            scope['qualified_dispatches'][attempt] = deepcopy(declaration)
            scope['reservations'].append({'attempt_id':attempt,'status':'RESERVED',
                                          'declaration':deepcopy(declaration)})
            scope['r7_authority'] = deepcopy(authority)
            scope['r7_authority_sha256'] = authority_sha256
            validate_dispatch(declaration,ledger,scope,gates)
            self._r7_bounds(declaration,ledger,scope,gates)
            db.execute('CREATE TABLE IF NOT EXISTS r7_transitions '
                       '(generation INTEGER PRIMARY KEY, kind TEXT, receipt TEXT)')
            db.execute('INSERT INTO r7_transitions VALUES (?,?,?)',
                       (head[1]+1,'NEW_CANDIDATE',encoded(authority)))
            db.execute('UPDATE head SET generation=?,scope=?',(head[1]+1,encoded(scope)))
        return {'status':'AUTHORIZED_NOT_DISPATCHED','generation':head[1]+1,'scope':scope}

    @staticmethod
    def _r7_bounds(declaration, ledger, scope, gates):
        authority = scope.get('r7_authority',{})
        require(document_hash(authority) == scope.get('r7_authority_sha256'), 'candidate receipt changed')
        require(declaration.get('candidate_owner_approval_sha256') == authority.get('owner_approval_sha256'),
                'candidate owner approval missing')
        for gate in gates.values():
            require(gate.get('candidate_owner_approval_sha256') == authority['owner_approval_sha256'],
                    'gate does not bind new candidate approval')
        for charged, floor, cap, seconds in [
            ('gpu_conservative_charged_seconds','initial_gpu_seconds',637200,declaration['seconds']),
            ('fidelity_generation_charged_seconds','initial_fidelity_seconds',169200,
             declaration['seconds'] if STAGES[declaration['stage']]['fidelity'] else 0)]:
            require(number(authority.get(floor)) and ledger[charged] >= authority[floor]
                    and ledger[charged]-authority[floor]+seconds <= cap, 'R7 allowance exhausted')

    def claim(self, declaration, ledger, scope, gates, expected_generation):
        # Historical R6 claims retain their original engineering-only retry rule.
        if 'r7_authority' not in scope:
            return super().claim(declaration,ledger,scope,gates,expected_generation)
        require(type(expected_generation) is int and expected_generation >= 0, 'invalid generation')
        validate_dispatch(declaration,ledger,scope,gates)
        require(declaration.get('ledger_generation') == expected_generation,
                'candidate declaration generation mismatch')
        self._r7_bounds(declaration,ledger,scope,gates)
        authority = scope['r7_authority']
        # Later stages need their own qualification; this path grants only the
        # exact newly authorized calibration and cannot substitute another run.
        require(declaration['stage'] == 'calibration'
                and document_hash(declaration) == authority['declaration_sha256'],
                'only exact authorized calibration may use candidate transition')
        with self.transaction() as (db, head):
            require(head[1] == expected_generation and head[2] == encoded(ledger)
                    and head[3] == encoded(scope) and head[4] is None,
                    'stale candidate head or unresolved dispatch')
            rows = db.execute("SELECT receipt FROM r7_transitions WHERE kind='NEW_CANDIDATE'").fetchall()
            require(len(rows) == 1 and rows[0][0] == encoded(authority), 'candidate transition missing')
            attempt = declaration['attempt_id']
            require(not db.execute('SELECT id FROM attempts WHERE id=?',(attempt,)).fetchone(),
                    'candidate replay forbidden')
            db.execute('INSERT INTO attempts VALUES (?,?,NULL)',(attempt,encoded(declaration)))
            db.execute('UPDATE head SET active=?',(attempt,))
        return {'status':'CONSUMED_UNRESOLVED','attempt_id':attempt,'generation':expected_generation,
                'ledger_sha256':document_hash(ledger),'scope_sha256':document_hash(scope),
                'journal_identity':self.identity,'candidate_authority_sha256':scope['r7_authority_sha256'],
                'retry':False}

    def sync_cpu_ledger(self, *, expected_generation, new_ledger, receipt, receipt_sha256):
        require(type(expected_generation) is int and expected_generation >= 0, 'invalid generation')
        require(digest(receipt_sha256) and document_hash(receipt) == receipt_sha256,
                'CPU receipt differs from controller pin')
        require(receipt.get('status') == 'VERIFIED_CPU_ONLY_RECONCILIATION'
                and receipt.get('journal_identity') == self.identity
                and digest(receipt.get('owner_approval_sha256'))
                and type(receipt.get('model_calls')) is int and receipt['model_calls'] == 0
                and type(receipt.get('gpu_seconds')) is int and receipt['gpu_seconds'] == 0
                and type(receipt.get('evidence_sha256')) is list and receipt['evidence_sha256']
                and all(digest(v) for v in receipt['evidence_sha256']), 'CPU evidence incomplete')
        with self.transaction() as (db, head):
            require(head[1] == expected_generation and head[4] is None,
                    'stale generation or unresolved dispatch')
            old = json.loads(head[2])
            require(receipt.get('old_ledger_sha256') == document_hash(old)
                    and receipt.get('new_ledger_sha256') == document_hash(new_ledger),
                    'CPU receipt ledger binding mismatch')
            validate_cpu_change(old, new_ledger, receipt)
            db.execute('CREATE TABLE IF NOT EXISTS r7_transitions '
                       '(generation INTEGER PRIMARY KEY, kind TEXT, receipt TEXT)')
            db.execute('INSERT INTO r7_transitions VALUES (?,?,?)',
                       (head[1]+1, 'CPU_ONLY', encoded(receipt)))
            db.execute('UPDATE head SET generation=?,ledger=?',
                       (head[1]+1, encoded(new_ledger)))
        return {'status':'CPU_ONLY_RECONCILED_NO_MODEL_AUTHORITY',
                'generation':head[1]+1, 'receipt_sha256':receipt_sha256}
