from pathlib import Path
import json,subprocess
A=Path('C:/Users/User/Desktop/myProject/patent-to-pilot/docs/healthtech/audits/ptp-r7-calibration-20261112')
code=r'''
from pathlib import Path
import json,hashlib
b=Path('/home/chaw/patent-to-pilot-jobs');rows=[]
for name in ['ptp-r7-calibration-20261112-v1','ptp-sg-compact-input-preflight-20261111-v1']:
 raw=(b/name/'isolation.json').read_bytes();value=json.loads(raw);host=value['host_config']
 assert value['status']=='PASS_BEFORE_START'
 assert host['NetworkMode']=='none' and host['ReadonlyRootfs'] is True
 mounts=[{'target':m['Destination'],'readonly':not m['RW']} for m in value['mounts']]
 assert not any('socket' in m['target'] or 'docker.sock' in m['target'] or 'test' in m['target'] for m in mounts)
 expected=({'/code','/out','/dispatch','/deps','/models/qwen3-8b','/models/.GPU-277ccc57-c3e5-0731-cd49-f4f8695f7089.lock'}
  if name.startswith('ptp-r7-calibration') else {'/code','/out','/declaration.json','/deps','/models/qwen3-8b','/input/sources-private.jsonl','/input/source-sample.json','/input/alias-sample.json'})
 assert {m['target'] for m in mounts}==expected
 assert all(m['readonly'] for m in mounts if m['target'] not in ('/out','/models/.GPU-277ccc57-c3e5-0731-cd49-f4f8695f7089.lock'))
 rows.append({'job':name,'status':value['status'],'original_receipt_sha256':hashlib.sha256(raw).hexdigest(),
  'mounts':mounts,'network_mode':host['NetworkMode'],'readonly_rootfs':host['ReadonlyRootfs'],
  'NanoCpus':host['NanoCpus'],'container_memory_limit_bytes':host['Memory'],
  'gpu_device_request_count':len(host.get('DeviceRequests') or []),
  'host_source_paths':'WITHHELD_FROM_SANITIZED_RECEIPT'})
print(json.dumps({'status':'EXISTING_PRESTART_RECEIPTS_COLLECTED','new_experiment':False,
 'model_calls':0,'rows':rows,'limitation':'Runtime mount isolation; controlling agent retains acknowledged host access.'}))
'''
r=subprocess.run(['ssh','-o','BatchMode=yes','chaw@100.77.149.83','python3 -'],input=code.encode(),capture_output=True,timeout=30)
if r.returncode:print(r.stderr.decode()[-2500:]);r.check_returncode()
value=json.loads(r.stdout)
(A/'terminal-jobs-isolation.json').write_text(json.dumps(value,indent=2)+'\n')
print(json.dumps({'status':value['status'],'jobs':len(value['rows']),'model_calls':0}))
