from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).parents[1]/'scripts/healthtech'))
from supervise_r7_backend_preflight import fixture_worker


@pytest.mark.parametrize('kind',['graph-input','native-input','critic','profile',None])
def test_other_data_and_model_routes_cannot_use_fixture_authority(kind):
    with pytest.raises(RuntimeError,match='fixture-only'):fixture_worker({'kind':kind})


def test_only_authored_pipeline_worker_is_selected():
    assert fixture_worker({'kind':'pipeline-fixture'})=='qualify_r7_calibration_pipeline.py'
