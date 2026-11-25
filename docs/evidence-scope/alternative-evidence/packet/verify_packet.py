"""Verify packet integrity and authored graph annotations offline."""

from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import unicodedata


PACKET = Path(__file__).resolve().parent
EVIDENCE_SCOPE = PACKET.parents[1]
LANES = ("th", "en", "natural-th", "natural-en")
FIELDS = {
    "sources": "source_id version language family_id text sha256",
    "units": (
        "unit_id source_id version sha256 locator char_start char_end "
        "unit_sha256 text family_id root topic facts answer"
    ),
    "edges": "from to kind basis",
    "requests": "case_id family_id language question topic conditions seed",
    "cases": "case_id family_id status decision witness_assignments stratum",
    "pairs": "pair_id kind cases",
    "assignments": "required permitted",
}
STATUSES = ("ANSWERABLE", "FINITE_UNANSWERABLE", "UNADJUDICATED")
EDGE_KINDS = {"applicability", "qualification", "reference", "amendment", "dependency"}


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def text_hash(text):
    return sha256(text.encode("utf-8"))


def read_json(path):
    return json.loads(path.read_bytes())


def unique_index(rows, field):
    index = {row[field]: row for row in rows}
    assert len(index) == len(rows), field
    return index


def check_fields(rows, kind):
    for row in rows:
        assert set(row) == set(FIELDS[kind].split()), (kind, row)


def closure(unit_id, links, active=frozenset()):
    assert unit_id not in active, ("cycle", unit_id)
    reached = {unit_id}
    for target in links[unit_id]:
        reached.update(closure(target, links, active | {unit_id}))
    return reached


def check_lane(lane):
    runtime = read_json(PACKET / lane / "runtime.json")
    labels = read_json(PACKET / lane / "labels.json")
    assert set(runtime) == {"sources", "units", "edges", "requests"}, lane
    assert set(labels) == {"cases", "pairs"}, lane
    for kind, rows in (runtime | labels).items():
        check_fields(rows, kind)

    language = lane.split("-")[-1]
    source_rows = runtime["sources"]
    sources = {(s["source_id"], s["version"]): s for s in source_rows}
    assert len(sources) == len(source_rows), lane
    for source in source_rows:
        assert source["language"] == language
        assert source["sha256"] == text_hash(source["text"])

    units = unique_index(runtime["units"], "unit_id")
    unit_counts = Counter(u["family_id"] for u in units.values())
    assert set(unit_counts) == {s["family_id"] for s in source_rows}, lane
    assert all(4 <= count <= 12 for count in unit_counts.values()), lane
    by_source = defaultdict(list)
    for unit_id, unit in units.items():
        key = (unit["source_id"], unit["version"])
        source = sources[key]
        start, end = unit["char_start"], unit["char_end"]
        assert type(start) is int and type(end) is int, unit_id
        assert 0 <= start < end <= len(source["text"]), unit_id
        assert unit["text"] == source["text"][start:end], unit_id
        assert unit["unit_sha256"] == text_hash(unit["text"]), unit_id
        assert unit["family_id"] == source["family_id"], unit_id
        assert unit["sha256"] == source["sha256"], unit_id
        assert unit["locator"] and type(unit["root"]) is bool, unit_id
        assert (unit["topic"] is not None) == unit["root"], unit_id
        assert all(value and value in unit["text"] for value in unit["facts"].values()), unit_id
        assert unit["answer"] is None or unit["answer"] in unit["text"], unit_id
        by_source[key].append(unit)
    for key, source in sources.items():
        source_units = sorted(by_source[key], key=lambda u: u["char_start"])
        assert len({u["locator"] for u in source_units}) == len(source_units), key
        assert "\n\n".join(u["text"] for u in source_units) + "\n" == source["text"], key

    links = defaultdict(set)
    for edge in runtime["edges"]:
        origin, target = edge["from"], edge["to"]
        assert edge["kind"] in EDGE_KINDS, edge
        assert edge["basis"] and edge["basis"] in units[origin]["text"], edge
        assert target not in links[origin], edge
        assert units[origin]["family_id"] == units[target]["family_id"], edge
        if edge["kind"] == "amendment":
            assert units[origin]["version"] != units[target]["version"], edge
        links[origin].add(target)
    paths = {unit_id: closure(unit_id, links) for unit_id in units}

    requests = unique_index(runtime["requests"], "case_id")
    cases = unique_index(labels["cases"], "case_id")
    assert requests.keys() == cases.keys(), lane
    assert len({r["question"] for r in requests.values()}) == len(requests), lane
    assert {r["family_id"] for r in requests.values()} == set(unit_counts), lane
    witness_signatures = {}
    for case_id, request in requests.items():
        case = cases[case_id]
        family = request["family_id"]
        seed = request["seed"]
        assert request["language"] == language and case["family_id"] == family, case_id
        assert 2 <= len(seed) <= 5 and len(set(seed)) == len(seed), case_id
        assert all(units[u]["family_id"] == family for u in seed), case_id
        assert case["stratum"] and case["status"] in STATUSES, case_id
        assert all(value and value in request["question"] for value in request["conditions"].values()), case_id
        reachable = set().union(*(paths[u] for u in seed))
        assignments = case["witness_assignments"]
        check_fields(assignments, "assignments")
        if case["status"] != "ANSWERABLE":
            assert case["decision"] == "ABSTAIN" and not assignments, case_id
        else:
            assert case["decision"] != "ABSTAIN" and assignments, case_id
        if case["status"] == "UNADJUDICATED":
            assert lane.startswith("natural-"), case_id
            continue
        if case["status"] == "FINITE_UNANSWERABLE":
            assert not lane.startswith("natural-"), case_id

        # Cross-check the corpus tags against the authored labels, using the
        # full static graph and no policy, budget, trace or retrieval result.
        authored_paths = {}
        for root_id, root in units.items():
            if root["family_id"] != family or not root["root"] or root["topic"] != request["topic"]:
                continue
            chain = paths[root_id]
            facts = defaultdict(set)
            for unit_id in chain:
                for key, value in units[unit_id]["facts"].items():
                    facts[key].add(value)
            if all(facts[key] == {value} for key, value in request["conditions"].items()):
                answers = {units[u]["answer"] for u in chain} - {None}
                assert answers == {case["decision"]}, (case_id, root_id)
                authored_paths[root_id] = chain
        observed_roots = set()
        for assignment in assignments:
            required = assignment["required"]
            assert required and len(required) == len(set(required)), case_id
            assert required == assignment["permitted"], case_id
            root_id = required[0]
            assert set(required) == authored_paths[root_id], case_id
            assert set(required) <= reachable, (case_id, "reference unreachable")
            assert root_id not in observed_roots, case_id
            observed_roots.add(root_id)
        assert observed_roots == set(authored_paths), case_id
        witness_signatures[case_id] = (
            case["decision"], frozenset(frozenset(path) for path in authored_paths.values())
        )

    paired_cases = set()
    for pair_id, pair in unique_index(labels["pairs"], "pair_id").items():
        first, second = pair["cases"]
        assert first != second and not ({first, second} & paired_cases), pair_id
        paired_cases.update((first, second))
        a, b = requests[first], requests[second]
        assert a["family_id"] == b["family_id"] and a["seed"] == b["seed"], pair_id
        assert a["topic"] == b["topic"], pair_id
        assert pair["kind"] in {"changing", "invariant"}, pair_id
        invariant = pair["kind"] == "invariant"
        a_conditions, b_conditions = a["conditions"], b["conditions"]
        assert a_conditions.keys() == b_conditions.keys(), pair_id
        edits = sum(a_conditions[key] != b_conditions[key] for key in a_conditions)
        assert edits == (0 if invariant else 1), pair_id
        assert (witness_signatures[first] == witness_signatures[second]) == invariant, pair_id

    counts = {
        "families": len(unit_counts),
        "sources": len(sources),
        "units": len(units),
        "edges": len(runtime["edges"]),
        "cases": len(cases),
        "status": {status: sum(c["status"] == status for c in cases.values()) for status in STATUSES},
        "pairs": {kind: sum(p["kind"] == kind for p in labels["pairs"]) for kind in ("changing", "invariant")},
        "changing_pairs_same_answer": sum(
            pair["kind"] == "changing"
            and cases[pair["cases"][0]]["decision"] == cases[pair["cases"][1]]["decision"]
            for pair in labels["pairs"]
        ),
    }
    return counts, set(unit_counts), source_rows


