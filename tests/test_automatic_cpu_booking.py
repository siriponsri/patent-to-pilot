import pytest
from patent_to_pilot.research.automatic_cpu_booking import book_cpu
from patent_to_pilot.research.r6_dispatch_journal import initialize, DispatchJournal, document_hash
from patent_to_pilot.research.mtm_runtime import InputBoundaryError


def test_cpu_debit_preserves_other_ledger_and_cannot_replay(tmp_path):
    ledger={'gpu_charged':123,'r6_phase0_cpu':{'cpu_cap_seconds':28800,'cpu_prior_upper_bound_seconds':25000,
        'local_cpu_conservative_charged_seconds':0,'local_cpu_measured_seconds':0,'remote_cpu_charged_seconds':0,
        'local_cpu_reserved_seconds':0,'remote_cpu_reserved_seconds':0}}
    path=tmp_path/'journal'; initialize(path,'a'*64,ledger,{'old_failure':'FAIL'})
    journal=DispatchJournal(path,'a'*64)
    receipt={'model_calls':0,'gpu_seconds':0,'owner_approval_sha256':'b'*64,'evidence_sha256':'c'*64,
             'conservative_cpu_seconds':600,'booking_id':'grammar','location':'remote',
             'prior_ledger_sha256':document_hash(ledger)}
    result=book_cpu(journal,expected_generation=0,receipt=receipt,receipt_sha256=document_hash(receipt))
    assert result['ledger']['gpu_charged']==123
    assert result['ledger']['r6_phase0_cpu']['remote_cpu_charged_seconds']==600
    receipt['prior_ledger_sha256']=document_hash(result['ledger'])
    with pytest.raises(InputBoundaryError):
        book_cpu(journal,expected_generation=1,receipt=receipt,receipt_sha256=document_hash(receipt))


from patent_to_pilot.research.automatic_cpu_booking import (
    amend_cpu_cap_and_book_preparation, cpu_cap, GPU_STAGE_HOST_CPU)
from patent_to_pilot.research.automatic_live_admission import validate_live, GPU


def _base_ledger(prior=23448.0):
    return {'gpu_charged': 9, 'disk_limit_bytes_combined_incremental': 40*1024**3,
            'r6_phase0_cpu': {'cpu_cap_seconds': 28800, 'cpu_prior_upper_bound_seconds': prior,
        'local_cpu_conservative_charged_seconds': 1600, 'local_cpu_measured_seconds': 121.03125,
        'remote_cpu_charged_seconds': 423.81512781, 'local_cpu_reserved_seconds': 0,
        'remote_cpu_reserved_seconds': 0}}


def _amendment(ledger, **change):
    receipt = {'kind': 'CPU_CAP_AMENDMENT_AND_PREPARATION_UPPER_BOUND', 'from_seconds': 28800,
               'to_seconds': 57600, 'basis': 'UPPER_BOUND_NOT_MEASURED',
               'gpu_stage_host_cpu': GPU_STAGE_HOST_CPU, 'model_calls': 0, 'gpu_seconds': 0,
               'location': 'local', 'owner_approval_sha256': 'b'*64, 'evidence_sha256': 'c'*64,
               'window_start_unix': 1000.5, 'window_end_unix': 2798.7, 'logical_cpus': 12,
               'upper_bound_seconds': 1799*12, 'booking_id': 'automatic-prep-window',
               'prior_ledger_sha256': document_hash(ledger)}
    receipt.update(change)
    return receipt


def _journal(tmp_path, ledger):
    path = tmp_path/'journal'; initialize(path, 'a'*64, ledger, {'old_failure': 'FAIL'})
    return DispatchJournal(path, 'a'*64)


def test_amendment_raises_cap_books_upper_bound_once_without_reset(tmp_path):
    ledger = _base_ledger(); journal = _journal(tmp_path, ledger)
    receipt = _amendment(ledger)
    result = amend_cpu_cap_and_book_preparation(journal, expected_generation=0, receipt=receipt,
                                                receipt_sha256=document_hash(receipt))
    cpu = result['ledger']['r6_phase0_cpu']
    assert cpu['cpu_cap_seconds'] == 57600 and cpu_cap(cpu) == 57600
    assert cpu['cpu_prior_upper_bound_seconds'] == 23448.0      # no reset
    assert cpu['remote_cpu_charged_seconds'] == 423.81512781
    assert cpu['local_cpu_conservative_charged_seconds'] == 1600 + 21588
    assert cpu['upper_bound_bookings'][0]['basis'] == 'UPPER_BOUND_NOT_MEASURED'
    assert cpu['gpu_stage_host_cpu'] == GPU_STAGE_HOST_CPU
    assert result['ledger']['gpu_charged'] == 9
    assert abs(result['remaining_seconds'] - (57600 - 25592.84637781 - 21588)) < 1e-6
    again = _amendment(result['ledger'])
    with pytest.raises(InputBoundaryError):  # replay / second amendment
        amend_cpu_cap_and_book_preparation(journal, expected_generation=1, receipt=again,
                                           receipt_sha256=document_hash(again))


