"""Authored CPU backend through the ACTUAL native SACR batch worker (2 authored queries).

No pretrained weights are loaded. Doubles: GPU slot/window, weight observer,
model loader (authored CPU model that must pass the real grammar callback),
CUDA telemetry, device->cpu. Real: worker main, declaration/package/KM/tokenizer
/decoder checks, tokenizer, R6Backend grammar+EOS, request_bound_executor,
automatic executor adapter, durable call markers and run_query.
"""
from contextlib import nullcontext
import hashlib, importlib.util, json, sys, time
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, '/code/src')
sha = lambda b: hashlib.sha256(b).hexdigest()


def main():
    import resource
    start = time.monotonic(); cpu = time.process_time()
    receipt = {'status': 'INCOMPLETE', 'real_model_calls': 0, 'gpu_seconds': 0, 'retry': False}
    try:
        raw = Path('/declaration.json').read_bytes()
        if sha(raw) != sys.argv[1]: raise RuntimeError('fixture declaration changed')
        outer = json.loads(raw)
        if outer['kind'] != 'automatic-native-pipeline-fixture': raise RuntimeError('fixture scope changed')
        with Path('/out/SIMULATED-ARTIFACTS.json').open('x') as f:
            json.dump({'scope': 'ENTIRE_OUTPUT_TREE_AUTHORED_CPU_QUALIFICATION', 'real_model_calls': 0,
                       'internal_attempt_metrics': 'SIMULATED_NEVER_IMPORT_TO_RESEARCH_LEDGER'}, f, indent=2)
        from patent_to_pilot.research.r7_dispatch_files import validate_worker_package, package_identity
        validate_worker_package('/code', outer['files_sha256'], outer['package_sha256'])
        from patent_to_pilot.research import sacr_r6_bundle_runner
        from patent_to_pilot.research.r6_backend import R6Backend
        from patent_to_pilot.research.automatic_grammar_cases import SOURCE
        from patent_to_pilot.research.km_automatic_review import CHECKS
        from patent_to_pilot.healthtech import local_execution
        import torch
        from transformers import AutoModelForCausalLM, GenerationConfig
        km = Path('/code/docs/healthtech/research/plans/PATENT-STRUCTURE-KM.md').read_bytes()
        identity = Path('/code/docs/healthtech/audits/ptp-method-first-r2-weights-20261110/identity.json').read_bytes()
        config = GenerationConfig.from_pretrained('/models/qwen3-8b', local_files_only=True)
        config.update(do_sample=False, num_beams=1, max_new_tokens=4096, use_cache=True,
                      eos_token_id=[151645, 151643], pad_token_id=151643)
        task = '\n'.join(json.dumps(t) for t in ({'id': 'authored-native-001', 'text': SOURCE},
                {'id': 'authored-native-002', 'text': 'The heater is not activated during transport.'})).encode() + b'\n'
        d = {'attempt_id': 'authored-fixture', 'stage': 'fidelity', 'maximum_calls': 4, 'queries': 2, 'seconds': 1800,
             'cpu_seconds': 150, 'input_token_cap': 5800, 'max_consecutive_whitespaces': 48, 'force_json_field_order': True, 'files_sha256': outer['files_sha256'], 'package_sha256': outer['package_sha256'],
             'input_manifest_sha256': sha(task), 'km_sha256': sha(km), 'model_sha256': sha(identity),
             'tokenizer_sha256': sha(Path('/models/qwen3-8b/tokenizer.json').read_bytes()),
             'decoder_sha256': sha(json.dumps(config.to_dict(), sort_keys=True, separators=(',', ':')).encode()),
             'lmfe_source_sha256': outer['lmfe_source_sha256']}
        draw = json.dumps(d).encode()
        Path('/dispatch/declaration.json').write_bytes(draw); Path('/dispatch/queries.jsonl').write_bytes(task)

        class Qwen3ForCausalLM:
            dtype = torch.float16
            device = torch.device('cuda:0')  # observation double; tensors stay on cpu
            config = type('AuthoredConfig', (), {'_attn_implementation': 'eager'})()
            def __init__(self): self.calls = 0; self.tokens_checked = 0; self.text = None
            def eval(self): return self
            def generate(self, **kwargs):
                self.calls += 1
                seq = kwargs['input_ids'][0].detach().cpu().tolist()
                callback = kwargs.get('prefix_allowed_tokens_fn')
                for token in self.tokenizer.encode(self.text, add_special_tokens=False) + [151645]:
                    if callback is not None and token not in callback(0, torch.tensor(seq, dtype=torch.long)):
                        raise RuntimeError('authored response violates actual grammar')
                    seq.append(token); self.tokens_checked += 1
                return torch.tensor([seq], dtype=torch.long)
        model = Qwen3ForCausalLM(); factory = R6Backend.factory; stages = []
        def authored_factory(backend, stage, schema, diagnostics, messages):
            model.tokenizer = backend.tokenizer; stages.append(stage)
            if stage == 'marking':
                props = schema['properties']; source = json.loads(messages[1]['content'])['source']
                model.text = json.dumps({'version': props['version']['const'], 'query_id': props['query_id']['const'],
                    'source_sha256': props['source_sha256']['const'], 'labels': ['entity'] * props['labels']['minItems'],
                    'uncertain_roles': [], 'abstraction': source}, ensure_ascii=False, separators=(',', ':'))
            else:
                binding = schema['properties']['binding_sha256']['const']
                model.text = json.dumps({'binding_sha256': binding, 'checks': {k: {'status': 'screened',
                    'source_quote': '', 'candidate_quote': '', 'reason': 'No issue detected.'} for k in CHECKS}},
                    ensure_ascii=False, separators=(',', ':'))
            return factory(backend, stage, schema, diagnostics, messages)
        executor = sacr_r6_bundle_runner.request_bound_executor
        def cpu_executor(**kwargs):
            kwargs['device'] = 'cpu'; return executor(**kwargs)
        original_spec = importlib.util.spec_from_file_location
        files = json.loads(identity)['files']
        def observe_spec(name, path, *args, **kwargs):
            if name != 'weight_identity': return original_spec(name, path, *args, **kwargs)
            class Loader:
                def create_module(self, spec): return None
                def exec_module(self, module): module.observe = lambda root: {'files': files}
            return importlib.util.spec_from_loader(name, Loader())
        spec = original_spec('automatic_actual_worker', '/code/scripts/healthtech/run_automatic_native.py')
        worker = importlib.util.module_from_spec(spec); spec.loader.exec_module(worker)
        with patch.object(local_execution, 'local_gpu_slot', return_value=nullcontext()), \
             patch.object(local_execution, 'check_local_window', return_value=None), \
             patch.object(AutoModelForCausalLM, 'from_pretrained', return_value=model), \
             patch.object(torch.cuda, 'reset_peak_memory_stats', return_value=None), \
             patch.object(torch.cuda, 'max_memory_allocated', return_value=0), \
             patch.object(R6Backend, 'factory', authored_factory), \
             patch.object(sacr_r6_bundle_runner, 'request_bound_executor', cpu_executor), \
             patch.object(importlib.util, 'spec_from_file_location', observe_spec), \
             patch.object(sys, 'argv', ['worker', str(time.monotonic() + 480), sha(draw)]):
            worker.main()
        out = Path('/out/attempt')
        completion = json.loads((out/'completion.json').read_bytes())
        admitted = json.loads((out/'before-model-input-admission.json').read_bytes())
        markers = sorted(p.name for p in out.glob('call-*.json'))
        if (model.calls != 4 or stages != ['marking', 'review'] * 2 or completion['call_slots_consumed'] != 4
                or len(markers) != 4 or admitted['over_limit'] != 0 or completion['queries'] != 2
                or completion['screened_candidates'] != 2 or completion['semantic_certified'] is not False):
            raise RuntimeError('authored two-call expectation differs')
        receipt.update(status='PASS_AUTHORED_NATIVE_PIPELINE', authored_backend_invocations=model.calls,
            grammar_tokens_checked=model.tokens_checked, decision={'screened_candidates': completion['screened_candidates'], 'fallbacks': completion['fallbacks']},
            marking_input_tokens=admitted['max_input_tokens'], decoder_sha256=d['decoder_sha256'],
            mocked_boundaries=['GPU_slot_and_window', 'model_weight_observer', 'model_loader', 'CUDA_telemetry', 'device_to_cpu'],
            actual_boundaries=['worker_main', 'declaration_package_KM_tokenizer_decoder_checks', 'tokenizer',
                               'grammar_EOS', 'request_bound_executor', 'executor_adapter', 'call_markers', 'run_query'])
    except BaseException as error:
        receipt.update(status='FAILED_AUTHORED_PIPELINE', exception_type=type(error).__name__,
                       exception=str(error)[:500]); raise
    finally:
        receipt.update(wall_seconds=time.monotonic()-start, cpu_seconds=time.process_time()-cpu,
                       worker_peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024)
        with Path('/out/receipt.json').open('x') as f: json.dump(receipt, f, indent=2)


if __name__ == '__main__': main()
