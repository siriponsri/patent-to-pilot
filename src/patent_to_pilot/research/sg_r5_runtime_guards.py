"""Approved Graph screening allowance inside unchanged cumulative ledgers."""
import math
from .mtm_runtime import InputBoundaryError
from .sacr_r3_runtime_guards import validate_sources as original_sources


def validate_sources(root,hashes):
    original_sources(root,hashes)
    required={'scripts/healthtech/run_sg_r5_screening.py','scripts/healthtech/supervise_sg_r5_screening.py',
              'src/patent_to_pilot/research/sg_screening_runner_v1.py','src/patent_to_pilot/research/literal_critic_contract_v1.py'}
    if not required<=set(hashes):raise InputBoundaryError('Graph screening pins missing')


def validate_budget(ledger,seconds):
    run=ledger.get('r5_long_run',{})
    if seconds!=57600 or run.get('owner_reply')!='call_172d9619b8e64a6781a0ff36fb183240':
        raise InputBoundaryError('approved Graph16h allocation required')
    if run.get('status')!='GRAPH_SCREEN_RESERVED' or run.get('reserved_gpu_seconds')!=seconds or run.get('reserved_fidelity_seconds')!=seconds:
        raise InputBoundaryError('Graph reservation missing')
    for used_key,left_key,cap_key,cap,initial,new_cap in [
        ('gpu_conservative_charged_seconds','gpu_remaining_seconds','gpu_limit_seconds',691200,'initial_gpu_charged_seconds',646200),
        ('fidelity_generation_charged_seconds','fidelity_generation_remaining_seconds','fidelity_limit_seconds',230400,'initial_fidelity_charged_seconds',178200)]:
        used,left=ledger[used_key],ledger[left_key];floor=run[initial]
        if (ledger[cap_key]!=cap or any(type(v) not in (float,int) or not math.isfinite(v) for v in [used,left,floor])
            or used<floor or left<seconds or not math.isclose(used+left,cap,rel_tol=0,abs_tol=1e-6)
            or used-floor+seconds>new_cap):
            raise InputBoundaryError('cumulative or extension allowance exceeded/reset')
