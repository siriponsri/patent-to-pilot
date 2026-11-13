import importlib.util
from pathlib import Path
import sys


def test_synthetic_mounts_limits_and_command():
    scripts = Path(__file__).resolve().parents[1] / 'scripts/healthtech'
    sys.path.insert(0, str(scripts))
    try:
        spec = importlib.util.spec_from_file_location('automatic_supervisor_fixture', scripts/'supervise_automatic_synthetic.py')
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        config, mounts = module.configuration(Path('/jobs/fixture'), 1234, 'a'*64)
    finally:
        sys.path.remove(str(scripts))
    host = config['HostConfig']
    assert host['NetworkMode'] == 'none' and host['ReadonlyRootfs']
    assert host['NanoCpus'] == 1_000_000_000
    assert host['Memory'] == host['MemorySwap'] == 31*1024**3
    assert set(t for _,t,_ in mounts) == {'/code','/out','/deps','/models/qwen3-8b',
                                         '/models/.'+module.GPU+'.lock','/dispatch'}
    assert all(ro for _,target,ro in mounts if target not in ('/out','/models/.'+module.GPU+'.lock'))
    assert config['Cmd'] == ['-s','/code/scripts/healthtech/run_automatic_synthetic.py','1234','a'*64]
    assert 'OMP_NUM_THREADS=1' in config['Env']


def test_cpu_grammar_mounts_only_tokenizer_files_without_gpu():
    scripts=Path(__file__).resolve().parents[1]/'scripts/healthtech'
    sys.path.insert(0,str(scripts))
    try:
        spec=importlib.util.spec_from_file_location('cpu_grammar_supervisor_fixture',scripts/'supervise_automatic_grammar.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        config,mounts=module.configuration(Path('/jobs/fixture'),1234,'a'*64,
                                         ['tokenizer.json','tokenizer_config.json','config.json'])
    finally: sys.path.remove(str(scripts))
    host=config['HostConfig']
    assert not host.get('DeviceRequests')
    assert host['NetworkMode']=='none' and host['Memory']==1536*1024**2
    assert host['NanoCpus']==1_000_000_000
    targets={t for _,t,_ in mounts}
    assert '/input/corpus.jsonl' not in targets and '/models/qwen3-8b' not in targets
    assert '/models/qwen3-8b/tokenizer.json' in targets


def test_pipeline_fixture_mounts_dispatch_rw_and_no_weights_or_gpu():
    scripts=Path(__file__).resolve().parents[1]/'scripts/healthtech'
    sys.path.insert(0,str(scripts))
    try:
        spec=importlib.util.spec_from_file_location('pipeline_fixture_supervisor',scripts/'supervise_automatic_pipeline_fixture.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        config,mounts=module.configuration(Path('/jobs/fixture'),1234,'a'*64,
            ['tokenizer.json','tokenizer_config.json','config.json','vocab.json','merges.txt','generation_config.json'])
    finally: sys.path.remove(str(scripts))
    host=config['HostConfig']
    assert not host.get('DeviceRequests') and host['NetworkMode']=='none' and host['NanoCpus']==1_000_000_000
    targets={t:ro for _,t,ro in mounts}
    assert targets['/dispatch'] is False and targets['/out'] is False
    assert '/models/qwen3-8b' not in targets and '/models/qwen3-8b/generation_config.json' in targets
    assert all(ro for t,ro in targets.items() if t not in ('/dispatch','/out'))
    assert config['Cmd']==['-s','/code/scripts/healthtech/qualify_automatic_synthetic_pipeline.py','a'*64]


