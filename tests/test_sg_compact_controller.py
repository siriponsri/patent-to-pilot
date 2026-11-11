from pathlib import Path
import sys
import pytest

sys.path.insert(0,str(Path(__file__).parents[1]/'scripts/healthtech'))
from supervise_sg_compact_preflight import require_calibration_terminal, validate_scope


@pytest.mark.parametrize('state, allowed', [
    ({'Running': False, 'Pid': 0}, True),
    ({'Running': True, 'Pid': 234}, False),
    ({'Running': False, 'Pid': 234}, False),
    ({'Pid': 0}, False),
])
def test_live_or_unknown_calibration_blocks_cpu_job(state, allowed):
    class Engine:
        def inspect(self,name):
            assert name=='ptp-r6-calibration-20261111-v1'
            return {'State': state}
    if allowed: require_calibration_terminal(Engine())
    else:
        with pytest.raises(RuntimeError):require_calibration_terminal(Engine())


def test_poll_failure_never_means_terminal():
    class Engine:
        def inspect(self,name):raise ConnectionError('observation unavailable')
    with pytest.raises(ConnectionError):require_calibration_terminal(Engine())


@pytest.mark.parametrize('changed', [{}, {'model_calls':1}, {'gpu_seconds':1},
    {'cpu_threads':8}, {'total_ram_bytes':32*1024**3}, {'wall_seconds':601},
    {'retry':True}, {'kind':'native-input'}])
def test_exact_cpu_only_declaration(changed):
    declaration={'kind':'graph-compact-input','wall_seconds':600,'cpu_threads':2,
                 'total_ram_bytes':2*1024**3,'model_calls':0,'gpu_seconds':0,'retry':False}
    declaration.update(changed)
    if not changed:validate_scope(declaration)
    else:
        with pytest.raises(RuntimeError):validate_scope(declaration)
