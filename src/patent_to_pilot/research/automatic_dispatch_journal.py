"""Append automatic-study authority to the existing journal; never reset it.

This transition alone authorizes no dispatch. A new bounded stage validator and
controller must bind exact declarations before consuming an attempt.
"""
import json
import math
import time
from copy import deepcopy
from .mtm_runtime import InputBoundaryError
from .r6_admission import digest
from .r6_dispatch_journal import DispatchJournal, document_hash, encoded


def require(value, message):
    if not value:
        raise InputBoundaryError(message)


class AutomaticDispatchJournal(DispatchJournal):
    def qualify_stage(self, *, expected_generation, receipt, receipt_sha256):
        """Append a stage to immutable root authority using current accounting."""
        require(type(expected_generation) is int and expected_generation >= 0, 'invalid generation')
        require(digest(receipt_sha256) and document_hash(receipt) == receipt_sha256, 'qualification pin changed')
        declaration = receipt.get('declaration', {})
        require(declaration.get('stage') == 'synthetic', 'later-stage qualification not implemented')
        require(digest(declaration.get('operation_sha256')), 'operation identity missing')
        with self.transaction() as (db, head):
            require(head[1] == expected_generation and head[4] is None, 'stale or active qualification')
            ledger, scope = json.loads(head[2]), json.loads(head[3])
            study = scope['automatic_study']; authority = study['authority']
            require(study['status'] in ('IDLE', 'ADOPTED_NO_DISPATCH'), 'study stopped')
            require(receipt.get('authority_sha256') == study['authority_sha256'] == document_hash(authority)
                    and receipt.get('ledger_sha256') == document_hash(ledger)
                    and receipt.get('scope_sha256') == document_hash(scope), 'qualification baseline changed')
            policy = authority.get('stage_envelopes', {}).get('synthetic', {})
            for field in ('seconds', 'maximum_calls'):
                require(type(declaration.get(field)) is int and declaration[field] > 0
                        and type(policy.get(field)) is int and declaration[field] <= policy[field],
                        'stage exceeds root authority envelope')
            require(declaration.get('configuration_sha256') in authority.get('configuration_sha256', []),
                    'configuration outside approved authority')
            attempt = declaration.get('attempt_id')
            require(type(attempt) is str and attempt.startswith('ptp-auto-'), 'invalid attempt')
            require(attempt not in study['qualified_dispatches']
                    and not db.execute('SELECT id FROM attempts WHERE id=?', (attempt,)).fetchone(),
                    'qualification replay')
            require(all(d.get('operation_sha256') != declaration['operation_sha256']
                        for d in study['qualified_dispatches'].values()), 'operation already qualified')
            study['qualified_dispatches'][attempt] = deepcopy(declaration)
            db.execute('INSERT INTO automatic_transitions VALUES (?,?,?)',
                       (head[1]+1, 'STAGE_QUALIFICATION', encoded(receipt)))
            db.execute('UPDATE head SET generation=?,scope=?', (head[1]+1, encoded(scope)))
        return {'status': 'QUALIFIED_NOT_DISPATCHED', 'generation': expected_generation+1, 'scope': scope}

    def adopt_scope(self, *, expected_generation, authority, authority_sha256):
        require(type(expected_generation) is int and expected_generation >= 0, 'invalid generation')
        require(digest(authority_sha256) and document_hash(authority) == authority_sha256,
                'authority differs from controller pin')
        require(authority.get('status') == 'OWNER_APPROVED_AUTOMATIC_DUAL_TRACK'
                and authority.get('journal_identity') == self.identity
                and authority.get('human_review_required') is False
                and authority.get('semantic_certification') is False,
                'automatic study authority missing')
        for key in ('owner_approval_sha256', 'protocol_sha256', 'policy_sha256',
                    'prior_ledger_sha256', 'prior_scope_sha256', 'prior_attempts_sha256'):
            require(digest(authority.get(key)), 'missing authority identity: ' + key)
        with self.transaction() as (db, head):
            require(head[1] == expected_generation and head[4] is None,
                    'stale generation or unresolved active attempt')
            ledger, scope = json.loads(head[2]), json.loads(head[3])
            require(document_hash(ledger) == authority['prior_ledger_sha256']
                    and document_hash(scope) == authority['prior_scope_sha256'],
                    'prior accounting or scope changed')
            attempts = db.execute('SELECT id,declaration,terminal FROM attempts ORDER BY id').fetchall()
            require(all(row[2] is not None for row in attempts), 'unresolved historical attempt')
            require(document_hash(attempts) == authority['prior_attempts_sha256'], 'attempt history changed')
            require(all(r.get('status') in ('SETTLED', 'CANCELLED_PRE_DISPATCH')
                        for r in scope.get('reservations', [])), 'outstanding reservation')
            require('automatic_study' not in scope, 'automatic scope already adopted')
            caps = {key: ledger.get(key) for key in (
                'gpu_limit_seconds', 'fidelity_limit_seconds', 'full_dev_limit_seconds',
                'disk_limit_bytes_combined_incremental',
                'human_cards_total_limit_all_benchmarks_all_configurations')}
            require(caps == authority.get('unchanged_ledger_caps'), 'resource ceilings changed')
            require(all(type(v) is int and v > 0 for v in caps.values()), 'missing cumulative cap')
            updated = deepcopy(scope)
            updated['automatic_study'] = {'authority': deepcopy(authority),
                'authority_sha256': authority_sha256, 'status': 'ADOPTED_NO_DISPATCH',
                'qualified_dispatches': {}, 'stage_costs': {}, 'reservations': []}
            db.execute('CREATE TABLE IF NOT EXISTS automatic_transitions '
                       '(generation INTEGER PRIMARY KEY, kind TEXT, receipt TEXT)')
            db.execute('INSERT INTO automatic_transitions VALUES (?,?,?)',
                       (expected_generation + 1, 'AUTOMATIC_SCOPE', encoded(authority)))
            db.execute('UPDATE head SET generation=?,scope=?',
                       (expected_generation + 1, encoded(updated)))
        return {'status': 'ADOPTED_NO_DISPATCH', 'generation': expected_generation + 1,
                'ledger_sha256': document_hash(ledger), 'scope': updated}

    def claim(self, *, declaration=None, gates=None, expected_generation=None, live_receipt=None):
        require(type(expected_generation) is int and expected_generation >= 0, 'invalid generation')
        require(type(declaration) is dict and type(gates) is dict, 'qualified declaration required')
        d = declaration
        require(d.get('retry') is False and d.get('stage') in ('synthetic', 'fidelity', 'pilot', 'full_dev'),
                'unknown stage or replay')
        require(d['stage'] == 'synthetic', 'later stages await explicit technical predecessor gates')
        require(type(d.get('attempt_id')) is str and d['attempt_id'].startswith('ptp-auto-'), 'attempt identity')
        require(type(d.get('maximum_calls')) is int and d['maximum_calls'] > 0,
                'explicit positive call ceiling required')
        require(type(d.get('seconds')) is int and d['seconds'] > 0, 'explicit time ceiling required')
        for key in ('package_sha256', 'configuration_sha256', 'input_manifest_sha256', 'model_sha256'):
            require(digest(d.get(key)), 'missing frozen identity: ' + key)
        required = {'integrity', 'isolation', 'runtime', 'resources', 'accounting'}
        require(set(gates) == required and set(d.get('gate_receipts', {})) == required,
                'engineering evidence incomplete')
        for name, receipt in gates.items():
            require(receipt.get('gate') == name and receipt.get('status') == 'PASS'
                    and receipt.get('package_sha256') == d['package_sha256']
                    and receipt.get('configuration_sha256') == d['configuration_sha256']
                    and document_hash(receipt) == d['gate_receipts'][name], 'gate identity changed')
        with self.transaction() as (db, head):
            require(head[1] == expected_generation and head[4] is None, 'stale or active journal')
            scope = json.loads(head[3]); ledger = json.loads(head[2])
            study = scope.get('automatic_study', {}); authority = study.get('authority', {})
            require(study.get('status') in ('ADOPTED_NO_DISPATCH', 'IDLE'), 'study stopped or active')
            require(document_hash(authority) == study.get('authority_sha256'), 'study authority changed')
            declared = study.get('qualified_dispatches', {}).get(d['attempt_id'])
            if declared is None:
                declared = authority.get('qualified_dispatches', {}).get(d['attempt_id'])
            require(declared == d,
                    'stage declaration not explicitly frozen in authority')
            require(all(r.get('status') == 'SETTLED' for r in study.get('reservations', [])),
                    'unsettled study reservation')
            require(not db.execute('SELECT id FROM attempts WHERE id=?', (d['attempt_id'],)).fetchone(),
                    'attempt replay prohibited')
            costs = study.get('stage_costs', {})
            study_used = sum(v['seconds'] for v in costs.values())
            require(study_used + d['seconds'] <= 160 * 3600, 'automatic GPU package exhausted')
            for used, left, cap, charge in (
                ('gpu_conservative_charged_seconds', 'gpu_remaining_seconds', 'gpu_limit_seconds', d['seconds']),
                ('fidelity_generation_charged_seconds', 'fidelity_generation_remaining_seconds', 'fidelity_limit_seconds',
                 d['seconds'] if d['stage'] in ('synthetic', 'fidelity') else 0)):
                require(all(type(ledger.get(k)) in (int, float) and math.isfinite(ledger[k]) and ledger[k] >= 0
                            for k in (used, left, cap)), 'invalid cumulative ledger')
                require(ledger[cap] == authority['unchanged_ledger_caps'][cap]
                        and math.isclose(ledger[used] + ledger[left], ledger[cap], abs_tol=1e-6, rel_tol=0)
                        and ledger[left] >= charge, 'cumulative allowance exceeded')
            require(gates['accounting'].get('ledger_sha256') == document_hash(ledger), 'stale accounting gate')
            require(gates['resources'].get('live_admission_required') is True, 'live resource gate required')
            from .automatic_live_admission import validate_live
            require(type(live_receipt) is dict, 'current controller resource observation required')
            validate_live(live_receipt, d, ledger, expected_generation, time.time())
            if d['stage'] == 'full_dev':
                full_used = ledger.get('full_dev_charged_seconds')
                require(type(full_used) in (int, float) and math.isfinite(full_used) and full_used >= 0
                        and full_used + d['seconds'] <= ledger.get('full_dev_limit_seconds', 0),
                        'full development accounting missing or exhausted')
            study['qualified_dispatches'][d['attempt_id']] = deepcopy(d)
            study['reservations'].append({'attempt_id': d['attempt_id'], 'status': 'RUNNING', 'declaration': deepcopy(d)})
            study['status'] = 'ACTIVE'
            ledger['r6_phase0_cpu']['remote_cpu_reserved_seconds'] += d['cpu_seconds']
            db.execute('INSERT INTO attempts VALUES (?,?,NULL)', (d['attempt_id'], encoded(d)))
            db.execute('UPDATE head SET active=?,scope=?,ledger=?', (d['attempt_id'], encoded(scope), encoded(ledger)))
        return {'status': 'CONSUMED_UNRESOLVED', 'attempt_id': d['attempt_id'], 'generation': expected_generation}

    def reconcile(self, *, attempt_id=None, terminal=None, terminal_sha256=None, expected_generation=None):
        require(type(expected_generation) is int and expected_generation >= 0, 'invalid generation')
        require(type(terminal) is dict and digest(terminal_sha256)
                and document_hash(terminal) == terminal_sha256, 'terminal evidence not pinned')
        require(terminal.get('attempt_id') == attempt_id and terminal.get('container_name') == attempt_id,
                'terminal attempt identity mismatch')
        state = terminal.get('container_state', {})
        exited = (state.get('Running') is False and state.get('Pid') == 0
                  and type(state.get('ExitCode')) is int)
        never_started = (terminal.get('container_outcome') == 'NO_CONTAINER'
                         and terminal.get('create_request_sent') is False)
        require(exited or never_started, 'authoritative terminal state required')
        wall = terminal.get('whole_wall_seconds'); calls = terminal.get('known_model_calls')
        require(type(wall) in (int, float) and math.isfinite(wall) and wall >= 0,
                'whole-stage elapsed cost required')
        require(type(calls) is int and calls >= 0 and type(terminal.get('calls_complete')) is bool,
                'explicit known/unknown call accounting required')
        require(digest(terminal.get('cost_evidence_sha256')), 'cost evidence missing')
        cpu_seconds = terminal.get('aggregate_cpu_seconds')
        require(type(cpu_seconds) in (int, float) and math.isfinite(cpu_seconds) and cpu_seconds >= 0,
                'controller plus worker CPU accounting required')
        with self.transaction() as (db, head):
            require(head[1] == expected_generation and head[4] == attempt_id,
                    'stale settlement or active attempt differs')
            row = db.execute('SELECT declaration,terminal FROM attempts WHERE id=?', (attempt_id,)).fetchone()
            require(row is not None and row[1] is None, 'attempt already settled or missing')
            declaration = json.loads(row[0])
            require(document_hash(declaration) == terminal.get('declaration_sha256'), 'terminal declaration changed')
            ledger = json.loads(head[2]); scope = json.loads(head[3]); study = scope['automatic_study']
            reservations = [r for r in study['reservations'] if r['attempt_id'] == attempt_id]
            require(len(reservations) == 1 and reservations[0]['status'] == 'RUNNING'
                    and reservations[0]['declaration'] == declaration, 'reservation mismatch')
            charge = math.ceil(wall)
            cpu = ledger['r6_phase0_cpu']
            require(cpu['remote_cpu_reserved_seconds'] >= declaration['cpu_seconds'], 'CPU reservation missing')
            cpu['remote_cpu_reserved_seconds'] -= declaration['cpu_seconds']
            cpu['remote_cpu_charged_seconds'] += math.ceil(cpu_seconds)
            for used, remaining, cap, delta in (
                ('gpu_conservative_charged_seconds', 'gpu_remaining_seconds', 'gpu_limit_seconds', charge),
                ('fidelity_generation_charged_seconds', 'fidelity_generation_remaining_seconds', 'fidelity_limit_seconds',
                 charge if declaration['stage'] in ('synthetic', 'fidelity') else 0)):
                require(type(ledger.get(used)) in (int, float) and math.isfinite(ledger[used]), 'invalid ledger charge')
                ledger[used] += delta
                # Preserve real overruns; subsequent admission rejects a negative remainder.
                ledger[remaining] = ledger[cap] - ledger[used]
            if declaration['stage'] == 'full_dev':
                require(type(ledger.get('full_dev_charged_seconds')) in (int, float), 'full-dev history missing')
                ledger['full_dev_charged_seconds'] += charge
            require(type(ledger.get('model_calls')) is int, 'historical call count missing')
            ledger['model_calls'] += calls
            ledger['model_calls_count_is_lower_bound'] = ledger.get('model_calls_count_is_lower_bound', False) or not terminal['calls_complete']
            study['stage_costs'][attempt_id] = {'stage': declaration['stage'], 'seconds': charge,
                                               'known_calls': calls, 'calls_complete': terminal['calls_complete']}
            reservations[0]['status'] = 'SETTLED'
            study['status'] = 'IDLE'
            if (charge > declaration['seconds'] or calls > declaration['maximum_calls']
                    or cpu_seconds > declaration['cpu_seconds']):
                study['status'] = 'RESOURCE_OVERRUN_STOP'
            db.execute('UPDATE attempts SET terminal=? WHERE id=?', (encoded(terminal), attempt_id))
            db.execute('UPDATE head SET generation=?,ledger=?,scope=?,active=NULL',
                       (head[1]+1, encoded(ledger), encoded(scope)))
        return {'status': 'RECONCILED', 'generation': expected_generation+1,
                'ledger': ledger, 'scope': scope, 'charged_seconds': charge}
