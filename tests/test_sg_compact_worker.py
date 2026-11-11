import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest
from test_sg_r6_manifest import fixture


@pytest.mark.parametrize('fault', [None, 'input', 'tokenizer', 'declaration'])
def test_actual_worker_fixed_input_routing_and_precount_failures(tmp_path, monkeypatch, fault):
    script=Path(__file__).parents[1]/'scripts/healthtech/preflight_sg_compact_inputs.py'
    spec=importlib.util.spec_from_file_location('compact_worker_fixture',script)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    def mapped(path):return tmp_path/str(path).lstrip('/')
    monkeypatch.setattr(module,'Path',mapped)
    monkeypatch.setitem(sys.modules,'resource',SimpleNamespace(
        RUSAGE_SELF=0,getrusage=lambda _:SimpleNamespace(ru_maxrss=1)))
    rows,source,aliases=fixture()
    inputs={'sources-private.jsonl':'\n'.join(json.dumps(r) for r in rows),
            'source-sample.json':json.dumps(source),'alias-sample.json':json.dumps(aliases)}
    def write(path,text):
        p=mapped(path);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
        return hashlib.sha256(p.read_bytes()).hexdigest()
    pins={name:write('/input/'+name,text) for name,text in inputs.items()}
    identity={'files':{name:{'sha256':write('/models/qwen3-8b/'+name,'{}')}
                       for name in ['tokenizer.json','tokenizer_config.json','config.json']}}
    identity_sha=write('/code/docs/healthtech/audits/ptp-method-first-r2-weights-20261110/identity.json',json.dumps(identity))
    declaration={'kind':'graph-compact-input','wall_seconds':600,'input_sha256':pins,
                 'identity_sha256':identity_sha,'lmfe_source_sha256':'a'*64}
    declaration_sha=write('/declaration.json',json.dumps(declaration))
    monkeypatch.setattr(sys,'argv',['worker',declaration_sha if fault!='declaration' else '0'*64])
    mapped('/out').mkdir()
    calls=[]
    class Tokenizer:
        @staticmethod
        def from_pretrained(path,local_files_only):
            assert path=='/models/qwen3-8b' and local_files_only
            return object()
    class Backend:
        def __init__(self,**kwargs):pass
        def count_tokens(self,messages):
            calls.append(messages)
            return 100
    monkeypatch.setitem(sys.modules,'transformers',SimpleNamespace(AutoTokenizer=Tokenizer))
    import patent_to_pilot.research.r6_backend as backend
    monkeypatch.setattr(backend,'R6Backend',Backend)
    if fault=='input':write('/input/source-sample.json','{}')
    if fault=='tokenizer':write('/models/qwen3-8b/tokenizer.json','changed')
    if fault:
        with pytest.raises(RuntimeError):module.main()
        assert not calls
        assert json.loads(mapped('/out/receipt.json').read_text())['status']=='FAILED_INPUT_PREFLIGHT'
    else:
        module.main()
        receipt=json.loads(mapped('/out/receipt.json').read_text())
        assert len(calls)==len(receipt['units'])==114
        assert receipt['source_coverage_units']==100 and receipt['source_abstentions']==86
        assert receipt['model_calls']==receipt['gpu_seconds']==0
        assert receipt['dispatch_authorized'] is False
        assert receipt['semantic_fidelity']=='NOT_ASSESSED'
