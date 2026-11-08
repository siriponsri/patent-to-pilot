from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys
import threading

import pytest

from patent_to_pilot.healthtech.local_execution import (
    APPROVED_GPU_UUID,
    check_local_window,
    local_gpu_slot,
)
from patent_to_pilot.providers.ledger_registry import CanonicalLedgerError
from patent_to_pilot.providers.round1 import Round1ProjectBudget
from test_healthtech_qwen_evidence_pack import _load, RUNNER


def test_local_without_api_registry_and_paid_still_fails_closed(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "empty-profile"))
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", APPROVED_GPU_UUID)
    runner = _load(RUNNER, "local_without_paid_state")
    monkeypatch.setattr(
        runner,
        "check_local_window",
        lambda **kw: check_local_window(now=datetime(2026, 11, 2, tzinfo=timezone.utc), **kw),
    )
    model = tmp_path / "models" / "qwen"
    model.mkdir(parents=True)
    seen = []
    monkeypatch.setattr(runner, "_run_generation", lambda *args: seen.append("local-only") or {"provider_calls": 0})
    assert runner.run_generation({}, model, tmp_path / "local.json", 8, 1)["provider_calls"] == 0
    assert seen == ["local-only"]
    with pytest.raises(CanonicalLedgerError):
        Round1ProjectBudget(
            tmp_path / "missing.sqlite3",
            model_provider_map={"qwen/qwen3-32b": "DeepInfra"},
            pricing_snapshot_sha256="a" * 64,
            pricing_snapshot_utc="2026-11-02T00:00:00Z",
            namespace="canonical",
        )
    assert not (tmp_path / "missing.sqlite3").exists()
    assert not (tmp_path / "empty-profile").exists()


def test_local_slot_is_exclusive_across_processes_and_released(tmp_path):
    model = tmp_path / "models" / "qwen"
    model.mkdir(parents=True)
    code = (
        "from pathlib import Path; from patent_to_pilot.healthtech.local_execution import local_gpu_slot; "
        "import sys;\nwith local_gpu_slot(Path(sys.argv[1])): print('ACQUIRED')"
    )
    command = [
        sys.executable,
        "-c",
        "import sys; sys.path.insert(0, "
        + repr(str(Path(__file__).resolve().parents[1] / "src"))
        + "); "
        + code,
        str(model),
    ]
    with local_gpu_slot(model):
        blocked = subprocess.run(command, capture_output=True, text=True, timeout=15)
        assert blocked.returncode != 0
        assert "already in use" in blocked.stderr
    available = subprocess.run(command, capture_output=True, text=True, timeout=15)
    assert available.returncode == 0, available.stderr
    assert available.stdout.strip() == "ACQUIRED"


def test_mock_api_can_finish_while_local_gpu_slot_is_held(tmp_path):
    # This is transport/queue isolation, never a claim of paid API parity.
    from test_healthtech_api_generation import test_api_runner_uses_exact_messages_and_mock_namespace_without_paid_dispatch

    model = tmp_path / "models" / "qwen"
    model.mkdir(parents=True)
    entered, release = threading.Event(), threading.Event()

    def hold_local():
        with local_gpu_slot(model):
            entered.set()
            assert release.wait(20)

    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(hold_local)
        try:
            assert entered.wait(5)
            test_api_runner_uses_exact_messages_and_mock_namespace_without_paid_dispatch(tmp_path / "api")
            assert not future.done()
        finally:
            release.set()
        future.result()


@pytest.mark.parametrize("visible", ["1", "0", "", APPROVED_GPU_UUID + ",0"])
def test_gpu_index_or_multiple_devices_cannot_replace_uuid(visible):
    with pytest.raises(RuntimeError, match="exact approved GPU UUID"):
        check_local_window(now=datetime(2026, 11, 2, tzinfo=timezone.utc), visible=visible)


def test_expired_allocation_is_not_refreshed():
    with pytest.raises(RuntimeError, match="window"):
        check_local_window(now=datetime(2026, 12, 31, 16, 59, tzinfo=timezone.utc), visible=APPROVED_GPU_UUID)


def test_existing_local_receipt_never_overwritten(tmp_path, monkeypatch):
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", APPROVED_GPU_UUID)
    runner = _load(RUNNER, "local_preserve_receipt")
    monkeypatch.setattr(
        runner,
        "check_local_window",
        lambda **kw: check_local_window(now=datetime(2026, 11, 2, tzinfo=timezone.utc), **kw),
    )
    receipt = tmp_path / "result.json"
    receipt.write_text("prior result")
    monkeypatch.setattr(runner, "_run_generation", lambda *a: pytest.fail("must not load model"))
    with pytest.raises(FileExistsError):
        runner.run_generation({}, tmp_path / "unused", receipt, 8, 1)
    assert receipt.read_text() == "prior result"


def test_transformer_embedding_launcher_holds_shared_slot_during_encode(tmp_path, monkeypatch):
    import importlib.util

    script_path = Path(__file__).resolve().parents[1] / "scripts" / "healthtech" / "encode_transformer_shards.py"
    spec = importlib.util.spec_from_file_location("encode_transformer_shards_under_test", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    model = tmp_path / "models" / "patembed"
    model.mkdir(parents=True)
    input_path = tmp_path / "input.jsonl"
    input_path.write_text("{}\n", encoding="utf-8")
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", APPROVED_GPU_UUID)

    class FakeEncoder:
        device = "cuda"
        stats = type("Stats", (), {"rows": 0, "token_count": 0})()

        def __init__(self, *args, **kwargs):
            pass

    def fake_encode(*args, **kwargs):
        code = (
            "from pathlib import Path; from patent_to_pilot.healthtech.local_execution import local_gpu_slot; "
            "import sys;\nwith local_gpu_slot(Path(sys.argv[1])): print('ACQUIRED')"
        )
        command = [
            sys.executable,
            "-c",
            "import sys; sys.path.insert(0, "
            + repr(str(Path(__file__).resolve().parents[1] / "src"))
            + "); "
            + code,
            str(model),
        ]
        blocked = subprocess.run(command, capture_output=True, text=True, timeout=15)
        assert blocked.returncode != 0
        assert "already in use" in blocked.stderr
        return {"status": "PASS", "row_count": 1, "dimension": 1, "shards": []}

    monkeypatch.setattr(module, "TransformerEncoder", FakeEncoder)
    monkeypatch.setattr(module, "build_transformer_model_binding", lambda *args, **kwargs: {})
    monkeypatch.setattr(module, "encode_vector_shards", fake_encode)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(script_path),
            "--input",
            str(input_path),
            "--output",
            str(tmp_path / "bundle"),
            "--model-dir",
            str(model),
            "--model-id",
            "test/model",
            "--model-revision",
            "rev",
            "--kind",
            "e5",
            "--role",
            "passage",
        ],
    )

    assert module.main() == 0
