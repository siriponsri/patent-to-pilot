"""No-replay fixed cohort orchestration with externally attested bundle results."""
import hashlib
import json
from copy import deepcopy
from pathlib import Path
from .mtm_runtime import InputBoundaryError
from .sacr_native_fidelity import write_new
from .sacr_outcomes import summarize_costs


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()


def native_manifest(rows,expected_sha256):
    if digest(rows)!=expected_sha256 or len(rows)!=100:
        raise InputBoundaryError('fixed native100 manifest identity')
    ids=[]
    for row in rows:
        if set(row)!={'query_id','source'} or type(row['source']) is not str or not row['source'].strip():
            raise InputBoundaryError('native runtime manifest fields')
        from .mtm_runtime import identifier
        identifier(row['query_id']);ids.append(row['query_id'])
    if len(ids)!=len(set(ids)):raise InputBoundaryError('duplicate native query')
    return deepcopy(rows)


def run_native_section(*,destination,rows,manifest_sha256,section,configuration_sha256,
                       run_bundle,check_admission,bridge=None,bridge_sha256=None):
    """run_bundle(index,row,path) must bind identities and return durable result.

    Remaining95 imports an exact immutable bridge receipt; it cannot invoke its
    first five tasks. Unknown executions stop the section; completed rejected
    units remain risks and consume the fixed denominator.
    """
    rows=native_manifest(rows,manifest_sha256)
    if section not in ('native5','native95'):raise InputBoundaryError('invalid native section')
    if type(configuration_sha256) is not str or len(configuration_sha256)!=64:
        raise InputBoundaryError('configuration identity')
    imported=[];risks=0
    if section=='native95':
        if (type(bridge) is not dict or digest(bridge)!=bridge_sha256
                or bridge.get('status')!='SECTION_COMPLETE' or bridge.get('section')!='native5'
                or bridge.get('configuration_sha256')!=configuration_sha256
                or bridge.get('manifest_sha256')!=manifest_sha256):
            raise InputBoundaryError('exact completed bridge required; never regenerate')
        imported=deepcopy(bridge['results'])
        if len(imported)!=5 or [r['query_id'] for r in imported]!=[r['query_id'] for r in rows[:5]]:
            raise InputBoundaryError('bridge cohort substitution')
        if any(r['index']!=i or r['source_sha256']!=hashlib.sha256(rows[i]['source'].encode()).hexdigest()
               or r['result_sha256']!=digest(r['result']) for i,r in enumerate(imported)):
            raise InputBoundaryError('bridge source or result changed')
        for item,row in zip(imported,rows[:5]):
            result=item['result']
            if (result.get('query_id')!=row['query_id'] or result.get('status') not in
                    ('UNASSESSABLE','AUTOMATIC_METHOD_FLAG','AUTOMATIC_UNFLAGGED_NOT_FIDELITY_PASS')
                    or type(item['risk']) is not bool
                    or item['risk']!=(result['status']!='AUTOMATIC_UNFLAGGED_NOT_FIDELITY_PASS')):
                raise InputBoundaryError('bridge outcome identity or risk mismatch')
        risks=sum(r['risk'] for r in imported)
        if risks!=bridge['risk_units']:raise InputBoundaryError('bridge risk accounting')
    imported_events=[event for item in imported for event in item['result']['events']]
    summarize_costs(imported_events)
    out=Path(destination);out.mkdir(parents=True,exist_ok=False)
    write_new(out/'reservation.json',{'section':section,'manifest_sha256':manifest_sha256,
        'configuration_sha256':configuration_sha256,'bridge_sha256':bridge_sha256,'retry':False})
    results=list(imported);events=[];active=None
    indices=range(5) if section=='native5' else range(5,100)
    status='SECTION_COMPLETE'
    try:
        for index in indices:
            check_admission(index)
            active=index;row=rows[index]
            bundle_path=out/f'unit-{index:03}'
            supplied=deepcopy(row)
            result=run_bundle(index,supplied,bundle_path)
            if supplied!=row:raise InputBoundaryError('bundle mutated fixed query input')
            if json.loads((bundle_path/'result.json').read_bytes())!=result:
                raise InputBoundaryError('bundle completion not durably identical')
            if result.get('query_id')!=row['query_id'] or result.get('status') not in (
                'UNASSESSABLE','AUTOMATIC_METHOD_FLAG','AUTOMATIC_UNFLAGGED_NOT_FIDELITY_PASS'):
                raise InputBoundaryError('unexpected bundle result; no inferred completion')
            risk=result['status']!='AUTOMATIC_UNFLAGGED_NOT_FIDELITY_PASS'
            item={'index':index,'query_id':row['query_id'],'source_sha256':hashlib.sha256(row['source'].encode()).hexdigest(),
                'result':result,'result_sha256':digest(result),'risk':risk}
            results.append(item);events.extend(result['events']);summarize_costs(imported_events+events)
            active=None;risks+=risk
            write_new(out/f'unit-{index:03}-receipt.json',item)
            if risks>20:status='STOPPED_RISK_CAP';break
        receipt={'status':status,'section':section,'configuration_sha256':configuration_sha256,
            'manifest_sha256':manifest_sha256,'results':results,'risk_units':risks,
            'new_costs':summarize_costs(events),'reused_units':len(imported),
            'fixed_denominator':100,'semantic_pass':False,'retrieval_ready':False,'retry':False}
        write_new(out/'completion.json',receipt);return receipt
    except BaseException as error:
        write_new(out/'failure.json',{'status':'INFRA_OR_INTEGRITY_STOP','exception_type':type(error).__name__,
            'active_index':active,'completed_units':len(results),'known_events':events,
            'retry':False,'unknown_attempt':'INSPECT_BUNDLE' if active is not None else None})
        raise
