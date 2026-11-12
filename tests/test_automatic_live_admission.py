from copy import deepcopy
import pytest
from patent_to_pilot.research.automatic_live_admission import validate_live, GPU
from patent_to_pilot.research.r6_dispatch_journal import document_hash
from patent_to_pilot.research.mtm_runtime import InputBoundaryError


@pytest.mark.parametrize('bad', ['stale', 'busy', 'ram', 'cpu', 'disk', 'identity', 'none'])
def test_live_admission_requires_actual_bounded_fields(bad):
    ledger = {'r6_phase0_cpu': {'cpu_cap_seconds': 28800, 'cpu_prior_upper_bound_seconds': 25000,
        'local_cpu_conservative_charged_seconds': 0, 'local_cpu_measured_seconds': 0,
        'remote_cpu_charged_seconds': 0, 'local_cpu_reserved_seconds': 0, 'remote_cpu_reserved_seconds': 0},
        'disk_limit_bytes_combined_incremental': 40*1024**3}
    d = {'attempt_id': 'ptp-auto-test', 'cpu_seconds': 60, 'additional_disk_bytes': 1024}
    r = {'observed_unix': 100, 'attempt_id': d['attempt_id'], 'generation': 6,
        'ledger_sha256': document_hash(ledger), 'gpu_uuid': GPU, 'gpu_idle': True,
        'owned_jobs_idle': True, 'network_disabled': True, 'protected_mounts_absent': True,
        'cpu_threads': 8, 'aggregate_ram_limit_bytes': 32*1024**3,
        'incremental_disk_bytes': 1000, 'free_disk_bytes': 100000}
    if bad == 'stale': r['observed_unix'] = 0
    if bad == 'busy': r['gpu_idle'] = False
    if bad == 'ram': r['aggregate_ram_limit_bytes'] += 1
    if bad == 'cpu': d['cpu_seconds'] = 5000
    if bad == 'disk': r['free_disk_bytes'] = 100
    if bad == 'identity': r['generation'] = 5
    if bad == 'none':
        assert validate_live(r, d, ledger, 6, 110)['status'] == 'LIVE_OBSERVATION_BOUND'
    else:
        with pytest.raises(InputBoundaryError): validate_live(r, d, ledger, 6, 110)
