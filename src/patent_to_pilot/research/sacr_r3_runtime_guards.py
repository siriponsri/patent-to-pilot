"""R3 pin completeness and cumulative non-reset budget floor."""
import hashlib
from .mtm_runtime import InputBoundaryError
from .sacr_r2_runtime_guards import validate_sources as legacy_sources, validate_budget as legacy_budget

REQUIRED = {
    'scripts/healthtech/run_sacr_r3_synthetic_smoke.py',
    'scripts/healthtech/supervise_sacr_r3_synthetic_smoke.py',
    *('src/patent_to_pilot/research/'+name+'.py' for name in (
        'sacr_r3_runtime_guards','sacr_r3_bundle_runner','sacr_evidence_v3',
        'sacr_evidence_prompt_v3','sacr_evidence_review_v3','sacr_views_v3',
        'sacr_generated_evidence_v3','sacr_generated_critic_v3')),
}


def validate_sources(root, hashes):
    if type(hashes) is not dict or not REQUIRED <= set(hashes):
        raise InputBoundaryError('R3 source pins missing')
    legacy_sources(root, hashes)  # Includes all shipped src files and shared dependencies.
    for name in REQUIRED:
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=hashes[name]:
            raise InputBoundaryError('R3 source changed')


def validate_budget(ledger, seconds):
    legacy_budget(ledger, seconds)
    if (ledger['gpu_conservative_charged_seconds'] < 9006.484789591283 - 1e-6
            or ledger['fidelity_generation_charged_seconds'] < 8727.597964742686 - 1e-6):
        raise InputBoundaryError('R2 smoke cost missing from cumulative ledger')
