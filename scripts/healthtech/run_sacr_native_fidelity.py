"""Single-use native SACR profile generation; requires an external bounded supervisor."""
import argparse
import importlib.util
import json
from pathlib import Path
import signal
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))

from patent_to_pilot.healthtech.local_execution import check_local_window, local_gpu_slot
from patent_to_pilot.research.mtm_runtime import InputBoundaryError
from patent_to_pilot.research.sacr_generation import GenerationLimits
from patent_to_pilot.research.sacr_native_fidelity import bind_sample, digest, run_profiles, write_new

REQUIRED_FILES = {
    'scripts/healthtech/run_sacr_native_fidelity.py',
    'scripts/healthtech/inspect_qwen_weight_identity.py',
    'src/patent_to_pilot/healthtech/local_execution.py',
    'docs/healthtech/research/prompts/sacr_profile_quotes_order_v2.txt',
    *('src/patent_to_pilot/research/' + name + '.py' for name in (
        'sacr_native_fidelity', 'sacr_generation', 'sacr_generation_receipt',
        'sacr_rejection_policy', 'sacr_schema', 'sacr_solo_fidelity', 'sacr_prompts',
        'sacr_profile', 'sacr_quote_profile', 'sacr_views', 'sacr_outcomes',
        'sacr_alphabet', 'sacr_escape_callback', 'sacr_grammar_guard', 'mtm_runtime')),
}


