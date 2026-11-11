from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy

import pytest

from test_r6_admission import fixture
from patent_to_pilot.research.r6_dispatch_journal import DispatchJournal,initialize,document_hash
from patent_to_pilot.research.mtm_runtime import InputBoundaryError


def setup(tmp_path):
    d,l,s,g=fixture();path=tmp_path/'global.sqlite'
    initialize(path,'a'*64,l,s)
    return DispatchJournal(path,'a'*64),(d,l,s,g)


def test_unknown_global_attempt_blocks_same_or_new_snapshot(tmp_path):
    journal,args=setup(tmp_path)
    journal.claim(*args,expected_generation=0)
    with pytest.raises(InputBoundaryError):journal.claim(*args,expected_generation=0)
    reopened=DispatchJournal(journal.path,'a'*64)
    with pytest.raises(InputBoundaryError):reopened.claim(*args,expected_generation=0)


def test_concurrent_global_admission_exactly_one_winner(tmp_path):
    journal,args=setup(tmp_path)
    def claim(_):
        try:journal.claim(*args,expected_generation=0);return 1
        except InputBoundaryError:return 0
    with ThreadPoolExecutor(max_workers=2) as pool:assert sum(pool.map(claim,range(2)))==1


@pytest.mark.parametrize('fault',['running','unknown_cost','undercharge','changed_floor'])
def test_unknown_or_undercharged_terminal_cannot_release_global_slot(tmp_path,fault):
    journal,args=setup(tmp_path);d,l,s,g=args;journal.claim(*args,expected_generation=0)
    nl=deepcopy(l);ns=deepcopy(s)
    terminal={'container_state':{'Running':False,'Pid':0,'ExitCode':0},'whole_wall_seconds':10,'costs_reconciled':True}
    terminal.update(attempt_id=d['attempt_id'],container_name=d['attempt_id'],declaration_sha256=document_hash(d))
    for charged,left in [('gpu_conservative_charged_seconds','gpu_remaining_seconds'),
                         ('fidelity_generation_charged_seconds','fidelity_generation_remaining_seconds')]:
        nl[charged]+=10;nl[left]-=10
    ns['reservations'][0]['status']='SETTLED'
    if fault=='running':terminal['container_state']['Running']=True
    if fault=='unknown_cost':terminal['costs_reconciled']=False
    if fault=='undercharge':nl=deepcopy(l)
    if fault=='changed_floor':ns['initial_gpu_seconds']=0
    with pytest.raises(InputBoundaryError):
        journal.reconcile(attempt_id=d['attempt_id'],terminal=terminal,new_ledger=nl,new_scope=ns)
    with pytest.raises(InputBoundaryError):journal.claim(*args,expected_generation=0)


@pytest.mark.parametrize('outcome',['exited','not_submitted','authoritative_absent'])
def test_reconciled_head_rejects_old_generation_and_snapshot(tmp_path,outcome):
    journal,args=setup(tmp_path);d,l,s,g=args;journal.claim(*args,expected_generation=0)
    nl=deepcopy(l);ns=deepcopy(s)
    for charged,left in [('gpu_conservative_charged_seconds','gpu_remaining_seconds'),
                         ('fidelity_generation_charged_seconds','fidelity_generation_remaining_seconds')]:
        nl[charged]+=10;nl[left]-=10
    ns['reservations'][0]['status']='SETTLED';ns['stage_costs']['calibration']={'calls':1,'seconds':10}
    terminal={'container_state':{'Running':False,'Pid':0,'ExitCode':0},'whole_wall_seconds':10,'costs_reconciled':True}
    terminal.update(attempt_id=d['attempt_id'],container_name=d['attempt_id'],declaration_sha256=document_hash(d))
    if outcome!='exited':
        del terminal['container_state'];terminal['container_outcome']='NO_CONTAINER'
        if outcome=='not_submitted':terminal['create_request_sent']=False
        else:terminal['absence_observation']='ENGINE_404'
    assert journal.reconcile(attempt_id=d['attempt_id'],terminal=terminal,new_ledger=nl,new_scope=ns)['generation']==1
    for generation in [0,1]:
        with pytest.raises(InputBoundaryError):journal.claim(*args,expected_generation=generation)


