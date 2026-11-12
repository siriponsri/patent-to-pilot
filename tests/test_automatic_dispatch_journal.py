import json
import sqlite3
import pytest
from patent_to_pilot.research.automatic_dispatch_journal import AutomaticDispatchJournal
from patent_to_pilot.research.r6_dispatch_journal import initialize, document_hash
from patent_to_pilot.research.mtm_runtime import InputBoundaryError


def setup_journal(tmp_path):
    path = tmp_path / 'journal.sqlite'
    ledger = {'gpu_limit_seconds': 691200, 'fidelity_limit_seconds': 230400,
              'full_dev_limit_seconds': 460800, 'disk_limit_bytes_combined_incremental': 40 * 1024**3,
              'human_cards_total_limit_all_benchmarks_all_configurations': 60,
              'gpu_conservative_charged_seconds': 15206}
    scope = {'reservations': [], 'old_failure': 'CALIBRATION_FAILED'}
    initialize(path, 'a' * 64, ledger, scope)
    authority = dict(status='OWNER_APPROVED_AUTOMATIC_DUAL_TRACK', journal_identity='a' * 64,
                     human_review_required=False, semantic_certification=False,
                     owner_approval_sha256='b' * 64, protocol_sha256='c' * 64, policy_sha256='d' * 64,
                     prior_ledger_sha256=document_hash(ledger), prior_scope_sha256=document_hash(scope),
                     prior_attempts_sha256=document_hash([]),
                     unchanged_ledger_caps={k: v for k, v in ledger.items() if k != 'gpu_conservative_charged_seconds'})
    return path, AutomaticDispatchJournal(path, 'a' * 64), authority, ledger, scope


def test_transition_preserves_accounting_and_failure(tmp_path):
    path, journal, a, ledger, scope = setup_journal(tmp_path)
    result = journal.adopt_scope(expected_generation=0, authority=a, authority_sha256=document_hash(a))
    with sqlite3.connect(path) as db:
        generation, raw, stored_scope, active = db.execute('SELECT generation,ledger,scope,active FROM head').fetchone()
    assert generation == 1 and active is None and json.loads(raw) == ledger
    assert json.loads(stored_scope)['old_failure'] == scope['old_failure']
    assert result['status'] == 'ADOPTED_NO_DISPATCH'
    with pytest.raises(InputBoundaryError):
        journal.claim()
    with pytest.raises(InputBoundaryError):
        journal.adopt_scope(expected_generation=0, authority=a, authority_sha256=document_hash(a))


@pytest.mark.parametrize('mutation', ['active', 'unresolved', 'cap', 'pin', 'generation'])
def test_rejects_unsafe_transition_atomically(tmp_path, mutation):
    path, journal, a, _, _ = setup_journal(tmp_path)
    generation = 0
    with sqlite3.connect(path) as db:
        if mutation == 'active':
            db.execute("UPDATE head SET active='old'")
        if mutation == 'unresolved':
            db.execute("INSERT INTO attempts VALUES ('old','{}',NULL)")
    if mutation == 'cap':
        a['unchanged_ledger_caps']['gpu_limit_seconds'] += 1
    if mutation == 'generation':
        generation = 1
    pin = 'f' * 64 if mutation == 'pin' else document_hash(a)
    with pytest.raises(InputBoundaryError):
        journal.adopt_scope(expected_generation=generation, authority=a, authority_sha256=pin)
    with sqlite3.connect(path) as db:
        stored = db.execute('SELECT generation,scope FROM head').fetchone()
    assert stored[0] == 0 and 'automatic_study' not in json.loads(stored[1])


def test_settled_history_preserved_and_readoption_rejected(tmp_path):
    path, journal, a, _, _ = setup_journal(tmp_path)
    rows = [('prior', '{"stage":"calibration"}', '{"failure_axis":"EVALUATOR_CALIBRATION"}')]
    with sqlite3.connect(path) as db:
        db.executemany('INSERT INTO attempts VALUES (?,?,?)', rows)
    a['prior_attempts_sha256'] = document_hash(rows)
    result = journal.adopt_scope(expected_generation=0, authority=a, authority_sha256=document_hash(a))
    with sqlite3.connect(path) as db:
        assert db.execute('SELECT id,declaration,terminal FROM attempts ORDER BY id').fetchall() == rows
    a['prior_scope_sha256'] = document_hash(result['scope'])
    with pytest.raises(InputBoundaryError):
        journal.adopt_scope(expected_generation=1, authority=a, authority_sha256=document_hash(a))
    with pytest.raises(InputBoundaryError):
        journal.reconcile()


@pytest.mark.parametrize('key', ['prior_scope_sha256', 'prior_ledger_sha256', 'prior_attempts_sha256'])
def test_stale_history_hash_rejected(tmp_path, key):
    _, journal, a, _, _ = setup_journal(tmp_path)
    a[key] = 'f' * 64
    with pytest.raises(InputBoundaryError):
        journal.adopt_scope(expected_generation=0, authority=a, authority_sha256=document_hash(a))


