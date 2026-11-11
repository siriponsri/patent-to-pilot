from copy import deepcopy
import json
import sqlite3
import pytest
from test_r6_admission import fixture
from patent_to_pilot.research.mtm_runtime import InputBoundaryError
from patent_to_pilot.research.r6_dispatch_journal import initialize, document_hash
from patent_to_pilot.research.r7_dispatch_journal import R7DispatchJournal, CPU_CHARGES, CPU_RESERVES
from patent_to_pilot.research.r6_admission import receipt_digest


def setup(tmp_path):
    d,l,s,g=fixture()
    l['r6_phase0_cpu']={'cpu_prior_upper_bound_seconds':23000,'cpu_cap_seconds':28800,
        'local_cpu_conservative_charged_seconds':100,'local_cpu_measured_seconds':20,
        'remote_cpu_charged_seconds':10,'local_cpu_reserved_seconds':200,
        'remote_cpu_reserved_seconds':0,'jobs':{},'model_calls':0}
    path=tmp_path/'journal.sqlite';initialize(path,'a'*64,l,s)
    j=R7DispatchJournal(path,'a'*64);n=deepcopy(l)
    n['r6_phase0_cpu']['local_cpu_reserved_seconds']=0
    n['r6_phase0_cpu']['local_cpu_conservative_charged_seconds']+=200
    n['r7_cpu']={'cap_seconds':3600,'approval_sha256':'b'*64,
                'conservative_charged_seconds':100,'measured_seconds':0,'reserved_seconds':0}
    r={'status':'VERIFIED_CPU_ONLY_RECONCILIATION','journal_identity':'a'*64,
       'owner_approval_sha256':'b'*64,'model_calls':0,'gpu_seconds':0,'evidence_sha256':['c'*64],
       'old_ledger_sha256':document_hash(l),'new_ledger_sha256':document_hash(n),
       'cpu_deltas':{k:n['r6_phase0_cpu'][k]-l['r6_phase0_cpu'][k] for k in CPU_CHARGES+CPU_RESERVES}}
    return j,(d,l,s,g),n,r


def head(j):
    with sqlite3.connect(j.path) as db:
        return db.execute('SELECT * FROM head').fetchone()


def sync(j,n,r):
    return j.sync_cpu_ledger(expected_generation=0,new_ledger=n,receipt=r,receipt_sha256=document_hash(r))


def test_cpu_sync_preserves_scope_and_all_model_history(tmp_path):
    j,args,n,r=setup(tmp_path);before=head(j)
    assert sync(j,n,r)['status']=='CPU_ONLY_RECONCILED_NO_MODEL_AUTHORITY'
    after=head(j)
    assert after[1]==1 and after[3:]==before[3:] and json.loads(after[2])==n
    with pytest.raises(InputBoundaryError):sync(j,n,r)
    # CPU sync does not authorize a calibration replay or any new declaration.
    d,l,s,g=args
    with pytest.raises(InputBoundaryError):j.claim(d,n,s,g,expected_generation=0)


@pytest.mark.parametrize('fault',['gpu','cap','floor','history','cpu_reset','over_budget',
    'r7_budget','model_job','delta','old_hash','active','approval','pending',
    'r7_unmirrored','r7_pending','gpu_job','evidence_type','bool_counter'])
def test_cpu_sync_rejects_unsafe_mutations_atomically(tmp_path,fault):
    j,args,n,r=setup(tmp_path)
    if fault=='gpu':n['gpu_conservative_charged_seconds']+=1
    elif fault=='cap':n['gpu_limit_seconds']+=1
    elif fault=='floor':n['r6_phase0_cpu']['cpu_prior_upper_bound_seconds']=0
    elif fault=='history':n['r6_phase0_cpu']['model_calls']=1
    elif fault=='cpu_reset':n['r6_phase0_cpu']['local_cpu_measured_seconds']=0
    elif fault=='over_budget':n['r6_phase0_cpu']['local_cpu_conservative_charged_seconds']=30000
    elif fault=='r7_budget':n['r7_cpu']['measured_seconds']=3601
    elif fault=='r7_unmirrored':n['r7_cpu']['measured_seconds']=1
    elif fault=='r7_pending':n['r7_cpu']['reserved_seconds']=1
    elif fault=='gpu_job':n['r6_phase0_cpu']['jobs']['bad']={'model_calls':0,'gpu_seconds':1,'cpu_seconds':1,'declaration_sha256':'f'*64}
    elif fault=='evidence_type':r['evidence_sha256']='c'*64
    elif fault=='bool_counter':r['model_calls']=False
    elif fault=='model_job':n['r6_phase0_cpu']['jobs']['bad']={'model_calls':1,'cpu_seconds':1,'declaration_sha256':'f'*64}
    elif fault=='delta':r['cpu_deltas']['local_cpu_measured_seconds']=1
    elif fault=='old_hash':r['old_ledger_sha256']='d'*64
    elif fault=='approval':n['r7_cpu']['approval_sha256']='f'*64
    elif fault=='pending':n['r6_phase0_cpu']['local_cpu_reserved_seconds']=1
    elif fault=='active':
        with sqlite3.connect(j.path) as db:db.execute("UPDATE head SET active='unknown'")
    r['new_ledger_sha256']=document_hash(n);before=head(j)
    with pytest.raises(InputBoundaryError):sync(j,n,r)
    assert head(j)==before


