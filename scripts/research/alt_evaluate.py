"""Independent packet and captured-trace evaluation for alternative evidence."""

from collections import defaultdict
from datetime import datetime
from hashlib import sha256
from math import floor, ceil
from random import Random


ARMS = ("assignments", "premise", "no_disagreement", "follow_reference", "coverage")
LIMITS = dict(actions=8, depth=12, inspections=96, graph_reads=96, returned=8,
              elapsed_ms=30_000, model_tokens=0)
IDENTITY = ("unit_id", "source_id", "version", "sha256", "locator", "char_start",
            "char_end", "unit_sha256", "text")
KINDS = {"applicability", "amendment", "qualification", "dependency", "reference"}
SEED = 20261125


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(text):
    return sha256(text.encode("utf-8")).hexdigest()


def validate_packet(packet):
    sources = {}
    for source in packet["sources"]:
        key = source["source_id"], source["version"]
        require(key not in sources, "duplicate source/version")
        require(digest(source["text"]) == source["sha256"], "source digest")
        sources[key] = source
    units = {}
    by_family = defaultdict(set)
    locators = set()
    for unit in packet["units"]:
        uid = unit["unit_id"]
        key = unit["source_id"], unit["version"]
        source = sources[key]
        start, end = unit["char_start"], unit["char_end"]
        locator = (*key, unit["locator"], start, end)
        require(uid not in units and locator not in locators and unit["locator"], "duplicate unit")
        require(unit["family_id"] == source["family_id"] and unit["sha256"] == source["sha256"]
                and type(start) is type(end) is int and 0 <= start < end <= len(source["text"])
                and source["text"][start:end] == unit["text"]
                and digest(unit["text"]) == unit["unit_sha256"], "source/unit mismatch")
        require(type(unit["root"]) is bool and (not unit["root"] or unit["topic"])
                and isinstance(unit["facts"], dict)
                and all(isinstance(v, str) for v in unit["facts"].values())
                and (unit["answer"] is None or isinstance(unit["answer"], str)), "annotations")
        units[uid] = unit
        locators.add(locator)
        by_family[unit["family_id"]].add(uid)
    require(all(4 <= len(ids) <= LIMITS["depth"] for ids in by_family.values()), "family size")

    edges = defaultdict(list)
    all_edges = set()
    for edge in packet["edges"]:
        origin, target = edge["from"], edge["to"]
        key = origin, target, edge["kind"]
        require(key not in all_edges and origin != target and edge["kind"] in KINDS
                and units[origin]["family_id"] == units[target]["family_id"]
                and edge["basis"] and edge["basis"] in units[origin]["text"], "edge identity")
        all_edges.add(key)
        edges[origin].append(edge)

    def check_cycle(uid, ancestors):
        require(uid not in ancestors, "circular witness obligation")
        for edge in edges[uid]:
            check_cycle(edge["to"], {*ancestors, uid})

    for ids in by_family.values():
        require(sum(len(edges[uid]) for uid in ids) <= 24, "family edge cap")
        for uid in ids:
            check_cycle(uid, set())
    requests = {}
    for request in packet["requests"]:
        case = request["case_id"]
        seed = request["seed"]
        require(set(request) == {"case_id", "family_id", "language", "question",
                                 "topic", "conditions", "seed"}, "request fields")
        require(case not in requests and 2 <= len(seed) <= 5 and len(seed) == len(set(seed))
                and set(seed) <= by_family[request["family_id"]] and request["question"]
                and request["topic"] and isinstance(request["conditions"], dict)
                and all(isinstance(value, str) for value in request["conditions"].values()),
                "invalid request")
        require(all(sources[units[uid]["source_id"], units[uid]["version"]]["language"] ==
                    request["language"] for uid in by_family[request["family_id"]]), "family language")
        requests[case] = request
    return units, by_family, edges, requests


def validate_labels(record, requests, by_family):
    labels = {}
    for label in record["cases"]:
        cid = label["case_id"]
        family = label["family_id"]
        status = label["status"]
        witnesses = label["witness_assignments"]
        require(cid not in labels and family == requests[cid]["family_id"]
                and status in {"ANSWERABLE", "FINITE_UNANSWERABLE", "UNADJUDICATED"}, "label identity")
        require(bool(witnesses) == (status == "ANSWERABLE"), "label witness count")
        require((status == "ANSWERABLE") == (label["decision"] not in (None, "ABSTAIN")),
                "label decision")
        require(status != "FINITE_UNANSWERABLE" or label["decision"] == "ABSTAIN",
                "finite-case decision")
        for assignment in witnesses:
            required = set(assignment["required"])
            permitted = set(assignment["permitted"])
            require(required and required <= permitted <= by_family[family], "invalid gold witness")
        labels[cid] = label
    require(set(labels) == set(requests), "request/label mismatch")
    pair_ids = set()
    for pair in record["pairs"]:
        a, b = pair["cases"]
        require(pair["pair_id"] not in pair_ids and a != b and pair["kind"] in ("changing", "invariant")
                and requests[a]["seed"] == requests[b]["seed"]
                and labels[a]["family_id"] == labels[b]["family_id"]
                and labels[a]["status"] == labels[b]["status"] == "ANSWERABLE", "pair mismatch")
        def signature(cid):
            label = labels[cid]
            return label["decision"], {frozenset(row["required"]) for row in label["witness_assignments"]}
        require((signature(a) == signature(b)) == (pair["kind"] == "invariant"), "pair semantics")
        pair_ids.add(pair["pair_id"])
    return labels


