import pytest
from patent_to_pilot.research.r6_admission import validate_dispatch, REQUIRED_GATES, STAGES, IDENTITIES, receipt_digest
from patent_to_pilot.research.mtm_runtime import InputBoundaryError


def fixture():
    d={'stage':'calibration','attempt_id':'r6-calibration-v1','retry':False,'maximum_calls':24,'seconds':7200}
    d.update({k:'a'*64 for k in ('approval_sha256','package_sha256','input_manifest_sha256','model_identity_sha256','decoder_sha256','tokenizer_sha256')})
    ledger={'gpu_conservative_charged_seconds':12310,'gpu_remaining_seconds':691200-12310,'gpu_limit_seconds':691200,
        'fidelity_generation_charged_seconds':12031,'fidelity_generation_remaining_seconds':230400-12031,'fidelity_limit_seconds':230400,
        'full_dev_limit_seconds':460800,'human_cards_total_limit_all_benchmarks_all_configurations':60,
        'disk_limit_bytes_combined_incremental':40*1024**3}
    scope={'status':'OWNER_APPROVED_R6','approval_sha256':'a'*64,'initial_gpu_seconds':12310,'initial_fidelity_seconds':12031,
        'stage_costs':{k:{'seconds':0,'calls':0} for k in STAGES},
        'stage_attempts':{k:[d['attempt_id']] if k=='calibration' else [] for k in STAGES},
        'reservations':[{'attempt_id':d['attempt_id'],'status':'RESERVED','declaration':dict(d)}]}
    gates={k:{'status':'PASS','package_sha256':'a'*64,'receipt_sha256':'b'*64,
        'dispatch_identity':{key:d[key] for key in IDENTITIES}} for k in REQUIRED_GATES}
    for receipt in gates.values():receipt['receipt_sha256']=receipt_digest(receipt)
    d['gate_receipts']={k:r['receipt_sha256'] for k,r in gates.items()}
    s=scope
    s['reservations'][0]['declaration']=dict(d)
    s['qualified_dispatches']={d['attempt_id']:dict(d)}
    return d,ledger,scope,gates


def test_static_qualification_never_claims_live_or_model_execution():
    result=validate_dispatch(*fixture())
    assert result['live_admission']=='REQUIRED' and result['model_calls']==0


@pytest.mark.parametrize('fault',['gate','package','request','reservation','parallel','unknown','reset','budget','cap','nan','calls','past_calls','past_time','approval','retry'])
def test_invalid_dispatch_rejected_before_backend(fault):
    d,l,s,g=fixture()
    if fault=='gate':del g['grammar']
    elif fault=='package':g['grammar']['package_sha256']='c'*64
    elif fault=='request':d['maximum_calls']=25
    elif fault=='reservation':s['reservations']=[]
    elif fault in ('parallel','unknown'):s['reservations'].append({'attempt_id':'other','status':'UNKNOWN' if fault=='unknown' else 'RUNNING'})
    elif fault=='reset':l['gpu_conservative_charged_seconds']-=1;l['gpu_remaining_seconds']+=1
    elif fault=='budget':l['gpu_conservative_charged_seconds']=690000;l['gpu_remaining_seconds']=1200
    elif fault=='cap':l['fidelity_limit_seconds']+=1
    elif fault=='nan':l['gpu_conservative_charged_seconds']=float('nan')
    elif fault=='calls':d['maximum_calls']=49;s['reservations'][0]['declaration']=dict(d)
    elif fault=='past_calls':s['stage_costs']['calibration']={'seconds':0,'calls':25}
    elif fault=='past_time':s['stage_costs']['calibration']={'seconds':7201,'calls':0}
    elif fault=='approval':s['approval_sha256']='c'*64
    elif fault=='retry':d['retry']=True
    with pytest.raises(InputBoundaryError):validate_dispatch(d,l,s,g)


@pytest.mark.parametrize('fault',['missing_costs','unreconciled','third_revision','missing_registry','gate_input','no_human','receipt_body','unqualified','unknown_status'])
def test_reviewer_reproductions(fault):
    d,l,s,g=fixture()
    if fault=='missing_costs':s['stage_costs']={}
    if fault=='unreconciled':l['gpu_conservative_charged_seconds']+=1;l['gpu_remaining_seconds']-=1
    if fault=='third_revision':s['stage_attempts']['calibration']+=['v2','v3']
    if fault=='missing_registry':s['stage_attempts']={}
    if fault=='gate_input':g['grammar']['dispatch_identity']['input_manifest_sha256']='c'*64
    if fault=='no_human':
        d['stage']='full474';s['stage_attempts']['full474']=[d['attempt_id']]
        s['reservations'][0]['declaration']=dict(d)
        s['qualified_dispatches'][d['attempt_id']]=dict(d)
    if fault=='receipt_body':g['grammar']['extra']='changed'
    if fault=='unqualified':s['qualified_dispatches']={}
    if fault=='unknown_status':s['reservations'].append({'attempt_id':'other','status':'LOST'})
    with pytest.raises(InputBoundaryError):validate_dispatch(d,l,s,g)


@pytest.mark.parametrize('tampered',[False,True])
def test_full_dev_predecessors_bound_to_frozen_receipt_bytes(tampered):
    d,l,s,g=fixture();d.update(stage='full474',configuration_sha256='d'*64)
    s['stage_attempts']['full474']=[d['attempt_id']]
    s['predecessors']={}
    for name in ('human_fidelity','integrity','pilot20'):
        r={'gate':name,'status':'PASS','configuration_sha256':'d'*64}
        r['receipt_sha256']=receipt_digest(r);s['predecessors'][name]=r
    d['predecessor_receipts']={k:r['receipt_sha256'] for k,r in s['predecessors'].items()}
    s['qualified_dispatches'][d['attempt_id']]=dict(d)
    s['reservations'][0]['declaration']=dict(d)
    if tampered:
        s['predecessors']['human_fidelity']['changed_decision']='critical error'
        with pytest.raises(InputBoundaryError,match='predecessor human_fidelity'):validate_dispatch(d,l,s,g)
    else:assert validate_dispatch(d,l,s,g)['live_admission']=='REQUIRED'
