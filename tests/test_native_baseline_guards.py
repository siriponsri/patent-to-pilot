import importlib.util
from pathlib import Path
import sys

import pytest


@pytest.fixture
def runner(monkeypatch):
    scripts = Path(__file__).resolve().parents[1] / "scripts" / "healthtech"
    monkeypatch.syspath_prepend(str(scripts))
    spec = importlib.util.spec_from_file_location("native_baseline_test_module", scripts / "run_dapfam_native_baseline.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_each_declared_binding_is_checked_before_gpu(runner, monkeypatch, tmp_path):
    runtime, model, vectors = tmp_path / "runtime", tmp_path / "model", tmp_path / "vectors"
    pins = {**{runtime / k: v for k, v in runner.PINS.items()},
            **{model / k: v for k, v in runner.MODEL_PINS.items()}, vectors: runner.VECTOR_SHA}
    monkeypatch.setattr(runner, "_sha256", pins.__getitem__)
    runner.verify_inputs(runtime, model, vectors)
    for path, expected in list(pins.items()):
        pins[path] = "0" * 64
        with pytest.raises(ValueError, match="hash mismatch"):
            runner.verify_inputs(runtime, model, vectors)
        pins[path] = expected


def test_existing_output_rejected_before_input_reads_or_model_creation(runner, monkeypatch, tmp_path):
    monkeypatch.setattr(runner, "check_local_window", lambda: None)
    def forbidden(*args):
        pytest.fail("input/model work started before exclusive output guard")
    monkeypatch.setattr(runner, "verify_inputs", forbidden)
    monkeypatch.setattr(runner, "MeanPoolEncoder", forbidden)
    monkeypatch.setattr(sys, "argv", ["runner", "--runtime", "unused", "--model", "unused",
                                      "--vectors", "unused", "--output", str(tmp_path)])
    with pytest.raises(ValueError, match="exclusive output"):
        runner.main()
