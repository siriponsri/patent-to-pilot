"""R6 stage and reservation validation. This module never grants authority."""
import math
import re
import hashlib
import json
from .mtm_runtime import InputBoundaryError

STAGES={
    'calibration':{'calls':48,'seconds':14400,'fidelity':True},
    'synthetic':{'calls':6,'seconds':3600,'fidelity':True},
    'native5':{'calls':15,'seconds':7200,'fidelity':True},
    'native95':{'calls':285,'seconds':108000,'fidelity':True},
    'graph114':{'calls':114,'seconds':43200,'fidelity':True},
    'pilot20':{'calls':60,'seconds':7200,'fidelity':False},
    'full474':{'calls':1422,'seconds':460800,'fidelity':False},
}
REQUIRED_GATES={'transport','attempt_accounting','grammar','cohorts','retrieval','input_admission','isolation'}
IDENTITIES=('approval_sha256','package_sha256','input_manifest_sha256','model_identity_sha256','decoder_sha256','tokenizer_sha256')
PREDECESSORS={'calibration':set(),'synthetic':{'calibration'},'native5':{'calibration','synthetic'},
    'native95':{'calibration','synthetic','native5'},'graph114':{'calibration'},
    'pilot20':{'human_fidelity','integrity'},'full474':{'human_fidelity','integrity','pilot20'}}


def require(value,message):
    if not value:raise InputBoundaryError(message)


def number(value):
    return type(value) in (int,float) and math.isfinite(value) and value>=0


def digest(value):
    return type(value) is str and re.fullmatch('[0-9a-f]{64}',value) is not None


