"""Authored evaluator fixtures for frozen P2-T04 coverage and metrics."""
import gzip
import hashlib
import json

import pytest

from scripts.healthtech.eval_bridgeret_dev import main as frozen_scorer
from scripts.research import p2t04_evaluate_screen as evaluator
from scripts.research import p2t04_run_screen as screen

APPS = ["a", "b", "c"]
HEADER = "app_id\trank\tunit\tscore\n"


def _pin(path):
    return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def _json(path, data):
    path.write_text(json.dumps(data) + "\n", encoding="utf-8")
    return _pin(path)


def _rank(path, rankings):
    text = HEADER + "".join(
        f"{app}\t{i}\t{unit}\t0\n"
        for app, units in rankings.items() for i, unit in enumerate(units, 1)
    )
    if path.suffix == ".gz":
        with gzip.open(path, "wt", encoding="utf-8") as stream:
            stream.write(text)
    else:
        path.write_text(text, encoding="utf-8")


def _fixture(tmp_path):
    tasks = tmp_path / "tasks.tsv"
    tasks.write_text("app_id\tblock\tfiling_date\n" + "".join(f"{app}\tP1-DEV\t2000-01-01\n" for app in APPS),
                     encoding="utf-8")
    clusters = tmp_path / "art-units.tsv"
    clusters.write_text("app_id\tblock\tart_unit\na\tP1-DEV\t101\nb\tP1-DEV\t\nc\tP1-DEV\t101\n",
                        encoding="utf-8")
    units = tmp_path / "corpus-units.tsv"
    units.write_text(
        "unit_id\tfirst_pub\nin-a\t1999-01-01\nout-a\t1998-01-01\nout-b\t1997-01-01\n"
        "other\t1999-01-01\nA:a\t1996-01-01\nfuture\t2000-01-01\n", encoding="utf-8",
    )
    pairs = tmp_path / "pairs-dev.tsv"
    pairs.write_text(
        "app_id\tblock\tunit\tunit_first_pub\tdom_ipc3\n"
        "a\tP1-DEV\tin-a\t1999-01-01\tIN3\n"
        "a\tP1-DEV\tout-a\t1998-01-01\tOUT3\n"
        "b\tP1-DEV\tout-b\t1997-01-01\tOUT3\n"
        "a\tP1-DEV\tA:a\t1996-01-01\tIN3\n"
        "a\tP1-DEV\tfuture\t2000-01-01\tOUT3\n"
        "a\tP1-DEV\tabout\t1996-01-01\tOUT3\n"
        "c\tP1-DEV\tother\t\tOUT3\n", encoding="utf-8",
    )
    target = {"a": ["in-a"], "b": [], "c": []}
    control = {"a": ["out-a"], "b": ["out-b"], "c": []}
    baseline_dense = {**control, "c": ["other"]}
    inputs = dict.fromkeys(screen.INPUTS, {}) | {"units": _pin(units), "tasks": _pin(tasks)}
    for route in screen.ROUTES:
        route_dir = tmp_path / route
        route_dir.mkdir()
        archive = route_dir / "run-P1-DEV.tsv.gz"
        _rank(archive, control if route == "L" else baseline_dense)
        inputs["route_" + route] = _pin(archive)
    runtime = {
        "schema": "ptp-p2t04-screen/1", "block": "P1-DEV", "policy_sha256": screen.POLICY_V1_SHA256,
        "query_ids": APPS, "screen_limits": {"final": screen.FINAL_DEPTH},
        "inputs": inputs,
    }
    run_pin = _json(tmp_path / "runtime-freeze.json", runtime)
    run_sha = run_pin["sha256"]
    run_dir = tmp_path / "screen"
    run_dir.mkdir()
    _json(run_dir / "runtime.json", {"block": "P1-DEV", "manifest_sha256": run_sha, "query_count": 3})
    _json(run_dir / "bm25-reproduction.json", {"status": "PASS", "manifest_sha256": run_sha, "queries": 3})
    for name in evaluator.RANKING_ARMS:
        rows = target if name == evaluator.TARGET else control
        if name in {"original_Q", "original_P", "original_A"}:
            rows = baseline_dense
        _rank(run_dir / f"{name}.tsv", rows)
    trace = [
        {"app_id": app, "frozen_manifest_sha256": run_sha, "shared_seed": control[app], "arms": {
            name: {"final_ids": (target if name == evaluator.TARGET else control)[app]} for name in screen.ARMS
        }}
        for app in APPS
    ]
    (run_dir / "trace.jsonl").write_text("".join(json.dumps(row) + "\n" for row in trace), encoding="utf-8")
    manifest = {
        "schema": evaluator.SCHEMA, "block": "P1-DEV", "runtime_manifest": run_pin,
        "cohort_sha256": evaluator.cohort_sha256(APPS), "inputs": {"pairs": _pin(pairs), "clusters": _pin(clusters)},
    }
    return manifest, run_dir