@pytest.mark.parametrize('change', [
    {'upper_bound_seconds': 14400},                 # estimate is not the physical bound
    {'basis': 'ESTIMATED_NOT_MEASURED'},
    {'to_seconds': 86400},
    {'logical_cpus': 0},
    {'window_end_unix': 999.0},
    {'gpu_stage_host_cpu': 'CHARGED'},
    {'prior_ledger_sha256': 'f'*64},
])
def test_amendment_rejects_altered_receipts(tmp_path, change):
    ledger = _base_ledger(); journal = _journal(tmp_path, ledger)
    receipt = _amendment(ledger, **change)
    with pytest.raises(InputBoundaryError):
        amend_cpu_cap_and_book_preparation(journal, expected_generation=0, receipt=receipt,
                                           receipt_sha256=document_hash(receipt))


def test_amendment_refuses_bound_that_exceeds_amended_cap(tmp_path):
    ledger = _base_ledger(prior=40000.0); journal = _journal(tmp_path, ledger)
    receipt = _amendment(ledger)
    with pytest.raises(InputBoundaryError):
        amend_cpu_cap_and_book_preparation(journal, expected_generation=0, receipt=receipt,
                                           receipt_sha256=document_hash(receipt))


def test_unbacked_cap_change_is_rejected():
    cpu = dict(_base_ledger()['r6_phase0_cpu'], cpu_cap_seconds=57600)
    with pytest.raises(InputBoundaryError):
        cpu_cap(cpu)


def test_gpu_stage_admission_does_not_consume_cpu_cap_but_cpu_stage_does():
    ledger = _base_ledger(prior=28000.0)          # used 30144.85 > 28800 only if amended cap
    cpu = ledger['r6_phase0_cpu']
    cpu.update(cpu_cap_seconds=57600, cap_amendments=[{'from_seconds': 28800, 'to_seconds': 57600,
               'owner_approval_sha256': 'b'*64, 'receipt_sha256': 'c'*64}])
    live = {'observed_unix': 100, 'attempt_id': 'ptp-auto-x', 'generation': 6,
            'ledger_sha256': document_hash(ledger), 'gpu_uuid': GPU, 'gpu_idle': True,
            'owned_jobs_idle': True, 'network_disabled': True, 'protected_mounts_absent': True,
            'cpu_threads': 8, 'aggregate_ram_limit_bytes': 32*1024**3,
            'incremental_disk_bytes': 0, 'free_disk_bytes': 10**9}
    gpu = {'attempt_id': 'ptp-auto-x', 'stage': 'full_dev', 'cpu_seconds': 40000,
           'additional_disk_bytes': 1024}
    assert validate_live(live, gpu, ledger, 6, 110)['cpu_reserved_seconds'] == 0
    cpu_only = dict(gpu, stage='cpu_grammar')
    with pytest.raises(InputBoundaryError):
        validate_live(live, cpu_only, ledger, 6, 110)
    assert validate_live(live, dict(cpu_only, cpu_seconds=600), ledger, 6, 110)['cpu_reserved_seconds'] == 600


def test_second_cap_link_follows_exact_chain_once(tmp_path):
    from patent_to_pilot.research.automatic_cpu_booking import amend_cpu_cap
    ledger = _base_ledger(); journal = _journal(tmp_path, ledger)
    first = _amendment(ledger)
    out = amend_cpu_cap_and_book_preparation(journal, expected_generation=0, receipt=first, receipt_sha256=document_hash(first))
    def link(led, frm, to):
        return {'kind': 'CPU_CAP_AMENDMENT', 'owner_approval_sha256': 'd'*64, 'model_calls': 0,
                'from_seconds': frm, 'to_seconds': to, 'prior_ledger_sha256': document_hash(led)}
    with pytest.raises(InputBoundaryError):           # not the approved next link
        r = link(out['ledger'], 57600, 100000); amend_cpu_cap(journal, expected_generation=1, receipt=r, receipt_sha256=document_hash(r))
    r = link(out['ledger'], 57600, 86400)
    res = amend_cpu_cap(journal, expected_generation=1, receipt=r, receipt_sha256=document_hash(r))
    cpu = res['ledger']['r6_phase0_cpu']
    assert cpu_cap(cpu) == 86400 and cpu['local_cpu_conservative_charged_seconds'] == 1600 + 21588
    assert len(cpu['cap_amendments']) == 2
    with pytest.raises(InputBoundaryError):           # chain exhausted / replay
        r2 = link(res['ledger'], 57600, 86400); amend_cpu_cap(journal, expected_generation=2, receipt=r2, receipt_sha256=document_hash(r2))
