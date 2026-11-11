from pathlib import Path
import json,subprocess
A=Path('C:/Users/User/Desktop/myProject/patent-to-pilot/docs/healthtech/audits/ptp-r7-calibration-20261112')
code=r'''
from pathlib import Path
import json,sys,hashlib
p=Path('/home/chaw/patent-to-pilot-jobs/ptp-r7-calibration-20261112-v1')
sys.path.insert(0,str(p))
from r3_engine_client import Engine
state=Engine().inspect(p.name)['State']
if state['Running'] or state['Pid']!=0 or not (p/'terminal.json').exists():
 print(json.dumps({'status':'WAIT_SAME_JOB','container_state':state}));sys.exit(0)
manifest_raw=(p/'dispatch/manifest.json').read_bytes()
assert hashlib.sha256(manifest_raw).hexdigest()=='a73e6502bf199780c53db790f8a9da0909a84bdef637687cf93afdc588905434'
manifest=json.loads(manifest_raw)
for entry in manifest['files'].values():
 path=(p/'dispatch'/entry['path']).resolve()
 assert path.is_relative_to((p/'dispatch').resolve())
 assert hashlib.sha256(path.read_bytes()).hexdigest()==entry['sha256']
d=json.loads((p/'dispatch/declaration.json').read_bytes())
for name,expected in d['files_sha256'].items():
 path=(p/'code'/name).resolve()
 assert path.is_relative_to((p/'code').resolve())
 assert hashlib.sha256(path.read_bytes()).hexdigest()==expected
sys.path[:0]=[str(p/'code/src'),'/home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031/venv/lib/python3.12/site-packages']
from patent_to_pilot.research.r6_critic_calibration import assess
from patent_to_pilot.research.r7_calibration_runner import frozen_tasks
from patent_to_pilot.research.r6_reference_runner import encoded,sha
from patent_to_pilot.research.sacr_outcomes import summarize_costs
from patent_to_pilot.research.r6_dispatch_journal import document_hash
from patent_to_pilot.research.sacr_generation import GenerationLimits
from patent_to_pilot.research.sacr_generation_receipt import bind_generation_record
from patent_to_pilot.research.sg_compact_transport import interpret,VERSION
from patent_to_pilot.research.mtm_runtime import InputBoundaryError
from jsonschema.exceptions import ValidationError
terminal=json.loads((p/'terminal.json').read_bytes())
assert terminal['container_state']['Running'] is False and terminal['container_state']['Pid']==0
d=json.loads((p/'dispatch/declaration.json').read_bytes())
assert terminal['attempt_id']==terminal['container_name']==p.name
assert terminal['declaration_sha256']==document_hash(d)
assert sha(encoded(frozen_tasks()))==d['input_manifest_sha256']
root=p/'out/attempt/calibration'
records=sorted(root.glob('unit-*/generation.json'))
markers=sorted(root.glob('unit-*-diagnostics-private/backend-dispatch.json'))
returns=sorted(root.glob('unit-*-diagnostics-private/backend-return.json'))
summary={'status':'TERMINAL_VERIFIED','terminal':terminal,'terminal_file_sha256':sha((p/'terminal.json').read_bytes()),
 'authoritative_state':state,'generation_records':len(records),'backend_dispatch_markers':len(markers),
 'backend_return_markers':len(returns),'counts_note':'Observed artifacts; dispatch intent alone is not completed inference.',
 'records_status_counts':{},'raw_private_retained':True,'retry':False,
 'frozen_tasks_sha256':sha(encoded(frozen_tasks()))}
for path in records:
 status=json.loads(path.read_bytes())['status']
 summary['records_status_counts'][status]=summary['records_status_counts'].get(status,0)+1
if (root/'result.json').exists() and (root/'calibration-assessment.json').exists():
 result=json.loads((root/'result.json').read_bytes());saved=json.loads((root/'calibration-assessment.json').read_bytes())
 assert saved['cohort_result_sha256']==sha((root/'result.json').read_bytes())
 assert saved['tasks_sha256']==d['input_manifest_sha256']
 assert saved['status']==saved['assessment']['status']
 assert saved['events']==result['events'] and saved['costs']==result['costs']==summarize_costs(result['events'])
 if result['status']=='SCREENING_COMPLETE_NOT_FIDELITY' and len(result['results'])==24:
  assert len(records)==len(markers)==len(returns)==len(result['events'])==24
  rows=[];rejected=0;tasks=frozen_tasks();limits=GenerationLimits()
  for i,row in enumerate(result['results']):
   raw=(root/f'unit-{i:03}/generation.json').read_bytes()
   assert sha(raw)==row['generation_sha256'] and json.loads(raw)['text']==row['critic_text']
   task=tasks[i]['prepared']
   assert row['compact_messages_sha256']==sha(encoded(task['messages'])) and row['compact_version']==VERSION
   assert row['query_id']==task['original']['payload']['query_id']
   reservation=json.loads((root/f'unit-{i:03}/reservation.json').read_bytes())
   assert reservation['status']=='RESERVED' and reservation['retry'] is False
   assert reservation['messages_sha256']==sha(encoded(task['messages'])) and reservation['limits']==limits.__dict__
   event=json.loads((root/f'unit-{i:03}/cost.json').read_bytes());assert event==result['events'][i]
   assert event['query_id']==row['query_id'] and event['stage']=='critic' and event['status']=='COMPLETED'
   assert event['event_id']==sha(encoded([saved['run_id'],row['query_id'],'critic']))
   binding=bind_generation_record(raw,expected_sha256=sha(raw),limits=limits,metrics=event['metrics'])
   expected_reason=binding['record']['status']
   if expected_reason=='EOS_COMPLETE':
    try:interpret(row['critic_text'].encode(),task);expected_reason='VALID_CRITIC'
    except (InputBoundaryError,UnicodeError,ValidationError):expected_reason='INVALID_EVALUATOR'
   assert row['reason']==expected_reason
   rejected+=expected_reason!='VALID_CRITIC'
   rows.append({'case_id':row['query_id'],'critic_text':row['critic_text']})
  rescored=assess(rows)
  rescored['execution_rejected_cases']=rejected
  if rejected:rescored['status']='CALIBRATION_FAILED'
  assert rescored==saved['assessment']
  summary.update(raw24_reassessment='MATCHES_FROZEN_ASSESSOR',assessment=rescored,
                 costs=saved['costs'],outcome=saved['status'],reason_counts={})
  for row in result['results']:
   reason=row['reason'];summary['reason_counts'][reason]=summary['reason_counts'].get(reason,0)+1
 else:
  summary.update(outcome=saved['status'],assessment=saved['assessment'],costs=saved['costs'])
 summary['assessment_file_sha256']=sha((root/'calibration-assessment.json').read_bytes())
 summary['cohort_result_sha256']=sha((root/'result.json').read_bytes())
else:
 summary.update(outcome='INCOMPLETE_NO_ASSESSMENT',raw24_reassessment='NOT_POSSIBLE')
print(json.dumps(summary))
'''
r=subprocess.run(['ssh','-o','BatchMode=yes','chaw@100.77.149.83','python3 -'],input=code.encode(),capture_output=True,timeout=45)
if r.returncode:
 print(r.stderr.decode()[-3000:]);r.check_returncode()
value=json.loads(r.stdout)
if value['status']=='TERMINAL_VERIFIED':
 p=A/'terminal-verification.json'
 if p.exists():assert json.loads(p.read_bytes())==value
 else:p.write_text(json.dumps(value,indent=2)+'\n')
print(json.dumps(value))