def test_append_stage_preserves_authority_and_rejects_same_operation(tmp_path):
    path, journal, authority, ledger, _ = setup_journal(tmp_path)
    authority.update(stage_envelopes={'synthetic': {'seconds': 1800, 'maximum_calls': 2}},
                     configuration_sha256=['b'*64])
    pin = document_hash(authority)
    adopted = journal.adopt_scope(expected_generation=0, authority=authority, authority_sha256=pin)
    d = {'attempt_id': 'ptp-auto-first', 'operation_sha256': 'c'*64, 'stage': 'synthetic',
         'configuration_sha256': 'b'*64, 'seconds': 1800, 'maximum_calls': 2}
    receipt = {'declaration': d, 'authority_sha256': pin, 'ledger_sha256': document_hash(ledger),
               'scope_sha256': document_hash(adopted['scope'])}
    result = journal.qualify_stage(expected_generation=1, receipt=receipt, receipt_sha256=document_hash(receipt))
    assert result['scope']['automatic_study']['authority'] == authority
    assert result['scope']['automatic_study']['qualified_dispatches'][d['attempt_id']] == d
    repeat = dict(receipt, declaration=dict(d, attempt_id='ptp-auto-renamed'),
                  scope_sha256=document_hash(result['scope']))
    with pytest.raises(InputBoundaryError):
        journal.qualify_stage(expected_generation=2, receipt=repeat, receipt_sha256=document_hash(repeat))
    with sqlite3.connect(path) as db:
        assert db.execute('SELECT generation FROM head').fetchone()[0] == 2


def test_only_exact_declared_stage_can_claim_once(tmp_path):
    path, journal, a, ledger, scope = setup_journal(tmp_path)
    ledger.update(gpu_remaining_seconds=691200-15206,
                  model_calls=132, model_calls_count_is_lower_bound=True,
                  fidelity_generation_charged_seconds=100,
                  fidelity_generation_remaining_seconds=230300)
    ledger['r6_phase0_cpu'] = {'cpu_cap_seconds': 28800, 'cpu_prior_upper_bound_seconds': 25000,
        'local_cpu_conservative_charged_seconds': 0, 'local_cpu_measured_seconds': 0,
        'remote_cpu_charged_seconds': 0, 'local_cpu_reserved_seconds': 0, 'remote_cpu_reserved_seconds': 0}
    with sqlite3.connect(path) as db:
        from patent_to_pilot.research.r6_dispatch_journal import encoded
        db.execute('UPDATE head SET ledger=?', (encoded(ledger),))
    a['prior_ledger_sha256'] = document_hash(ledger)
    gates = {name: {'gate': name, 'status': 'PASS', 'package_sha256': 'a'*64,
                    'configuration_sha256': 'b'*64} for name in
             ('integrity', 'isolation', 'runtime', 'resources', 'accounting')}
    gates['accounting']['ledger_sha256'] = document_hash(ledger)
    gates['resources']['live_admission_required'] = True
    d = {'attempt_id': 'ptp-auto-fixture', 'stage': 'synthetic', 'retry': False,
         'cpu_seconds': 30, 'additional_disk_bytes': 1024,
         'maximum_calls': 2, 'seconds': 1800, 'package_sha256': 'a'*64,
         'configuration_sha256': 'b'*64, 'input_manifest_sha256': 'c'*64, 'model_sha256': 'd'*64,
         'gate_receipts': {k: document_hash(v) for k,v in gates.items()}}
    a['qualified_dispatches'] = {d['attempt_id']: d}
    journal.adopt_scope(expected_generation=0, authority=a, authority_sha256=document_hash(a))
    altered = dict(d, maximum_calls=3)
    with pytest.raises(InputBoundaryError):
        journal.claim(declaration=altered, gates=gates, expected_generation=1)
    import time
    from patent_to_pilot.research.automatic_live_admission import GPU
    live = {'observed_unix': time.time(), 'attempt_id': d['attempt_id'], 'generation': 1,
            'ledger_sha256': document_hash(ledger), 'gpu_uuid': GPU, 'gpu_idle': True,
            'owned_jobs_idle': True, 'network_disabled': True, 'protected_mounts_absent': True,
            'cpu_threads': 8, 'aggregate_ram_limit_bytes': 32*1024**3,
            'incremental_disk_bytes': 1000, 'free_disk_bytes': 1000000}
    with pytest.raises(InputBoundaryError):
        journal.claim(declaration=d, gates=gates, expected_generation=1)
    assert journal.claim(declaration=d, gates=gates, expected_generation=1, live_receipt=live)['status'] == 'CONSUMED_UNRESOLVED'
    with pytest.raises(InputBoundaryError):
        journal.claim(declaration=d, gates=gates, expected_generation=1)
    with sqlite3.connect(path) as db:
        assert db.execute('SELECT active FROM head').fetchone()[0] == d['attempt_id']
        assert db.execute('SELECT terminal FROM attempts WHERE id=?', (d['attempt_id'],)).fetchone()[0] is None
    terminal = {'attempt_id': d['attempt_id'], 'container_name': d['attempt_id'],
                'container_state': {'Running': False, 'Pid': 0, 'ExitCode': 1},
                'whole_wall_seconds': 12.2, 'known_model_calls': 1, 'calls_complete': False,
                'aggregate_cpu_seconds': 4.3,
                'cost_evidence_sha256': 'e'*64, 'declaration_sha256': document_hash(d)}
    unknown = dict(terminal, container_state={'Running': True, 'Pid': 123, 'ExitCode': 0})
    with pytest.raises(InputBoundaryError):
        journal.reconcile(attempt_id=d['attempt_id'], terminal=unknown,
                          terminal_sha256=document_hash(unknown), expected_generation=1)
    result = journal.reconcile(attempt_id=d['attempt_id'], terminal=terminal,
                               terminal_sha256=document_hash(terminal), expected_generation=1)
    assert result['charged_seconds'] == 13
    assert result['ledger']['gpu_conservative_charged_seconds'] == 15219
    assert result['ledger']['fidelity_generation_charged_seconds'] == 113
    assert result['ledger']['model_calls'] == 133
    assert result['ledger']['r6_phase0_cpu']['remote_cpu_reserved_seconds'] == 0
    # GPU-stage host CPU is telemetry only (owner definition, 12 Nov 2026).
    assert result['ledger']['r6_phase0_cpu']['remote_cpu_charged_seconds'] == 0
    assert result['ledger']['gpu_stage_host_cpu_telemetry_seconds'] == 4.3
    assert result['scope']['automatic_study']['stage_costs'][d['attempt_id']]['host_cpu_seconds_telemetry'] == 4.3
    assert result['ledger']['model_calls_count_is_lower_bound'] is True
    assert result['scope']['old_failure'] == 'CALIBRATION_FAILED'
    with pytest.raises(InputBoundaryError):
        journal.reconcile(attempt_id=d['attempt_id'], terminal=terminal,
                          terminal_sha256=document_hash(terminal), expected_generation=2)


