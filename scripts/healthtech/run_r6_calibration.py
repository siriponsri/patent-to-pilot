"""R6 frozen24 worker; controller must qualify/isolate and reserve before launch."""
import hashlib
import importlib.util
import json
from pathlib import Path
import signal
import sys
import time

ROOT=Path('/code')
sys.path.insert(0,str(ROOT/'src'))


def sha(raw):return hashlib.sha256(raw).hexdigest()


def main():
    from patent_to_pilot.healthtech.local_execution import check_local_window,local_gpu_slot
    from patent_to_pilot.research.r6_dispatch_files import load_dispatch,validate_worker_package,validate_deadline
    from patent_to_pilot.research.sacr_native_fidelity import write_new
    from patent_to_pilot.research.r6_calibration_runner import run_calibration,frozen_tasks
    from patent_to_pilot.research.r6_reference_runner import preflight_requests,encoded
    from patent_to_pilot.research.r6_backend import R6Backend
    from patent_to_pilot.research.sacr_r6_bundle_runner import request_bound_executor
    stop=float(sys.argv[1])
    evidence=load_dispatch('/dispatch',manifest_path='manifest.json',manifest_sha256=sys.argv[2])
    d=evidence['declaration']
    if d['stage']!='calibration' or d['maximum_calls']!=24:
        raise RuntimeError('fixed24 calibration declaration required')
    validate_deadline(stop,time.monotonic(),d['seconds'])
    validate_worker_package(ROOT,d['files_sha256'])
    out=Path('/out/attempt');out.mkdir(exist_ok=False)
    write_new(out/'dispatch-binding.json',evidence['receipt'])
    start=time.monotonic()
    def admission(stage=None):
        check_local_window()
        if time.monotonic()+30>=stop:raise TimeoutError('calibration shutdown reserve')
    def expired(*_):raise TimeoutError('calibration deadline')
    signal.signal(signal.SIGALRM,expired)
    signal.signal(signal.SIGTERM,expired)
    signal.alarm(max(1,int(stop-time.monotonic())))
    try:
        admission()
        tasks=frozen_tasks()
        if sha(encoded(tasks))!=d['input_manifest_sha256']:raise RuntimeError('calibration task hash changed')
        spec=importlib.util.spec_from_file_location('weight_identity',ROOT/'scripts/healthtech/inspect_qwen_weight_identity.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        identity=ROOT/'docs/healthtech/audits/ptp-method-first-r2-weights-20261110/identity.json'
        if sha(identity.read_bytes())!=d['model_identity_sha256']:raise RuntimeError('model identity receipt changed')
        if module.observe(Path('/models/qwen3-8b'))['files']!=json.loads(identity.read_bytes())['files']:
            raise RuntimeError('model files changed')
        with local_gpu_slot(Path('/models/qwen3-8b')):
            admission()
            import torch
            import transformers
            from transformers import AutoTokenizer,AutoModelForCausalLM,GenerationConfig
            tokenizer=AutoTokenizer.from_pretrained('/models/qwen3-8b',local_files_only=True)
            if sha(Path('/models/qwen3-8b/tokenizer.json').read_bytes())!=d['tokenizer_sha256']:
                raise RuntimeError('tokenizer identity changed')
            config=GenerationConfig.from_pretrained('/models/qwen3-8b',local_files_only=True)
            config.update(do_sample=False,num_beams=1,max_new_tokens=4096,use_cache=True,
                          eos_token_id=[151645,151643],pad_token_id=151643)
            if sha(json.dumps(config.to_dict(),sort_keys=True,separators=(',',':')).encode())!=d['decoder_sha256']:
                raise RuntimeError('decoder changed')
            def count_before_load(messages):
                tokens=tokenizer.apply_chat_template(messages,tokenize=True,add_generation_prompt=True,enable_thinking=False)
                if type(tokens) is not list or any(type(t) is not int for t in tokens):
                    raise RuntimeError('calibration token shape changed')
                return len(tokens)
            preflight=preflight_requests(tasks,mode='calibration',count_tokens=count_before_load)
            write_new(out/'before-model-input-admission.json',preflight)
            if preflight['status']!='ADMITTED':raise RuntimeError('calibration input gate failed before model load')
            admission()
            model=AutoModelForCausalLM.from_pretrained('/models/qwen3-8b',local_files_only=True,
                torch_dtype=torch.float16,device_map='cuda:0',low_cpu_mem_usage=True,attn_implementation='eager').eval()
            model.generation_config=config
            observed={'model_class':type(model).__name__,'tokenizer_class':type(tokenizer).__name__,
                'dtype':str(model.dtype),'device':str(model.device),'attention':model.config._attn_implementation,
                'torch':torch.__version__,'transformers':transformers.__version__,
                'decoder_sha256':sha(json.dumps(model.generation_config.to_dict(),sort_keys=True,separators=(',',':')).encode())}
            write_new(out/'loaded-runtime.json',observed)
            if (observed['dtype']!='torch.float16' or observed['device']!='cuda:0' or observed['attention']!='eager'
                    or observed['model_class']!='Qwen3ForCausalLM' or observed['tokenizer_class']!='Qwen2TokenizerFast'
                    or observed['decoder_sha256']!=d['decoder_sha256']):
                raise RuntimeError('loaded runtime contract mismatch')
            torch.cuda.reset_peak_memory_stats()
            backend=R6Backend(tokenizer=tokenizer,model=model,output_root=out,lmfe_source_sha256=d['lmfe_source_sha256'])
            invoke=request_bound_executor(tokenizer=tokenizer,model_factory=backend.factory,device='cuda:0',
                eos_token_ids=[151645,151643],check_admission=admission,
                peak_memory_bytes=lambda:torch.cuda.max_memory_allocated())
            # reference-000..023 are distinct grammar receipt names in this root.
            result=run_calibration(destination=out/'calibration',tasks_sha256=d['input_manifest_sha256'],
                run_id=d['attempt_id'],invoke=invoke,count_tokens=backend.count_tokens,check_admission=admission)
            write_new(out/'completion.json',{'status':result['status'],'events':result['events'],'costs':result['costs'],
                'wall_seconds':time.monotonic()-start,'peak_gpu_allocated_bytes':torch.cuda.max_memory_allocated(),
                'native_fidelity_proven':False,'retry':False})
    except BaseException as error:
        write_new(out/'failure.json',{'exception_type':type(error).__name__,'retry':False,
            'wall_seconds':time.monotonic()-start,'costs':'INSPECT_ATTEMPTS_AND_WHOLE_SUPERVISOR',
            'model_calls':'UNKNOWN_UNTIL_DIAGNOSTICS_RECONCILED'})
        raise
    finally:signal.alarm(0)


if __name__=='__main__':main()
