"""Evaluator only. No retrieval, policy calls, fitting or corpus-wide scoring."""

LIMITS = {"actions": 4, "returned": 8, "inspected": 24, "candidate_depth": 6,
          "model_tokens": 0, "elapsed_ms": 30000}
IDENTITY = ("unit_id", "source_id", "version", "sha256", "locator",
            "char_start", "char_end", "unit_sha256", "text")


def score_case(label, response, corpus):
    """Score one trace-validated response. The S3 adapter supplies metered usage."""
    if label["status"] == "UNADJUDICATED":
        return None
    if (not isinstance(response, dict) or response.get("case_id") != label["case_id"]
            or not isinstance(response.get("usage"), dict)):
        return 0
    usage = response["usage"]
    for field, ceiling in LIMITS.items():
        value = usage.get(field)
        if type(value) is not int or not 0 <= value <= ceiling:
            return 0
    citations = response.get("evidence")
    if (not isinstance(citations, list) or usage["actions"] < 1 or usage["candidate_depth"] < 4
            or not 4 <= usage["inspected"] <= usage["actions"] * usage["candidate_depth"]
            or usage["returned"] != len(citations) or len(citations) > usage["inspected"]):
        return 0
    support = set()
    seen = set()
    for citation in citations:
        if not isinstance(citation, dict) or type(citation.get("unit_id")) is not str:
            return 0
        uid = citation["unit_id"]
        unit = corpus.get(uid)
        if (unit is None or uid in seen
                or any(type(citation.get(k)) is not type(unit[k]) or citation[k] != unit[k]
                       for k in IDENTITY)):
            return 0
        if unit["family_id"] != label["family_id"] or citation.get("role") not in ("support", "alternative"):
            return 0
        seen.add(uid)
        if citation["role"] == "support":
            support.add(uid)
    if response.get("decision") != label["decision"]:
        return 0
    if label["status"] == "FINITE_UNANSWERABLE":
        return int(not support)
    # A justified extra citation must be individually licensed for the SAME assignment.
    return int(any(set(w["required"]) <= support <= set(w["permitted"])
                   for w in label["witness_assignments"]))


def check_splits(groups):
    """Each family, template, translation and descendant stays with its ancestor."""
    assigned = {}
    for group in groups:
        if not group["family_id"].startswith("s1-"):
            raise ValueError("unexpected evaluation family namespace")
        for identity in [group["family_id"], *group["lineages"]]:
            lane = assigned.setdefault(identity, group["lane"])
            if lane != group["lane"]:
                raise ValueError(f"lineage crosses lanes: {identity}")
