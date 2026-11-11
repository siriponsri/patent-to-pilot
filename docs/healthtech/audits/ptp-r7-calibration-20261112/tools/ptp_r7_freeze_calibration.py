from pathlib import Path
import json,hashlib,sys,sqlite3,tempfile
R=Path('C:/Users/User/Desktop/myProject/patent-to-pilot');sys.path.insert(0,str(R/'src'))
from patent_to_pilot.research.r6_admission import IDENTITIES,receipt_digest
from patent_to_pilot.research.r6_dispatch_journal import initialize,document_hash,encoded
from patent_to_pilot.research.r7_dispatch_journal import R7DispatchJournal,CPU_CHARGES,CPU_RESERVES,validate_cpu_change
from patent_to_pilot.research.r7_dispatch_files import load_dispatch,package_identity
from patent_to_pilot.research.r7_calibration_runner import frozen_tasks
from patent_to_pilot.research.r6_reference_runner import encoded as task_encoded
sha=lambda raw:hashlib.sha256(raw).hexdigest()
A=R/'docs/healthtech/audits/ptp-r7-calibration-20261112'
P=R/'docs/healthtech/audits/ptp-r7-pipeline-20261112'
Q=R/'docs/healthtech/audits/ptp-r7-preparation-20261112'
H=R/'docs/healthtech/audits/ptp-r6-phase0-execution-20261111'
probe=json.loads((A/'current-resource-probe.json').read_bytes())
head=probe['remote']['journal_head'];assert head['generation']==1 and head['active'] is None
outer=json.loads((P/'pipeline-fixture-declaration.json').read_bytes());pins=outer['files_sha256']
assert all(sha((R/p).read_bytes())==h for p,h in pins.items()),'qualified source changed'
summary=json.loads((P/'pipeline-fixture-summary.json').read_bytes())
assert summary['status']=='PASS_AUTHORED_FULL_CALIBRATION_PIPELINE'
tasks=frozen_tasks();task_sha=sha(task_encoded(tasks))
assert task_sha==summary['tasks_sha256']
approval=json.loads((Q/'owner-approval.json').read_bytes());approval_sha=sha((Q/'owner-approval.json').read_bytes())
assert approval_sha==outer['owner_approval_sha256']
base=json.loads((Q/'accounting-baseline.json').read_bytes())
for kind,components in [('critic',['r6_backend.py','r6_qualification.py','reference_critic_v1.py','r6_critic_tasks.py','sacr_boundary_callback_v3.py','sacr_grammar_guard.py']),
                        ('profile',['r6_backend.py','sacr_r6_candidate.py','sacr_r6_prompt.py','sacr_boundary_callback_v3.py','sacr_grammar_guard.py'])]:
 old=json.loads((H/(kind+'-declaration.json')).read_bytes())
 for c in components:
  key='src/patent_to_pilot/research/'+c;assert old['files_sha256'][key]==pins[key],(kind,c)
measurements=[json.loads(line) for line in (Q/'local-cpu-measurements.jsonl').read_text().splitlines()]
assert all(x['exit_code']==0 and not x['timed_out'] for x in measurements)
latest={p:h for x in measurements for p,h in x['test_sha256'].items()}
assert all(sha((R/p).read_bytes())==h for p,h in latest.items()),'tested source changed'
verification={'status':'PASS_AUTHORED_ENGINEERING_ONLY','test_files_sha256':latest,
 'measurements_sha256':sha((Q/'local-cpu-measurements.jsonl').read_bytes()),
 'qualified_package_sha256':package_identity(pins),'real_model_calls':0,'gpu_seconds':0,
 'scope':'Exact compact calibration worker; live GPU admission remains separate; no native fidelity claim.'}
if (A/'verification.json').exists():
 assert json.loads((A/'verification.json').read_bytes())==verification
else:
 with (A/'verification.json').open('x') as f:json.dump(verification,f,indent=2)
