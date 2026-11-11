from types import SimpleNamespace
import sys
import pytest
from patent_to_pilot.research.r6_backend import R6Backend
from patent_to_pilot.research.sacr_failure_diagnostics import AttemptDiagnostics
from patent_to_pilot.research.mtm_runtime import InputBoundaryError


def test_actual_factory_two_guarded_stages_have_distinct_receipts(tmp_path,monkeypatch):
    from patent_to_pilot.research import sacr_alphabet,sacr_boundary_callback_v3
    monkeypatch.setitem(sys.modules,'lmformatenforcer',SimpleNamespace(CharacterLevelParserConfig=lambda **k:k))
    monkeypatch.setattr(sacr_alphabet,'build_alphabet',lambda tokenizer,text:{'alphabet':text})
    def callback(*args,**kwargs):
        def fn(batch,seq):return [123]
        fn.configuration_receipt={'requested':{},'effective_root':{}}
        return fn
    monkeypatch.setattr(sacr_boundary_callback_v3,'build_boundary_callback',callback)
    observed=[]
    class Model:
        def generate(self,**kwargs):
            assert callable(kwargs['prefix_allowed_tokens_fn']);observed.append('backend');return 'authored-output'
    backend=R6Backend.__new__(R6Backend)
    backend.tokenizer=object();backend.model=Model();backend.output_root=tmp_path
    backend.token_data=None;backend.lmfe_source_sha256='a'*64
    for stage in ('profile','critic'):
        diagnostics=AttemptDiagnostics(tmp_path/(stage+'-diagnostics'))
        model=backend.factory(stage,{'type':'object'},diagnostics,[{'role':'user','content':'source ไทย 🚰'}])
        assert diagnostics.backend_invocations==0
        assert model.generate(input_ids=SimpleNamespace(shape=(1,10)))=='authored-output'
        assert diagnostics.backend_invocations==diagnostics.backend_returns==1
        assert (tmp_path/(stage+'-grammar-private.json')).exists()
    assert observed==['backend','backend']
    with pytest.raises(FileExistsError):backend.factory('profile',{'type':'object'},AttemptDiagnostics(tmp_path/'repeat'),[])


def test_cpu_qualification_backend_cannot_execute_model():
    backend=R6Backend.__new__(R6Backend);backend.model=None
    with pytest.raises(InputBoundaryError):backend.factory('profile',{},None,[])
