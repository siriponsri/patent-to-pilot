"""Development-only eligibility diagnostics; never changes a qrel or population."""
from collections import Counter
from collections.abc import Callable, Iterable

from patent_to_pilot.research.mtm_runtime import InputBoundaryError, calendar_date, identifier, validate_metadata


def audit_eligibility(metadata: dict, qrels: dict, corpus: Iterable[dict], *, keep_mask: Callable) -> dict:
    """Use the frozen runtime predicate on each known-target slice (main/X).

    Pair reasons overlap. A separate exclusive classification sums to all pairs.
    Missing/invalid date or CPC metadata is indeterminate, not a silently repaired
    candidate. No identifiers, texts or labels are emitted in the aggregate.
    """
    if not metadata or set(metadata) != set(qrels):
        raise InputBoundaryError("development population mismatch")
    wanted = set()
    for query_id, row in metadata.items():
        validate_metadata(row)
        if row["id"] != query_id or not qrels[query_id]:
            raise InputBoundaryError("invalid development population")
        wanted.update(qrels[query_id])
    candidates, seen = {}, set()
    for row in corpus:
        identifier(row.get("id"))
        if row["id"] in seen:
            raise InputBoundaryError("duplicate corpus family")
        seen.add(row["id"])
        if row["id"] in wanted:
            candidates[row["id"]] = {key: row.get(key) for key in ("id", "visible_from", "c3")}
    reasons = Counter({name: 0 for name in (
        "absent_from_corpus", "unknown_publication_date", "malformed_publication_date",
        "malformed_cpc3", "publication_after_cutoff", "own_family", "shared_cpc3")})
    exclusive = Counter(eligible=0, ineligible=0, indeterminate=0)
    zero_eligible, queries_indeterminate = 0, 0
    for query_id, query in metadata.items():
        eligible_count, uncertain = 0, False
        for target in qrels[query_id]:
            identifier(target)
            candidate = candidates.get(target)
            if candidate is None:
                reasons["absent_from_corpus"] += 1
                exclusive["ineligible"] += 1
                continue
            invalid = False
            publication = candidate["visible_from"]
            if publication is None:
                reasons["unknown_publication_date"] += 1
                invalid = True
            else:
                try:
                    calendar_date(publication)
                except InputBoundaryError:
                    reasons["malformed_publication_date"] += 1
                    invalid = True
            try:
                validate_metadata({"id": target, "family_id": target, "priority": query["priority"],
                                   "c3": candidate["c3"]})
            except InputBoundaryError:
                reasons["malformed_cpc3"] += 1
                invalid = True
            if invalid:
                exclusive["indeterminate"] += 1
                uncertain = True
                continue
            own = target == query["family_id"]
            shared = bool(set(query["c3"]) & set(candidate["c3"]))
            reasons["publication_after_cutoff"] += int(publication > query["priority"])
            reasons["own_family"] += int(own)
            reasons["shared_cpc3"] += int(shared)
            accepted = bool(keep_mask([publication], query["priority"], 0 if own else None,
                                      [True], [0] if shared else [], "X")[0])
            exclusive["eligible" if accepted else "ineligible"] += 1
            eligible_count += int(accepted)
        zero_eligible += int(eligible_count == 0)
        queries_indeterminate += int(uncertain)
    pairs = sum(len(v) for v in qrels.values())
    assert sum(exclusive.values()) == pairs
    return {"format": "ptp-mtm-dev-eligibility-v1", "split": "dev", "view": "main", "lane": "X",
            "status": "PASS" if exclusive["eligible"] == pairs else "REQUIRES_REVIEW",
            "queries": len(metadata), "pairs": pairs, "corpus_families": len(seen),
            "pair_classification": dict(exclusive), "overlapping_reasons": dict(reasons),
            "queries_with_zero_verified_eligible_targets": zero_eligible,
            "queries_with_indeterminate_targets": queries_indeterminate,
            "labels_changed": False, "queries_dropped": 0,
            "cited_vs_representative_cpc": "REPRESENTATIVE_CHECKED_CITED_METADATA_NOT_SUPPLIED"}
