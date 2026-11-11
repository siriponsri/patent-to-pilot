import copy
import pytest
from patent_to_pilot.research.sacr_r3_runtime_guards import validate_budget, validate_sources
from patent_to_pilot.research.mtm_runtime import InputBoundaryError


def ledger():
    return {'gpu_conservative_charged_seconds':9006.484789591283,
            'gpu_remaining_seconds':259200-9006.484789591283,
            'fidelity_generation_charged_seconds':8727.597964742686,
            'fidelity_generation_remaining_seconds':28800-8727.597964742686}


def test_r3_preserves_r2_cost_floor():
    d=ledger();validate_budget(d,1800)
    for charged,remaining in [('gpu_conservative_charged_seconds','gpu_remaining_seconds'),
                              ('fidelity_generation_charged_seconds','fidelity_generation_remaining_seconds')]:
        bad=copy.deepcopy(d);bad[charged]-=163;bad[remaining]+=163
        with pytest.raises(InputBoundaryError):validate_budget(bad,1800)


def test_missing_new_source_pins_stops_before_loading(tmp_path):
    with pytest.raises(InputBoundaryError):validate_sources(tmp_path,{})
