"""Authored CPU backend through the actual R7 worker, grammar and cohort.

No pretrained weights are loaded. Hardware/load/dispatch authority boundaries
are explicit doubles; request assembly, tokenizer, grammar, generation adapter,
reservations, raw records, cohort and semantic grading are the real code.
"""
from contextlib import nullcontext
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time
from unittest.mock import patch

sys.path.insert(0,'/code/src')


def main():
    import resource
    start=time.monotonic();cpu=time.process_time()
    receipt={'status':'INCOMPLETE','real_model_calls':0,'gpu_seconds':0,'retry':False}
    try:
        raw=Path('/declaration.json').read_bytes()
        if hashlib.sha256(raw).hexdigest()!=sys.argv[1]:raise RuntimeError('qualification declaration changed')
        outer=json.loads(raw)
        if outer['kind']!='pipeline-fixture' or outer['wall_seconds']!=600:raise RuntimeError('qualification scope changed')
        with Path('/out/SIMULATED-ARTIFACTS.json').open('x') as f:
            json.dump({'scope':'ENTIRE_OUTPUT_TREE_AUTHORED_CPU_QUALIFICATION','real_model_calls':0,'real_gpu_seconds':0,
                'internal_attempt_metrics':'SIMULATED_MODEL_GPU_FIELDS_NEVER_IMPORT_TO_RESEARCH_LEDGER',
                'accounting':'Charge outer measured worker and controller CPU only'},f,indent=2)
        from patent_to_pilot.research.r7_dispatch_files import validate_worker_package,package_identity
        validate_worker_package('/code',outer['files_sha256'],package_identity(outer['files_sha256']))
        from patent_to_pilot.research.r7_calibration_runner import frozen_tasks
        from patent_to_pilot.research.r7_reference_runner import encoded,sha
        from patent_to_pilot.research import r7_dispatch_files,sacr_r6_bundle_runner
        from patent_to_pilot.research.r6_backend import R6Backend
        from patent_to_pilot.healthtech import local_execution
        import torch
        from transformers import AutoModelForCausalLM,GenerationConfig
        identity=Path('/code/docs/healthtech/audits/ptp-method-first-r2-weights-20261110/identity.json')
        identity_bytes=identity.read_bytes()
        if sha(identity_bytes)!=outer['identity_sha256']:raise RuntimeError('identity source changed')
        identity_value=json.loads(identity_bytes)
        for name in ['tokenizer.json','tokenizer_config.json','config.json']:
            if sha((Path('/models/qwen3-8b')/name).read_bytes())!=identity_value['files'][name]['sha256']:
                raise RuntimeError('qualification tokenizer changed')
        config=GenerationConfig.from_pretrained('/models/qwen3-8b',local_files_only=True)
        config.update(do_sample=False,num_beams=1,max_new_tokens=4096,use_cache=True,
                      eos_token_id=[151645,151643],pad_token_id=151643)
        d={'stage':'calibration','maximum_calls':24,'seconds':600,'attempt_id':'authored-calibration-fixture',
           'files_sha256':outer['files_sha256'],'package_sha256':package_identity(outer['files_sha256']),
           'model_identity_sha256':sha(identity_bytes),'tokenizer_sha256':sha(Path('/models/qwen3-8b/tokenizer.json').read_bytes()),
           'decoder_sha256':sha(json.dumps(config.to_dict(),sort_keys=True,separators=(',',':')).encode()),
           'input_manifest_sha256':sha(encoded(frozen_tasks())),'lmfe_source_sha256':outer['lmfe_source_sha256']}
        class Qwen3ForCausalLM:
            dtype=torch.float16
            device=torch.device('cuda:0') # Authored observation double, never a tensor destination.
            config=type('AuthoredConfig',(),{'_attn_implementation':'eager'})()
            def __init__(self):self.calls=0;self.tokens_checked=0;self.fault=None;self.stage=None
            def eval(self):return self
            def generate(self,**kwargs):
                self.calls+=1
                if self.fault=='post_backend' and self.stage=='generic':raise RuntimeError('authored post-dispatch failure')
                seq=kwargs['input_ids'][0].detach().cpu().tolist()
                callback=kwargs.get('prefix_allowed_tokens_fn')
                for token in self.tokenizer.encode(self.text,add_special_tokens=False)+[151645]:
                    if callback is not None:
                        allowed=callback(0,torch.tensor(seq,dtype=torch.long))
                        if token not in allowed:raise RuntimeError('authored response violates actual grammar')
                    seq.append(token);self.tokens_checked+=1
                return torch.tensor([seq],dtype=torch.long)
        model=Qwen3ForCausalLM();factory=R6Backend.factory
        synthetic_source='The pump moves water below 5 bar.'
        def authored_factory(backend,stage,schema,diagnostics,messages):
            model.stage=stage
            model.tokenizer=backend.tokenizer
            if stage=='profile':
                from patent_to_pilot.research.sacr_token_profile import source_catalogue
                model.text=json.dumps({'version':'sacr-evidence-roles-v3','query_id':'fixture-q','source_sha256':sha(synthetic_source.encode()),
                    'blocks':[{'id':'b','evidence':[{'field':'allowed_query','start_token':0,
                    'end_token':len(source_catalogue(synthetic_source)['tokens'])}],
                    'roles':{},'conditions':[],'abstraction':None}]})
            elif stage=='generic':
                model.text=json.dumps({'bad':[]} if model.fault=='invalid_envelope' else {'views':[synthetic_source]})
            else:
                payload=json.loads(messages[1]['content'])
                if stage.startswith('reference-'):
                    index=int(stage.split('-')[-1]);bound=frozen_tasks()[index]['prepared']
                    if messages!=bound['messages'] or schema!=bound['original']['schema']:
                        raise RuntimeError('actual worker did not use exact compact request')
                model.text=json.dumps({'binding_sha256':payload['binding_sha256'],
                    'dimensions':{key:'supported' for key in schema['properties']['dimensions']['properties']},'findings':[]})
            return factory(backend,stage,schema,diagnostics,messages)
        executor=sacr_r6_bundle_runner.request_bound_executor
        def cpu_executor(**kwargs):
            kwargs['device']='cpu'
            return executor(**kwargs)
        spec=importlib.util.spec_from_file_location('r7_actual_worker','/code/scripts/healthtech/run_r7_calibration.py')
        worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)
        original_spec=importlib.util.spec_from_file_location
        def observe_spec(name,path,*args,**kwargs):
            if name!='weight_identity':return original_spec(name,path,*args,**kwargs)
            class Loader:
                def create_module(self,spec):return None
                def exec_module(self,module):module.observe=lambda path:identity_value
            return importlib.util.spec_from_loader(name,Loader())
        with patch.object(r7_dispatch_files,'load_dispatch',return_value={'declaration':d,'receipt':{'status':'AUTHORED_DISPATCH_DOUBLE'}}), \
             patch.object(local_execution,'local_gpu_slot',return_value=nullcontext()), \
             patch.object(local_execution,'check_local_window',return_value=None), \
             patch.object(AutoModelForCausalLM,'from_pretrained',return_value=model), \
             patch.object(torch.cuda,'reset_peak_memory_stats',return_value=None), \
             patch.object(torch.cuda,'max_memory_allocated',return_value=0), \
             patch.object(R6Backend,'factory',authored_factory), \
             patch.object(sacr_r6_bundle_runner,'request_bound_executor',cpu_executor), \
             patch.object(importlib.util,'spec_from_file_location',observe_spec), \
             patch.object(sys,'argv',['worker',str(start+500),'authored-manifest']):
            worker.main()
            calibration_calls=model.calls
            from patent_to_pilot.research.sacr_r6_candidate import VERSION
            from patent_to_pilot.research.sacr_generation import GenerationLimits
            from patent_to_pilot.research.mtm_runtime import InputBoundaryError
            fixture_results=[]
            for mode in ['normal','invalid_envelope','post_backend','exhausted_budget','deadline','missing_file']:
                base=Path('/out')/('bundle-'+mode);base.mkdir()
                backend=R6Backend(tokenizer=model.tokenizer,model=model,output_root=base,lmfe_source_sha256=outer['lmfe_source_sha256'])
                model.fault=mode;before=model.calls
                def admission(stage):
                    if mode in ('exhausted_budget','deadline'):raise TimeoutError('authored '+mode)
                invoke=cpu_executor(tokenizer=model.tokenizer,model_factory=backend.factory,device='cpu',
                    eos_token_ids=[151645,151643],check_admission=admission,peak_memory_bytes=lambda:0)
                args=dict(destination=base/'bundle',source=synthetic_source,query_id='fixture-q',
                    execution={'profile_contract':VERSION,'limits':GenerationLimits().__dict__,'run_id':'fixture-'+mode},
                    prompt_root=Path('/code/docs/healthtech/research/prompts'),
                    generic_prompt_sha256=outer['generic_prompt_sha256'],invoke=invoke,check_admission=admission,
                    count_tokens=backend.count_tokens,maximum_characters=65536)
                if mode=='missing_file':args['prompt_root']=Path('/missing-authored-prompt')
                error=None;outcome=None
                try:outcome=sacr_r6_bundle_runner.run_bundle(**args)
                except (RuntimeError,TimeoutError,FileNotFoundError,InputBoundaryError) as caught:error=type(caught).__name__
                count=model.calls-before
                if mode=='normal':
                    if error or outcome['status']!='AUTOMATIC_UNFLAGGED_NOT_FIDELITY_PASS' or count!=3:
                        raise RuntimeError('authored complete bundle mismatch')
                    try:sacr_r6_bundle_runner.run_bundle(**args)
                    except FileExistsError:pass
                    else:raise RuntimeError('authored replay unexpectedly admitted')
                    if model.calls-before!=3:raise RuntimeError('replay entered backend')
                elif mode=='invalid_envelope':
                    if error or outcome['status']!='UNASSESSABLE' or count!=2:raise RuntimeError('invalid envelope did not stop')
                elif mode=='post_backend':
                    if error!='RuntimeError' or count!=2:raise RuntimeError('unknown backend did not stop')
                    failed=json.loads((base/'bundle/failure.json').read_bytes())
                    if failed['unsettled_attempt_cost']!='UNKNOWN':raise RuntimeError('unknown cost falsely settled')
                elif error is None or count:raise RuntimeError('denied fixture entered backend')
                fixture_results.append({'case':mode,'authored_backend_invocations':count,'expected_error':error,'pass':True})
        result=json.loads(Path('/out/attempt/calibration/calibration-assessment.json').read_bytes())
        if (calibration_calls!=24 or result['status']!='CALIBRATION_FAILED'
                or result['assessment']['required_verdict_misses']!=14
                or result['assessment']['execution_rejected_cases']!=0):
            raise RuntimeError('authored negative calibration expectation differs')
        receipt.update(status='PASS_AUTHORED_FULL_CALIBRATION_PIPELINE',authored_backend_invocations=model.calls,
            bundle_fixture_results=fixture_results,
            actual_grammar_tokens_checked=model.tokens_checked,expected_semantic_failure=True,
            tasks_sha256=d['input_manifest_sha256'],assessment_sha256=sha(Path('/out/attempt/calibration/calibration-assessment.json').read_bytes()),
            mocked_boundaries=['dispatch_authority','model_weight_observer','GPU_lock','model_loader','CUDA_telemetry','device_to_cpu'],
            actual_boundaries=['worker_main','request_assembly','tokenizer','grammar_EOS','generation_adapter','durable_attempts','cohort','calibration_assess'])
    except BaseException as error:
        receipt.update(status='FAILED_AUTHORED_PIPELINE',exception_type=type(error).__name__);raise
    finally:
        receipt.update(wall_seconds=time.monotonic()-start,cpu_seconds=time.process_time()-cpu,
            worker_peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024)
        with Path('/out/receipt.json').open('x') as f:json.dump(receipt,f,indent=2)


if __name__=='__main__':main()
