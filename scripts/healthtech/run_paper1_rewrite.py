"""Paper 1 FA/GR native rewrite batch (frozen protocol 2026-11-13): one arm per job, one grammar-constrained
call per query, global call ceiling, stop on any backend exception; no corpus/qrels/evaluator mounts."""
import hashlib
import importlib.util
import json
import signal
import sys
import time
from pathlib import Path

ROOT = Path('/code')
sys.path.insert(0, str(ROOT / 'src'))
STAGE_SECONDS = {'synthetic': 1800, 'fidelity': 3600, 'full_dev': 10800}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    from patent_to_pilot.healthtech.local_execution import check_local_window, local_gpu_slot
    from patent_to_pilot.research.r7_dispatch_files import validate_worker_package, validate_deadline
    from patent_to_pilot.research.sacr_native_fidelity import write_new
    from patent_to_pilot.research.paper1_rewrite_runner import run_rewrite, USE
    from patent_to_pilot.research.paper1_rewrite_arms import prepare
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
    if (d.get('arm') not in ('FA', 'GR') or d['stage'] not in STAGE_SECONDS or d['maximum_calls'] != d['queries']
            or d['seconds'] > STAGE_SECONDS[d['stage']]):
        raise RuntimeError('Paper 1 rewrite contract required')
    validate_deadline(stop, time.monotonic(), d['seconds'])
    validate_worker_package(ROOT, d['files_sha256'], d['package_sha256'])
    task_raw = Path('/dispatch/queries.jsonl').read_bytes()
    if sha(task_raw) != d['input_manifest_sha256']: raise RuntimeError('rewrite input changed')
    tasks = [json.loads(line) for line in task_raw.decode().splitlines() if line.strip()]
    if len(tasks) != d['queries'] or any(set(t) != {'id', 'text'} for t in tasks) or len({t['id'] for t in tasks}) != len(tasks):
        raise RuntimeError('frozen rewrite query set required')
    if type(d.get('input_token_cap')) is not int or not 1000 <= d['input_token_cap'] <= 8192:
        raise RuntimeError('declared memory-safe input cap required')
    if type(d.get('max_consecutive_whitespaces')) is not int: raise RuntimeError('declared whitespace cap required')
    if d.get('force_json_field_order') is not True: raise RuntimeError('declared JSON field order required')
    out = Path('/out/attempt'); out.mkdir(exist_ok=False)
    calls = 0; started = time.monotonic()
    def admission(*args):
        check_local_window()
        if time.monotonic()+30 >= stop: raise TimeoutError('worker shutdown reserve')
    def expired(*args): raise TimeoutError('rewrite deadline')
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
            admitted = {t['id']: len(tokenizer.apply_chat_template(prepare(d['arm'], t['text'], t['id'])['messages'],
                        tokenize=True, add_generation_prompt=True, enable_thinking=False)) for t in tasks}
            write_new(out/'before-model-input-admission.json', {'arm': d['arm'], 'input_token_cap': d['input_token_cap'],
                'over_limit': sum(v > d['input_token_cap'] for v in admitted.values()),
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
                                max_consecutive_whitespaces=d['max_consecutive_whitespaces'],
                                force_json_field_order=d['force_json_field_order'], lmfe_source_sha256=d['lmfe_source_sha256'])
            executor = request_bound_executor(tokenizer=tokenizer, model_factory=backend.factory,
                device='cuda:0', eos_token_ids=[151645,151643], check_admission=admission,
                peak_memory_bytes=lambda: torch.cuda.max_memory_allocated())
            decisions = {}
            for index, t in enumerate(tasks):
                adapted = adapt_reserved_executor(destination=out / 'backend' / ('q%03d' % index), executor=executor,
                                                  stages=('rewrite',))
                def invoke(stage, request):
                    nonlocal calls
                    admission()
                    if calls >= d['maximum_calls']: raise RuntimeError('call ceiling exhausted')
                    calls += 1
                    write_new(out / f'call-{calls}.json', {'stage': stage, 'arm': d['arm'], 'query_index': index,
                                                           'status': 'CONSUMED_BEFORE_BACKEND', 'retry': False})
                    return adapted(stage, request)
                # Per-query grammar directory (R6Backend writes '<stage>-grammar-private.json' exclusively).
                backend.output_root = out / 'grammar' / ('q%03d' % index); backend.output_root.mkdir(parents=True)
                result = run_rewrite(destination=out / 'queries' / ('q%03d' % index), arm=d['arm'], query_id=t['id'],
                    source=t['text'], invoke=invoke, admit=admission, count_tokens=backend.count_tokens,
                    input_token_cap=d['input_token_cap'])
                decisions[t['id']] = {'action': result['action'], 'reason': result['reason']}
            write_new(out / 'decisions-private.json', decisions)
            reasons = sorted({v['reason'] for v in decisions.values()})
            write_new(out / 'completion.json', {'status': 'PIPELINE_TERMINAL', 'arm': d['arm'], 'queries': len(tasks),
                'rewrites_used': sum(v['action'] == USE for v in decisions.values()),
                'fallbacks': sum(v['action'] != USE for v in decisions.values()),
                'reasons': {r: sum(v['reason'] == r for v in decisions.values()) for r in reasons},
                'call_slots_consumed': calls, 'wall_seconds': time.monotonic()-started,
                'process_cpu_seconds': time.process_time(), 'semantic_certified': False})
    except BaseException as error:
        write_new(out / 'failure.json', {'exception_type': type(error).__name__, 'arm': d.get('arm'),
            'call_slots_consumed': calls, 'process_cpu_seconds': time.process_time(), 'retry': False,
            'cost_status': 'CONTROLLER_AND_DIAGNOSTICS_RECONCILIATION_REQUIRED'})
        raise
    finally:
        signal.alarm(0)


if __name__ == '__main__':
    main()
