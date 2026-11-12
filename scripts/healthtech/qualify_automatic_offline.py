"""Record exact local test evidence; no data, backend or journal operations."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
TESTS = ['test_automatic_supervisor_configuration.py','test_automatic_live_admission.py',
 'test_automatic_dispatch_journal.py','test_automatic_executor_adapter.py',
 'test_sacr_automatic_runner.py','test_km_automatic_review.py',
 'test_patent_structure_marking.py','test_automatic_screening.py',
 'test_sg_automatic_evidence.py','test_sg_bounded_traversal.py']


def main():
    destination = Path(sys.argv[1]); destination.mkdir(parents=True, exist_ok=False)
    paths = [ROOT/'tests'/name for name in TESTS]
    started = time.monotonic()
    result = subprocess.run([sys.executable,'-m','pytest',*[str(p) for p in paths],'-q'],
                            cwd=ROOT,capture_output=True,text=True,timeout=180)
    elapsed = time.monotonic()-started
    (destination/'pytest-output.txt').write_text(result.stdout+result.stderr,encoding='utf-8')
    sources = [p for p in (ROOT/'src/patent_to_pilot/research').glob('*.py')
               if p.name.startswith(('automatic_', 'sacr_automatic', 'km_automatic', 'patent_structure', 'sg_automatic', 'sg_bounded'))]
    sources += paths + [ROOT/'scripts/healthtech'/name for name in
                       ('run_automatic_synthetic.py','supervise_automatic_synthetic.py','qualify_automatic_offline.py')]
    receipt = {'status':'PASS_OFFLINE_ENGINEERING' if result.returncode==0 else 'FAIL_OFFLINE_ENGINEERING',
               'exit_code':result.returncode,'wall_seconds':elapsed,
               'cpu_accounting':'PENDING_CONSERVATIVE_SETTLEMENT','model_calls':0,'gpu_seconds':0,
               'runtime_qualified':False,'semantic_certified':False,
               'files_sha256':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}}
    (destination/'verification.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in receipt.items() if k!='files_sha256'}))
    print(result.stdout)
    raise SystemExit(result.returncode)


if __name__ == '__main__': main()
