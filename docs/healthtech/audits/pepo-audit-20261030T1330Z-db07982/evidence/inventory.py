from pathlib import Path
from hashlib import sha256
import csv,json,subprocess

repo=Path(r'C:\Users\User\Desktop\myProject\patent-to-pilot')
out=Path(__file__).resolve().parent
base='889958eeb3174a09df9ef3840231a0f0577f00f2'
head='db0798276e3158b04131b4e910abc0a11511e94c'
def git(*args):
    return subprocess.check_output(['git','-c','safe.directory='+repo.as_posix(),'-C',str(repo),*args],text=True,encoding='utf-8')
commits=[dict(zip(['sha','utc','subject'],line.split('|',2))) for line in git('log','--reverse','--format=%H|%cI|%s',base+'..'+head).splitlines()]
paths=git('diff','--name-only',base,head).splitlines()
files=[]
for rel in paths:
    p=repo/rel
    files.append({'path':rel,'exists':p.is_file(),'bytes':p.stat().st_size if p.is_file() else None,
        'sha256':sha256(p.read_bytes()).hexdigest() if p.is_file() else None})
audits=[]
for d in sorted((repo/'docs/healthtech/audits').glob('luna-long-run-*')):
    if not any(rel.startswith(d.relative_to(repo).as_posix()+'/') for rel in paths):continue
    readme=d/'README.md'
    text=readme.read_text(encoding='utf-8') if readme.exists() else ''
    receipt=d/'verification.json'
    data=json.loads(receipt.read_text(encoding='utf-8')) if receipt.exists() else {}
    keys={k:v for k,v in data.items() if any(x in k.lower() for x in ['commit','status','head','base','source_revision']) and isinstance(v,(str,int,float,bool,type(None)))}
    audits.append({'run':d.name,'path':d.relative_to(repo).as_posix(),'title':text.splitlines()[0] if text else '',
        'status_lines':[line for line in text.splitlines() if 'Status:' in line or 'สถานะ' in line][:3],
        'receipt_fields':keys,'receipt_exists':receipt.exists(),
        'readme_sha256':sha256(readme.read_bytes()).hexdigest() if readme.exists() else None,
        'verification_sha256':sha256(receipt.read_bytes()).hexdigest() if receipt.exists() else None,
        'independent_verification':'receipt/source inventory only; substantive checks identified separately in AUDIT'})
(out/'commit-inventory.json').write_text(json.dumps(commits,indent=2),encoding='utf-8')
(out/'changed-file-manifest.json').write_text(json.dumps(files,indent=2),encoding='utf-8')
(out/'milestone-inventory.json').write_text(json.dumps(audits,ensure_ascii=False,indent=2),encoding='utf-8')
with (out/'claim-evidence-matrix.csv').open('w',encoding='utf-8',newline='') as f:
    w=csv.writer(f);w.writerow(['run','claimed_status','evidence','verified_scope'])
    for row in audits:w.writerow([row['run'],'; '.join(row['status_lines']) or row['receipt_fields'].get('status','UNKNOWN'),row['path']+'/verification.json',row['independent_verification']])
print(json.dumps({'commits':len(commits),'changed_files':len(files),'audits_inventoried':len(audits),
    'changed_python_source_script_test_files':sum(x['path'].endswith('.py') and x['path'].split('/')[0] in ['src','scripts','tests'] for x in files)}))
