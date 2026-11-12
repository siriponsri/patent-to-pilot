"""Native SACR fidelity batch (NATIVE-STAGES-20261112): frozen pilot query texts, <=2 calls/query,
global call ceiling, stop on any backend exception; no corpus/qrels/evaluator mounts."""
import hashlib
import importlib.util
import json
import signal
import sys
import time
from pathlib import Path

ROOT = Path('/code')
sys.path.insert(0, str(ROOT / 'src'))


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    from patent_to_pilot.healthtech.local_execution import check_local_window, local_gpu_slot
    from patent_to_pilot.research.r7_dispatch_files import validate_worker_package, validate_deadline
    from patent_to_pilot.research.sacr_native_fidelity import write_new
    from patent_to_pilot.research.sacr_automatic_runner import run_query
    from patent_to_pilot.research.automatic_executor_adapter import adapt_reserved_executor
    from patent_to_pilot.research.sacr_r6_bundle_runner import request_bound_executor
    from patent_to_pilot.research.r6_backend import R6Backend
    stop = float(sys.argv[1])
    raw = Path('/dispatch/declaration.json').read_bytes()
    if sha(raw) != sys.argv[2]: raise RuntimeError('dispatch declaration changed')
    d = json.loads(raw)
    import resource
    if type(d.get('cpu_seconds')) is not int or d['cpu_seconds'] <= 60:
        raise RuntimeError('aggregate worker/controller CPU reservation required')
    resource.setrlimit(resource.RLIMIT_CPU, (d['cpu_seconds']-60, d['cpu_seconds']-60))
    if d['stage'] != 'fidelity' or d['maximum_calls'] > 2 * d['queries'] or d['seconds'] > 3600:
        raise RuntimeError('native fidelity contract required')
    validate_deadline(stop, time.monotonic(), d['seconds'])
    validate_worker_package(ROOT, d['files_sha256'], d['package_sha256'])
    task_raw = Path('/dispatch/queries.jsonl').read_bytes()
    if sha(task_raw) != d['input_manifest_sha256']: raise RuntimeError('native input changed')
    tasks = [json.loads(line) for line in task_raw.decode().splitlines() if line.strip()]
    if len(tasks) != d['queries'] or any(set(t) != {'id', 'text'} for t in tasks):
        raise RuntimeError('frozen native query set required')
    km_raw = (ROOT / 'docs/healthtech/research/plans/PATENT-STRUCTURE-KM.md').read_bytes()
    if sha(km_raw) != d['km_sha256']: raise RuntimeError('KM changed')
    out = Path('/out/attempt'); out.mkdir(exist_ok=False)
    calls = 0; started = time.monotonic()
    def admission(*args):
        check_local_window()
        if time.monotonic()+30 >= stop: raise TimeoutError('worker shutdown reserve')
    def expired(*args): raise TimeoutError('synthetic deadline')
    signal.signal(signal.SIGALRM, expired); signal.signal(signal.SIGTERM, expired)
    signal.alarm(max(1, int(stop-time.monotonic())))
    try:
        admission()
        identity_path = ROOT / 'docs/healthtech/audits/ptp-method-first-r2-weights-20261110/identity.json'
        if sha(identity_path.read_bytes()) != d['model_sha256']: raise RuntimeError('model identity pin changed')
        spec = importlib.util.spec_from_file_location('weight_identity', ROOT / 'scripts/healthtech/inspect_qwen_weight_identity.py')
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        if module.observe(Path('/models/qwen3-8b'))['files'] != json.loads(identity_path.read_bytes())['files']:
            raise RuntimeError('model files changed')
        with local_gpu_slot(Path('/models/qwen3-8b')):
            import torch
            from transformers import AutoTokenizer, AutoModelForCausalLM, GenerationConfig
            tokenizer = AutoTokenizer.from_pretrained('/models/qwen3-8b', local_files_only=True)
            if sha(Path('/models/qwen3-8b/tokenizer.json').read_bytes()) != d['tokenizer_sha256']:
                raise RuntimeError('tokenizer identity changed')
            config = GenerationConfig.from_pretrained('/models/qwen3-8b', local_files_only=True)
            config.update(do_sample=False, num_beams=1, max_new_tokens=4096, use_cache=True,
                          eos_token_id=[151645,151643], pad_token_id=151643)
            if sha(json.dumps(config.to_dict(), sort_keys=True, separators=(',', ':')).encode()) != d['decoder_sha256']:
                raise RuntimeError('decoder changed')
            from patent_to_pilot.research.patent_structure_marking import prepare
            admitted = {}
            for t in tasks:
                marking = prepare(t['text'], t['id'], km_raw.decode(), d['km_sha256'])
                admitted[t['id']] = len(tokenizer.apply_chat_template(marking['messages'], tokenize=True,
                    add_generation_prompt=True, enable_thinking=False))
            write_new(out/'before-model-input-admission.json', {'over_limit': sum(v > 8192 for v in admitted.values()),
                'max_input_tokens': max(admitted.values()), 'queries': len(tasks), 'model_calls': 0})
            admission()
            model = AutoModelForCausalLM.from_pretrained('/models/qwen3-8b', local_files_only=True,
                torch_dtype=torch.float16, device_map='cuda:0', low_cpu_mem_usage=True, attn_implementation='eager').eval()
            model.generation_config = config
            if str(model.dtype) != 'torch.float16' or str(model.device) != 'cuda:0' or model.config._attn_implementation != 'eager':
                raise RuntimeError('loaded runtime changed')
            write_new(out / 'loaded-runtime.json', {'model_class': type(model).__name__,
                'dtype': str(model.dtype), 'device': str(model.device), 'attention': model.config._attn_implementation})
            backend = R6Backend(tokenizer=tokenizer, model=model, output_root=out,
                                lmfe_source_sha256=d['lmfe_source_sha256'])
            executor = request_bound_executor(tokenizer=tokenizer, model_factory=backend.factory,
                device='cuda:0', eos_token_ids=[151645,151643], check_admission=admission,
                peak_memory_bytes=lambda: torch.cuda.max_memory_allocated())
            decisions = {}
            for index, t in enumerate(tasks):
                adapted = adapt_reserved_executor(destination=out / 'backend' / ('q%03d' % index), executor=executor)
                def invoke(stage, request):
                    nonlocal calls
                    admission()
                    if calls >= d['maximum_calls']: raise RuntimeError('call ceiling exhausted')
                    calls += 1
                    write_new(out / f'call-{calls}.json', {'stage': stage, 'query_index': index, 'status': 'CONSUMED_BEFORE_BACKEND', 'retry': False})
                    return adapted(stage, request)
                if admitted[t['id']] > 8192:
                    decisions[t['id']] = {'action': 'ORIGINAL_QUERY_FALLBACK', 'screening': 'invalid_output', 'reason': 'INPUT_LIMIT'}
                    continue
                result = run_query(destination=out / 'queries' / ('q%03d' % index), query_id=t['id'], source=t['text'],
                    km_text=km_raw.decode(), km_sha256=d['km_sha256'], invoke=invoke,
                    admit=admission, count_tokens=backend.count_tokens)
                decisions[t['id']] = dict(result['decision'], reason=result.get('reason'))
            actions = [v['action'] for v in decisions.values()]
            write_new(out / 'decisions-private.json', decisions)
            write_new(out / 'completion.json', {'status': 'PIPELINE_TERMINAL', 'queries': len(tasks),
                'screened_candidates': actions.count('USE_SCREENED_CANDIDATE'),
                'fallbacks': sum(a == 'ORIGINAL_QUERY_FALLBACK' for a in actions),
                'reasons': {r: sum(v.get('reason') == r for v in decisions.values()) for r in sorted({str(v.get('reason')) for v in decisions.values()})},
                'call_slots_consumed': calls, 'wall_seconds': time.monotonic()-started,
                'process_cpu_seconds': time.process_time(), 'semantic_certified': False})
    except BaseException as error:
        write_new(out / 'failure.json', {'exception_type': type(error).__name__,
            'call_slots_consumed': calls, 'process_cpu_seconds': time.process_time(), 'retry': False,
            'cost_status': 'CONTROLLER_AND_DIAGNOSTICS_RECONCILIATION_REQUIRED'})
        raise
    finally:
        signal.alarm(0)


if __name__ == '__main__':
    main()
