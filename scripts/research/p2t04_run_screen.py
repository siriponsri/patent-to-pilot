"""Run the frozen P2-T04 screen on P1-DEV with evaluator input kept outside this process."""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import re
from array import array
from contextlib import ExitStack
from pathlib import Path
from time import perf_counter

from patent_to_pilot.workbench.relation_search import POLICY_V1_SHA256, RerankRequest
from scripts.research.g03_route_acquisition import FINAL_DEPTH, ROUTES, WINDOW, final_ranking
from scripts.research.p2t04_bm25_backend import BM25FullIndex
from scripts.research.p2t04_matched_screen import ScreenLimits, SourceUnit, run_matched_query
from scripts.research.p2t04_requirements import AssessorLimits, LexicalAssessor, extract_requirements

BLOCK = "P1-DEV"
ARMS = (
    "seed_only", "unresolved_relation", "original_query_deeper", "static_requirement",
    "generic_feedback", "extractive_feedback", "shuffled_binding",
)
INPUTS = {"queries", "bm25_queries", "tasks", "units", "full_passages", *("route_" + route for route in ROUTES)}
FORBIDDEN = re.compile(r"(?:^|[/\\_.-])(?:P[123]-TEST|sealed|\.env)(?:$|[/\\_.-])", re.IGNORECASE)


def checked_path(path: Path) -> Path:
    resolved = path.resolve()
    if any(FORBIDDEN.search(str(candidate)) or "test" in {part.lower() for part in candidate.parts}
           for candidate in (path, resolved)):
        raise ValueError(f"protected or credential path outside the screen scope: {path.name}")
    return resolved


def checked_digest(path: Path, expected: str) -> Path:
    path = checked_path(path)
    with path.open("rb") as stream:
        actual = hashlib.file_digest(stream, "sha256").hexdigest()
    if actual != expected:
        raise ValueError(f"frozen SHA-256 mismatch: {path.name}")
    return path


def dev_records(path, *, tsv=False):
    with path.open(encoding="utf-8", newline="") as stream:
        records = csv.DictReader(stream, delimiter="\t") if tsv else map(json.loads, stream)
        for record in records:
            if record["block"] != BLOCK:
                raise ValueError(f"non-{BLOCK} record in {path.name}")
            yield record


def selected_records(records, expected):
    selected = {}
    for record in records:
        app = record["app_id"]
        if app not in expected:
            continue
        if app in selected:
            raise ValueError(f"duplicate record for app {app}")
        selected[app] = record
    if selected.keys() != expected:
        raise ValueError("input does not cover every frozen query ID")
    return selected


def read_route(path, apps):
    if path.name != f"run-{BLOCK}.tsv.gz":
        raise ValueError("route must be a P1-DEV run")
    seen = {}
    with gzip.open(path, "rt", encoding="utf-8", newline="") as stream:
        rows = csv.DictReader(stream, delimiter="\t")
        if tuple(rows.fieldnames or ()) != ("app_id", "rank", "unit", "score"):
            raise ValueError(f"unexpected ranking header: {path}")
        for row in rows:
            if row["app_id"] in apps:
                seen.setdefault(row["app_id"], []).append((int(row["rank"]), row["unit"], row["score"]))
    for app, rows in seen.items():
        rows.sort()
        if [rank for rank, _, _ in rows] != list(range(1, len(rows) + 1)) or len({u for _, u, _ in rows}) != len(rows):
            raise ValueError(f"invalid archived rank or duplicate unit for app {app}")
    return seen


class Passages:
    def __init__(self, stream, version):
        self.stream = stream
        self.version = version
        self.offsets = array("Q")

    def rows(self):
        while line := self.stream.readline():
            self.offsets.append(self.stream.tell() - len(line))
            row = json.loads(line)
            yield row["unit"], row["text"]

    def read(self, unit_id, unit_rows):
        self.stream.seek(self.offsets[unit_rows[unit_id]])
        row = json.loads(self.stream.readline())
        if row["unit"] != unit_id:
            raise ValueError("source offset does not resolve to the frozen unit")
        return SourceUnit(unit_id, unit_id, self.version, row["text"])


def query_requirements(app, row, limits):
    prefix = "\n".join((row["title"], row["abstract"], ""))
    text = prefix + row["claim"]
    return extract_requirements(app, text, claim_start=len(prefix), claim_end=len(text), limits=limits)


def write_row_set(stream, app, ids):
    for rank, unit_id in enumerate(ids, start=1):
        stream.write(f"{app}\t{rank}\t{unit_id}\t0\n")


