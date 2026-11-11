"""Compact-v2 execution preserving frozen parents, exact messages and raw costs."""
from copy import deepcopy
import json
from pathlib import Path
from jsonschema.exceptions import ValidationError
from .mtm_runtime import InputBoundaryError
from .r6_reference_runner import encoded, sha
from .sacr_generation import GenerationLimits
from .sacr_generation_receipt import bind_generation_record
from .sacr_native_fidelity import write_new
from .sacr_outcomes import summarize_costs
from .sg_compact_transport import VERSION, prepare, reconstruct, interpret


def task(unit):
    """An oversized catalogue remains a bound parent, never an omitted sample."""
    unit=deepcopy(unit)
    try:prepared=prepare(**unit)
    except InputBoundaryError as error:
        if str(error)!='catalogue too large; no truncation':raise
        prepared=None
    return {'unit':unit,'prepared':prepared}


def validate_task(value):
    if value!=task(value['unit']):
        raise InputBoundaryError('compact task or original source changed')
    prepared=value['prepared']
    if prepared is not None:
        if prepared['version']!=VERSION:raise InputBoundaryError('compact version mismatch')
        reconstruct(prepared)
    return value['unit']['query_id']


def preflight_requests(tasks,*,mode,count_tokens):
    if mode not in ('calibration','graph') or len(tasks)!=(24 if mode=='calibration' else 114):
        raise InputBoundaryError('fixed compact cohort count')
    tasks=deepcopy(tasks);ids=[validate_task(t) for t in tasks]
    if len(ids)!=len(set(ids)):raise InputBoundaryError('duplicate compact parent')
    rows=[]
    for value,query_id in zip(tasks,ids):
        prepared=value['prepared']
        if prepared is None:
            rows.append({'query_id':query_id,'input_tokens':None,'status':'CATALOGUE_LIMIT','messages_sha256':None})
            continue
        messages=deepcopy(prepared['messages']);before=encoded(messages)
        count=count_tokens(messages)
        if encoded(messages)!=before or type(count) is not int or count<1:
            raise InputBoundaryError('compact tokenizer count invalid or request mutated')
        rows.append({'query_id':query_id,'input_tokens':count,
                     'status':'INPUT_LIMIT' if count>8192 else 'ADMITTED','messages_sha256':sha(before)})
    risks=sum(r['status']!='ADMITTED' for r in rows)
    return {'status':'STOP_INPUT_GATE' if (risks>20 if mode=='graph' else risks>0) else 'ADMITTED',
            'version':VERSION,'mode':mode,'tasks_sha256':sha(encoded(tasks)),
            'rows':rows,'input_limit_units':risks,'model_calls':0}