def test_authority_amendment_adds_revised_configurations_with_owner_cap(tmp_path):
    path, journal, authority, ledger, _ = setup_journal(tmp_path)
    authority.update(stage_envelopes={'synthetic': {'seconds': 1800, 'maximum_calls': 2}},
                     configuration_sha256=['1'*64])
    pin = document_hash(authority)
    state = journal.adopt_scope(expected_generation=0, authority=authority, authority_sha256=pin)['scope']
    gen = 1
    def qualify(attempt, config, op):
        nonlocal state, gen
        d = {'attempt_id': attempt, 'operation_sha256': op*64, 'stage': 'synthetic',
             'configuration_sha256': config*64, 'seconds': 1800, 'maximum_calls': 2}
        r = {'declaration': d, 'authority_sha256': pin, 'ledger_sha256': document_hash(ledger),
             'scope_sha256': document_hash(state)}
        state = journal.qualify_stage(expected_generation=gen, receipt=r, receipt_sha256=document_hash(r))['scope']; gen += 1
    def amend(configs, extra):
        nonlocal state, gen
        r = {'kind': 'AUTHORITY_AMENDMENT', 'owner_approval_sha256': 'e'*64, 'evidence_sha256': 'f'*64,
             'add_configuration_sha256': [c*64 for c in configs], 'additional_synthetic_attempts': extra,
             'authority_sha256': pin, 'ledger_sha256': document_hash(ledger), 'scope_sha256': document_hash(state)}
        state = journal.amend_authority(expected_generation=gen, receipt=r, receipt_sha256=document_hash(r))['scope']; gen += 1
    qualify('ptp-auto-v1', '1', 'a')
    with pytest.raises(InputBoundaryError):          # unapproved revised configuration
        qualify('ptp-auto-v2', '2', 'b')
    with pytest.raises(InputBoundaryError):          # owner cap is 2 additional attempts
        amend(['2', '3', '4'], 3)
    amend(['2', '3'], 2)
    with pytest.raises(InputBoundaryError):          # same configuration never twice
        qualify('ptp-auto-v2', '1', 'b')
    qualify('ptp-auto-v2', '2', 'b')
    qualify('ptp-auto-v3', '3', 'c')
    with pytest.raises(InputBoundaryError):          # allowance exhausted (1 + 2)
        amend(['4'], 0); qualify('ptp-auto-v4', '4', 'd')
    with pytest.raises(InputBoundaryError):          # no further synthetic allowance
        amend(['5'], 1)
    assert state['automatic_study']['authority'] == authority   # root never changes
