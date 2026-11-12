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
