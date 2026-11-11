"""One bounded read-only SSH character probe, no models/data/remote writes."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from patent_to_pilot.research.sacr_grammar_qualification import fixture_matrix


def main():
    out = ROOT / 'docs/healthtech/audits/ptp-r5-diagnosis-20261111/character-probe'
    out.mkdir(parents=True, exist_ok=False)
    matrix = fixture_matrix()
    old = json.loads((ROOT / 'docs/healthtech/audits/ptp-r4-preparation-20261111/cpu-v2-declaration.json').read_bytes())
    matrix['lmfe_source_sha256'] = old['lmfe_source_sha256']
    raw = json.dumps(matrix, ensure_ascii=True, sort_keys=True).encode()
    (out / 'fixtures.json').write_bytes(raw)
    worker = (ROOT / 'scripts/healthtech/qualify_sacr_character_grammar.py').read_text(encoding='utf-8')
    worker = worker.split("if __name__ == '__main__':")[0]
    code = worker + '\nmain(' + repr(matrix) + ')\n'
    declaration = {'status': 'DECLARED_CPU_DIAGNOSIS', 'authority': 'Owner current request to diagnose and test grammar',
        'fixture_sha256': hashlib.sha256(raw).hexdigest(), 'worker_sha256': hashlib.sha256(code.encode()).hexdigest(),
        'cpu_seconds': 60, 'wall_seconds': 90, 'cpu_affinity_count': 2, 'ram_bytes': 2*1024**3,
        'no_model_tokenizer_corpus_queries_qrels_test': True, 'no_remote_files_written': True, 'retry': False}
    (out / 'declaration.json').write_text(json.dumps(declaration, indent=2), encoding='utf-8')
    start = time.monotonic()
    receipt = {'status': 'UNKNOWN', 'retry': False, 'model_calls': 0, 'gpu_seconds': 0}
    try:
        result = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10',
            'chaw@100.77.149.83', 'python3 -I -S -B -'], input=code.encode(), capture_output=True, timeout=110)
        (out / 'stdout.json').write_bytes(result.stdout)
        (out / 'stderr.txt').write_bytes(result.stderr)
        receipt.update(status='TERMINAL', exit_code=result.returncode)
        if result.returncode == 0:
            observation = json.loads(result.stdout)
            receipt.update(r5_mismatches=[r['case'] for r in observation['results']
                if r['version']=='r5' and not r['matches_schema_expectation']],
                r4_mismatches=[r['case'] for r in observation['results']
                if r['version']=='r4' and not r['matches_schema_expectation']],
                worker_wall_seconds=observation['wall_seconds'], peak_rss_bytes=observation['peak_rss_bytes'])
    finally:
        receipt['whole_wall_seconds'] = time.monotonic()-start
        (out / 'terminal.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    print(json.dumps(receipt))


if __name__ == '__main__': main()
