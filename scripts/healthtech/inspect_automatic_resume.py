"""Read-only current journal identity/cost inspection; never adopts or dispatches."""
import json
from pathlib import Path
import subprocess
import sys


def main():
    root = Path(__file__).resolve().parents[2]
    ledger = json.loads((root / 'docs/healthtech/audits/ptp-mtm-dapfam-resume-20261110/resource-ledger.json').read_bytes())
    code = '''import sqlite3,json,hashlib,subprocess
def h(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
with sqlite3.connect('file:/home/chaw/patent-to-pilot-jobs/ptp-r6-control/dispatch.sqlite?mode=ro',uri=True) as db:
 head=db.execute('SELECT identity,generation,ledger,scope,active FROM head').fetchone()
 attempts=db.execute('SELECT id,declaration,terminal FROM attempts ORDER BY id').fetchall()
ledger=json.loads(head[2]);scope=json.loads(head[3])
gpu=subprocess.run(['nvidia-smi','--query-compute-apps=pid,gpu_uuid','--format=csv,noheader'],capture_output=True,text=True,timeout=10,check=True).stdout
print(json.dumps({'journal_identity':head[0],'generation':head[1],'active':head[4],
 'ledger_sha256':h(ledger),'scope_sha256':h(scope),'attempts_sha256':h(attempts),
 'attempts':[{'id':r[0],'terminal':r[2] is not None} for r in attempts],
 'outstanding_reservations':[r.get('attempt_id') for r in scope.get('reservations',[]) if r.get('status') not in ('SETTLED','CANCELLED_PRE_DISPATCH')],
 'approved_gpu_occupied':'GPU-277ccc57-c3e5-0731-cd49-f4f8695f7089' in gpu,
 'gpu_remaining_seconds':ledger['gpu_remaining_seconds'],
 'fidelity_remaining_seconds':ledger['fidelity_generation_remaining_seconds'],
 'cpu':ledger['r6_phase0_cpu'],'new_model_calls':0}))
'''
    proc = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10',
                           'chaw@100.77.149.83', 'python3 -'], input=code.encode(), capture_output=True, timeout=30)
    if proc.returncode:
        raise RuntimeError('read-only remote inspection failed: ' + proc.stderr.decode()[-1000:])
    result = json.loads(proc.stdout)
    sys.path.insert(0, str(root / 'src'))
    from patent_to_pilot.research.r6_dispatch_journal import document_hash
    result['local_ledger_matches'] = document_hash(ledger) == result['ledger_sha256']
    if len(sys.argv) != 2:
        raise ValueError('explicit new receipt path required')
    with Path(sys.argv[1]).open('x', encoding='utf-8') as target:
        json.dump(result, target, indent=2)
        target.write('\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'cpu'}))


if __name__ == '__main__':
    main()
