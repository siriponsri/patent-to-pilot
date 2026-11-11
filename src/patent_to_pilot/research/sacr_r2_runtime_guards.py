"""Pre-load R2 source completeness and cumulative budget checks."""
import hashlib
import math

from .mtm_runtime import InputBoundaryError

REQUIRED = {
    'scripts/healthtech/run_sacr_r2_synthetic_smoke.py',
    'scripts/healthtech/supervise_sacr_r2_synthetic_smoke.py',
    'scripts/healthtech/inspect_qwen_weight_identity.py',
    'src/patent_to_pilot/healthtech/local_execution.py',
    'docs/healthtech/audits/ptp-method-first-r2-weights-20261110/identity.json',
    *('src/patent_to_pilot/research/'+n+'.py' for n in (
        'sacr_r2_runtime_guards','sacr_r2_bundle_runner','sacr_generated_token_profile',
        'sacr_token_profile','sacr_schema','sacr_compact_v2','sacr_generation',
        'sacr_generation_receipt','sacr_fidelity_bundle','sacr_fidelity_screen',
        'sacr_profile','sacr_prompts','sacr_outcomes','sacr_native_fidelity',
        'sacr_generated_profile','sacr_generated_view','sacr_components','sacr_views',
        'sacr_alphabet','sacr_escape_callback','sacr_grammar_guard','mtm_runtime')),
    *('docs/healthtech/research/prompts/'+n+'.txt' for n in (
        'sacr_profile_tokens_v1','sacr_generic_views_v0','sacr_selective_v0','sacr_fidelity_screen_v1')),
}


def validate_sources(root, hashes):
    root=root.resolve()
    # Every shipped package source is pinned, including transitive dependencies.
    required=REQUIRED | {p.relative_to(root).as_posix() for p in (root/'src').rglob('*.py')}
    if type(hashes) is not dict or not required <= set(hashes):
        raise InputBoundaryError('mandatory runtime source pins missing')
    for name,expected in hashes.items():
        p=(root/name).resolve()
        if not p.is_relative_to(root) or hashlib.sha256(p.read_bytes()).hexdigest()!=expected:
            raise InputBoundaryError('runtime source bytes changed')


def validate_budget(ledger, seconds):
    if type(seconds) is not int or not 0 < seconds <= 1800:
        raise InputBoundaryError('invalid smoke allocation')
    for charged_key,remaining_key,cap,minimum in (
        ('gpu_conservative_charged_seconds','gpu_remaining_seconds',259200,8843.154638132546),
        ('fidelity_generation_charged_seconds','fidelity_generation_remaining_seconds',28800,8564.26781328395)):
        charged,remaining=ledger[charged_key],ledger[remaining_key]
        if (any(type(v) not in (int,float) or not math.isfinite(v) for v in (charged,remaining))
                or charged<minimum or remaining<seconds or charged>cap
                or not math.isclose(charged+remaining,cap,rel_tol=0,abs_tol=1e-6)):
            raise InputBoundaryError('cumulative budget arithmetic or prior cost invalid')