L=R/'docs/healthtech/audits/ptp-mtm-dapfam-resume-20261110/resource-ledger.json'
ledger=json.loads(L.read_bytes());cpu=ledger['r6_phase0_cpu'];r7=ledger['r7_cpu']
assert cpu['remote_cpu_reserved_seconds']==cpu['local_cpu_reserved_seconds']==r7['reserved_seconds']==0
# Covers local declaration, packaging and controller preparation; no further
# local metered test may alter this snapshot between sync and GPU claim.
cpu['local_cpu_conservative_charged_seconds']+=100;r7['conservative_charged_seconds']+=100
sync={'status':'VERIFIED_CPU_ONLY_RECONCILIATION','journal_identity':head['identity'],
 'owner_approval_sha256':approval_sha,'model_calls':0,'gpu_seconds':0,
 'old_ledger_sha256':document_hash(head['ledger']),'new_ledger_sha256':document_hash(ledger),
 'cpu_deltas':{k:cpu.get(k,0)-head['ledger']['r6_phase0_cpu'].get(k,0) for k in CPU_CHARGES+CPU_RESERVES},
 'evidence_sha256':[sha(p.read_bytes()) for p in [P/'terminal-observation.json',P/'pipeline-fixture-summary.json',
 Q/'local-cpu-measurements.jsonl',Q/'accounting-baseline.json',
 R/'docs/healthtech/audits/ptp-sg-compact-v2-preparation-20261111/summary.json']]}
validate_cpu_change(head['ledger'],ledger,sync)
old=json.loads((R/'docs/healthtech/audits/ptp-r5-execution-20261111/smoke-execution-declaration.json').read_bytes())
identity=json.loads((R/'docs/healthtech/audits/ptp-method-first-r2-weights-20261110/identity.json').read_bytes())
d={'stage':'calibration','attempt_id':'ptp-r7-calibration-20261112-v1','retry':False,'maximum_calls':24,'seconds':7200,
 'approval_sha256':head['identity'],'candidate_owner_approval_sha256':approval_sha,
 'package_sha256':package_identity(pins),'input_manifest_sha256':task_sha,
 'model_identity_sha256':outer['identity_sha256'],'decoder_sha256':old['decoder_sha256'],
 'tokenizer_sha256':identity['files']['tokenizer.json']['sha256'],'files_sha256':pins,
 'lmfe_source_sha256':outer['lmfe_source_sha256'],'ledger_generation':3,
 'transport_version':'sg-compact-transport-v2',
 'transport_sha256':pins['src/patent_to_pilot/research/sg_compact_transport.py'],
 'gold_sha256':pins['src/patent_to_pilot/research/r6_critic_calibration.py'],
 'criteria_sha256':pins['src/patent_to_pilot/research/r6_critic_tasks.py']}
d['configuration_sha256']=document_hash({k:d[k] for k in ('input_manifest_sha256','decoder_sha256','transport_sha256','gold_sha256','criteria_sha256')})
sources={
 'transport':[P/'pipeline-fixture-summary.json',P/'terminal-observation.json',A/'verification.json'],
 'attempt_accounting':[A/'verification.json'],
 'grammar':[H/'profile-terminal-observation.json',H/'critic-terminal-observation.json',P/'pipeline-fixture-summary.json'],
 'cohorts':[A/'verification.json',H/'native-input-summary.json'],
 'retrieval':[R/'docs/healthtech/audits/ptp-r6-calibration-20261111/verification.json'],
 'input_admission':[P/'pipeline-fixture-summary.json'],
 'isolation':[H/'isolation-receipts.json',A/'verification.json',A/'current-resource-probe.json']}
gates={}
for name,paths in sources.items():
 receipt={'gate':name,'status':'PASS','package_sha256':d['package_sha256'],
 'candidate_owner_approval_sha256':approval_sha,'dispatch_identity':{k:d[k] for k in IDENTITIES},
 'evidence_sha256':{p.relative_to(R).as_posix():sha(p.read_bytes()) for p in paths},
 'qualification':'ENGINEERING_PRECONDITIONS_ONLY; exact calibration path; live GPU/model/isolation checks required',
 'source_mapping':'Package exactly matches authored CPU pipeline; unchanged critic/profile grammar dependencies verified by hash; retrieval historical unchanged control only',
 'graph_status':'INPUT_ADMITTED_100_OF_114_NOT_FIDELITY'}
 receipt['receipt_sha256']=receipt_digest(receipt);gates[name]=receipt
