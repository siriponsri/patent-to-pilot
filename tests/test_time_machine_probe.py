import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "probe_time_machine_dev", Path(__file__).resolve().parents[1] / "scripts/healthtech/probe_time_machine_dev.py")
probe = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(probe)


def test_time_filter_drops_newer_and_keeps_unknown():
    years = {"a": 2001, "b": 2012, "c": None, "d": 2010}
    kept, unknown = probe.time_filter(["a", "b", "c", "d"], years, 2010)
    assert kept == ["a", "c", "d"] and unknown == 1


def test_mixed_takes_half_then_fills_without_duplicates():
    assert probe.mixed(["u1", "u2", "x1"], ["x1", "x2", "x3"], k=4) == ["u1", "u2", "x1", "x2"]


def test_hit_recall_and_decision():
    gold = {"g1", "g2"}
    assert probe.hit(["n", "g2"], gold, 2) == 1.0 and probe.hit(["n", "g2"], gold, 1) == 0.0
    assert probe.recall(["g1", "n", "g2"], gold, 2) == 0.5
    assert probe.year("2014-05-01") == 2014 and probe.year(None) is None
    assert probe.decide(25, 0.30, 0.10, 0.05) == "GO_SHOCK"
    assert probe.decide(25, 0.20, 0.10, 0.05) == "GO_DESCRIPTIVE"
    assert probe.decide(15, 0.40, 0.10, 0.05) == "GO_DESCRIPTIVE"
    assert probe.decide(25, 0.30, 0.10, -0.01) == "NO_GO"
