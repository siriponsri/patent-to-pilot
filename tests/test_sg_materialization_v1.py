import hashlib,json
from pathlib import Path
import pytest
from patent_to_pilot.research.sg_materialization_v1 import materialize,select_pairs
from patent_to_pilot.research.sg_census_runner import config_hash
from patent_to_pilot.research.mtm_runtime import InputBoundaryError

def fixture(tmp_path):
    rows=[{'id':name,'title':'','abstract':'A device is configured to reduce pressure.','claims':''} for name in ['F2','F1']]
    source=tmp_path/'corpus.jsonl';source.write_bytes(b''.join(json.dumps(r).encode()+b'\n' for r in rows))
    return source,dict(expected_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),expected_config_sha256=config_hash(),
         expected_families=2,sample_ids=['F1','F2'],expected_counts={'families_seen':2,'cross_family_pair_key_incidences':1},max_pairs=1)

def test_materializes_exact_sample_and_pairs_no_fidelity(tmp_path):
    source,args=fixture(tmp_path);out=tmp_path/'out';result=materialize(source,out,**args)
    assert result['status']=='COMPLETE_UNSCREENED_ARTIFACTS_NO_EDGES' and result['accepted_edges']==0
    sample=json.loads((out/'alias-sample.json').read_bytes())
    assert sample['sample'][0]['families']==['F1','F2'] and len(sample['witness_records'])==2
    assert result['source_sample_count']==2
    with pytest.raises(FileExistsError):materialize(source,out,**args)

def test_pair_sampling_order_invariant_and_bounded():
    a={'k':{'F2':'r2','F1':'r1','F3':'r3'}}
    b={'k':{'F3':'r3','F1':'r1','F2':'r2'}}
    assert select_pairs(a)==select_pairs(b)
    with pytest.raises(InputBoundaryError):select_pairs(a,max_pairs=2)

@pytest.mark.parametrize('fault',['identity','sample','counts','disk','deadline'])
def test_failure_receipts_preserved_without_retries(tmp_path,fault):
    source,args=fixture(tmp_path);out=tmp_path/'out'
    if fault=='identity':args['expected_sha256']='0'*64
    if fault=='sample':args['sample_ids']=['missing']
    if fault=='counts':args['expected_counts']['cross_family_pair_key_incidences']=2
    if fault=='disk':args['max_output_bytes']=16384
    if fault=='deadline':args['max_seconds']=0
    with pytest.raises((InputBoundaryError,TimeoutError)):materialize(source,out,**args)
    receipt=json.loads((out/'receipt.json').read_bytes())
    assert receipt['status']=='FAILED_NO_RETRY' and receipt['model_calls']==0
