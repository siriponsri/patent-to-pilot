import json
import pytest
from patent_to_pilot.research.sacr_boundary_callback_v2 import boundary_token_records
from patent_to_pilot.research.mtm_runtime import InputBoundaryError


def test_only_cache_omissions_outside_existing_roots():
    strings=['plain','end"','.', '.",','\\','\\"','a\\n','a\\"b','a\n','\n','",','x\\q','x\\']
    selected=dict(boundary_token_records([(i,s,False) for i,s in enumerate(strings)]))
    assert selected=={3:'.",',8:'a\n',9:'\n',11:'x\\q'}


def test_each_selected_token_is_omitted_by_pinned_cache_and_needs_extra_root():
    strings=['a",','a\\q','\\q','"x','good','a\\n','\r']
    for _,text in boundary_token_records([(i,s,False) for i,s in enumerate(strings)]):
        assert text[0] not in ('"','\\')
        with pytest.raises(json.JSONDecodeError):json.loads('"'+text+'"')


def test_ceiling_is_checked_before_dispatch():
    with pytest.raises(InputBoundaryError):boundary_token_records([(i,'.",',False) for i in range(20001)])
