"""Independent identity and operation validation. No runtime policy import."""

from collections import defaultdict
from datetime import datetime
from hashlib import sha256
import json

from s1_scorer import IDENTITY, LIMITS


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(text):
    return sha256(text.encode("utf-8")).hexdigest()


def identities(data):
    sources = {}
    for source in data["sources"]:
        key = (source["source_id"], source["version"])
        require(key not in sources and sha(source["text"]) == source["sha256"], "source identity")
        sources[key] = source
    units = {}
    locators = set()
    counts = defaultdict(int)
    for unit in data["units"]:
        uid = unit["unit_id"]
        loc = tuple(unit[key] for key in ("source_id", "version", "locator", "char_start", "char_end"))
        source = sources[loc[:2]]
        start, end = loc[-2:]
        require(uid not in units and loc not in locators, "duplicate evidence identity")
        require(unit["sha256"] == source["sha256"] and unit["family_id"] == source["family_id"]
                and unit["language"] == source["language"] and
                0 <= start < end <= len(source["text"]) and source["text"][start:end] == unit["text"]
                and source["text"][:start].endswith(unit["locator"] + "\n")
                and sha(unit["text"]) == unit["unit_sha256"], "invalid span provenance")
        units[uid] = unit
        locators.add(loc)
        counts[unit["family_id"]] += 1
    require(all(count == 6 for count in counts.values()), "six-unit index")
    edges = defaultdict(set)
    for edge in data["edges"]:
        a, b = (units[edge[key]] for key in ("from", "to"))
        require(a != b and a["family_id"] == b["family_id"] and edge["inferred"] is False
                and a["unit_id"] not in edges and edge["basis"] and edge["basis"] in a["text"],
                "invalid or ambiguous reference provenance")
        edges[edge["from"]].add(edge["to"])
    return units, edges


def valid_timestamp(value):
    return datetime.fromisoformat(value).utcoffset().total_seconds() == 0


def validate(trial, request, units, edges):
    seed = request["seed_pool"]
    family = {uid for uid, unit in units.items() if unit["family_id"] == request["family_id"]}
    require(len(seed) == len(set(seed)) == 4 and set(seed) <= family, "invalid seed")
    require(trial["case_id"] == request["case_id"] and
            trial["initial_pool_hash"] == sha(json.dumps(seed, separators=(",", ":"))),
            "case/seed identity")
    start, end = trial["start_ns"], trial["end_ns"]
    require(type(start) is type(end) is int and 0 <= start <= end
            and valid_timestamp(trial["start_utc"]), "trial clock")
    require(type(trial["cpu_ns"]) is int and trial["cpu_ns"] >= 0, "CPU clock")
    events = trial["events"]
    require(1 <= len(events) <= LIMITS["actions"], "action count")
    pool = seed[:]
    choice = pool[:2]
    last_end = start
    inspected = set()
    depths = []
    for i, event in enumerate(events):
        ids = event["inspected"]
        kind = event["action"]
        require(type(event["start_ns"]) is type(event["end_ns"]) is int
                and last_end <= event["start_ns"] <= event["end_ns"] <= end
                and valid_timestamp(event["utc"]), "nonmonotonic event clock")
        require(len(ids) == len(set(ids)) and set(ids) <= family, "unknown/foreign/repeated inspected ID")
        require(len(ids) <= LIMITS["candidate_depth"], "candidate depth")
        if i == 0:
            require(kind == "seed" and ids == seed, "seed order")
        elif kind == "rerank":
            order, chosen = event["ordered"], event["chosen"]
            require(ids == pool and len(order) == len(pool) and set(order) == set(pool)
                    and 1 <= len(chosen) <= 2 and order[:len(chosen)] == chosen,
                    "rerank outside current pool")
            pool, choice = order, chosen
        elif kind == "acquire":
            require(ids == sorted(family), "unaccounted candidate search")
            target = event["target"]
            require(target is None or (target in family - set(pool)
                    and any(target in edges[uid] for uid in pool)), "unlicensed search target")
            selected = event["selected"]
            require(len(selected) == int(len(pool) < len(family)) and
                    set(selected) <= set(ids) - set(pool), "invalid acquisition")
            pool.extend(selected)
        else:
            raise ValueError("unexpected action")
        inspected.update(ids)
        depths.append(len(ids))
        last_end = event["end_ns"]
    require(trial["final_pool"] == pool and trial["chosen"] == choice, "final ranking")
    evidence = trial["evidence"]
    seen = set()
    for citation in evidence:
        uid = citation["unit_id"]
        require(uid in inspected and uid not in seen and uid in pool, "uninspected/repeated return")
        require(all(type(citation[key]) is type(units[uid][key]) and
                    citation[key] == units[uid][key] for key in IDENTITY), "altered returned identity")
        require(citation["role"] in ("support", "alternative"), "evidence role")
        if citation["role"] == "support":
            require(uid in choice, "support outside chosen assignment")
        seen.add(uid)
    usage = dict(actions=len(events), candidate_depth=max(depths), inspected=sum(depths),
                 returned=len(evidence), model_tokens=0,
                 elapsed_ms=(end - start + 999_999) // 1_000_000)
    require(all(0 <= usage[key] <= limit for key, limit in LIMITS.items()), "usage cap")
    return {key: trial[key] for key in ("case_id", "decision", "evidence")} | {"usage": usage}
