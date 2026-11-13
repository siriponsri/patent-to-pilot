"""Authored CPU backend through the ACTUAL Paper 1 rewrite worker (FA then GR, 2 authored queries each).

No pretrained weights are loaded. Doubles: GPU slot/window, weight observer, model loader (authored CPU
model that must pass the real grammar callback), CUDA telemetry, device->cpu. Real: worker main,
declaration/package/tokenizer/decoder checks, tokenizer, R6Backend grammar+EOS, request_bound_executor,
executor adapter (stage 'rewrite'), durable call markers and run_rewrite incl. the declared input-cap fallback.
v2 (2026-11-13): v1 failed because the authored whitespace-only FA field (" ") was refused by the real grammar
under canonical tokenization (fixture artifact; v1 retained). v2 exercises the INPUT_LIMIT fallback instead
(FA cap 1000 with a long query 2; GR cap 5800 calls both) and records the first refused token on any violation.
"""
from contextlib import nullcontext
import hashlib, importlib.util, json, sys, time
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, '/code/src')
sha = lambda b: hashlib.sha256(b).hexdigest()
QUERIES = ({'id': 'authored-rewrite-001', 'text': 'A pump reduces line pressure below 5 kPa except during cleaning.'},
           {'id': 'authored-rewrite-002', 'text': 'The heater is not activated during transport. ' * 120})
CAPS = {'FA': 1000, 'GR': 5800}


