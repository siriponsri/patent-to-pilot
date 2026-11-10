import importlib.util
from pathlib import Path
import pytest

spec=importlib.util.spec_from_file_location('cap_stop',Path(__file__).resolve().parents[1]/'scripts/healthtech/stop_sacr_at_frozen_review_cap.py')
stop=importlib.util.module_from_spec(spec);spec.loader.exec_module(stop)


def bound(flags):
    return {'counts':{'checked_completed':54,'rejected_profiles':13,'compact_unavailable':0,
        'compact_lexical_flagged':flags-13,'compact_unflagged_only':54-flags},
        'flagged_queries_lower_bound':flags,'full_sample':100,'cap':20}


@pytest.mark.parametrize('n',[19,20])
def test_does_not_stop_at_or_below_cap(n):
    with pytest.raises(ValueError):stop.validate_bound(bound(n))


def test_stops_only_on_consistent_distinct_lower_bound_above_cap():
    assert stop.validate_bound(bound(21))==21
    v=bound(21);v['counts']['checked_completed']=53
    with pytest.raises(ValueError):stop.validate_bound(v)