d['gate_receipts']={k:v['receipt_sha256'] for k,v in gates.items()}
previous=probe['remote']['attempts'];assert len(previous)==1
prior=previous[0];assert prior['terminal']['failure_axis']=='EVALUATOR_CALIBRATION'
authority={'status':'OWNER_APPROVED_R7_SINGLE_CANDIDATE','journal_identity':head['identity'],
 'owner_approval_sha256':approval_sha,'plan_sha256':approval['plan_sha256'],
 'gold_or_threshold_changed':False,'previous_attempt_id':prior['id'],
 'previous_terminal_sha256':document_hash(prior['terminal']),'declaration_sha256':document_hash(d),
 'gold_sha256':d['gold_sha256'],'criteria_sha256':d['criteria_sha256'],'transport_sha256':d['transport_sha256'],
 'gpu_seconds':637200,'fidelity_seconds':169200,'full_dev_seconds':460800,'cpu_seconds':3600,
 'initial_gpu_seconds':base['gpu_charged_seconds'],'initial_fidelity_seconds':base['fidelity_charged_seconds']}
# Exercise the exact transitions on a disposable copy of the observed head.
# Never initialize or overwrite the real existing remote journal.
with tempfile.TemporaryDirectory(prefix='ptp-r7-shadow-') as td:
 path=Path(td)/'shadow.sqlite';initialize(path,head['identity'],head['ledger'],head['scope'])
 with sqlite3.connect(path) as db:
  db.execute('UPDATE head SET generation=?',(head['generation'],))
  db.execute('INSERT INTO attempts VALUES (?,?,?)',(prior['id'],encoded(prior['declaration']),encoded(prior['terminal'])))
 db.close()
 journal=R7DispatchJournal(path,head['identity'])
 journal.sync_cpu_ledger(expected_generation=1,new_ledger=ledger,receipt=sync,receipt_sha256=document_hash(sync))
 authorized=journal.authorize_calibration(expected_generation=2,ledger=ledger,declaration=d,gates=gates,
     authority=authority,authority_sha256=document_hash(authority))
 scope=authorized['scope']
 journal.claim(d,ledger,scope,gates,expected_generation=3)
dispatch=A/'dispatch';dispatch.mkdir(exist_ok=False)
values={'declaration':d,'ledger':ledger,'scope':scope,**{'gate:'+k:v for k,v in gates.items()}}
files={}
for role,value in values.items():
 path=dispatch/(role.replace(':','-')+'.json');path.write_text(json.dumps(value,indent=2)+'\n')
 files[role]={'path':path.name,'sha256':sha(path.read_bytes())}
manifest=dispatch/'manifest.json';manifest.write_text(json.dumps({'version':'r6-dispatch-files-v1','files':files},indent=2)+'\n')
mh=sha(manifest.read_bytes());load_dispatch(dispatch,manifest_path='manifest.json',manifest_sha256=mh)
for name,value in [('cpu-sync.json',sync),('candidate-authority.json',authority)]:
 with (A/name).open('x') as f:json.dump(value,f,indent=2)
L.write_text(json.dumps(ledger,indent=2)+'\n')
summary={'status':'FROZEN_QUALIFIED_NOT_LIVE_AUTHORIZED','attempt_id':d['attempt_id'],'maximum_calls':24,'seconds':7200,
 'manifest_sha256':mh,'package_sha256':d['package_sha256'],'configuration_sha256':d['configuration_sha256'],
 'task_manifest_sha256':task_sha,'owner_approval_sha256':approval_sha,'journal_original_identity':head['identity'],
 'cpu_sync_sha256':document_hash(sync),'candidate_authority_sha256':document_hash(authority),
 'expected_current_generation':1,'after_cpu_sync_generation':2,'after_authorization_generation':3,
 'GPU_remaining_after_reservation_seconds':ledger['gpu_remaining_seconds']-7200,
 'fidelity_remaining_after_reservation_seconds':ledger['fidelity_generation_remaining_seconds']-7200,
 'model_calls':0,'real_journal_mutation':False,'shadow_transition_and_claim':'PASS'}
with (A/'freeze-summary.json').open('x') as f:json.dump(summary,f,indent=2)
print(json.dumps(summary))
