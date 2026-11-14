import pytest
from patent_to_pilot.research.automatic_disk_cap import amend_disk_cap, GIB
from patent_to_pilot.research.r6_dispatch_journal import initialize, DispatchJournal, document_hash
from patent_to_pilot.research.mtm_runtime import InputBoundaryError


def _setup(tmp_path):
    ledger = {'gpu_conservative_charged_seconds': 45691.6, 'disk_limit_bytes_combined_incremental': 40 * GIB,
              'r6_phase0_cpu': {'cpu_cap_seconds': 86400}}
    path = tmp_path / 'journal'; initialize(path, 'a' * 64, ledger, {'old_failure': 'FAIL'})
    return DispatchJournal(path, 'a' * 64), ledger


def _receipt(ledger, **change):
    r = {'kind': 'DISK_CAP_AMENDMENT', 'from_bytes': 40 * GIB, 'to_bytes': 52 * GIB, 'owner_approval_sha256': 'b' * 64,
         'model_calls': 0, 'gpu_seconds': 0, 'prior_ledger_sha256': document_hash(ledger)}
    r.update(change); return r


def test_raises_cap_once_without_touching_other_accounting(tmp_path):
    journal, ledger = _setup(tmp_path)
    r = _receipt(ledger)
    out = amend_disk_cap(journal, expected_generation=0, receipt=r, receipt_sha256=document_hash(r))['ledger']
    assert out['disk_limit_bytes_combined_incremental'] == 52 * GIB
    assert out['gpu_conservative_charged_seconds'] == 45691.6 and out['r6_phase0_cpu'] == ledger['r6_phase0_cpu']
    assert out['disk_cap_amendments'][0]['generation'] == 1
    again = _receipt(out)
    with pytest.raises(InputBoundaryError):  # chain exhausted: no second amendment
        amend_disk_cap(journal, expected_generation=1, receipt=again, receipt_sha256=document_hash(again))


@pytest.mark.parametrize('change', [{'to_bytes': 64 * GIB}, {'from_bytes': 41 * GIB}, {'kind': 'CPU_CAP_AMENDMENT'},
                                    {'model_calls': 1}, {'prior_ledger_sha256': 'c' * 64}])
def test_rejects_anything_outside_the_approved_link(tmp_path, change):
    journal, ledger = _setup(tmp_path)
    r = _receipt(ledger, **change)
    with pytest.raises(InputBoundaryError):
        amend_disk_cap(journal, expected_generation=0, receipt=r, receipt_sha256=document_hash(r))


def test_stale_generation_rejected(tmp_path):
    journal, ledger = _setup(tmp_path)
    r = _receipt(ledger)
    with pytest.raises(InputBoundaryError):
        amend_disk_cap(journal, expected_generation=5, receipt=r, receipt_sha256=document_hash(r))