def test_missing_journal_never_autocreates(tmp_path):
    with pytest.raises(FileNotFoundError):DispatchJournal(tmp_path/'missing','a'*64)


@pytest.mark.parametrize('fault',['nan','history','declaration','terminal_identity','stage_reassignment'])
def test_reviewer_reconciliation_integrity_regressions(tmp_path,fault):
    journal,args=setup(tmp_path);d,l,s,g=args;journal.claim(*args,expected_generation=0)
    nl=deepcopy(l);ns=deepcopy(s)
    for charged,left in [('gpu_conservative_charged_seconds','gpu_remaining_seconds'),
                         ('fidelity_generation_charged_seconds','fidelity_generation_remaining_seconds')]:
        nl[charged]+=10;nl[left]-=10
    ns['reservations'][0]['status']='SETTLED';ns['stage_costs']['calibration']={'calls':1,'seconds':10}
    terminal={'attempt_id':d['attempt_id'],'container_name':d['attempt_id'],'declaration_sha256':document_hash(d),
        'container_state':{'Running':False,'Pid':0,'ExitCode':0},'whole_wall_seconds':10,'costs_reconciled':True}
    if fault=='nan':nl['gpu_remaining_seconds']=float('nan')
    if fault=='history':ns['stage_attempts']['calibration']=[]
    if fault=='declaration':ns['reservations'][0]['declaration']['seconds']=1
    if fault=='terminal_identity':terminal['declaration_sha256']='0'*64
    if fault=='stage_reassignment':ns['stage_costs']['synthetic']={'calls':1,'seconds':1}
    with pytest.raises(InputBoundaryError):
        journal.reconcile(attempt_id=d['attempt_id'],terminal=terminal,new_ledger=nl,new_scope=ns)


@pytest.mark.parametrize('fault',[None,'method_failure','missing_repair','changed_gold','wrong_configuration'])
def test_second_revision_requires_reconciled_engineering_repair(tmp_path,fault):
    journal,args=setup(tmp_path);d,l,s,g=args;journal.claim(*args,expected_generation=0)
    nl=deepcopy(l);ns=deepcopy(s)
    for charged,left in [('gpu_conservative_charged_seconds','gpu_remaining_seconds'),
                         ('fidelity_generation_charged_seconds','fidelity_generation_remaining_seconds')]:
        nl[charged]+=10;nl[left]-=10
    ns['reservations'][0]['status']='SETTLED';ns['stage_costs']['calibration']={'calls':1,'seconds':10}
    d2=dict(d,attempt_id='r6-calibration-v2',configuration_sha256='f'*64)
    ns['stage_attempts']['calibration'].append(d2['attempt_id'])
    ns['qualified_dispatches'][d2['attempt_id']]=d2
    ns['reservations'].append({'attempt_id':d2['attempt_id'],'status':'RESERVED','declaration':d2})
    repair={'previous_attempt_id':d['attempt_id'],'status':'APPROVED_BOUNDED_ENGINEERING_REVISION',
        'gold_or_threshold_changed':False,'cause_evidence_sha256':'b'*64,'tests_sha256':'c'*64,
        'configuration_sha256':'f'*64}
    ns['revision_receipts']={d2['attempt_id']:repair}
    terminal={'attempt_id':d['attempt_id'],'container_name':d['attempt_id'],'declaration_sha256':document_hash(d),
        'container_state':{'Running':False,'Pid':0,'ExitCode':1},'whole_wall_seconds':10,
        'costs_reconciled':True,'failure_axis':'ENGINEERING'}
    if fault=='method_failure':terminal['failure_axis']='METHOD'
    if fault=='missing_repair':ns['revision_receipts']={}
    if fault=='changed_gold':repair['gold_or_threshold_changed']=True
    if fault=='wrong_configuration':repair['configuration_sha256']='e'*64
    journal.reconcile(attempt_id=d['attempt_id'],terminal=terminal,new_ledger=nl,new_scope=ns)
    if fault:
        with pytest.raises(InputBoundaryError):journal.claim(d2,nl,ns,g,expected_generation=1)
    else:assert journal.claim(d2,nl,ns,g,expected_generation=1)['status']=='CONSUMED_UNRESOLVED'
