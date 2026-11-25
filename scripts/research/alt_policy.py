"""Research-only policy worker for version-bound alternative evidence assignments."""

import argparse
from collections import Counter, defaultdict, deque
from datetime import datetime, timezone
import json
from math import log1p
from pathlib import Path
from time import perf_counter_ns, process_time_ns
import unicodedata


ARMS = ("assignments", "premise", "no_disagreement", "follow_reference", "coverage")
LIMITS = dict(actions=8, depth=12, inspections=96, graph_reads=96, returned=8,
              elapsed_ms=30_000, model_tokens=0)
IDENTITY = ("unit_id", "source_id", "version", "sha256", "locator", "char_start",
            "char_end", "unit_sha256", "text")
EDGE_ORDER = {"applicability": 0, "amendment": 0, "qualification": 0,
              "dependency": 1, "reference": 2}


def utc():
    return datetime.now(timezone.utc).isoformat()


def lexical_terms(text):
    text = " ".join(unicodedata.normalize("NFKC", text).casefold().split())
    return Counter(text[i:i + 3] for i in range(len(text) - 2))


class Index:
    def __init__(self, units, edges):
        self.units = {unit["unit_id"]: unit for unit in units}
        self.ids = tuple(sorted(self.units))
        self.edges = defaultdict(list)
        for edge in edges:
            self.edges[edge["from"]].append(edge)
        self.vectors = {uid: lexical_terms(unit["locator"] + " " + unit["text"])
                        for uid, unit in self.units.items()}
        self.frequency = Counter(term for vector in self.vectors.values() for term in vector)
        self.length = {uid: sum(vector.values()) for uid, vector in self.vectors.items()}
        self.average = max(1, sum(self.length.values()) / len(self.ids))

    def bm25(self, uid, query):
        vector = self.vectors[uid]
        norm = 1.2 * (0.25 + 0.75 * self.length[uid] / self.average)
        return sum(
            log1p((len(self.ids) - self.frequency[term] + 0.5) / (self.frequency[term] + 0.5))
            * vector[term] * 2.2 / (vector[term] + norm)
            for term in sorted(query) if term in vector
        )


def build_assignment(root, visible, edges, request, relevance):
    queue = deque([root])
    bound = []
    bindings = defaultdict(dict)
    values = set()
    traversed = []
    unresolved = []
    seen = {root}
    while queue:
        uid = queue.popleft()
        unit = visible[uid]
        bound.append(uid)
        if unit["answer"] is not None:
            values.add(unit["answer"])
        for key in request["conditions"]:
            if key in unit["facts"]:
                bindings[key][uid] = unit["facts"][key]
        for edge in edges[uid]:
            target = edge["to"]
            if target in visible:
                traversed.append(edge)
                if target not in seen:
                    queue.append(target)
                    seen.add(target)
            else:
                unresolved.append(edge)
    missing = [key for key in request["conditions"] if not bindings[key]]
    conflicts = [key for key, value in request["conditions"].items()
                 if any(bound_value != value for bound_value in bindings[key].values())]
    answer = next(iter(values)) if len(values) == 1 else None
    if len(values) > 1:
        conflicts.append("conflicting_conclusions")
    identifiers = [{key: visible[uid][key] for key in IDENTITY if key != "text"} for uid in bound]
    return dict(root=root, witnesses=bound, identity=identifiers, conclusion=answer,
                observed_conclusions=sorted(values), bindings=dict(bindings),
                missing_conditions=missing, conflicting_conditions=conflicts,
                licensed_edges=traversed, unresolved=unresolved,
                complete=not (missing or conflicts or unresolved) and answer is not None,
                lexical=sum(relevance[uid] for uid in sorted(bound)))


def rank_assignments(visible, edges, request, relevance):
    proposals = [
        build_assignment(uid, visible, edges, request, relevance)
        for uid, unit in visible.items() if unit["root"] and unit["topic"] == request["topic"]
    ]
    return sorted(proposals, key=lambda row: (
        bool(row["conflicting_conditions"]), not row["complete"],
        len(row["missing_conditions"]), len(row["unresolved"]),
        -row["lexical"], row["root"],
    ))


def select_prospect(arm, proposals):
    rows = [item for item in proposals if not item["conflicting_conditions"]]
    # A purely lexical search remains available with no visible obligation.
    options = defaultdict(list)
    for position, row in enumerate(rows):
        for edge in row["unresolved"]:
            options[edge["to"]].append((position, row["root"], edge))
    if not options:
        return dict(target=None, reason="no_visible_obligation", options=[])

    answer_groups = {
        row["root"]: ("answer", row["conclusion"]) if row["conclusion"] is not None
        else ("open", row["root"]) for row in rows
    }
    n_groups = len(set(answer_groups.values()))
    candidates = []
    for target, records in options.items():
        roots = sorted({root for _, root, _ in records})
        group_count = len({answer_groups[root] for root in roots})
        gate = min(EDGE_ORDER[edge["kind"]] for _, _, edge in records)
        best_position = min(position for position, _, _ in records)
        if arm == "assignments":
            split = len(roots) * (len(rows) - len(roots))
        elif arm == "premise":
            # Adaptation of premise-directed acquisition. Branches expressing one
            # conclusion share a hypothesis, with no access to unopened text.
            split = group_count * (n_groups - group_count)
        elif arm == "coverage":
            split = sum(bool(rows[position]["missing_conditions"]) for position, _, _ in records)
        else:
            split = 0
        preference = (best_position,) if arm == "follow_reference" else (-split, gate, best_position)
        candidates.append(dict(target=target, affected_roots=roots, split=split,
                               kind_priority=gate, priority=preference,
                               basis=[edge for _, _, edge in records]))
    candidates.sort(key=lambda row: (row["priority"], row["target"]))
    picked = candidates[0]
    return dict(target=picked["target"], reason="resolve_visible_obligation",
                options=candidates)


