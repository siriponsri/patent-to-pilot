"""Validate controller observations; caller must actually observe the host."""
import math
from .mtm_runtime import InputBoundaryError
from .r6_dispatch_journal import document_hash

GPU = 'GPU-277ccc57-c3e5-0731-cd49-f4f8695f7089'
GPU_STAGES = frozenset(('synthetic', 'fidelity', 'pilot', 'full_dev'))


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
    from .automatic_cpu_booking import cpu_cap, cpu_used
    cpu = ledger.get('r6_phase0_cpu', {})
    cap, used = cpu_cap(cpu), cpu_used(cpu)
    # cpu_seconds is always a worker RLIMIT safety bound. Owner definition:
    # GPU-stage host CPU is telemetry; only CPU-only stages consume the cap.
    reserved = declaration.get('cpu_seconds')
    charged = 0 if declaration.get('stage') in GPU_STAGES else reserved
    require(number(reserved) and reserved > 0 and used + charged <= cap, 'CPU allowance exhausted')
    disk = receipt.get('incremental_disk_bytes'); addition = declaration.get('additional_disk_bytes')
    require(number(disk) and type(addition) is int and addition > 0
            and disk + addition <= ledger.get('disk_limit_bytes_combined_incremental', 0),
            'incremental disk allowance exceeded')
    require(number(receipt.get('free_disk_bytes')) and receipt['free_disk_bytes'] >= addition,
            'physical disk space insufficient')
    return {'status': 'LIVE_OBSERVATION_BOUND', 'cpu_reserved_seconds': charged,
            'cpu_safety_bound_seconds': reserved}
