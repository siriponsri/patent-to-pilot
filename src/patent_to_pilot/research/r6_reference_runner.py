"""Shared calibrated-critic execution for frozen24 and Graph114 manifests."""
from copy import deepcopy
import hashlib,json
from pathlib import Path
from jsonschema.exceptions import ValidationError
from .mtm_runtime import InputBoundaryError
from .sacr_generation import GenerationLimits
from .sacr_generation_receipt import bind_generation_record
from .sacr_native_fidelity import write_new
from .sacr_outcomes import summarize_costs
from .reference_critic_v1 import interpret


def encoded(v):return json.dumps(v,ensure_ascii=False,sort_keys=True).encode()
def sha(raw):return hashlib.sha256(raw).hexdigest()


def preflight_requests(tasks,*,mode,count_tokens):
    if mode not in ('calibration','graph') or len(tasks)!=(24 if mode=='calibration' else 114):
        raise InputBoundaryError('fixed reference cohort count')
    tasks=deepcopy(tasks);ids=[r['prepared']['payload']['query_id'] for r in tasks]
    if len(ids)!=len(set(ids)):raise InputBoundaryError('duplicate reference task')
    rows=[]
    for task in tasks:
        messages=deepcopy(task['prepared']['messages']);before=encoded(messages)
        count=count_tokens(messages)
        if encoded(messages)!=before or type(count) is not int or count<1:
            raise InputBoundaryError('mutated or invalid tokenizer preflight')
        rows.append({'query_id':task['prepared']['payload']['query_id'],'input_tokens':count,
            'status':'INPUT_LIMIT' if count>8192 else 'ADMITTED','messages_sha256':sha(before)})
    risks=sum(r['status']=='INPUT_LIMIT' for r in rows)
    return {'status':'STOP_INPUT_GATE' if (risks>20 if mode=='graph' else risks>0) else 'ADMITTED',
        'mode':mode,'tasks_sha256':sha(encoded(tasks)),'rows':rows,'input_limit_units':risks,'model_calls':0}


def run_reference_cohort(*,destination,tasks,preflight,mode,run_id,invoke,check_admission):
    tasks=deepcopy(tasks);preflight=deepcopy(preflight)
    if (preflight.get('tasks_sha256')!=sha(encoded(tasks)) or preflight.get('mode')!=mode
            or mode not in ('calibration','graph') or len(tasks)!=(24 if mode=='calibration' else 114)
            or len(preflight.get('rows',[]))!=len(tasks)):
        raise InputBoundaryError('reference preflight identity mismatch')
    for task,row in zip(tasks,preflight['rows']):
        if (row['query_id']!=task['prepared']['payload']['query_id']
                or row['messages_sha256']!=sha(encoded(task['prepared']['messages']))
                or type(row['input_tokens']) is not int or row['input_tokens']<1
                or row['status']!=('INPUT_LIMIT' if row['input_tokens']>8192 else 'ADMITTED')):
            raise InputBoundaryError('reference request admission changed')
    initial=sum(row['status']=='INPUT_LIMIT' for row in preflight['rows'])
    stopped=initial>20 if mode=='graph' else initial>0
    if preflight['input_limit_units']!=initial or preflight['status']!=('STOP_INPUT_GATE' if stopped else 'ADMITTED'):
        raise InputBoundaryError('reference preflight outcome changed')
    out=Path(destination);out.mkdir(parents=True,exist_ok=False)
    write_new(out/'input-preflight.json',preflight)
    events=[];results=[];active=None;risks=initial;limits=GenerationLimits()
    def finish(status):
        result={'status':status,'mode':mode,'fixed_denominator':len(tasks),'results':results,'events':events,
            'costs':summarize_costs(events),'risk_units':risks,'initial_input_risks':initial,
            'semantic_pass':False,'accepted_edges':0,'retry':False}
        write_new(out/'result.json',result);return result
    if stopped:return finish('STOP_INPUT_GATE')
    try:
        for index,(task,admission) in enumerate(zip(tasks,preflight['rows'])):
            query_id=admission['query_id'];request=task['prepared']
            if admission['status']=='INPUT_LIMIT':
                results.append({'query_id':query_id,'status':'UNASSESSABLE','reason':'INPUT_LIMIT','model_calls':0});continue
            check_admission(index);active=index;path=out/f'unit-{index:03}'
            messages=deepcopy(request['messages']);schema=deepcopy(request['schema'])
            before=encoded(messages);schema_before=encoded(schema)
            metrics=invoke(f'reference-{index:03}',path,messages,schema)
            if encoded(messages)!=before or encoded(schema)!=schema_before:raise InputBoundaryError('reference request mutated')
            reservation=json.loads((path/'reservation.json').read_bytes())
            if (reservation.get('status')!='RESERVED' or reservation.get('retry') is not False
                    or reservation.get('messages_sha256')!=sha(before) or reservation.get('limits')!=limits.__dict__):
                raise InputBoundaryError('reference reservation mismatch')
            raw=(path/'generation.json').read_bytes()
            binding=bind_generation_record(raw,expected_sha256=sha(raw),limits=limits,metrics=metrics)
            if binding['record']['input_tokens']!=admission['input_tokens']:
                raise InputBoundaryError('reference exact token count mismatch')
            event={'event_id':sha(encoded([run_id,query_id,'critic'])),'query_id':query_id,'stage':'critic','status':'COMPLETED','metrics':metrics}
            summarize_costs(events+[event]);write_new(path/'cost.json',event);events.append(event);active=None
            record=binding['record'];result={'query_id':query_id,'status':'UNASSESSABLE','reason':record['status']}
            if record['status']=='EOS_COMPLETE':
                try:
                    review=interpret(record['text'].encode(),request)
                    result.update(status='AUTOMATIC_UNFLAGGED' if review['method_screen']=='UNFLAGGED' else 'AUTOMATIC_METHOD_FLAG',reason='VALID_CRITIC',review=review)
                except (InputBoundaryError,UnicodeError,ValidationError):result['reason']='INVALID_EVALUATOR'
            result['critic_text']=record['text'];result['generation_sha256']=sha(raw)
            write_new(path/'screening.json',result);results.append(result)
            risks+=result['status']!='AUTOMATIC_UNFLAGGED'
            if mode=='graph' and risks>20:return finish('STOP_RISK_CAP')
        return finish('SCREENING_COMPLETE_NOT_FIDELITY')
    except BaseException as error:
        write_new(out/'failure.json',{'status':'INFRA_OR_INTEGRITY_STOP','exception_type':type(error).__name__,
            'active_index':active,'known_events':events,'unknown_attempt':active is not None,'retry':False})
        raise
