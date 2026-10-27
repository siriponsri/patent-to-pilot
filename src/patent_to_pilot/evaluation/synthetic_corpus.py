"""Reproducible synthetic development/demo corpus, never independent gold."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import random
from pathlib import Path

VERSION = "ptp-synthetic-20261027-v2"
DOMAINS = ("barrier film", "powder mixing", "sensor housing", "water filtration")
EVENTS = ("withdrawal", "policy_revision", "contradiction", "partner_delay")


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def generate(seed: int = 20261027, families: int = 24) -> dict:
    if type(seed) is not int or type(families) is not int or not 8 <= families <= 120 or families % 4:
        raise ValueError("integer seed and 8..120 families divisible by four required")
    rng = random.Random(seed)
    cases = []
    for family in range(families):
        component = family % 4
        template = f"SYN-TEMPLATE-{component}"
        split = "development" if component < 2 else "demo"
        capacity = rng.randrange(10, 41) * 10
        for variant in range(2):
            case_id = f"SYN-{family:03}-{variant}"
            source_id = f"SYN-SOURCE-{family:03}-{variant}"
            content = f"SYNTHETIC FICTION. {case_id}. Fictional {DOMAINS[component]} prototype. Capacity {capacity} units/day. Partner test access is unconfirmed. No market demand or patent validity is established."
            row = {
                "case_id": case_id, "label": "SYNTHETIC", "independent_validation": False,
                "family_id": f"SYN-FAMILY-{family:03}", "template_id": template,
                "split": split, "brief": {"project_id": case_id, "version": 1,
                    "objective": f"Compare evidence needs for a fictional {DOMAINS[component]} pilot", "audience": "entrepreneur" if variant == 0 else "investor", "data_class": "synthetic"},
                "source": {"source_id": source_id, "version": 1, "content": content,
                    "sha256": hashlib.sha256(content.encode()).hexdigest(), "rights": "Project-authored synthetic fixture; repository license applies; no third-party patent reproduced"},
                "organization": {"owned_capacity_units_per_day": capacity, "partner_access": "unknown", "clinical_approval": "unknown"},
                "routes": [{"route_id": "prototype", "state": "candidate"}, {"route_id": "commercial", "state": "blocked_by_missing_evidence"}],
                "event": {"kind": EVENTS[component], "source_id": source_id, "before_version": 1, "after_version": 2,
                    "affected_route_ids": ["prototype"], "preserved_route_ids": ["commercial"], "effective_day": 7 + variant},
                "unknowns": ["demand", "market valuation", "FTO", "partner test access"],
            }
            row["event"]["change"] = (
                {"source_state": "withdrawn", "reason": "Fictional supplier corrected an unsupported capacity statement"},
                {"policy": "outsourced prototyping", "before": "conditional", "after": "prohibited", "scope": "prototype only"},
                {"claim": "owned capacity", "previous_units_per_day": capacity, "new_units_per_day": capacity // 2, "resolution": "unknown pending document review"},
                {"partner_access": "unknown", "earliest_test_day": 30 + variant, "business_impact": "unknown; no revenue forecast"},
            )[component]
            cases.append(row)
    result = {"version": VERSION, "seed": seed, "purpose": "development/demo only", "cases": cases,
        "held_out_cases": [], "scientific_gold": "NONE", "multimodal": "NOT_IMPLEMENTED; text, Markdown, CSV, JSON only"}
    validate(result)
    return result


def validate(corpus: dict) -> dict:
    from patent_to_pilot.product.contracts import ProjectBrief
    if corpus.get("version") != VERSION or corpus.get("held_out_cases") != [] or corpus.get("scientific_gold") != "NONE":
        raise ValueError("synthetic development-only contract required")
    seen = set()
    grouping = {}
    events = set()
    for row in corpus["cases"]:
        if set(row) != {"case_id", "label", "independent_validation", "family_id", "template_id", "split", "brief", "source", "organization", "routes", "event", "unknowns"}:
            raise ValueError("closed synthetic row required")
        brief = ProjectBrief.model_validate(row["brief"])
        if row["case_id"] in seen or brief.project_id != row["case_id"] or brief.data_class != "synthetic":
            raise ValueError("duplicate or inconsistent synthetic identity")
        seen.add(row["case_id"])
        if row["label"] != "SYNTHETIC" or row["independent_validation"] is not False:
            raise ValueError("synthetic labeling/validation claim invalid")
        if row["split"] not in {"development", "demo"}:
            raise ValueError("synthetic cases cannot enter held-out evaluation")
        for group in (row["family_id"], row["template_id"]):
            if group in grouping and grouping[group] != row["split"]:
                raise ValueError("family/template leakage across splits")
            grouping[group] = row["split"]
        source = row["source"]
        if set(source) != {"source_id", "version", "content", "sha256", "rights"} or set(row["organization"]) != {"owned_capacity_units_per_day", "partner_access", "clinical_approval"} or any(set(route) != {"route_id", "state"} for route in row["routes"]):
            raise ValueError("closed source/organization/route schema required")
        if not source["source_id"].startswith("SYN-") or not source["content"].startswith("SYNTHETIC FICTION."):
            raise ValueError("source must be explicitly fictional")
        if hashlib.sha256(source["content"].encode()).hexdigest() != source["sha256"]:
            raise ValueError("source content hash mismatch")
        capacity = row["organization"]["owned_capacity_units_per_day"]
        if type(capacity) is not int or capacity <= 0 or f"Capacity {capacity} units/day." not in source["content"]:
            raise ValueError("cross-field capacity mismatch")
        event = row["event"]
        events.add(event["kind"])
        route_ids = {x["route_id"] for x in row["routes"]}
        affected, preserved = set(event["affected_route_ids"]), set(event["preserved_route_ids"])
        if event["source_id"] != source["source_id"] or event["before_version"] != source["version"] or event["after_version"] != source["version"] + 1:
            raise ValueError("event provenance/version mismatch")
        if affected & preserved or affected | preserved != route_ids:
            raise ValueError("event route partition mismatch")
    if len(seen) < 16 or events != set(EVENTS):
        raise ValueError("minimum coverage missing")
    return {"cases": len(seen), "families": len({x["family_id"] for x in corpus["cases"]}),
        "template_components": len({x["template_id"] for x in corpus["cases"]}), "event_types": sorted(events),
        "split_counts": {s: sum(x["split"] == s for x in corpus["cases"]) for s in ("development", "demo")}, "independent_real_cases": 0}


def write_corpus(out: Path, seed: int = 20261027, families: int = 24) -> dict:
    corpus = generate(seed, families)
    out.mkdir(parents=True, exist_ok=False)
    files = {"corpus.json": canonical(corpus) + b"\n"}
    for row in corpus["cases"]:
        prefix = row["case_id"]
        # Current input deliberately excludes future event definitions.
        public = {k: row[k] for k in ("case_id", "label", "brief", "source", "organization", "routes", "unknowns")}
        files[f"current/{prefix}.json"] = canonical(public) + b"\n"
        files[f"documents/{prefix}.md"] = ("# SYNTHETIC fixture\n\n" + row["source"]["content"] + "\n").encode()
        files[f"documents/{prefix}.txt"] = row["source"]["content"].encode()
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(["case_id", "label", "split", "capacity_units_per_day"])
    writer.writerows([r["case_id"], "SYNTHETIC", r["split"], r["organization"]["owned_capacity_units_per_day"]] for r in corpus["cases"])
    files["inventory.csv"] = stream.getvalue().encode()
    hashes = {}
    for name, data in sorted(files.items()):
        path = out / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        hashes[name] = hashlib.sha256(data).hexdigest()
    manifest = {"version": VERSION, "coverage": validate(corpus), "seed": seed, "files": hashes,
        "runtime_mount": "one selected current/*.json only, never corpus.json or inventory.csv", "oracle_status": "No independent gold; future event definitions curator-only"}
    (out / "manifest.json").write_bytes(canonical(manifest) + b"\n")
    return manifest
