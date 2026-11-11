"""R7 compact-v2 calibration against the unchanged frozen24 semantic gold."""
import json
from pathlib import Path

from .mtm_runtime import InputBoundaryError
from .r6_critic_calibration import fixtures,request,assess
from .r7_reference_runner import preflight_requests,run_reference_cohort,encoded,sha,task
from .sacr_native_fidelity import write_new


def frozen_tasks():
    # Expected verdicts are never inserted into model requests.
    tasks=[]
    for case in fixtures():
        payload=request(case)['payload']
        unit={'query_id':payload['query_id'],
              'source':''.join(u['text'] for u in payload['source_units']),
              'artifacts':{name:''.join(u['text'] for u in units)
                           for name,units in payload['artifact_units'].items()},
              'criteria':payload['criteria'],'scope':payload['scope']}
        tasks.append(task(unit))
    return tasks


def run_calibration(*,destination,tasks_sha256,run_id,invoke,count_tokens,check_admission):
    tasks=frozen_tasks()
    if sha(encoded(tasks))!=tasks_sha256:
        raise InputBoundaryError('frozen calibration request identity changed')
    check_admission('preflight')
    preflight=preflight_requests(tasks,mode='calibration',count_tokens=count_tokens)
    result=run_reference_cohort(destination=destination,tasks=tasks,preflight=preflight,
        mode='calibration',run_id=run_id,invoke=invoke,check_admission=check_admission)
    out=Path(destination)
    if json.loads((out/'result.json').read_bytes())!=result:
        raise InputBoundaryError('calibration completion differs from durable result')
    if result['status']!='SCREENING_COMPLETE_NOT_FIDELITY' or len(result['results'])!=24:
        score={'status':'CALIBRATION_NOT_ASSESSABLE','reason':'INCOMPLETE_OR_INPUT_GATE',
               'native_fidelity_proven':False}
    else:
        for index,row in enumerate(result['results']):
            raw=(out/f'unit-{index:03}'/'generation.json').read_bytes()
            if sha(raw)!=row['generation_sha256'] or json.loads(raw)['text']!=row['critic_text']:
                raise InputBoundaryError('calibration raw output identity mismatch')
        score=assess([{'case_id':row['query_id'],'critic_text':row['critic_text']} for row in result['results']])
        rejected=sum(row['reason']!='VALID_CRITIC' for row in result['results'])
        score['execution_rejected_cases']=rejected
        if rejected:score['status']='CALIBRATION_FAILED'
    receipt={'status':score['status'],'assessment':score,'run_id':run_id,
             'tasks_sha256':tasks_sha256,'cohort_result_sha256':sha((out/'result.json').read_bytes()),
             'events':result['events'],'costs':result['costs'],
             'native_fidelity_proven':False,'independent_expert_review':False,'retry':False}
    write_new(out/'calibration-assessment.json',receipt)
    return receipt
