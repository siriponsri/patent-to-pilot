"""Validate controller observations; caller must actually observe the host."""
import math
from .mtm_runtime import InputBoundaryError
from .r6_dispatch_journal import document_hash

GPU = 'GPU-277ccc57-c3e5-0731-cd49-f4f8695f7089'


def validate_live(receipt, declaration, ledger, generation, now):
    def require(value, message):
        if not value: raise InputBoundaryError(message)
    def number(value):
        return type(value) in (int, float) and math.isfinite(value) and value >= 0
    require(number(now) and number(receipt.get('observed_unix'))
            and 0 <= now - receipt['observed_unix'] <= 60, 'stale live resource observation')
    require(receipt.get('attempt_id') == declaration['attempt_id']
            and receipt.get('generation') == generation
            and receipt.get('ledger_sha256') == document_hash(ledger), 'live receipt identity mismatch')
    require(receipt.get('gpu_uuid') == GPU and receipt.get('gpu_idle') is True
            and receipt.get('owned_jobs_idle') is True, 'GPU or owned job not observed idle')
    require(receipt.get('network_disabled') is True and receipt.get('protected_mounts_absent') is True,
            'runtime isolation not confirmed')
    require(type(receipt.get('cpu_threads')) is int and 0 < receipt['cpu_threads'] <= 8
            and type(receipt.get('aggregate_ram_limit_bytes')) is int
            and 0 < receipt['aggregate_ram_limit_bytes'] <= 32*1024**3, 'host resource caps changed')
    cpu = ledger.get('r6_phase0_cpu', {})
    keys = ('cpu_prior_upper_bound_seconds', 'local_cpu_conservative_charged_seconds',
            'local_cpu_measured_seconds', 'remote_cpu_charged_seconds',
            'local_cpu_reserved_seconds', 'remote_cpu_reserved_seconds')
    require(cpu.get('cpu_cap_seconds') == 28800 and all(number(cpu.get(k)) for k in keys),
            'CPU cumulative accounting incomplete')
    reserved = declaration.get('cpu_seconds')
    require(number(reserved) and reserved > 0
            and sum(cpu[k] for k in keys) + reserved <= cpu['cpu_cap_seconds'], 'CPU allowance exhausted')
    disk = receipt.get('incremental_disk_bytes'); addition = declaration.get('additional_disk_bytes')
    require(number(disk) and type(addition) is int and addition > 0
            and disk + addition <= ledger.get('disk_limit_bytes_combined_incremental', 0),
            'incremental disk allowance exceeded')
    require(number(receipt.get('free_disk_bytes')) and receipt['free_disk_bytes'] >= addition,
            'physical disk space insufficient')
    return {'status': 'LIVE_OBSERVATION_BOUND', 'cpu_reserved_seconds': reserved}