def validate_code_declaration(declaration, root):
    hashes = declaration['files_sha256']
    if type(hashes) is not dict or not REQUIRED_FILES <= set(hashes):
        raise InputBoundaryError('mandatory runtime source pins missing')
    for relative, expected in hashes.items():
        target = (root / relative).resolve()
        if not target.is_relative_to(root.resolve()) or digest(target.read_bytes()) != expected:
            raise InputBoundaryError('declared code/prompt hash mismatch')
    if declaration['prompt_sha256'] != hashes['docs/healthtech/research/prompts/sacr_profile_quotes_order_v2.txt']:
        raise InputBoundaryError('prompt declaration disagrees before model loading')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('model-root', 'identity', 'queries', 'sample', 'declaration', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--declaration-sha256', required=True)
    args = parser.parse_args()
    raw = args.declaration.read_bytes()
    if digest(raw) != args.declaration_sha256:
        raise InputBoundaryError('unbound run declaration')
    declaration = json.loads(raw)
    if (declaration['maximum_calls'] != 100 or declaration['retry'] is not False or
            type(declaration['wall_seconds']) is not int or not 60 <= declaration['wall_seconds'] <= 28800):
        raise InputBoundaryError('invalid bounded generation declaration')
    validate_code_declaration(declaration, ROOT)
    entries = bind_sample(args.queries.read_bytes(), args.sample.read_bytes(),
        query_sha256=declaration['query_sha256'], sample_sha256=declaration['sample_sha256'])
    identity = args.identity.read_bytes()
    if digest(identity) != declaration['identity_sha256']:
        raise InputBoundaryError('model identity receipt mismatch')
    if args.output.exists():
        raise InputBoundaryError('output exists; no restart/retry')
    check_local_window()
    args.output.mkdir(parents=True, exist_ok=False)
    write_new(args.output / 'declaration.json', declaration)
    start = time.monotonic()
    def deadline(*_):
        raise TimeoutError('native fidelity generation deadline reached')
    signal.signal(signal.SIGALRM, deadline)
    signal.alarm(declaration['wall_seconds'] - 5)
    try:
        spec = importlib.util.spec_from_file_location('identity_inspector', Path(__file__).with_name('inspect_qwen_weight_identity.py'))
        inspector = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(inspector)
        if inspector.observe(args.model_root)['files'] != json.loads(identity)['files']:
            raise InputBoundaryError('model weights/configuration changed')
        with local_gpu_slot(args.model_root):
            check_local_window()
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer, GenerationConfig
            from jsonschema import Draft202012Validator
            from lmformatenforcer import CharacterLevelParserConfig
            from lmformatenforcer.integrations.transformers import build_token_enforcer_tokenizer_data
            from patent_to_pilot.research.sacr_alphabet import build_alphabet
            from patent_to_pilot.research.sacr_escape_callback import build_escape_callback
            from patent_to_pilot.research.sacr_grammar_guard import CompleteJsonEOSGuard
            limits = GenerationLimits()
            tokenizer = AutoTokenizer.from_pretrained(args.model_root, local_files_only=True)
            config = GenerationConfig.from_pretrained(args.model_root, local_files_only=True)
            config.update(do_sample=False, num_beams=1, max_new_tokens=4096, use_cache=True,
                          eos_token_id=[151645, 151643], pad_token_id=151643)
            if digest(json.dumps(config.to_dict(), sort_keys=True, separators=(',', ':')).encode()) != '20232bca268d86c6e4bad73eb53be74c881ad06e004eb0aaa6ddb5af831368ae':
                raise InputBoundaryError('effective decoder changed')
            model = AutoModelForCausalLM.from_pretrained(args.model_root, local_files_only=True,
                torch_dtype=torch.float16, device_map='cuda:0', low_cpu_mem_usage=True,
                attn_implementation='eager').eval()
            model.generation_config = config
            torch.cuda.reset_peak_memory_stats()
            import transformers
            write_new(args.output / 'loaded-runtime.json', {
                'torch': torch.__version__, 'transformers': transformers.__version__,
                'python': sys.version.split()[0], 'model_class': type(model).__name__,
                'tokenizer_class': type(tokenizer).__name__, 'model_dtype': str(model.dtype),
                'model_device': str(model.device), 'attention': model.config._attn_implementation,
                'model_files_match': True, 'identity_sha256': declaration['identity_sha256'],
                'effective_decoder_sha256': digest(json.dumps(config.to_dict(), sort_keys=True,
                    separators=(',', ':')).encode()), 'load_and_preflight_seconds': time.monotonic() - start})
            token_data = build_token_enforcer_tokenizer_data(tokenizer)
            def factory(schema, source, attempt):
                validator = Draft202012Validator(schema)
                alphabet = build_alphabet(tokenizer, source)
                settings = CharacterLevelParserConfig(alphabet=alphabet['alphabet'],
                    max_consecutive_whitespaces=4096, force_json_field_order=False, max_json_array_length=4096)
                callback = build_escape_callback(token_data, schema, settings,
                    expected_source_sha256=declaration['lmfe_source_sha256'])
                if callback.configuration_receipt['requested'] != callback.configuration_receipt['effective_root']:
                    raise InputBoundaryError('grammar configuration changed')
                write_new(attempt / 'grammar-config.json', callback.configuration_receipt)
                class Guarded:
                    def generate(self, **kwargs):
                        guard = CompleteJsonEOSGuard(prefix_fn=callback, tokenizer=tokenizer,
                            prompt_tokens=int(kwargs['input_ids'].shape[1]), eos_token_ids=[151645, 151643],
                            validate=validator.validate)
                        return model.generate(**kwargs, prefix_allowed_tokens_fn=guard)
                return Guarded()
            result = run_profiles(entries=entries, output=args.output / 'profiles',
                prompt_root=ROOT / 'docs/healthtech/research/prompts', prompt_sha256=declaration['prompt_sha256'],
                tokenizer=tokenizer, guarded_model_factory=factory, device='cuda:0', limits=limits,
                check_authorization=check_local_window,
                remaining_seconds=lambda: declaration['wall_seconds'] - (time.monotonic() - start),
                peak_memory_bytes=lambda: torch.cuda.max_memory_allocated())
            write_new(args.output / 'terminal.json', {'status': result['status'],
                'wall_seconds': time.monotonic() - start, 'queries': len(result['outcomes']),
                'peak_gpu_allocated_bytes': torch.cuda.max_memory_allocated(),
                'peak_gpu_reserved_bytes': torch.cuda.max_memory_reserved(), 'semantic_status': 'NOT_ASSESSED'})
    except BaseException as error:
        write_new(args.output / 'failure.json', {'status': 'FAILED_OR_INTERRUPTED',
            'exception_type': type(error).__name__, 'wall_seconds': time.monotonic() - start, 'retry': False})
        raise
    finally:
        signal.alarm(0)


if __name__ == '__main__':
    main()