class Meter:
    def __init__(self, index, request):
        self.start = perf_counter_ns()
        self.cpu_start = process_time_ns()
        self.started_utc = utc()
        self.index = index
        self.request = request
        self.pool = []
        self.events = []
        self.visible = {}
        self.query = lexical_terms(request["question"])

    def record(self, started, kind, inspected, opened, **details):
        self.events.append(dict(kind=kind, inspected=list(inspected), opened=list(opened),
                                start_ns=started, end_ns=perf_counter_ns(), utc=utc(),
                                **details))

    def seed(self):
        start = perf_counter_ns()
        self.pool = list(self.request["seed"])
        self.record(start, "seed", self.pool, self.pool, graph_reads=0)

    def rerank(self):
        start = perf_counter_ns()
        self.visible = {uid: self.index.units[uid] for uid in self.pool}
        edges = {uid: tuple(self.index.edges.get(uid, ())) for uid in self.visible}
        relevance = {uid: self.index.bm25(uid, self.query) for uid in self.visible}
        proposals = rank_assignments(self.visible, edges, self.request, relevance)
        self.record(start, "rerank", self.pool, (), graph_reads=sum(map(len, edges.values())),
                    proposals=proposals)
        return proposals

    def acquire(self, arm, proposals):
        start = perf_counter_ns()
        plan = select_prospect(arm, proposals)
        plan_ns = perf_counter_ns() - start
        target = plan["target"]
        new_ids = set(self.index.ids) - set(self.pool)
        relevance = {uid: self.index.bm25(uid, self.query) for uid in self.index.ids}
        selected = min(new_ids, key=lambda uid: (uid != target,
                       -relevance[uid], uid))
        self.pool.append(selected)
        self.record(start, "acquire", self.index.ids, (selected,), graph_reads=0,
                    plan=plan, plan_ns=plan_ns)


def final_assignment(proposals):
    active = [row for row in proposals if not row["conflicting_conditions"]]
    if not active or any(not row["complete"] for row in active):
        return None
    if len({row["conclusion"] for row in active}) != 1:
        return None
    return active[0] if len(active[0]["witnesses"]) <= LIMITS["returned"] else None


def solve(index, request, arm):
    meter = Meter(index, request)
    meter.seed()
    while True:
        proposals = meter.rerank()
        choice = final_assignment(proposals)
        if choice or len(meter.events) + 2 > LIMITS["actions"] or len(meter.pool) >= len(index.ids):
            break
        if (perf_counter_ns() - meter.start) // 1_000_000 >= LIMITS["elapsed_ms"]:
            break
        meter.acquire(arm, proposals)
    evidence = []
    if choice:
        for uid in choice["witnesses"]:
            unit = meter.visible[uid]
            evidence.append({key: unit[key] for key in IDENTITY} | {"role": "support"})
    kept = choice and choice["witnesses"] == request["seed"][:len(choice["witnesses"])]
    disposition = ("abstain" if choice is None else "acquire" if len(meter.events) > 2
                   else "keep" if kept else "rerank")
    return dict(case_id=request["case_id"], arm=arm, response=choice["conclusion"] if choice else "ABSTAIN",
                selected_root=choice["root"] if choice else None, evidence=evidence,
                disposition=disposition, events=meter.events, start_ns=meter.start,
                end_ns=perf_counter_ns(), start_utc=meter.started_utc,
                cpu_ns=process_time_ns() - meter.cpu_start, model_tokens=0)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("runtime", type=Path)
    args = parser.parse_args()
    start, cpu = perf_counter_ns(), process_time_ns()
    content = args.runtime.read_bytes()
    data = json.loads(content)
    family_ids = {row["family_id"] for row in data["requests"]}
    indexes = {}
    for family in sorted(family_ids):
        units = [unit for unit in data["units"] if unit["family_id"] == family]
        ids = {unit["unit_id"] for unit in units}
        indexes[family] = Index(units, [edge for edge in data["edges"] if edge["from"] in ids])
    print(json.dumps(dict(kind="ingestion", bytes=len(content), elapsed_ns=perf_counter_ns() - start,
                          cpu_ns=process_time_ns() - cpu)), flush=True)
    for request in data["requests"]:
        for arm in ARMS:
            result = solve(indexes[request["family_id"]], request, arm)
            print(json.dumps(result, ensure_ascii=True), flush=True)


if __name__ == "__main__":
    main()
