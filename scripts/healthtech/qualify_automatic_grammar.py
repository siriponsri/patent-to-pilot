"""CPU-only real-tokenizer grammar replay; no model weights or corpus reads."""
import hashlib
import json
from pathlib import Path
import resource
import signal
import sys
import time

ROOT = Path('/code')
sys.path.insert(0, str(ROOT/'src'))


def main():
    raw = Path('/declaration.json').read_bytes()
    if hashlib.sha256(raw).hexdigest() != sys.argv[1]: raise RuntimeError('declaration changed')
    d = json.loads(raw)
    if d.get('kind') != 'automatic-grammar-only' or d.get('model_calls') != 0 or d.get('gpu_seconds') != 0:
        raise RuntimeError('CPU-only scope required')
    if type(d.get('cpu_seconds')) is not int or not 1 <= d['cpu_seconds'] <= 540:
        raise RuntimeError('bounded CPU budget required')
    resource.setrlimit(resource.RLIMIT_CPU, (d['cpu_seconds'],d['cpu_seconds']))
    def expired(*args): raise TimeoutError('grammar deadline')
    signal.signal(signal.SIGALRM,expired); signal.signal(signal.SIGTERM,expired); signal.alarm(540)
    out = Path('/out/attempt'); out.mkdir(exist_ok=False)
    started = time.monotonic()
    try:
        from patent_to_pilot.research.r7_dispatch_files import validate_worker_package
        validate_worker_package(ROOT,d['files_sha256'],d['package_sha256'])
        model = Path('/models/qwen3-8b')
        # Only tokenizer files are inspected; model tensors are never opened.
        for name, expected in d['tokenizer_files_sha256'].items():
            if name not in ('tokenizer.json','tokenizer_config.json','special_tokens_map.json','config.json','vocab.json','merges.txt'):
                raise RuntimeError('non-tokenizer file in CPU manifest')
            if hashlib.sha256((model/name).read_bytes()).hexdigest() != expected:
                raise RuntimeError('tokenizer file changed')
        km_raw = (ROOT/'docs/healthtech/research/plans/PATENT-STRUCTURE-KM.md').read_bytes()
        if hashlib.sha256(km_raw).hexdigest() != d['km_sha256']: raise RuntimeError('KM changed')
        from transformers import AutoTokenizer
        from patent_to_pilot.research.r6_backend import R6Backend
        from patent_to_pilot.research.automatic_grammar_cases import qualify
        tokenizer = AutoTokenizer.from_pretrained(str(model),local_files_only=True)
        backend = R6Backend(tokenizer=tokenizer,output_root=out,lmfe_source_sha256=d['lmfe_source_sha256'])
        result = qualify(backend, km_raw.decode())
        result.update(wall_seconds=time.monotonic()-started,process_cpu_seconds=time.process_time())
        (out/'qualification.json').write_text(json.dumps(result,indent=2)+'\n')
        if result['status'] != 'PASS_GRAMMAR_ONLY': raise RuntimeError('grammar cases failed')
    except BaseException as error:
        (out/'failure.json').write_text(json.dumps({'exception_type':type(error).__name__,
            'process_cpu_seconds':time.process_time(),'wall_seconds':time.monotonic()-started,
            'model_calls':0,'gpu_seconds':0,'retry':False},indent=2)+'\n')
        raise
    finally: signal.alarm(0)


if __name__ == '__main__': main()
