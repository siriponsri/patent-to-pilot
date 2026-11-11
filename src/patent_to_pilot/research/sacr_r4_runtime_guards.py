"""R4 owner-amended cumulative caps; historical guards remain immutable."""
import math
from .mtm_runtime import InputBoundaryError
from .sacr_r3_runtime_guards import validate_sources as previous_sources

def validate_sources(root,hashes):
    previous_sources(root,hashes)
    required={'scripts/healthtech/run_sacr_r4_synthetic_smoke.py',
              'scripts/healthtech/supervise_sacr_r4_engine.py'}
    if not required<=set(hashes):raise InputBoundaryError('R4 runtime pins missing')

def validate_budget(ledger,seconds):
    if type(seconds) is not int or not 0<seconds<=1800:
        raise InputBoundaryError('invalid R4 smoke allocation')
    amendment=ledger.get('r4_budget_amendment',{})
    if amendment.get('owner_reply')!='call_c4ec345a29784975ab45f71412715d87' or amendment.get('status')!='APPROVED':
        raise InputBoundaryError('R4 budget approval missing')
    for charge,remain,cap_key,cap,floor in [
        ('gpu_conservative_charged_seconds','gpu_remaining_seconds','gpu_limit_seconds',691200,9326.788862183224),
        ('fidelity_generation_charged_seconds','fidelity_generation_remaining_seconds','fidelity_limit_seconds',230400,9047.902037334628)]:
        used,left=ledger[charge],ledger[remain]
        if (ledger.get(cap_key)!=cap or any(type(v) not in (int,float) or not math.isfinite(v) for v in [used,left])
                or used<floor-1e-6 or left<seconds or used>cap or not math.isclose(used+left,cap,abs_tol=1e-6,rel_tol=0)):
            raise InputBoundaryError('R4 cumulative budget invalid or reset')