def test_frozen_cohort_matches_original_scorer_and_retains_empty_rankings(tmp_path):
    manifest, run_dir = _fixture(tmp_path)
    archive_dir = tmp_path / "P1-DEV"
    archive_dir.mkdir()
    archive = archive_dir / f"{evaluator.F3_ALLOCATION}.tsv"
    _rank(archive, {"a": ["out-a"], "b": ["out-b"], "c": [], "elsewhere": ["other"]})
    manifest[evaluator.F3_NAME] = {"ranking": _pin(archive), "empty_query_ids": ["c"]}
    pin = _json(tmp_path / "freeze.json", manifest)
    result = tmp_path / "evaluation.json"
    report = evaluator.evaluate(tmp_path / "freeze.json", pin["sha256"], run_dir, result)
    assert json.loads(result.read_text(encoding="utf-8")) == report
    assert report["query_count"] == 3 and report["metric_support"] == {"ALL": 2, "IN": 1, "OUT": 2}
    assert report["arms"][evaluator.TARGET]["empty_rankings"] == 2
    assert report["decision"]["status"] == "NOT_RUN"
    old_output = tmp_path / "unchanged-scorer.json"
    frozen_scorer([str(run_dir / f"{evaluator.TARGET}.tsv"), str(tmp_path / "pairs-dev.tsv"),
                   str(tmp_path / "corpus-units.tsv"), str(tmp_path / "tasks.tsv"), "P1-DEV", str(old_output)])
    old = json.loads(old_output.read_text(encoding="utf-8"))
    metrics = report["arms"][evaluator.TARGET]["metrics"]
    assert metrics == {key: old["metrics"][key] for key in metrics}
    against = report["comparisons_against"][evaluator.F3_NAME]
    assert against["paired_recall"]["ALL_R@200"]["delta"] == -0.5
    assert against["paired_recall"]["ALL_R@200"]["n"] == 2
    assert against["paired_recall"]["ALL_R@200"]["ci95"] == [-1.0, 0.0]
    assert against["candidates"]["queries"] == 3
    assert against["candidates"]["new_judged_positive_recovery"] == {"ALL": 1, "IN": 1, "OUT": 0}
    assert against["candidates"]["displaced_positives"] == {"ALL": 2, "IN": 0, "OUT": 2}
    assert all("original_" + route in report["comparisons_against"] for route in screen.ROUTES)


@pytest.mark.parametrize(
    ("problem", "message"),
    [
        ("outer_digest", "frozen SHA-256 mismatch"),
        ("different_cohort", "cohort differs"),
        ("drop_trace", "trace does not cover"),
        ("modified_arm", "ranking differs from its trace"),
        ("modified_labels", "frozen SHA-256 mismatch"),
        ("protected_pairs", "protected or credential"),
        ("missing_clusters", "cover every frozen query"),
        ("unproven_empty_archive", r"archived F3\* query coverage"),
        ("failed_reproduction", "reproduction gate did not pass"),
        ("changed_baseline", "differs from the frozen archive"),
    ],
)
def test_refuses_unfrozen_or_incomplete_inputs(tmp_path, problem, message):
    manifest, run_dir = _fixture(tmp_path)
    if problem == "different_cohort":
        manifest["cohort_sha256"] = evaluator.cohort_sha256(list(reversed(APPS)))
    elif problem == "drop_trace":
        trace = run_dir / "trace.jsonl"
        trace.write_text("\n".join(trace.read_text().splitlines()[:-1]) + "\n", encoding="utf-8")
    elif problem == "modified_arm":
        _rank(run_dir / f"{evaluator.TARGET}.tsv", {"a": ["in-a"], "b": ["out-b"]})
    elif problem == "modified_labels":
        (tmp_path / "pairs-dev.tsv").write_text("changed\n", encoding="utf-8")
    elif problem == "protected_pairs":
        manifest["inputs"]["pairs"] = {"path": "P1-TEST/not-created.tsv", "sha256": "0" * 64}
    elif problem == "missing_clusters":
        clusters = tmp_path / "art-units.tsv"
        clusters.write_text("app_id\tblock\tart_unit\na\tP1-DEV\t101\n", encoding="utf-8")
        manifest["inputs"]["clusters"] = _pin(clusters)
    elif problem == "unproven_empty_archive":
        archive_dir = tmp_path / "P1-DEV"
        archive_dir.mkdir()
        archive = archive_dir / f"{evaluator.F3_ALLOCATION}.tsv"
        _rank(archive, {"a": ["out-a"], "b": ["out-b"]})
        manifest[evaluator.F3_NAME] = {"ranking": _pin(archive)}
    elif problem == "failed_reproduction":
        _json(run_dir / "bm25-reproduction.json", {"status": "FAIL"})
    elif problem == "changed_baseline":
        _rank(run_dir / "original_Q.tsv", {"a": ["in-a"], "b": ["out-b"], "c": ["other"]})
    pin = _json(tmp_path / "freeze.json", manifest)
    freeze_sha = "0" * 64 if problem == "outer_digest" else pin["sha256"]
    out = tmp_path / "evaluation.json"
    with pytest.raises(ValueError, match=message):
        evaluator.evaluate(tmp_path / "freeze.json", freeze_sha, run_dir, out)
    assert not out.exists()


def test_unjudged_subgroup_remains_unsupported(tmp_path):
    manifest, run_dir = _fixture(tmp_path)
    pairs = tmp_path / "pairs-dev.tsv"
    pairs.write_text(
        "app_id\tblock\tunit\tunit_first_pub\tdom_ipc3\na\tP1-DEV\tin-a\t1999-01-01\tIN3\n",
        encoding="utf-8",
    )
    manifest["inputs"]["pairs"] = _pin(pairs)
    pin = _json(tmp_path / "freeze.json", manifest)
    report = evaluator.evaluate(tmp_path / "freeze.json", pin["sha256"], run_dir, tmp_path / "evaluation.json")
    assert report["arms"][evaluator.TARGET]["metrics"]["OUT_R@200"] == {"mean": None, "n": 0}
    assert report["comparisons_against"]["seed_only"]["paired_recall"]["OUT_R@200"] == {
        "status": "NOT_RUN", "delta": None, "ci95": None, "n": 0,
    }
