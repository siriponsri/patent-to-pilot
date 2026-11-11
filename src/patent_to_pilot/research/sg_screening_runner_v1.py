"""Bounded fixed200 screening with early risk-cap stop and no retries/cards."""
import hashlib,json
from pathlib import Path
from .mtm_runtime import InputBoundaryError
from .sg_critic_screen_v1 import request,screen_record
from .sacr_generation import GenerationLimits
from .sacr_generation_receipt import bind_generation_record
from .sacr_outcomes import summarize_costs

SENTINEL_SALT='ptp-r5-sentinel-v1-20261111|'


def review_selection(results,config_sha256):
    risk=[row for row in results if row['status']=='RISK']
    if len(risk)>20:return {'status':'STOP_REVIEW_CAP_EXCEEDED','card_indices':[]}
    if len(results)!=200:return {'status':'INCOMPLETE_NO_CARDS','card_indices':[]}
    selected=[]
    for kind in ['source','alias']:
        pool=[r for r in results if r['status']=='SCREENING_PASS' and r['unit_type']==kind]
        def rank(row):
            canonical=json.dumps(['SG',config_sha256,kind,row['stable_id']],ensure_ascii=False,separators=(',',':'))
            return hashlib.sha256((SENTINEL_SALT+canonical).encode()).hexdigest(),canonical
        if len(pool)<5:return {'status':'STOP_SENTINEL_STRATUM_TOO_SMALL','card_indices':[]}
        selected+=sorted(pool,key=rank)[:5]
    return {'status':'HUMAN_REVIEW_PENDING','risk_indices':[r['index'] for r in risk],
            'sentinel_indices':[r['index'] for r in selected],
            'card_indices':[r['index'] for r in risk+selected],
            'card_count':len(risk)+10,'cards_issued':0,'semantic_pass':False}


def run_screening(unit_list,destination,*,invoke,check_admission,config_sha256):
    if len(unit_list)!=200 or sum(u['unit_type']=='source' for u in unit_list)!=100 or sum(u['unit_type']=='alias' for u in unit_list)!=100:
        raise InputBoundaryError('fixed source100 and alias100 required')
    if len({(u['unit_type'],u['stable_id']) for u in unit_list})!=200:
        raise InputBoundaryError('duplicate fixed screening unit')
    out=Path(destination);out.mkdir(parents=True,exist_ok=False)
    def write(name,value):
        with (out/name).open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2)
    manifest=[{'index':i,'query_id':u['query_id'],'unit_type':u['unit_type'],'stable_id':u['stable_id'],
               'source_sha256':hashlib.sha256(u['source'].encode()).hexdigest()} for i,u in enumerate(unit_list)]
    write('fixed-manifest-private.json',{'config_sha256':config_sha256,'units':manifest,'retrieval_scores_seen':False})
    results=[];events=[];active=None
    def finish(status):
        result={'status':status,'screened_units':len(results),'risk_units':sum(r['status']=='RISK' for r in results),
            'results':results,'costs':summarize_costs(events),'events':events,
            'review_selection':review_selection(results,config_sha256),
            'semantic_pass':False,'accepted_edges':0,'cards_issued':0,'retry':False,'retrieval':'NOT_RUN'}
        write('result-private.json',result);return result
    try:
        for i,unit in enumerate(unit_list):
            check_admission(str(i));active=i
            messages,grammar=request(unit);attempt=out/f'unit-{i:03}'
            metrics=invoke(f'unit-{i:03}',attempt,messages,grammar)
            reservation=json.loads((attempt/'reservation.json').read_bytes())
            expected=hashlib.sha256(json.dumps(messages,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
            if (reservation.get('messages_sha256')!=expected or reservation.get('retry') is not False
                or reservation.get('status')!='RESERVED' or reservation.get('limits')!=GenerationLimits().__dict__):
                raise InputBoundaryError('critic request binding mismatch')
            raw=(attempt/'generation.json').read_bytes()
            binding=bind_generation_record(raw,expected_sha256=hashlib.sha256(raw).hexdigest(),limits=GenerationLimits(),metrics=metrics)
            event={'event_id':f'unit-{i:03}','query_id':unit['query_id'],'stage':'graph_critic','status':'COMPLETED','metrics':metrics}
            summarize_costs([event]);events.append(event)
            result={**manifest[i],**screen_record(binding['record'],unit)}
            write(f'screen-{i:03}-private.json',result);results.append(result);active=None
            if sum(r['status']=='RISK' for r in results)>20:
                return finish('STOP_REVIEW_CAP_EXCEEDED')
        return finish('SCREENING_COMPLETE_NOT_FIDELITY_PASS')
    except BaseException as error:
        write('failure.json',{'status':'INFRA_OR_INTEGRITY_STOP','exception_type':type(error).__name__,
            'completed_units':len(results),'events':events,'unsettled_unit':active,'retry':False})
        raise
