"""Evaluate a finished P2-T04 run on its separately frozen P1-DEV cohort.

The evaluation manifest pins the screen manifest and its ordered cohort digest, P1-DEV
pairs and art-unit TSVs, and optionally the archived P1-DEV A3r1 F3* ranking. Units
and tasks retain their screen-manifest pins. This process owns the judged pairs.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import re
from collections import defaultdict
from itertools import zip_longest
from pathlib import Path

from patent_to_pilot.workbench.relation_search import POLICY_V1_SHA256
from scripts.research.p2t02_analyse import B, KINDS, SEED, cluster_bootstrap, overlap_stats
from scripts.research.p2t04_run_screen import (
    ARMS, BLOCK, BM25_EXACT, FINAL_DEPTH, INPUTS, ROUTES, bm25_gate_mode, checked_digest, checked_path,
    dev_records, selected_records,
)

SCHEMA = "ptp-p2t04-evaluation/1"
RANKING_ARMS = (*ARMS, "complete_content_fusion", *("original_" + route for route in ROUTES))
TARGET = "unresolved_relation"
F3_ALLOCATION = "alloc-L0-Q1-P1-H1-K1"
F3_NAME = "archived_a3r1_f3"


def cohort_sha256(query_ids: list[str]) -> str:
    return hashlib.sha256(json.dumps(query_ids, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()


def _pinned(base: Path, pin: dict) -> Path:
    if pin.keys() != {"path", "sha256"} or not re.fullmatch(r"[0-9a-f]{64}", pin["sha256"]):
        raise ValueError("expected exactly a path and a lowercase SHA-256")
    return checked_digest(base / pin["path"], pin["sha256"])


def _json(path: Path) -> dict:
    return json.loads(checked_path(path).read_text(encoding="utf-8"))


def _sha(path: Path) -> str:
    with checked_path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _corpus(units_path: Path) -> set[str]:
    with units_path.open(encoding="utf-8", newline="") as stream:
        return {row["unit_id"] for row in csv.DictReader(stream, delimiter="\t")}


def _positives(pairs_path: Path, tasks: dict, corpus: set[str]) -> dict:
    """Conditional ALL/IN/OUT sets from the unchanged BridgeRet evaluator."""
    positives = defaultdict(lambda: defaultdict(set))
    for row in dev_records(pairs_path, tsv=True):
        app, unit, first_pub = row["app_id"], row["unit"], row["unit_first_pub"]
        if app not in tasks or not unit or not first_pub or unit not in corpus:
            continue
        if first_pub >= tasks[app]["filing_date"] or unit == "A:" + app:
            continue
        positives[app]["ALL"].add(unit)
        if row["dom_ipc3"] in {"IN3", "OUT3"}:
            positives[app][row["dom_ipc3"][:-1]].add(unit)
    return positives


def _rankings(path: Path, apps: set[str], corpus: set[str], *, archive=False, take_prefix=False) -> dict:
    path = checked_path(path)
    read = gzip.open if path.suffix == ".gz" else open
    by_app = {app: [] for app in apps}
    with read(path, "rt", encoding="utf-8", newline="") as stream:
        rows = csv.DictReader(stream, delimiter="\t")
        if tuple(rows.fieldnames or ()) != ("app_id", "rank", "unit", "score"):
            raise ValueError(f"unexpected ranking header: {path.name}")
        for row in rows:
            app = row["app_id"]
            if app not in apps:
                if archive:
                    continue
                raise ValueError(f"ranking outside frozen cohort: {path.name}")
            rank, unit = int(row["rank"]), row["unit"]
            if take_prefix and rank > FINAL_DEPTH:
                continue
            if rank < 1 or rank > FINAL_DEPTH or unit not in corpus:
                raise ValueError(f"ranking has an invalid rank or corpus unit: {path.name}")
            by_app[app].append((rank, unit))
    rankings = {}
    for app, rows in by_app.items():
        rows.sort()
        if [rank for rank, _ in rows] != list(range(1, len(rows) + 1)) or len({u for _, u in rows}) != len(rows):
            raise ValueError(f"invalid ranks or duplicate units in {path.name}, app {app}")
        rankings[app] = [unit for _, unit in rows]
    return rankings


def _trace(path: Path, query_ids: list[str], runtime_sha: str, rankings: dict) -> None:
    with checked_path(path).open(encoding="utf-8") as stream:
        for app, line in zip_longest(query_ids, stream):
            if app is None or line is None:
                raise ValueError("runtime trace does not cover the exact frozen cohort")
            row = json.loads(line)
            if row["app_id"] != app or row["frozen_manifest_sha256"] != runtime_sha or row["arms"].keys() != set(ARMS):
                raise ValueError("runtime trace does not match the frozen query or arm set")
            if row["shared_seed"] != rankings["complete_content_fusion"][app]:
                raise ValueError(f"complete-content fusion differs from its trace for app {app}")
            for name in ARMS:
                if row["arms"][name]["final_ids"] != rankings[name][app]:
                    raise ValueError(f"{name} ranking differs from its trace for app {app}")


def _recall(rankings: dict, positives: dict, support: dict) -> dict:
    return {
        kind: {
            app: len(positives[app][kind].intersection(rankings[app])) / len(positives[app][kind])
            for app in support[kind]
        }
        for kind in KINDS
    }


def _summary(per_query: dict) -> dict:
    return {
        f"{kind}_R@{FINAL_DEPTH}": {
            "mean": round(sum(rows.values()) / len(rows), 5) if rows else None, "n": len(rows),
        }
        for kind, rows in per_query.items()
    }


def _contrast(arm: dict, reference: dict, clusters: dict) -> dict:
    result = {}
    for kind in KINDS:
        key = f"{kind}_R@{FINAL_DEPTH}"
        if arm[kind].keys() != reference[kind].keys():
            raise ValueError(f"matched metric support differs: {key}")
        apps = sorted(arm[kind])
        if not apps:
            result[key] = {"status": "NOT_RUN", "delta": None, "ci95": None, "n": 0}
            continue
        values = [arm[kind][app] - reference[kind][app] for app in apps]
        labels = [clusters[app] for app in apps]
        mean, lo, hi = cluster_bootstrap(values, labels)
        result[key] = {
            "status": "MEASURED", "delta": mean, "ci95": [lo, hi], "n": len(apps),
            "clusters": len(set(labels)), "wins": sum(value > 0 for value in values),
            "losses": sum(value < 0 for value in values),
        }
    return result


def evaluate(manifest_path: Path, freeze_sha: str, run_dir: Path, out: Path) -> dict:
    manifest_path = checked_digest(manifest_path, freeze_sha)
    manifest = _json(manifest_path)
    base = manifest_path.parent
    if (manifest["schema"] != SCHEMA or manifest["block"] != BLOCK
            or manifest["inputs"].keys() != {"pairs", "clusters"}):
        raise ValueError("expected a frozen P1-DEV evaluation manifest")
    runtime_pin = manifest["runtime_manifest"]
    runtime_path = _pinned(base, runtime_pin)
    runtime_manifest = _json(runtime_path)
    runtime_sha = runtime_pin["sha256"]
    if (runtime_manifest["schema"] != "ptp-p2t04-screen/1" or runtime_manifest["block"] != BLOCK
            or runtime_manifest["policy_sha256"] != POLICY_V1_SHA256 or runtime_manifest["inputs"].keys() != INPUTS
            or runtime_manifest["screen_limits"]["final"] != FINAL_DEPTH):
        raise ValueError("expected the frozen P1-DEV screen and common final depth")
    query_ids = runtime_manifest["query_ids"]
    if not isinstance(query_ids, list) or not all(isinstance(app, str) and app for app in query_ids):
        raise ValueError("query cohort must be an ordered list of application IDs")
    apps = set(query_ids)
    if not apps or len(apps) != len(query_ids) or manifest["cohort_sha256"] != cohort_sha256(query_ids):
        raise ValueError("evaluation cohort differs from the frozen runtime query IDs")

    out = checked_path(out)
    if out.exists():
        raise FileExistsError(f"choose a new evaluation output path: {out}")
    run_dir = checked_path(run_dir)
    runtime = _json(run_dir / "runtime.json")
    reproduction = _json(run_dir / "bm25-reproduction.json")
    gate_mode = bm25_gate_mode(runtime_manifest)
    if runtime["block"] != BLOCK or runtime["manifest_sha256"] != runtime_sha or runtime["query_count"] != len(apps):
        raise ValueError("completed runtime receipt does not match the frozen cohort")
    if (reproduction["status"] != "PASS" or reproduction["manifest_sha256"] != runtime_sha
            or reproduction["queries"] != len(apps) or reproduction.get("mode", BM25_EXACT) != gate_mode):
        raise ValueError("BM25-full reproduction gate did not pass for the frozen cohort")
    if "mode" in reproduction:
        exact, ties = reproduction.get("exact_queries"), reproduction.get("cutoff_ties")
        if (type(exact) is not int or type(ties) is not int or min(exact, ties) < 0
                or exact + ties != len(apps) or (gate_mode == BM25_EXACT and ties != 0)):
            raise ValueError("invalid BM25-full reproduction counts for the frozen gate")

    units_path = _pinned(runtime_path.parent, runtime_manifest["inputs"]["units"])
    tasks_path = _pinned(runtime_path.parent, runtime_manifest["inputs"]["tasks"])
    pairs_path = _pinned(base, manifest["inputs"]["pairs"])
    clusters_path = _pinned(base, manifest["inputs"]["clusters"])
    tasks = selected_records(dev_records(tasks_path, tsv=True), apps)
    cluster_rows = selected_records(dev_records(clusters_path, tsv=True), apps)
    clusters = {app: row["art_unit"].strip() or f"q:{app}" for app, row in cluster_rows.items()}
    corpus = _corpus(units_path)
    positives = _positives(pairs_path, tasks, corpus)
    support = {kind: [app for app in query_ids if positives.get(app, {}).get(kind)] for kind in KINDS}

    rankings, digests = {}, {}
    for name in RANKING_ARMS:
        path = run_dir / f"{name}.tsv"
        rankings[name], digests[name] = _rankings(path, apps, corpus), _sha(path)
    _trace(run_dir / "trace.jsonl", query_ids, runtime_sha, rankings)
    if any(not all(rankings["original_" + route].values()) for route in ROUTES if route != "L"):
        raise ValueError("a dense complete-content comparator is missing a frozen query")
    for route in ROUTES:
        pin = runtime_manifest["inputs"]["route_" + route]
        path = checked_path(runtime_path.parent / pin["path"])
        if path.name != f"run-{BLOCK}.tsv.gz":
            raise ValueError("complete-content comparator archive must be a P1-DEV run")
        path = _pinned(runtime_path.parent, pin)
        if rankings["original_" + route] != _rankings(path, apps, corpus, archive=True, take_prefix=True):
            raise ValueError(f"complete-content comparator {route} differs from the frozen archive")

    archive = manifest.get(F3_NAME)
    if archive is not None:
        path = checked_path(base / archive["ranking"]["path"])
        if path.parent.name != BLOCK or path.name not in {f"{F3_ALLOCATION}.tsv", f"{F3_ALLOCATION}.tsv.gz"}:
            raise ValueError("archived comparator must be the P1-DEV F3* ranking")
        path = _pinned(base, archive["ranking"])
        rankings[F3_NAME], digests[F3_NAME] = _rankings(path, apps, corpus, archive=True), archive["ranking"]["sha256"]
        empty = {app for app in apps if not rankings[F3_NAME][app]}
        if empty != set(archive.get("empty_query_ids", [])):
            raise ValueError("archived F3* query coverage differs from its frozen empty-ranking list")

    recalls = {name: _recall(rows, positives, support) for name, rows in rankings.items()}
    comparisons = {
        name: {
            "paired_recall": _contrast(recalls[TARGET], recalls[name], clusters),
            "candidates": overlap_stats(rankings[TARGET], rows, positives)[f"@{FINAL_DEPTH}"],
        }
        for name, rows in rankings.items() if name != TARGET
    }
    report = {
        "schema": SCHEMA, "block": BLOCK, "manifest_sha256": freeze_sha,
        "runtime_manifest_sha256": runtime_sha, "cohort_sha256": manifest["cohort_sha256"],
        "query_count": len(apps), "metric_support": {kind: len(ids) for kind, ids in support.items()},
        "bootstrap": {"unit": "examiner art unit", "replicates": B, "seed": SEED},
        "ranking_sha256": digests, "runtime_trace_sha256": _sha(run_dir / "trace.jsonl"),
        "runtime_receipt_sha256": _sha(run_dir / "runtime.json"),
        "bm25_reproduction_sha256": _sha(run_dir / "bm25-reproduction.json"),
        "target": TARGET,
        "arms": {
            name: {"metrics": _summary(recalls[name]), "empty_rankings": sum(not row for row in rows.values())}
            for name, rows in rankings.items()
        },
        "comparisons_against": comparisons,
        "archived_f3_allocation": F3_ALLOCATION if archive is not None else None,
        "decision": {"status": "NOT_RUN", "reason": "no scientific selection rule declared by this evaluator"},
    }
    with out.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--freeze-sha256", required=True)
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    evaluate(args.manifest, args.freeze_sha256, args.run_dir, args.out)