def candidate(tmp_path):
    j,args,n,r=setup(tmp_path);d,l,s,g=args
    j.claim(d,l,s,g,expected_generation=0)
    nl=deepcopy(l);ns=deepcopy(s)
    for used,left in [('gpu_conservative_charged_seconds','gpu_remaining_seconds'),
                      ('fidelity_generation_charged_seconds','fidelity_generation_remaining_seconds')]:
        nl[used]+=100;nl[left]-=100
    ns['stage_costs']['calibration']={'calls':24,'seconds':100}
    ns['reservations'][0]['status']='SETTLED'
    terminal={'attempt_id':d['attempt_id'],'container_name':d['attempt_id'],
        'declaration_sha256':document_hash(d),'container_state':{'Running':False,'Pid':0,'ExitCode':0},
        'costs_reconciled':True,'whole_wall_seconds':100,'failure_axis':'EVALUATOR_CALIBRATION'}
    j.reconcile(attempt_id=d['attempt_id'],terminal=terminal,new_ledger=nl,new_scope=ns)
    nd=dict(d,attempt_id='r7-calibration-v1',ledger_generation=2,candidate_owner_approval_sha256='b'*64,
            transport_version='sg-compact-transport-v2',gold_sha256='d'*64,
            criteria_sha256='e'*64,transport_sha256='f'*64)
    ng=deepcopy(g)
    for gate in ng.values():
        gate['candidate_owner_approval_sha256']='b'*64
        gate['receipt_sha256']=receipt_digest(gate)
    nd['gate_receipts']={k:v['receipt_sha256'] for k,v in ng.items()}
    authority={'status':'OWNER_APPROVED_R7_SINGLE_CANDIDATE','journal_identity':'a'*64,
        'gold_or_threshold_changed':False,'owner_approval_sha256':'b'*64,'plan_sha256':'c'*64,
        'previous_attempt_id':d['attempt_id'],'previous_terminal_sha256':document_hash(terminal),
        'declaration_sha256':document_hash(nd),'gold_sha256':'d'*64,'criteria_sha256':'e'*64,
        'transport_sha256':'f'*64,'gpu_seconds':637200,'fidelity_seconds':169200,
        'full_dev_seconds':460800,'cpu_seconds':3600,
        'initial_gpu_seconds':nl['gpu_conservative_charged_seconds'],
        'initial_fidelity_seconds':nl['fidelity_generation_charged_seconds']}
    return j,nl,nd,ng,authority


def authorize(j,l,d,g,a):
    return j.authorize_calibration(expected_generation=1,ledger=l,declaration=d,gates=g,
                                  authority=a,authority_sha256=document_hash(a))


def test_explicit_candidate_preserves_semantic_failure_and_dispatches_only_once(tmp_path):
    j,l,d,g,a=candidate(tmp_path)
    result=authorize(j,l,d,g,a);scope=result['scope']
    assert result['generation']==2
    assert scope['stage_costs']['calibration']['calls']==24
    assert scope['stage_attempts']['calibration']==['r6-calibration-v1','r7-calibration-v1']
    with sqlite3.connect(j.path) as db:
        terminal=json.loads(db.execute('SELECT terminal FROM attempts WHERE id=?',('r6-calibration-v1',)).fetchone()[0])
    assert terminal['failure_axis']=='EVALUATOR_CALIBRATION'
    assert j.claim(d,l,scope,g,expected_generation=2)['status']=='CONSUMED_UNRESOLVED'
    with pytest.raises(InputBoundaryError):j.claim(d,l,scope,g,expected_generation=2)
    with pytest.raises(InputBoundaryError):authorize(j,l,d,g,a)


@pytest.mark.parametrize('fault',['gold','terminal','owner','transport','calls','time','cap','floor','gate','old_identity','generation'])
def test_candidate_authority_mutations_cannot_grant_dispatch(tmp_path,fault):
    j,l,d,g,a=candidate(tmp_path)
    if fault=='gold':a['gold_or_threshold_changed']=True
    elif fault=='terminal':a['previous_terminal_sha256']='0'*64
    elif fault=='owner':d['candidate_owner_approval_sha256']='0'*64
    elif fault=='transport':d['transport_version']='v3'
    elif fault=='calls':d['maximum_calls']=25
    elif fault=='time':d['seconds']=7201
    elif fault=='cap':a['gpu_seconds']+=1
    elif fault=='floor':a['initial_gpu_seconds']=0
    elif fault=='gate':
        g['grammar']['candidate_owner_approval_sha256']='0'*64
        g['grammar']['receipt_sha256']=receipt_digest(g['grammar'])
        d['gate_receipts']['grammar']=g['grammar']['receipt_sha256']
    elif fault=='old_identity':a['journal_identity']='0'*64
    elif fault=='generation':d['ledger_generation']=1
    a['declaration_sha256']=document_hash(d);before=head(j)
    with pytest.raises(InputBoundaryError):authorize(j,l,d,g,a)
    assert head(j)==before
