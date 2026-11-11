import hashlib,json
import pytest
from test_r7_dispatch_journal import candidate,authorize
from patent_to_pilot.research.r7_dispatch_files import load_dispatch
from patent_to_pilot.research.r6_admission import receipt_digest
from patent_to_pilot.research.mtm_runtime import InputBoundaryError


@pytest.mark.parametrize('fault',[None,'authority','gate_approval','declaration'])
def test_actual_pinned_files_bind_new_owner_candidate(tmp_path,fault):
    j,l,d,g,a=candidate(tmp_path);s=authorize(j,l,d,g,a)['scope']
    if fault=='authority':s['r7_authority']['owner_approval_sha256']='0'*64
    elif fault=='gate_approval':
        g['grammar']['candidate_owner_approval_sha256']='0'*64
        g['grammar']['receipt_sha256']=receipt_digest(g['grammar'])
        d['gate_receipts']['grammar']=g['grammar']['receipt_sha256']
    elif fault=='declaration':d['attempt_id']='replacement'
    if fault in ('gate_approval','declaration'):
        s['qualified_dispatches'][d['attempt_id']]=d
        s['reservations'][-1]={'attempt_id':d['attempt_id'],'status':'RESERVED','declaration':d}
        s['stage_attempts']['calibration'][-1]=d['attempt_id']
    root=tmp_path/'dispatch';root.mkdir();files={}
    values={'declaration':d,'ledger':l,'scope':s,**{'gate:'+k:v for k,v in g.items()}}
    for role,value in values.items():
        name=role.replace(':','-')+'.json';raw=json.dumps(value).encode();(root/name).write_bytes(raw)
        files[role]={'path':name,'sha256':hashlib.sha256(raw).hexdigest()}
    raw=json.dumps({'version':'r6-dispatch-files-v1','files':files}).encode();(root/'manifest.json').write_bytes(raw)
    def load():return load_dispatch(root,manifest_path='manifest.json',manifest_sha256=hashlib.sha256(raw).hexdigest())
    if fault:
        with pytest.raises(InputBoundaryError):load()
    else:assert load()['receipt']['candidate_authority_sha256']==s['r7_authority_sha256']
