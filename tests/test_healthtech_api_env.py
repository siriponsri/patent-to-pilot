import importlib.util
import os
from pathlib import Path
from types import SimpleNamespace
import pytest
from patent_to_pilot.providers import env_file

ROOT=Path(__file__).parents[1]

def module():
    spec=importlib.util.spec_from_file_location('api_env_test',ROOT/'scripts/healthtech/run_openrouter_generation_evidence_pack.py')
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result

def test_api_mock_never_reads_env(monkeypatch,tmp_path):
    mod=module()
    def forbidden(*a,**k):raise AssertionError('must not read key')
    monkeypatch.setattr(mod,'scoped_env_file_key',forbidden)
    runner=SimpleNamespace(run=lambda pack:pack)
    assert mod._run_with_local_key(runner,{'fixture':True},live_enabled=False,env_file=tmp_path/'absent')=={'fixture':True}

def test_api_live_env_is_process_scoped_and_restored(monkeypatch,tmp_path):
    mod=module();isolated={};monkeypatch.setattr(env_file.os,'environ',isolated)
    source=tmp_path/'fake.env';source.write_text('OPENROUTER_API_KEY=FAKE_TEST_ONLY')
    def fake_run(pack):
        assert isolated['OPENROUTER_API_KEY']=='FAKE_TEST_ONLY'
        raise RuntimeError('synthetic')
    with pytest.raises(RuntimeError):
        mod._run_with_local_key(SimpleNamespace(run=fake_run),{},live_enabled=True,env_file=source)
    assert isolated=={}
