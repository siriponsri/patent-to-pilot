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
