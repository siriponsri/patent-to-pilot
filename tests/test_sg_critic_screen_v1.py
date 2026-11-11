import hashlib,json
from patent_to_pilot.research.sg_critic_screen_v1 import units,request,screen_record
from patent_to_pilot.research.sacr_fidelity_screen import DIMENSIONS
from test_sg_sample_integrity import samples


def test_units_keep_empty_source_units_and_fixed_pair_population():
    source,alias=samples();alias['representative_policy']='MIN_RELATION_ID_PER_FAMILY_KEY'
    rows=[{'id':fid,'title':'','abstract':'A valve is configured to reduce pressure below 40 kPa.','claims':''} for fid in source['records_by_family']]
    source['records_by_family']['F000']=[]
    result=units(rows,source,alias)
    assert len(result)==200 and result[0]['record_count']==0
    assert result[0]['source'] and result[0]['artifacts']['extracted_records']=='[]'
    assert result[100]['unit_type']=='alias' and result[100]['scope']['full_family_source']=='NOT_PROVIDED'
    assert 'Empty output is supported only' in result[0]['criteria']['essential_coverage']


def test_completed_invalid_critic_is_risk_not_salvaged():
    unit={'query_id':'q','source':'source','artifacts':{'record':'candidate'},'criteria':{},'scope':{}}
    assert screen_record({'status':'INPUT_LIMIT'},unit)['status']=='RISK'
    assert screen_record({'status':'EOS_COMPLETE','text':'{"bad":1}'},unit)['status']=='RISK'
    r={'query_id':'q','source_sha256':hashlib.sha256(b'source').hexdigest(),
       'dimensions':{d:'supported' for d in DIMENSIONS},'findings':[]}
    result=screen_record({'status':'EOS_COMPLETE','text':json.dumps(r)},unit)
    assert result['status']=='SCREENING_PASS' and not result['semantic_pass']
    assert len(request(unit))==2
