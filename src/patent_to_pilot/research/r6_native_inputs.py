"""Full-source native100 input admission, without generation or label access."""
import hashlib
import json
from copy import deepcopy
from pathlib import Path

from .mtm_runtime import InputBoundaryError
from .r6_cohort import digest,native_manifest
from .sacr_native_fidelity import bind_sample
from .sacr_r6_candidate import build_messages,proposal_schema
from .sacr_prompts import build_messages as generic_messages


def fixed_native_rows(query_bytes,sample_bytes,*,query_sha256,sample_sha256):
    entries=bind_sample(query_bytes,sample_bytes,query_sha256=query_sha256,sample_sha256=sample_sha256)
    return [{'query_id':query_id,'source':source} for query_id,source,_ in entries]


def preflight_native(rows,*,manifest_sha256,prompt_root,generic_prompt_sha256,
                     count_tokens,check_admission):
    rows=native_manifest(rows,manifest_sha256)
    units=[]
    for index,row in enumerate(rows):
        check_admission(index)
        generic=generic_messages(prompt_root=Path(prompt_root),kind='generic',
            query_id=row['query_id'],input_kind='DAPFAM_TA',source=row['source'])
        if generic['prompt_sha256']!=generic_prompt_sha256:
            raise InputBoundaryError('native generic prompt changed')
        profile=build_messages(row['source'],row['query_id'])
        schema=proposal_schema(row['source'],row['query_id'])
        counts={};hashes={}
        for stage,messages in [('profile',profile),('generic',generic['messages'])]:
            supplied=deepcopy(messages)
            count=count_tokens(supplied)
            if supplied!=messages or type(count) is not int or count<1:
                raise InputBoundaryError('native exact token counter contract')
            counts[stage]=count;hashes[stage]=digest(messages)
        units.append({'query_id':row['query_id'],
            'source_sha256':hashlib.sha256(row['source'].encode()).hexdigest(),
            'messages_sha256':hashes,'profile_schema_sha256':digest(schema),
            'input_tokens':counts,'status':'INPUT_LIMIT' if max(counts.values())>8192 else 'ADMITTED'})
    risks=sum(unit['status']!='ADMITTED' for unit in units)
    return {'status':'STOPPED_INPUT_RISK_CAP' if risks>20 else 'INPUT_PREFLIGHT_COMPLETE',
        'manifest_sha256':manifest_sha256,'units':units,'risk_units':risks,'fixed_denominator':100,
        'model_calls':0,'semantic_pass':False,'retry':False,
        'critic_input_admission':'REQUIRES_ACTUAL_GENERATED_VIEWS_BEFORE_EACH_CRITIC_CALL'}