def receipt_digest(receipt):
    return hashlib.sha256(json.dumps({k:v for k,v in receipt.items() if k!='receipt_sha256'},
        sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()


def validate_dispatch(declaration, ledger, scope, gates):
    """Validate frozen receipts at dispatch, in addition to live supervisor checks.

    Caller must bind these input bytes and independently observe model identity,
    Docker isolation, the shared GPU lock and current hardware/resource state.
    Reservation is not consumed by this pure function; durable controller owns it.
    """
    d=declaration
    require(scope.get('status')=='OWNER_APPROVED_R6','R6 approval scope missing')
    require(d.get('stage') in STAGES,'unknown R6 stage')
    stage=STAGES[d['stage']]
    for key in IDENTITIES:
        require(digest(d.get(key)),f'missing {key}')
    require(d['approval_sha256']==scope.get('approval_sha256'),'approval binding changed')
    require(scope.get('qualified_dispatches',{}).get(d.get('attempt_id'))==d,
        'dispatch differs from frozen qualified declaration')
    require(d.get('retry') is False,'dispatch replay prohibited')
    require(type(d.get('maximum_calls')) is int and 0<d['maximum_calls']<=stage['calls'],'stage call ceiling')
    require(number(d.get('seconds')) and 0<d['seconds']<=stage['seconds'],'stage time ceiling')
    require(type(d.get('attempt_id')) is str and re.fullmatch('[a-z0-9][a-z0-9_-]{0,127}',d['attempt_id']),'attempt identity')
    require(set(gates)==REQUIRED_GATES,'incomplete Phase0 gate set')
    for gate,receipt in gates.items():
        require(receipt.get('status')=='PASS' and receipt.get('package_sha256')==d['package_sha256']
            and digest(receipt.get('receipt_sha256')),f'unqualified {gate}')
        require(receipt.get('dispatch_identity')=={k:d[k] for k in IDENTITIES},f'{gate} target binding mismatch')
        require(receipt_digest(receipt)==receipt['receipt_sha256']
            and d.get('gate_receipts',{}).get(gate)==receipt['receipt_sha256'],f'{gate} receipt content changed')
    predecessors=scope.get('predecessors',{})
    for name in PREDECESSORS[d['stage']]:
        receipt=predecessors.get(name,{})
        require(receipt.get('status')=='PASS' and digest(receipt.get('receipt_sha256'))
            and receipt.get('configuration_sha256')==d.get('configuration_sha256')
            and digest(d.get('configuration_sha256')),f'missing or changed predecessor {name}')
        require(receipt.get('gate')==name and receipt_digest(receipt)==receipt['receipt_sha256']
            and d.get('predecessor_receipts',{}).get(name)==receipt['receipt_sha256'],
            f'predecessor {name} body or frozen binding changed')
    # Completed costs and all outstanding reservations count, never only this job.
    reservations=scope.get('reservations',[])
    require(type(reservations) is list,'reservation collection')
    require(all(r.get('status') in ('RESERVED','RUNNING','UNKNOWN','SETTLED','CANCELLED_PRE_DISPATCH')
        for r in reservations),'unknown reservation state')
    matches=[r for r in reservations if r.get('attempt_id')==d['attempt_id']]
    require(len(matches)==1,'missing or duplicate same-attempt reservation')
    own=matches[0]
    require(own.get('status')=='RESERVED' and own.get('declaration')==d,'reservation identity mismatch')
    require(sum(r.get('status') in ('RESERVED','RUNNING','UNKNOWN') for r in reservations)==1,
        'another reservation/running/unknown job prevents GPU admission')
    spent=scope.get('stage_costs',{})
    require(set(spent)==set(STAGES),'incomplete stage accounting cannot imply zero')
    for name,limit in STAGES.items():
        cost=spent[name]
        require(number(cost.get('seconds')) and type(cost.get('calls')) is int and cost['calls']>=0,'invalid prior cost')
        extra=d['seconds'] if name==d['stage'] else 0
        calls=d['maximum_calls'] if name==d['stage'] else 0
        require(cost['seconds']+extra<=limit['seconds'] and cost['calls']+calls<=limit['calls'],'stage allowance exhausted')
    versions=scope.get('stage_attempts',{})
    require(set(versions)==set(STAGES),'incomplete version registry')
    for name,attempts in versions.items():
        require(type(attempts) is list and all(type(a) is str for a in attempts)
            and len(attempts)==len(set(attempts)),'duplicate stage attempt')
        require(len(attempts)<=(2 if name in ('calibration','synthetic') else 1),'revision ceiling exceeded')
    require(d['attempt_id'] in versions[d['stage']],'attempt not registered')
    require(d['maximum_calls']<=({'calibration':24,'synthetic':3}.get(d['stage'],stage['calls'])),
        'per-version call ceiling')
    for used,left,cap_key,cap,floor_key,new_cap,charge in [
        ('gpu_conservative_charged_seconds','gpu_remaining_seconds','gpu_limit_seconds',691200,'initial_gpu_seconds',644400,d['seconds']),
        ('fidelity_generation_charged_seconds','fidelity_generation_remaining_seconds','fidelity_limit_seconds',230400,'initial_fidelity_seconds',176400,d['seconds'] if stage['fidelity'] else 0)]:
        floor=scope.get(floor_key)
        require(all(number(x) for x in (ledger.get(used),ledger.get(left),floor)),'invalid cumulative accounting')
        require(ledger.get(cap_key)==cap and ledger[used]>=floor and ledger[left]>=charge
            and math.isclose(ledger[used]+ledger[left],cap,rel_tol=0,abs_tol=1e-6)
            and ledger[used]-floor+charge<=new_cap,'cumulative allowance exceeded or reset')
        recorded=sum(cost['seconds'] for name,cost in spent.items()
            if used=='gpu_conservative_charged_seconds' or STAGES[name]['fidelity'])
        require(math.isclose(recorded,ledger[used]-floor,rel_tol=0,abs_tol=1e-6),'stage and cumulative charges disagree')
    require(ledger.get('full_dev_limit_seconds')==460800,'full dev cap changed')
    require(ledger.get('human_cards_total_limit_all_benchmarks_all_configurations')==60,'card cap changed')
    require(ledger.get('disk_limit_bytes_combined_incremental')==40*1024**3,'disk cap changed')
    return {'status':'PASS_STATIC_DISPATCH_CONTRACT','live_admission':'REQUIRED','model_calls':0}
