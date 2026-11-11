import hashlib,json
import pytest
from patent_to_pilot.research.sg_fixed_source_attachment import attach_fixed_sources
from patent_to_pilot.research.mtm_runtime import InputBoundaryError


@pytest.mark.parametrize('fault',[None,'hash','missing','duplicate','output','deadline'])
def test_private_attachment_never_substitutes_or_reextracts(tmp_path,fault):
    rows=[{'id':fid,'title':'','abstract':'No extraction cue here.','claims':''} for fid in ['a','b']]
    if fault=='duplicate':rows.append(rows[0])
    raw=b''.join(json.dumps(row).encode()+b'\n' for row in rows)
    source=tmp_path/'corpus';source.write_bytes(raw);out=tmp_path/'out'
    args={'expected_sha256':hashlib.sha256(raw).hexdigest(),'fixed_ids':['b']}
    if fault=='hash':args['expected_sha256']='0'*64
    if fault=='missing':args['fixed_ids']=['missing']
    if fault=='output':args['max_output_bytes']=16384
    if fault=='deadline':args['max_seconds']=0
    if fault:
        with pytest.raises((InputBoundaryError,TimeoutError)):attach_fixed_sources(source,out,**args)
        assert not (out/'sources-private.jsonl').exists()
    else:
        result=attach_fixed_sources(source,out,**args)
        assert result['source_units']==1 and result['extraction']=='NOT_RUN'
        assert json.loads((out/'sources-private.jsonl').read_bytes())['id']=='b'
        with pytest.raises(FileExistsError):attach_fixed_sources(source,out,**args)