def evidence_for(root, pool, edges, units, conditions):
    visited = {root}
    frontier = [root]
    missing_links = []
    for uid in frontier:
        for edge in edges[uid]:
            target = edge["to"]
            if target not in pool:
                missing_links.append(edge)
            elif target not in visited:
                visited.add(target)
                frontier.append(target)
    bindings = {k: {uid: units[uid]["facts"][k] for uid in visited if k in units[uid]["facts"]}
                for k in conditions}
    mismatch = any(fact != conditions[key] for key, values in bindings.items()
                   for fact in values.values())
    answers = {units[uid]["answer"] for uid in visited if units[uid]["answer"] is not None}
    possible = not mismatch and len(answers) <= 1
    complete = possible and not missing_links and all(bindings.values()) and len(answers) == 1
    return visited, missing_links, bindings, answers, possible, complete


def utc_ns_is_valid(value):
    return datetime.fromisoformat(value).utcoffset().total_seconds() == 0


def validate_trace(trace, request, units, family, edges):
    pool = list(request["seed"])
    candidates = trace["events"]
    require(trace["arm"] in ARMS and trace["case_id"] == request["case_id"], "trace identity")
    require(type(trace["start_ns"]) is type(trace["end_ns"]) is int
            and 0 <= trace["start_ns"] <= trace["end_ns"] and utc_ns_is_valid(trace["start_utc"])
            and type(trace["cpu_ns"]) is int and trace["cpu_ns"] >= 0, "trace clock")
    require(2 <= len(candidates) <= LIMITS["actions"] and len(candidates) % 2 == 0,
            "action schedule")
    previous = trace["start_ns"]
    pending = {}
    seen = frozenset()
    last_roots = []
    for i, event in enumerate(candidates):
        kind, inspected, opened = (event[key] for key in ("kind", "inspected", "opened"))
        require(type(event["start_ns"]) is type(event["end_ns"]) is int
                and previous <= event["start_ns"] <= event["end_ns"] <= trace["end_ns"]
                and utc_ns_is_valid(event["utc"]), "event clock")
        require(len(inspected) <= LIMITS["depth"], "event depth")
        expected = "seed" if i == 0 else "rerank" if i % 2 else "acquire"
        require(kind == expected, "action ordering")
        if kind == "seed":
            require(inspected == opened == pool and event["graph_reads"] == 0, "seed mismatch")
        elif kind == "acquire":
            require(inspected == sorted(family) and len(opened) == 1 and opened[0] in family - set(pool)
                    and event["graph_reads"] == 0 and type(event["plan_ns"]) is int
                    and 0 <= event["plan_ns"] <= event["end_ns"] - event["start_ns"], "acquisition")
            target = event["plan"]["target"]
            require(target is None or target == opened[0] and target in pending, "unlicensed target")
            for option in event["plan"]["options"]:
                require(option["target"] in pending and option["affected_roots"]
                        and all(root in pending[option["target"]] for root in option["affected_roots"])
                        and all(edge in edges[edge["from"]] and edge["from"] in seen
                                and edge["to"] == option["target"] for edge in option["basis"]),
                        "unobserved option basis")
            pool.extend(opened)
        else:
            require(inspected == pool and not opened
                    and event["graph_reads"] == sum(len(edges[uid]) for uid in pool), "rerank meter")
            roots = {uid for uid in pool if units[uid]["root"] and units[uid]["topic"] == request["topic"]}
            proposals = event["proposals"]
            ranked = [proposal["root"] for proposal in proposals]
            require(len(ranked) == len(roots) and set(ranked) == roots, "assignment coverage")
            pending = defaultdict(set)
            last_roots = []
            seen = frozenset(pool)
            for proposal in proposals:
                root = proposal["root"]
                visitors, missing, bindings, answers, possible, complete = evidence_for(
                    root, seen, edges, units, request["conditions"])
                require(set(proposal["witnesses"]) == visitors
                        and len(proposal["witnesses"]) == len(visitors)
                        and sorted(proposal["observed_conclusions"]) == sorted(answers)
                        and proposal["bindings"] == bindings
                        and bool(proposal["conflicting_conditions"]) != possible
                        and proposal["complete"] is complete
                        and proposal["unresolved"] == missing
                        and proposal["conclusion"] == (next(iter(answers)) if len(answers) == 1 else None),
                        "false assignment state")
                licensed = {(edge["from"], edge["to"], edge["kind"], edge["basis"])
                            for uid in visitors for edge in edges[uid] if edge["to"] in visitors}
                traced = [(edge["from"], edge["to"], edge["kind"], edge["basis"])
                          for edge in proposal["licensed_edges"]]
                require({unit["unit_id"] for unit in proposal["identity"]} == visitors
                        and len(proposal["identity"]) == len(visitors)
                        and set(proposal["missing_conditions"]) == {key for key, hits in bindings.items() if not hits}
                        and len(traced) == len(licensed) and set(traced) == licensed,
                        "assignment inspection")
                for unit in proposal["identity"]:
                    require(unit["unit_id"] in visitors and
                            all(unit[key] == units[unit["unit_id"]][key]
                                for key in IDENTITY if key != "text"), "assignment provenance")
                if possible:
                    last_roots.append((root, visitors, answers, complete))
                    for edge in missing:
                        pending[edge["to"]].add(root)
        previous = event["end_ns"]

    response = trace["response"]
    support = trace["evidence"]
    ready = (last_roots and len(last_roots[0][1]) <= LIMITS["returned"]
             and all(complete and answers == last_roots[0][2]
                     for _, _, answers, complete in last_roots))
    if response == "ABSTAIN":
        require(not ready and not support and trace["selected_root"] is None, "invalid abstention")
    else:
        require(ready and last_roots[0][2] == {response}, "unresolved release")
        root, witness, _, _ = last_roots[0]
        require(trace["selected_root"] == root and len(support) == len(witness)
                and {item["unit_id"] for item in support} == witness, "release witness chain")
        for item in support:
            require(item["role"] == "support" and all(
                type(item[key]) is type(units[item["unit_id"]][key])
                and item[key] == units[item["unit_id"]][key] for key in IDENTITY), "release provenance")
    usage = dict(actions=len(candidates), depth=max(len(event["inspected"]) for event in candidates),
                 inspections=sum(len(event["inspected"]) for event in candidates),
                 graph_reads=sum(event["graph_reads"] for event in candidates),
                 returned=len(support), elapsed_ms=(trace["end_ns"] - trace["start_ns"] + 999_999) // 1_000_000,
                 model_tokens=trace["model_tokens"])
    require(all(type(usage[key]) is int and 0 <= usage[key] <= cap
                for key, cap in LIMITS.items()), "runtime budget")
    return usage


