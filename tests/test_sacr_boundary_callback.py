import pytest
from patent_to_pilot.research.sacr_boundary_callback import boundary_token_records
from patent_to_pilot.research.mtm_runtime import InputBoundaryError


def test_fused_string_end_and_escapes_selected_without_full_vocabulary():
    values=['plain','.', 'end"', '.",', '\\', 'a\\n', '\n', 'x\r', '\\"']
    records=[(i,text,False) for i,text in enumerate(values)]
    result=dict(boundary_token_records(records))
    assert 3 in result and result[3]=='.",'
    assert 0 not in result and 1 not in result and 2 not in result
    assert set(result)==set(range(3,len(values)))


def test_boundary_vocabulary_ceiling_stops_before_model():
    with pytest.raises(InputBoundaryError):
        boundary_token_records([(i,'\\',False) for i in range(20001)])
