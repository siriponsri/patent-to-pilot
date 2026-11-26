"""Bounded deterministic evidence-reading policies for authored research fixtures."""
from hashlib import sha256

ROUTES = ("deeper", "claim_parent", "legal_reference", "attachment")
SCOPE_FIELDS = ("subject", "role", "issuer", "jurisdiction", "edition")
ORIGINS = {
    "patent_disclosure": "patent",
    "claim_limitation": "patent",
    "regulatory_requirement": "regulatory",
    "applicant_result": "regulatory",
    "incoming_request": "correspondence",
}
READ_LIMIT = 2


def digest(data):
    return sha256(data).hexdigest()


def read_case(case, preference=None):
    request = case["request"]
    remaining = list(case["candidates"])
    actions = []
    found = None
    while remaining and len(actions) < READ_LIMIT:
        selected = min(remaining, key=lambda candidate: (
            candidate["route"] != preference, candidate["rank"],
            digest(candidate["id"].encode("utf-8")),
        ))
        remaining.remove(selected)
        source = case["sources"][selected["id"]]
        encoded = source["text"].encode("utf-8")
        actions.append({
            "route": selected["route"], "source_id": selected["id"],
            "inspections": len(remaining) + 1, "bytes": len(encoded),
            "sha256": digest(encoded), "locator": source["locator"],
            "version": source["edition"], "issuer": source["issuer"],
            "routes_available": sorted({selected["route"], *(c["route"] for c in remaining)}),
        })
        if source["topic"] == request["topic"]:
            found = source | {"id": selected["id"]}
            break
    return actions, found


def handoff(case, actions, source, specialists, verify, check_role=True):
    request = case["request"]
    supported = source is not None and (
        not verify or all(
            request[field] is not None and request[field] == source[field]
            for field in SCOPE_FIELDS if field != "role" or check_role
        )
    )
    issuer = ORIGINS[source["role"]] if specialists and source else "single"
    if specialists and not source:
        issuer = ORIGINS[request["role"]]
    evidence = {
        "schema_version": "ra-pharma/1", "dossier_id": case["id"],
        "item_id": f'{case["id"]}/evidence', "agent": issuer,
        "task": "supply bounded statement",
        "subject_id": source["subject"] if source else request["subject"],
        "evidence_role": source["role"] if source else request["role"],
        "jurisdiction": source["jurisdiction"] if source else request["jurisdiction"],
        "as_of": request["as_of"],
        "statement": source["value"] if source else None,
        "sources": [actions[-1] | {"source_owner": source["issuer"]}] if source else [],
        "status": "supported" if source else "missing",
        "missing": [] if source else [request["role"]], "depends_on": [],
        "trace_id": case["id"],
    }
    outgoing = evidence | {
        "item_id": f'{case["id"]}/outgoing', "task": "draft bounded outgoing assertion",
        "agent": "correspondence" if specialists else "single",
        "subject_id": request["subject"], "evidence_role": request["role"],
        "jurisdiction": request["jurisdiction"],
        "status": "supported" if supported else "missing",
        "statement": source["value"] if supported else None,
        "sources": evidence["sources"] if supported else [],
        "depends_on": [evidence["item_id"]] if specialists and source else [],
        "missing": [] if supported else [request["role"]],
    }
    return {"actions": actions, "stop": "topic" if source else "exhausted",
            "evidence": evidence if specialists else None, "outgoing": outgoing}


def cost(actions):
    return {
        "reads": len(actions),
        "candidate_inspections": sum(row["inspections"] for row in actions),
        "source_bytes": sum(row["bytes"] for row in actions),
    }


def correct(trace, key):
    outgoing = trace["outgoing"]
    if outgoing["status"] != "supported":
        return False
    reference = outgoing["sources"][0]
    return (reference["source_id"] in key["permitted_sources"]
            and outgoing["statement"] == key["value"])


def learn(cases, keys):
    preferences = [None, *ROUTES]
    skills = {}
    ledger = []
    for role in sorted({case["request"]["role"] for case in cases}):
        counts = {}
        for route in preferences:
            hits = 0
            for case in cases:
                if case["request"]["role"] != role:
                    continue
                actions, source = read_case(case, route)
                trace = handoff(case, actions, source, specialists=True, verify=True)
                success = correct(trace, keys[case["id"]])
                hits += success
                ledger.append({"case": case["id"], "role": role, "preference": route,
                               "correct": success, **cost(actions)})
            counts[route] = hits
        best = max(counts.values())
        winners = [route for route in preferences if counts[route] == best]
        if best > counts[None] and len(winners) == 1:
            skills[role] = winners[0]
    return skills, ledger


def diagnose(cases, skills):
    for case in cases:
        flat, flat_source = read_case(case)
        learned, learned_source = read_case(case, skills.get(case["request"]["role"]))
        arms = {
            "single": handoff(case, flat, flat_source, specialists=False, verify=True),
            "fixed": handoff(case, flat, flat_source, specialists=True, verify=True),
            "learned": handoff(case, learned, learned_source, specialists=True, verify=True),
            "learned_without_role": handoff(
                case, learned, learned_source, specialists=True, verify=True, check_role=False,
            ),
            "learned_unverified": handoff(
                case, learned, learned_source, specialists=True, verify=False,
            ),
        }
        for arm, trace in arms.items():
            trace_id = f'{case["id"]}/{arm}'
            trace["outgoing"]["trace_id"] = trace_id
            if trace["evidence"] is not None:
                trace["evidence"]["trace_id"] = trace_id
        yield {"case": case["id"], "arms": arms}