def score_case(label, trace, usage):
    if label["status"] == "UNADJUDICATED":
        return None
    if (usage is None or trace["case_id"] != label["case_id"]
            or trace["response"] != label["decision"]):
        return 0
    if label["status"] == "FINITE_UNANSWERABLE":
        return int(trace["response"] == "ABSTAIN" and not trace["evidence"])
    support = {unit["unit_id"] for unit in trace["evidence"]}
    return int(any(set(w["required"]) <= support <= set(w["permitted"])
                   for w in label["witness_assignments"]))


def interval(rows, left, right):
    groups = defaultdict(list)
    for row in rows:
        groups[row["family_id"]].append(row["arms"][left]["hit"] - row["arms"][right]["hit"])
    if len(groups) < 2:
        return None
    vectors = [groups[group] for group in sorted(groups)]
    rng = Random(SEED)
    samples = []
    for _ in range(10_000):
        chosen = rng.choices(vectors, k=len(vectors))
        samples.append(sum(sum(group) for group in chosen) / sum(map(len, chosen)))
    samples.sort()

    def percentile(p):
        i = p * (len(samples) - 1)
        return samples[floor(i)] + (i - floor(i)) * (samples[ceil(i)] - samples[floor(i)])

    return [percentile(0.025), percentile(0.975)]


def matched_risk(rows, a, b):
    answered = {
        arm: sorted((row for row in rows if row["arms"][arm]["answered"]),
                    key=lambda row: digest(f"{SEED}:{row['case_id']}"))
        for arm in (a, b)
    }
    count = min(map(len, answered.values()))
    return dict(answered_each=count, total=len(rows), full_answer_count={
        arm: len(candidates) for arm, candidates in answered.items()}, wrong_scope={
        arm: sum(row["arms"][arm]["wrong_scope"] for row in candidates[:count])
        for arm, candidates in answered.items()})