def run_reference_cohort(*,destination,tasks,preflight,mode,run_id,invoke,check_admission):
    tasks=deepcopy(tasks);preflight=deepcopy(preflight)
    if (mode not in ('calibration','graph') or len(tasks)!=(24 if mode=='calibration' else 114)
            or preflight.get('tasks_sha256')!=sha(encoded(tasks)) or preflight.get('mode')!=mode
            or preflight.get('version')!=VERSION or len(preflight.get('rows',[]))!=len(tasks)):
        raise InputBoundaryError('compact preflight identity mismatch')
    ids=[]
    for value,row in zip(tasks,preflight['rows']):
        query_id=validate_task(value);ids.append(query_id);prepared=value['prepared']
        if row['query_id']!=query_id:raise InputBoundaryError('compact parent order changed')
        if prepared is None:
            if row!={'query_id':query_id,'input_tokens':None,'status':'CATALOGUE_LIMIT','messages_sha256':None}:
                raise InputBoundaryError('catalogue risk receipt changed')
        elif (row['messages_sha256']!=sha(encoded(prepared['messages']))
                or type(row['input_tokens']) is not int or row['input_tokens']<1
                or row['status']!=('INPUT_LIMIT' if row['input_tokens']>8192 else 'ADMITTED')):
            raise InputBoundaryError('compact message admission changed')
    if len(ids)!=len(set(ids)):raise InputBoundaryError('duplicate compact parent')
    initial=sum(row['status']!='ADMITTED' for row in preflight['rows'])
    stopped=initial>20 if mode=='graph' else initial>0
    if preflight['input_limit_units']!=initial or preflight['status']!=('STOP_INPUT_GATE' if stopped else 'ADMITTED'):
        raise InputBoundaryError('compact admission outcome changed')
    out=Path(destination);out.mkdir(parents=True,exist_ok=False)
    write_new(out/'input-preflight.json',preflight)
    events=[];results=[];active=None;risks=initial;limits=GenerationLimits()
    def finish(status):
        result={'status':status,'mode':mode,'version':VERSION,'fixed_denominator':len(tasks),
                'results':results,'events':events,'costs':summarize_costs(events),
                'risk_units':risks,'initial_input_risks':initial,
                'initial_risk_parent_ids':[r['query_id'] for r in preflight['rows'] if r['status']!='ADMITTED'],
                'unstarted_parent_ids':[r['query_id'] for r in preflight['rows'][len(results):]],
                'semantic_pass':False,'accepted_edges':0,'retry':False}
        write_new(out/'result.json',result);return result
    if stopped:return finish('STOP_INPUT_GATE')
    try:
        for index,(value,admission) in enumerate(zip(tasks,preflight['rows'])):
            query_id=admission['query_id'];request=value['prepared']
            if admission['status']!='ADMITTED':
                results.append({'query_id':query_id,'status':'UNASSESSABLE','reason':admission['status'],'model_calls':0})
                continue
            check_admission(index);active=index;path=out/f'unit-{index:03}'
            messages=deepcopy(request['messages']);schema=deepcopy(request['original']['schema'])
            before=encoded(messages);schema_before=encoded(schema)
            metrics=invoke(f'reference-{index:03}',path,messages,schema)
            if encoded(messages)!=before or encoded(schema)!=schema_before:raise InputBoundaryError('compact request mutated')
            reservation=json.loads((path/'reservation.json').read_bytes())
            if (reservation.get('status')!='RESERVED' or reservation.get('retry') is not False
                    or reservation.get('messages_sha256')!=sha(before) or reservation.get('limits')!=limits.__dict__):
                raise InputBoundaryError('compact reservation mismatch')
            raw=(path/'generation.json').read_bytes()
            binding=bind_generation_record(raw,expected_sha256=sha(raw),limits=limits,metrics=metrics)
            if binding['record']['input_tokens']!=admission['input_tokens']:
                raise InputBoundaryError('compact exact token count mismatch')
            event={'event_id':sha(encoded([run_id,query_id,'critic'])),'query_id':query_id,'stage':'critic','status':'COMPLETED','metrics':metrics}
            summarize_costs(events+[event]);write_new(path/'cost.json',event);events.append(event);active=None
            record=binding['record'];result={'query_id':query_id,'status':'UNASSESSABLE','reason':record['status']}
            if record['status']=='EOS_COMPLETE':
                try:
                    review=interpret(record['text'].encode(),request)
                    result.update(status='AUTOMATIC_UNFLAGGED' if review['method_screen']=='UNFLAGGED' else 'AUTOMATIC_METHOD_FLAG',reason='VALID_CRITIC',review=review)
                except (InputBoundaryError,UnicodeError,ValidationError):result['reason']='INVALID_EVALUATOR'
            result.update(critic_text=record['text'],generation_sha256=sha(raw),
                          compact_messages_sha256=sha(before),compact_version=VERSION)
            write_new(path/'screening.json',result);results.append(result)
            risks+=result['status']!='AUTOMATIC_UNFLAGGED'
            if mode=='graph' and risks>20:return finish('STOP_RISK_CAP')
        return finish('SCREENING_COMPLETE_NOT_FIDELITY')
    except BaseException as error:
        write_new(out/'failure.json',{'status':'INFRA_OR_INTEGRITY_STOP','exception_type':type(error).__name__,
                                     'active_index':active,'known_events':events,'unknown_attempt':active is not None,'retry':False})
        raise