def main():
    import resource
    start = time.monotonic(); cpu = time.process_time()
    receipt = {'status': 'INCOMPLETE', 'real_model_calls': 0, 'gpu_seconds': 0, 'retry': False}
    try:
        raw = Path('/declaration.json').read_bytes()
        if sha(raw) != sys.argv[1]: raise RuntimeError('fixture declaration changed')
        outer = json.loads(raw)
        if outer['kind'] != 'paper1-rewrite-pipeline-fixture': raise RuntimeError('fixture scope changed')
        with Path('/out/SIMULATED-ARTIFACTS.json').open('x') as f:
            json.dump({'scope': 'ENTIRE_OUTPUT_TREE_AUTHORED_CPU_QUALIFICATION', 'real_model_calls': 0,
                       'internal_attempt_metrics': 'SIMULATED_NEVER_IMPORT_TO_RESEARCH_LEDGER'}, f, indent=2)
        from patent_to_pilot.research.r7_dispatch_files import validate_worker_package
        validate_worker_package('/code', outer['files_sha256'], outer['package_sha256'])
        from patent_to_pilot.research import sacr_r6_bundle_runner
        from patent_to_pilot.research.r6_backend import R6Backend
        from patent_to_pilot.research import paper1_rewrite_arms as arms
        from patent_to_pilot.healthtech import local_execution
        import torch
        from transformers import AutoModelForCausalLM, GenerationConfig
        identity = Path('/code/docs/healthtech/audits/ptp-method-first-r2-weights-20261110/identity.json').read_bytes()
        config = GenerationConfig.from_pretrained('/models/qwen3-8b', local_files_only=True)
        config.update(do_sample=False, num_beams=1, max_new_tokens=4096, use_cache=True,
                      eos_token_id=[151645, 151643], pad_token_id=151643)
        task = '\n'.join(json.dumps(t) for t in QUERIES).encode() + b'\n'

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
                tokens = self.tokenizer.encode(self.text, add_special_tokens=False) + [151645]
                for i, token in enumerate(tokens):
                    if callback is not None and token not in callback(0, torch.tensor(seq, dtype=torch.long)):
                        self.violation = {'token_index': i, 'token_id': token, 'token_text': self.tokenizer.decode([token]),
                                          'prefix_tail': self.tokenizer.decode(tokens[max(0, i-8):i])}
                        raise RuntimeError('authored response violates actual grammar')
                    seq.append(token); self.tokens_checked += 1
                return torch.tensor([seq], dtype=torch.long)
        model = Qwen3ForCausalLM(); factory = R6Backend.factory; stages = []
        def authored_factory(backend, stage, schema, diagnostics, messages):
            model.tokenizer = backend.tokenizer; stages.append(stage)
            props = schema['properties']; qid = props['query_id']['const']
            head = {'version': props['version']['const'], 'query_id': qid, 'source_sha256': props['source_sha256']['const']}
            if 'abstract' in props:
                value = dict(head, abstract='A heating or pumping device whose operation depends on a stated mode.')
            else:
                value = dict(head, function='Lowers fluid pressure in a conduit.', mechanism='A pumping element draws fluid.',
                             problem='Keeps pressure below a limit.', conditions='Below 5 kPa, except during cleaning.')
            model.text = json.dumps(value, ensure_ascii=False, separators=(',', ':'))
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
        spec = original_spec('paper1_actual_worker', '/code/scripts/healthtech/run_paper1_rewrite.py')
        worker = importlib.util.module_from_spec(spec); spec.loader.exec_module(worker)
        summary = {}
        for arm in ('FA', 'GR'):
            d = {'attempt_id': 'authored-fixture-' + arm, 'arm': arm, 'stage': 'synthetic', 'maximum_calls': 2, 'queries': 2,
                 'seconds': 1800, 'cpu_seconds': 150, 'input_token_cap': CAPS[arm], 'max_consecutive_whitespaces': 48,
                 'force_json_field_order': True, 'files_sha256': outer['files_sha256'], 'package_sha256': outer['package_sha256'],
                 'input_manifest_sha256': sha(task), 'model_sha256': sha(identity),
                 'tokenizer_sha256': sha(Path('/models/qwen3-8b/tokenizer.json').read_bytes()),
                 'decoder_sha256': sha(json.dumps(config.to_dict(), sort_keys=True, separators=(',', ':')).encode()),
                 'lmfe_source_sha256': outer['lmfe_source_sha256']}
            draw = json.dumps(d).encode()
            Path('/dispatch/declaration.json').write_bytes(draw); Path('/dispatch/queries.jsonl').write_bytes(task)
            before = model.calls
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
            out = Path('/out/attempt'); out.rename('/out/attempt-' + arm); out = Path('/out/attempt-' + arm)
            completion = json.loads((out/'completion.json').read_bytes())
            admitted = json.loads((out/'before-model-input-admission.json').read_bytes())
            q2 = json.loads((out/'queries/q001/result.json').read_bytes())
            expected = 1 if arm == 'FA' else 2
            if (model.calls - before != expected or completion['call_slots_consumed'] != expected
                    or len(list(out.glob('call-*.json'))) != expected or admitted['over_limit'] != 2 - expected
                    or completion['rewrites_used'] != expected
                    or q2['reason'] != ('INPUT_LIMIT' if arm == 'FA' else 'REWRITE_VALIDATED')
                    or completion['semantic_certified'] is not False):
                raise RuntimeError('authored expectation differs for ' + arm)
            summary[arm] = {'rewrites_used': completion['rewrites_used'], 'fallbacks': completion['fallbacks'],
                            'reasons': completion['reasons'], 'max_input_tokens': admitted['max_input_tokens']}
        if stages != ['rewrite'] * 3: raise RuntimeError('unexpected stage sequence')
        receipt.update(status='PASS_AUTHORED_PAPER1_REWRITE_PIPELINE', authored_backend_invocations=model.calls,
            grammar_tokens_checked=model.tokens_checked, arms=summary, decoder_sha256=d['decoder_sha256'],
            mocked_boundaries=['GPU_slot_and_window', 'model_weight_observer', 'model_loader', 'CUDA_telemetry', 'device_to_cpu'],
            actual_boundaries=['worker_main', 'declaration_package_tokenizer_decoder_checks', 'tokenizer', 'grammar_EOS',
                               'request_bound_executor', 'executor_adapter_rewrite_stage', 'call_markers', 'run_rewrite_fallback'])
    except BaseException as error:
        receipt.update(status='FAILED_AUTHORED_PIPELINE', exception_type=type(error).__name__, exception=str(error)[:500],
                       grammar_violation=getattr(locals().get('model'), 'violation', None)); raise
    finally:
        receipt.update(wall_seconds=time.monotonic()-start, cpu_seconds=time.process_time()-cpu,
                       worker_peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024)
        with Path('/out/receipt.json').open('x') as f: json.dump(receipt, f, indent=2)


if __name__ == '__main__': main()
