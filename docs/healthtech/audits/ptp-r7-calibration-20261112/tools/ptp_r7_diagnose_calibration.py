from pathlib import Path
import json,subprocess
A=Path('C:/Users/User/Desktop/myProject/patent-to-pilot/docs/healthtech/audits/ptp-r7-calibration-20261112')
assert json.loads((A/'terminal-verification.json').read_bytes())['raw24_reassessment']=='MATCHES_FROZEN_ASSESSOR'
code=r'''
from pathlib import Path
import sys,json,hashlib,collections
p=Path('/home/chaw/patent-to-pilot-jobs/ptp-r7-calibration-20261112-v1')
sys.path[:0]=[str(p/'code/src'),'/home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031/venv/lib/python3.12/site-packages']
from patent_to_pilot.research.r6_critic_calibration import fixtures,request
from patent_to_pilot.research.reference_critic_v1 import interpret
from patent_to_pilot.research.mtm_runtime import decode_json
from jsonschema import Draft202012Validator
rows=[]
for i,case in enumerate(fixtures()):
 raw=(p/f'out/attempt/calibration/unit-{i:03}/generation.json').read_bytes()
 record=json.loads(raw);prepared=request(case)
 row={'case_id':case['case_id'],'expected_kind':case['expected']['kind'],
      'generation_sha256':hashlib.sha256(raw).hexdigest(),'generation_status':record['status']}
 try:
  value=decode_json(record['text'].encode())
  errors=list(Draft202012Validator(prepared['schema']).iter_errors(value))
  row['schema_errors']=[{'validator':e.validator,'path':list(e.path)} for e in errors]
  if not errors:
   flags={k for k,v in value['dimensions'].items() if v!='supported'}
   row.update(flagged_dimensions=sorted(flags),finding_dimensions=[f['dimension'] for f in value['findings']],
    findings_on_supported_dimensions=sum(f['dimension'] not in flags for f in value['findings']),
    findings_without_references=sum(not(f['source_units'] or f['candidate_units']) for f in value['findings']),
    findings_with_blank_reason=sum(not f['reason'].strip() for f in value['findings']),
    missing_flagged_dimensions=sorted(flags-{f['dimension'] for f in value['findings']}))
  try:interpret(record['text'].encode(),prepared);row['contract']='VALID'
  except Exception as e:row.update(contract=type(e).__name__,contract_reason=str(e)[:180] if not errors else 'JSON_SCHEMA_REJECTION')
 except Exception as e:row.update(contract=type(e).__name__,contract_reason='PARSE_FAILURE')
 rows.append(row)
print(json.dumps({'status':'READ_ONLY_RAW_DIAGNOSIS','model_calls':0,'output_repaired':False,
 'contract_counts':dict(collections.Counter(row.get('contract_reason',row['contract']) for row in rows)),
 'rows':rows,'no_native_semantic_conclusion':True}))
'''
r=subprocess.run(['ssh','-o','BatchMode=yes','chaw@100.77.149.83','python3 -'],input=code.encode(),capture_output=True,timeout=30)
if r.returncode:print(r.stderr.decode()[-2000:]);r.check_returncode()
value=json.loads(r.stdout)
(A/'calibration-diagnosis.json').write_text(json.dumps(value,indent=2)+'\n')
print(json.dumps({k:v for k,v in value.items() if k!='rows'}))
print(json.dumps(value['rows'][:2]))