def test_graph_census_mounts_only_inputs_code_and_out():
    scripts=Path(__file__).resolve().parents[1]/'scripts/healthtech'
    sys.path.insert(0,str(scripts))
    try:
        spec=importlib.util.spec_from_file_location('graph_census_supervisor',scripts/'supervise_graph_census.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        config,mounts=module.configuration(Path('/jobs/census'),1234,'a'*64,[])
    finally: sys.path.remove(str(scripts))
    targets={t:ro for _,t,ro in mounts}
    assert targets['/input/queries.jsonl'] and targets['/input/postings.json'] and targets['/out'] is False
    assert not any('qrels' in t or 'models' in t for t in targets) and not config['HostConfig'].get('DeviceRequests')
    assert config['Cmd'][1]=='/code/scripts/healthtech/run_graph_query_census.py'


def test_native_supervisor_and_fixture_commands():
    scripts=Path(__file__).resolve().parents[1]/'scripts/healthtech'
    sys.path.insert(0,str(scripts))
    try:
        mods={}
        for name in ('supervise_automatic_native','supervise_automatic_native_fixture'):
            spec=importlib.util.spec_from_file_location(name+'_t',scripts/(name+'.py'))
            mods[name]=importlib.util.module_from_spec(spec);spec.loader.exec_module(mods[name])
        native,_=mods['supervise_automatic_native'].configuration(Path('/jobs/n'),1234,'a'*64)
        fixture,fm=mods['supervise_automatic_native_fixture'].configuration(Path('/jobs/f'),1234,'a'*64,['tokenizer.json','generation_config.json'])
    finally: sys.path.remove(str(scripts))
    assert native['Cmd']==['-s','/code/scripts/healthtech/run_automatic_native.py','1234','a'*64]
    assert native['HostConfig']['NetworkMode']=='none' and native['HostConfig']['DeviceRequests']
    assert fixture['Cmd'][1]=='/code/scripts/healthtech/qualify_automatic_native_pipeline.py'
    assert not fixture['HostConfig'].get('DeviceRequests')


def test_pilot_retrieval_mounts_are_read_only_inputs_without_qrels():
    scripts=Path(__file__).resolve().parents[1]/'scripts/healthtech'
    sys.path.insert(0,str(scripts))
    try:
        spec=importlib.util.spec_from_file_location('pilot_retrieval_supervisor',scripts/'supervise_sacr_pilot_retrieval.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        config,mounts=module.configuration(Path('/jobs/p'),1234,'a'*64)
    finally: sys.path.remove(str(scripts))
    targets={t:ro for _,t,ro in mounts}
    assert '/models/qwen3-8b' not in targets and targets['/models/patembed-large'] and targets['/native/out/attempt']
    assert not any('qrels' in str(s) or 'evaluation' in str(s) for s,_,_ in mounts)
    assert all(ro for t,ro in targets.items() if t not in ('/out','/models/.'+module.GPU+'.lock'))
    assert config['Cmd'][1]=='/code/scripts/healthtech/run_sacr_pilot_retrieval.py' and config['HostConfig']['NetworkMode']=='none'


def test_paper1_retrieval_mounts_are_read_only_arm_outputs_without_qrels():
    import pytest
    scripts=Path(__file__).resolve().parents[1]/'scripts/healthtech'
    sys.path.insert(0,str(scripts))
    try:
        spec=importlib.util.spec_from_file_location('paper1_retrieval_supervisor',scripts/'supervise_paper1_retrieval.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        arms={'FA':{'kind':'rewrite','jobs':[{'job':'ptp-auto-paper1-fa-pilot20-20261113-v1'}]}}
        config,mounts=module.configuration(Path('/jobs/p'),1234,'a'*64,arms)
        with pytest.raises(RuntimeError):
            module.configuration(Path('/jobs/p'),1234,'a'*64,{'FA':{'jobs':[{'job':'ptp-native-baseline-20261110-v1'}]}})
    finally: sys.path.remove(str(scripts))
    targets={t:ro for _,t,ro in mounts}
    assert '/models/qwen3-8b' not in targets and targets['/models/patembed-large'] and targets['/arm/FA/0/out'] and targets['/arm/FA/0/dispatch']
    assert not any('qrels' in str(s) or 'evaluation' in str(s) for s,_,_ in mounts)
    assert all(ro for t,ro in targets.items() if t not in ('/out','/models/.'+module.GPU+'.lock'))
    assert config['Cmd'][1]=='/code/scripts/healthtech/run_paper1_retrieval.py' and config['HostConfig']['NetworkMode']=='none'
    assert module.JOB_NAME.fullmatch('ptp-auto-paper1-fa-pilot-retrieval-20261113-v1') and not module.JOB_NAME.fullmatch('ptp-auto-paper1-test-retrieval-20261113-v1')
