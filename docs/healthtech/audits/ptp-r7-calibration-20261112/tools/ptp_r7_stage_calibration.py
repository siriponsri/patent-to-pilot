from pathlib import Path
import json,hashlib,subprocess,tarfile
R=Path('C:/Users/User/Desktop/myProject/patent-to-pilot');A=R/'docs/healthtech/audits/ptp-r7-calibration-20261112'
summary=json.loads((A/'freeze-summary.json').read_bytes());d=json.loads((A/'dispatch/declaration.json').read_bytes())
sha=lambda raw:hashlib.sha256(raw).hexdigest()
assert sha((A/'dispatch/manifest.json').read_bytes())==summary['manifest_sha256']
assert all(sha((R/p).read_bytes())==h for p,h in d['files_sha256'].items())
assert json.loads((R/'docs/healthtech/audits/ptp-mtm-dapfam-resume-20261110/resource-ledger.json').read_bytes())==json.loads((A/'dispatch/ledger.json').read_bytes())
t=Path('C:/Users/User/AppData/Local/Temp/ptp-r7-calibration-v1.tar')
with tarfile.open(t,'x') as tar:
 for name in d['files_sha256']:tar.add(R/name,arcname='code/'+name)
 for path in (A/'dispatch').glob('*.json'):tar.add(path,arcname='dispatch/'+path.name)
 for name in ['cpu-sync.json','candidate-authority.json']:tar.add(A/name,arcname=name)
 for name in ['r3_engine_client.py','supervise_sacr_r5_engine.py','supervise_r7_calibration.py']:
  tar.add(R/'scripts/healthtech'/name,arcname=name)
transport={'status':'FROZEN_TRANSPORT','bytes':t.stat().st_size,'sha256':sha(t.read_bytes()),
 'dispatch_manifest_sha256':summary['manifest_sha256'],'package_sha256':d['package_sha256']}
with (A/'transport.json').open('x') as f:json.dump(transport,f,indent=2)
host='chaw@100.77.149.83';job='/home/chaw/patent-to-pilot-jobs/'+d['attempt_id']
subprocess.run(['ssh','-o','BatchMode=yes',host,'mkdir '+job],check=True,timeout=30)
subprocess.run(['scp','-q',str(t),host+':'+job+'/transport.tar'],check=True,timeout=60)
code=f"""from pathlib import Path
import tarfile,hashlib,json,sys,sqlite3
p=Path('{job}');t=p/'transport.tar'
assert hashlib.sha256(t.read_bytes()).hexdigest()=='{transport['sha256']}'
with tarfile.open(t) as archive:
 assert all(not Path(m.name).is_absolute() and '..' not in Path(m.name).parts for m in archive.getmembers())
 archive.extractall(p,filter='data')
sys.path.insert(0,str(p/'code/src'))
from patent_to_pilot.research.r7_dispatch_files import load_dispatch,validate_worker_package
from patent_to_pilot.research.r7_dispatch_journal import R7DispatchJournal
from patent_to_pilot.research.r6_dispatch_journal import document_hash
e=load_dispatch(p/'dispatch',manifest_path='manifest.json',manifest_sha256='{summary['manifest_sha256']}')
d=e['declaration'];validate_worker_package(p/'code',d['files_sha256'],d['package_sha256'])
sync=json.loads((p/'cpu-sync.json').read_bytes());authority=json.loads((p/'candidate-authority.json').read_bytes())
assert document_hash(sync)=='{summary['cpu_sync_sha256']}'
assert document_hash(authority)=='{summary['candidate_authority_sha256']}'
journal=R7DispatchJournal(p.parent/'ptp-r6-control/dispatch.sqlite',d['approval_sha256'])
cpu=journal.sync_cpu_ledger(expected_generation=1,new_ledger=e['ledger'],receipt=sync,
 receipt_sha256='{summary['cpu_sync_sha256']}')
with (p/'cpu-sync-applied.json').open('x') as f:json.dump(cpu,f,indent=2)
result=journal.authorize_calibration(expected_generation=2,ledger=e['ledger'],declaration=d,gates=e['gates'],
 authority=authority,authority_sha256='{summary['candidate_authority_sha256']}')
assert result['scope']==e['scope'] and result['generation']==3
receipt={{'status':'STAGED_EXISTING_JOURNAL_EXTENDED_NO_RESET','attempt_id':d['attempt_id'],'generation':3,
 'manifest_sha256':'{summary['manifest_sha256']}','package_sha256':d['package_sha256'],
 'candidate_authority_sha256':'{summary['candidate_authority_sha256']}','model_calls':0,'active':None}}
with (p/'staging.json').open('x') as f:json.dump(receipt,f)
print(json.dumps(receipt))
"""
r=subprocess.run(['ssh','-o','BatchMode=yes',host,'python3 -'],input=code.encode(),capture_output=True,timeout=60)
if r.returncode:
 print(r.stderr.decode()[-3000:]);r.check_returncode()
receipt=json.loads(r.stdout)
with (A/'staging.json').open('x') as f:json.dump(receipt,f,indent=2)
print(json.dumps(receipt))
