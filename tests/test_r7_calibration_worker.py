"""Actual worker main with authored model/transport doubles; no GPU access."""
from contextlib import nullcontext
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest


def setup(tmp_path,monkeypatch,fault=None):
    path=Path(__file__).parents[1]/'scripts/healthtech/run_r7_calibration.py'
    spec=importlib.util.spec_from_file_location('r7_worker_under_test',path)
    worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)
    calls=[]
    root=tmp_path/'code';root.mkdir();(tmp_path/'out').mkdir()
    modelroot=tmp_path/'models/qwen3-8b';modelroot.mkdir(parents=True)
    (modelroot/'tokenizer.json').write_bytes(b'authored tokenizer')
    identity=root/'docs/healthtech/audits/ptp-method-first-r2-weights-20261110/identity.json'
    identity.parent.mkdir(parents=True);identity.write_text('{"files": {}}')
    inspector=root/'scripts/healthtech/inspect_qwen_weight_identity.py';inspector.parent.mkdir(parents=True)
    inspector.write_text('def observe(path): return {"files": {}}\n')
    def mapped(value):
        value=str(value)
        return tmp_path/value.lstrip('/') if value.startswith(('/out','/models')) else Path(value)
    monkeypatch.setattr(worker,'ROOT',root);monkeypatch.setattr(worker,'Path',mapped)
    monkeypatch.setattr(worker,'signal',SimpleNamespace(SIGALRM=1,SIGTERM=2,signal=lambda *a:None,alarm=lambda *a:None))
    monkeypatch.setattr(worker,'time',SimpleNamespace(monotonic=lambda:100))
    monkeypatch.setattr(sys,'argv',['worker','1000','a'*64])
    from patent_to_pilot.research import r7_dispatch_files as files
    from patent_to_pilot.research import r7_calibration_runner as calibration
    from patent_to_pilot.research.r7_reference_runner import encoded,sha
    from patent_to_pilot.healthtech import local_execution
    from patent_to_pilot.research import r6_backend,sacr_r6_bundle_runner
    config_values=dict(do_sample=False,num_beams=1,max_new_tokens=4096,use_cache=True,eos_token_id=[151645,151643],pad_token_id=151643)
    d={'stage':'calibration','maximum_calls':24,'seconds':1200,'files_sha256':{},'package_sha256':'a'*64,
       'model_identity_sha256':sha(identity.read_bytes()),'tokenizer_sha256':sha((modelroot/'tokenizer.json').read_bytes()),
       'decoder_sha256':sha(json.dumps(config_values,sort_keys=True,separators=(',',':')).encode()),
       'input_manifest_sha256':sha(encoded(calibration.frozen_tasks())), 'attempt_id':'authored', 'lmfe_source_sha256':{}}
    if fault=='tasks':d['input_manifest_sha256']='0'*64
    if fault=='decoder':d['decoder_sha256']='0'*64
    if fault=='deadline':monkeypatch.setattr(sys,'argv',['worker','9999','a'*64])
    monkeypatch.setattr(files,'load_dispatch',lambda *a,**k:{'declaration':d,'receipt':{'status':'authored'}})
    def package(*a):
        if fault=='pins':raise RuntimeError('authored source pin failure')
    monkeypatch.setattr(files,'validate_worker_package',package)
    monkeypatch.setattr(local_execution,'check_local_window',lambda:None)
    def lock(*a):
        calls.append('lock')
        if fault=='lock':raise RuntimeError('authored occupied lock')
        return nullcontext()
    monkeypatch.setattr(local_execution,'local_gpu_slot',lock)
    class Qwen2TokenizerFast:
        def apply_chat_template(self,*a,**k):
            calls.append('tokenize')
            return [1]*(8193 if fault=='input_limit' else 10)
    class GenerationConfig:
        @classmethod
        def from_pretrained(cls,*a,**k):return cls()
        def update(self,**kwargs):self.values=kwargs
        def to_dict(self):return self.values
    class Qwen3ForCausalLM:
        dtype='torch.float16';device='cuda:0';config=SimpleNamespace(_attn_implementation='eager')
        def eval(self):return self
    def load_model(*a,**k):
        calls.append('load_model')
        if fault=='model_load':raise RuntimeError('authored model load failure')
        return Qwen3ForCausalLM()
    monkeypatch.setitem(sys.modules,'transformers',SimpleNamespace(__version__='authored',
        AutoTokenizer=SimpleNamespace(from_pretrained=lambda *a,**k:Qwen2TokenizerFast()),
        GenerationConfig=GenerationConfig,AutoModelForCausalLM=SimpleNamespace(from_pretrained=load_model)))
    monkeypatch.setitem(sys.modules,'torch',SimpleNamespace(__version__='authored',float16='authored',
        cuda=SimpleNamespace(reset_peak_memory_stats=lambda:None,max_memory_allocated=lambda:0)))
    monkeypatch.setattr(r6_backend,'R6Backend',lambda **k:SimpleNamespace(factory=object(),count_tokens=lambda m:10))
    monkeypatch.setattr(sacr_r6_bundle_runner,'request_bound_executor',lambda **k:object())
    def run(**kwargs):
        calls.append('cohort')
        if fault=='backend_unknown':raise RuntimeError('authored unknown backend')
        return {'status':'CALIBRATION_FAILED','events':[],'costs':{}}
    monkeypatch.setattr(calibration,'run_calibration',run)
    return worker,calls,tmp_path/'out/attempt'


def test_actual_entrypoint_pretokenizes24_before_loading_model(tmp_path,monkeypatch):
    worker,calls,out=setup(tmp_path,monkeypatch)
    worker.main()
    assert calls.count('tokenize')==24 and calls.index('load_model')>max(i for i,x in enumerate(calls) if x=='tokenize')
    assert calls[-1]=='cohort' and (out/'completion.json').exists()


@pytest.mark.parametrize('fault',['tasks','decoder','deadline','pins','lock','input_limit','model_load','backend_unknown'])
def test_actual_entrypoint_failures_do_not_become_completion(tmp_path,monkeypatch,fault):
    worker,calls,out=setup(tmp_path,monkeypatch,fault)
    with pytest.raises((RuntimeError,ValueError)):worker.main()
    assert not (out/'completion.json').exists()
    if fault not in ('model_load','backend_unknown'):assert 'load_model' not in calls
    if fault=='backend_unknown':
        assert json.loads((out/'failure.json').read_bytes())['model_calls']=='UNKNOWN_UNTIL_DIAGNOSTICS_RECONCILED'
