import hashlib
import pytest
from patent_to_pilot.research.sg_r6_scoring import query_keys,structured_rankings,fuse
from patent_to_pilot.research.mtm_runtime import InputBoundaryError
from patent_to_pilot.research.sg_relations_v2 import extract_family_v2


def test_distinct_key_parity_and_hand_computed_rrf():
    universe=['A','B','C','D']
    r=structured_rankings(['k1','k2','k1'],{'k1':{'A':'r1','B':'r2'},'k2':{'A':'r3','C':'r4'}},universe)
    assert r['S']==r['G']==['A','B','C']
    assert r['matched_key_counts']=={'A':2,'B':1,'C':1}
    assert fuse(['B','D','A'],r['S'],universe)==['B','A','D','C']
    assert fuse(['B','A'],['A','B'],universe)==['A','B']


def test_structured_rank201_contributes_before_final_cutoff():
    ranking=[f'A{i:03}' for i in range(200)]+['Z']
    assert fuse(['Z'],ranking,ranking)[0]=='Z'
    assert len(fuse(['Z'],ranking,ranking))==200


def test_empty_extraction_keeps_baseline_order_and_denominator():
    text='  No functional cue here.\n'
    assert query_keys('q',text,hashlib.sha256(text.encode()).hexdigest())==[]
    assert fuse(['B','A'],[],['A','B'])==['B','A']


def test_positive_query_preserves_exact_whitespace_mapping_and_hash():
    text='  A pump is configured to transfer water at 5 bar.\n'
    expected=extract_family_v2({'id':'q','title':'','abstract':text,'claims':''})
    keys=query_keys('q',text,hashlib.sha256(text.encode()).hexdigest())
    assert keys==sorted({r['alias_key'] for r in expected['records']}) and len(keys)==1
    with pytest.raises(InputBoundaryError):query_keys('q',text.strip(),hashlib.sha256(text.encode()).hexdigest())


@pytest.mark.parametrize('fault',['hash','duplicate','unknown','posting'])
def test_input_boundary_failures(fault):
    with pytest.raises(InputBoundaryError):
        if fault=='hash':query_keys('q','text','0'*64)
        elif fault=='duplicate':fuse(['A','A'],[],['A'])
        elif fault=='unknown':fuse(['B'],[],['A'])
        else:structured_rankings(['k'],{'k':{'B':'r'}},['A'])