def run(manifest_path: Path, freeze_sha: str, out: Path):
    started = perf_counter()
    manifest_path = checked_digest(manifest_path, freeze_sha)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (
        manifest["schema"] != "ptp-p2t04-screen/1" or manifest["block"] != BLOCK
        or manifest["policy_sha256"] != POLICY_V1_SHA256 or manifest["inputs"].keys() != INPUTS
    ):
        raise ValueError("manifest must pin the P1-DEV screen, policy, and exact runtime input roles")
    query_ids = manifest["query_ids"]
    apps = set(query_ids)
    if not apps or len(apps) != len(query_ids):
        raise ValueError("freeze a unique, nonempty list of P1-DEV query IDs")
    seed_windows = manifest["seed_windows"]
    if (
        seed_windows.keys() != set(ROUTES) or any(type(n) is not int or n < 0 for n in seed_windows.values())
        or sum(seed_windows.values()) != 4
    ):
        raise ValueError("freeze a share of four G03 seed windows for each route")
    screen_limits = ScreenLimits(**manifest["screen_limits"])
    assessor_limits = AssessorLimits(**manifest["assessor_limits"])
    if screen_limits.seed != FINAL_DEPTH or screen_limits.final != FINAL_DEPTH:
        raise ValueError("retain the G03 200-unit common seed and final depths")
    inputs = {
        key: checked_digest(manifest_path.parent / pin["path"], pin["sha256"])
        for key, pin in manifest["inputs"].items()
    }
    work = checked_path(out).with_name(out.name + ".partial")
    if out.exists() or work.exists():
        raise FileExistsError(f"choose a new output path; existing run at {out}")
    work.mkdir(parents=True)
    tasks = selected_records(dev_records(inputs["tasks"], tsv=True), apps)
    queries = selected_records(dev_records(inputs["queries"]), apps)
    bm25_queries = selected_records(dev_records(inputs["bm25_queries"]), apps)
    route_rows = {route: read_route(inputs["route_" + route], apps) for route in ROUTES}
    if any(rows.keys() != apps for route, rows in route_rows.items() if route != "L"):
        raise ValueError("an archived dense route does not cover the entire frozen query set")
    with inputs["units"].open(encoding="utf-8", newline="") as stream:
        dates = {r["unit_id"]: r["first_pub"] for r in csv.DictReader(stream, delimiter="\t")}
    with ExitStack() as stack:
        passages = Passages(stack.enter_context(inputs["full_passages"].open("rb")), manifest["corpus_version"])
        index_started = perf_counter()
        index = BM25FullIndex(passages.rows(), dates)
        index_seconds = perf_counter() - index_started
        gate_started = perf_counter()
        for app in query_ids:
            eligibility = index.eligibility_for(app, tasks[app]["filing_date"])
            request = RerankRequest(app, bm25_queries[app]["text"], ())
            reproduced = [
                (i, unit, f"{score:.4f}") for i, (unit, score) in enumerate(index.original(request, eligibility), 1)
            ]
            if reproduced != route_rows["L"].get(app, []):
                raise RuntimeError(f"archived BM25-full reproduction failed for frozen app {app}")
        (work / "bm25-reproduction.json").write_text(
            json.dumps({"status": "PASS", "queries": len(apps), "manifest_sha256": freeze_sha,
                        "wall_seconds": perf_counter() - gate_started}) + "\n",
            encoding="utf-8",
        )
        streams = {}
        for name in (*ARMS, "complete_content_fusion", *("original_" + route for route in ROUTES)):
            stream = stack.enter_context((work / f"{name}.tsv").open("w", encoding="utf-8", newline="\n"))
            stream.write("app_id\trank\tunit\tscore\n")
            streams[name] = stream
        trace = stack.enter_context((work / "trace.jsonl").open("w", encoding="utf-8", newline="\n"))
        assessor = LexicalAssessor(assessor_limits)
        for app in query_ids:
            query_started = perf_counter()
            ranking_lists = {
                route: [unit for _, unit, _ in route_rows[route].get(app, [])] for route in ROUTES
            }
            acquired = {route: WINDOW * seed_windows[route] for route in ROUTES if seed_windows[route]}
            seed = [unit for unit, _ in final_ranking(acquired, ranking_lists)]
            record = run_matched_query(
                requirements=query_requirements(app, queries[app], assessor_limits),
                seed_ids=seed,
                limits=screen_limits,
                eligibility=index.eligibility_for(app, tasks[app]["filing_date"]),
                read_source=lambda unit: passages.read(unit, index.unit_rows),
                assess=assessor,
                search=index.search,
                rerank=index.rerank,
            )
            for name, arm in record["arms"].items():
                write_row_set(streams[name], app, arm["final_ids"])
            write_row_set(streams["complete_content_fusion"], app, seed)
            for route in ROUTES:
                write_row_set(streams["original_" + route], app, ranking_lists[route][:FINAL_DEPTH])
            trace.write(json.dumps({"app_id": app, "frozen_manifest_sha256": freeze_sha,
                                    "wall_seconds_all_arms": perf_counter() - query_started, **record}) + "\n")
    (work / "runtime.json").write_text(
        json.dumps({"block": BLOCK, "manifest_sha256": freeze_sha, "query_count": len(apps),
                    "index_wall_seconds": index_seconds, "wall_seconds": perf_counter() - started}) + "\n",
        encoding="utf-8",
    )
    work.rename(out)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--freeze-sha256", required=True)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    run(args.manifest, args.freeze_sha256, args.out)
