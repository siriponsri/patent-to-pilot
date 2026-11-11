import hashlib
import json
from copy import deepcopy
import pytest
from patent_to_pilot.research.sg_relations_v2 import extract_family_v2
from patent_to_pilot.research.sg_materialization_v1 import SALT
from patent_to_pilot.research.sg_sample_integrity import check_samples
from patent_to_pilot.research.mtm_runtime import InputBoundaryError


def samples():
    records={f'F{i:03}':extract_family_v2({'id':f'F{i:03}','title':'','abstract':'A valve is configured to reduce pressure below 40 kPa.','claims':''})['records'] for i in range(101)}
    pairs=[]; witnesses={}
    for i in range(1,101):
        left,right=records['F000'][0],records[f'F{i:03}'][0]
        members=[left['family_id'],right['family_id']]; key=left['alias_key']
        canonical=json.dumps([key,*members],ensure_ascii=False,separators=(',',':'))
        pairs.append({'families':members,'alias_key':key,'relation_ids':[left['relation_id'],right['relation_id']],
                      'sampling_sha256':hashlib.sha256((SALT+canonical).encode()).hexdigest()})
        witnesses.update({r['relation_id']:r for r in [left,right]})
    return {'no_substitution':True,'records_by_family':dict(list(records.items())[:100])}, {
        'salt':SALT,'sample':sorted(pairs,key=lambda p:p['sampling_sha256']),
        'witness_records':witnesses,'uses_queries_qrels_retrieval_scores':False}


def test_integrity_is_not_semantic_acceptance():
    source,alias=samples(); result=check_samples(source,alias)
    assert result['accepted_edges']==0 and result['semantic_fidelity']=='NOT_ASSESSED'


@pytest.mark.parametrize('fault',['offset','text','alias','witness','sample','accepted','relation-id','source-hash','field'])
def test_corruption_stops(fault):
    source,alias=deepcopy(samples()); row=source['records_by_family']['F000'][0]
    if fault=='offset':row['action_span']['start']=-1
    elif fault=='text':row['operand_span']['text']='wrong'
    elif fault=='alias':row['alias_key']='wrong'
    elif fault=='witness':alias['sample'][0]['families']=['FA','FB']
    elif fault=='sample':alias['sample'].reverse()
    elif fault=='accepted':row['semantic_status']='ACCEPTED'
    elif fault=='relation-id':row['relation_id']='0'*64
    elif fault=='source-hash':row['source_sha256']='invalid'
    else:row['source_field']='private-label'
    with pytest.raises(InputBoundaryError):check_samples(source,alias)


def test_conflicting_same_id_body_rejected():
    source,alias=samples()
    source=deepcopy(source) # Independent artifact objects, same relation IDs.
    source['records_by_family']['F000'][0]['condition_policy']='changed'
    with pytest.raises(InputBoundaryError,match='conflicting relation body'):check_samples(source,alias)
