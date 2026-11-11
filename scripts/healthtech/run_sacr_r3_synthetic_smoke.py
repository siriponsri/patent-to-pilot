"""One declared synthetic R3 bundle, existing local model, no benchmark mount."""
import hashlib
import importlib.util
import json
from pathlib import Path
import signal
import sys
import time

ROOT = Path('/code')
sys.path.insert(0, str(ROOT/'src'))
from patent_to_pilot.healthtech.local_execution import check_local_window, local_gpu_slot
from patent_to_pilot.research.sacr_native_fidelity import write_new
from patent_to_pilot.research.sacr_r3_bundle_runner import run_bundle
from patent_to_pilot.research.sacr_r2_bundle_runner import local_executor
from patent_to_pilot.research.sacr_r3_runtime_guards import validate_sources, validate_budget


def sha(raw): return hashlib.sha256(raw).hexdigest()


def main():
    stop = float(sys.argv[1])
    declaration_raw = Path('/declaration.json').read_bytes()
    if sha(declaration_raw) != sys.argv[2]: raise RuntimeError('declaration changed')
    d = json.loads(declaration_raw)
    if d['run_id'] != 'ptp-sacr-r3-synthetic-smoke-20261111-v1' or d['maximum_calls'] != 3:
        raise RuntimeError('wrong synthetic smoke declaration')
    validate_sources(ROOT,d['files_sha256'])
    ledger = json.loads(Path('/resource-ledger.json').read_bytes())
    if sha(Path('/resource-ledger.json').read_bytes()) != d['resource_ledger_sha256']:
        raise RuntimeError('ledger differs')
    validate_budget(ledger,d['wall_seconds'])
    out=Path('/out/attempt'); out.mkdir(exist_ok=False)
    write_new(out/'declaration.json',d)
    start=time.monotonic()
    def admission(stage=None):
        check_local_window()
        if time.monotonic()+30 >= stop: raise TimeoutError('supervisor stop deadline near')
    def expired(*_): raise TimeoutError('synthetic smoke deadline')
    signal.signal(signal.SIGALRM,expired)
    signal.alarm(max(1,int(stop-time.monotonic())))
    try:
        admission()
        path=ROOT/'scripts/healthtech/inspect_qwen_weight_identity.py'
        spec=importlib.util.spec_from_file_location('weight_identity',path)
        module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        identity=ROOT/'docs/healthtech/audits/ptp-method-first-r2-weights-20261110/identity.json'
        if sha(identity.read_bytes()) != d['identity_sha256']: raise RuntimeError('identity receipt changed')
        if module.observe(Path('/models/qwen3-8b'))['files'] != json.loads(identity.read_bytes())['files']:
            raise RuntimeError('model identity changed')
        with local_gpu_slot(Path('/models/qwen3-8b')):
            admission()
            import torch
            from transformers import AutoTokenizer, AutoModelForCausalLM, GenerationConfig
            from jsonschema import Draft202012Validator
            from lmformatenforcer import CharacterLevelParserConfig
            from lmformatenforcer.integrations.transformers import build_token_enforcer_tokenizer_data
            from patent_to_pilot.research.sacr_alphabet import build_alphabet
            from patent_to_pilot.research.sacr_escape_callback import build_escape_callback
            from patent_to_pilot.research.sacr_grammar_guard import CompleteJsonEOSGuard
            tokenizer=AutoTokenizer.from_pretrained('/models/qwen3-8b',local_files_only=True)
            config=GenerationConfig.from_pretrained('/models/qwen3-8b',local_files_only=True)
            config.update(do_sample=False,num_beams=1,max_new_tokens=4096,use_cache=True,
                          eos_token_id=[151645,151643],pad_token_id=151643)
            if sha(json.dumps(config.to_dict(),sort_keys=True,separators=(',',':')).encode()) != d['decoder_sha256']:
                raise RuntimeError('decoder changed')
            model=AutoModelForCausalLM.from_pretrained('/models/qwen3-8b',local_files_only=True,
                torch_dtype=torch.float16,device_map='cuda:0',low_cpu_mem_usage=True,
                attn_implementation='eager').eval()
            model.generation_config=config
            import transformers
            observed={'model_class':type(model).__name__,'tokenizer_class':type(tokenizer).__name__,
                'dtype':str(model.dtype),'device':str(model.device),'attention':model.config._attn_implementation,
                'torch':torch.__version__,'transformers':transformers.__version__,
                'decoder_sha256':sha(json.dumps(model.generation_config.to_dict(),sort_keys=True,separators=(',',':')).encode())}
            write_new(out/'loaded-runtime.json',observed)
            if (observed['dtype']!='torch.float16' or observed['device']!='cuda:0'
                    or observed['attention']!='eager' or observed['model_class']!='Qwen3ForCausalLM'
                    or observed['tokenizer_class']!='Qwen2TokenizerFast'
                    or observed['decoder_sha256']!=d['decoder_sha256']):
                raise RuntimeError('observed loaded model differs from contract')
            torch.cuda.reset_peak_memory_stats()
            token_data=build_token_enforcer_tokenizer_data(tokenizer)
            def factory(stage,schema):
                if schema is None: return model
                validator=Draft202012Validator(schema)
                alphabet=build_alphabet(tokenizer,d['source'])
                settings=CharacterLevelParserConfig(alphabet=alphabet['alphabet'],max_consecutive_whitespaces=4096,
                    force_json_field_order=False,max_json_array_length=4096)
                callback=build_escape_callback(token_data,schema,settings,expected_source_sha256=d['lmfe_source_sha256'])
                if callback.configuration_receipt['requested'] != callback.configuration_receipt['effective_root']:
                    raise RuntimeError('grammar configuration changed')
                write_new(out/'profile-grammar.json',callback.configuration_receipt)
                class Guarded:
                    def generate(self,**kwargs):
                        guard=CompleteJsonEOSGuard(prefix_fn=callback,tokenizer=tokenizer,
                            prompt_tokens=int(kwargs['input_ids'].shape[1]),eos_token_ids=[151645,151643],
                            validate=validator.validate)
                        return model.generate(**kwargs,prefix_allowed_tokens_fn=guard)
                return Guarded()
            invoke=local_executor(tokenizer=tokenizer,model_factory=factory,device='cuda:0',
                eos_token_ids=[151645,151643],check_admission=admission,
                peak_memory_bytes=lambda:torch.cuda.max_memory_allocated())
            result=run_bundle(destination=out/'bundle',query_id=d['query_id'],source=d['source'],
                execution=d['execution'],prompt_root=ROOT/'docs/healthtech/research/prompts',
                generic_prompt_sha256=d['generic_prompt_sha256'],invoke=invoke,check_admission=admission,
                maximum_characters=65536)
            write_new(out/'completion.json',{'status':result['status'],'model_calls':result['costs']['metrics']['model_calls'],
                'events':result['events'],'wall_seconds':time.monotonic()-start,
                'peak_gpu_allocated_bytes':torch.cuda.max_memory_allocated(),
                'semantic_pass':False,'retrieval':'NOT_RUN'})
    except BaseException as error:
        write_new(out/'failure.json',{'exception_type':type(error).__name__,'retry':False,
            'wall_seconds':time.monotonic()-start,'costs':'INSPECT_ATTEMPTS_AND_WHOLE_SUPERVISOR'})
        raise
    finally:
        signal.alarm(0)


if __name__=='__main__': main()