def check_baseline(all_families, source_rows):
    research = EVIDENCE_SCOPE / "research"
    demos = read_json(EVIDENCE_SCOPE / "receipts" / "S2-sources.json")
    splits = (research / "evaluator" / "splits.jsonl").read_text(encoding="utf-8").splitlines()
    old_family_ids = {json.loads(row)["family_id"] for row in splits}
    old_source_ids = {row["source_id"] for row in demos["display_sources"]}
    old_hashes = {row["canonical_sha256"] for row in demos["display_sources"]}
    old_hashes.update(row["sha256"] for row in demos["originals"].values())
    old_text_hashes = set()
    for lane in ("proposal", "selection", "dev"):
        rows = (research / "runtime" / lane / "sources.jsonl").read_text(encoding="utf-8").splitlines()
        for entry in map(json.loads, rows):
            old_source_ids.add(entry["source_id"])
            old_hashes.add(entry["sha256"])
            old_text_hashes.add(normalized_hash(entry["text"]))
    assert all_families.isdisjoint(old_family_ids)
    assert {s["source_id"] for s in source_rows}.isdisjoint(old_source_ids)
    assert {s["sha256"] for s in source_rows}.isdisjoint(old_hashes)
    assert {normalized_hash(s["text"]) for s in source_rows}.isdisjoint(old_text_hashes)


def normalized_hash(text):
    return text_hash(" ".join(unicodedata.normalize("NFC", text).split()))


def main():
    manifest = read_json(PACKET / "manifest.json")
    files = manifest["files"]
    actual = {
        path.relative_to(PACKET).as_posix()
        for path in PACKET.rglob("*")
        if path.is_file() and path.name != "manifest.json" and "__pycache__" not in path.parts
    }
    assert actual == set(files), (actual ^ set(files))
    for name, record in files.items():
        data = (PACKET / name).read_bytes()
        assert b"\r" not in data and data.endswith(b"\n"), name
        assert record == {"bytes": len(data), "sha256": sha256(data)}, name

    all_families = set()
    all_sources = []
    for lane in LANES:
        counts, families, sources = check_lane(lane)
        assert all_families.isdisjoint(families), lane
        assert counts == manifest["lanes"][lane]["counts"], lane
        assert sorted(families) == manifest["lanes"][lane]["family_ids"], lane
        all_families.update(families)
        all_sources.extend(sources)
        print(f"{lane}: {json.dumps(counts, sort_keys=True)}")
    check_baseline(all_families, all_sources)
    print("PASS: packet integrity, authored graph contracts, baseline ID and digest disjointness")


if __name__ == "__main__":
    main()
