"""Dev-only ordered-ranking parity; no qrels, relevance metrics or test inputs."""
from pathlib import Path

from patent_to_pilot.research.mtm_runtime import InputBoundaryError, decode_json, exact_fields, identifier
from patent_to_pilot.research.vector_identity import sha256


def load_rankings(root: Path, *, manifest_sha256: str, query_ids: set[str], view: str, lane: str) -> dict:
    root = root.resolve(strict=True)
    manifest, payload = root / "manifest.json", root / "rankings.jsonl"
    for path in (manifest, payload):
        if path.is_symlink() or path.resolve().parent != root:
            raise InputBoundaryError("ranking bundle escapes directory")
    if sha256(manifest) != manifest_sha256:
        raise InputBoundaryError("ranking manifest differs from trusted digest")
    value = decode_json(manifest.read_bytes())
    exact_fields(value, {"format", "split", "view", "lane", "corpus_view", "sha256", "queries"})
    if (value["format"] != "ptp-mtm-dev-rankings-v1" or value["split"] != "dev" or
            view not in ("P", "T", "A") or lane not in ("U", "X") or
            value["view"] != view or value["lane"] != lane or value["corpus_view"] != "main"):
        raise InputBoundaryError("only the declared dev view and lane are permitted")
    if type(value["queries"]) is not int or value["queries"] != len(query_ids):
        raise InputBoundaryError("ranking manifest population mismatch")
    if sha256(payload) != value["sha256"]:
        raise InputBoundaryError("ranking payload hash mismatch")
    result = {}
    for line in payload.read_bytes().splitlines():
        row = decode_json(line)
        exact_fields(row, {"query_id", "families"})
        identifier(row["query_id"])
        if row["query_id"] not in query_ids or row["query_id"] in result:
            raise InputBoundaryError("unknown or duplicate ranking query")
        families = row["families"]
        if type(families) is not list or len(families) > 200:
            raise InputBoundaryError("invalid ranking depth")
        for family in families:
            identifier(family)
        if len(set(families)) != len(families):
            raise InputBoundaryError("duplicate ranking family")
        result[row["query_id"]] = families
    if set(result) != query_ids:
        raise InputBoundaryError("ranking rows omit available queries")
    return result


def compare_rankings(reference: dict, candidate: dict, *, cohort_ids: set[str], missing_ids: set[str]) -> dict:
    if not cohort_ids or not missing_ids <= cohort_ids:
        raise InputBoundaryError("invalid declared parity cohort")
    available = cohort_ids - missing_ids
    if not available or set(reference) != available or set(candidate) != available:
        raise InputBoundaryError("parity inputs differ from available-query cohort")
    identical, order_only, membership, changed_length, empty = 0, 0, 0, 0, 0
    prefix = {str(k): 0 for k in (20, 100, 200)}
    for qid in sorted(available):
        old, new = reference[qid], candidate[qid]
        for ranking in (old, new):
            if type(ranking) is not list or len(ranking) > 200:
                raise InputBoundaryError("invalid comparison ranking")
            for family in ranking:
                identifier(family)
            if len(set(ranking)) != len(ranking):
                raise InputBoundaryError("duplicate comparison family")
        if old == new:
            identical += 1
        elif set(old) == set(new):
            order_only += 1
        else:
            membership += 1
        changed_length += int(len(old) != len(new))
        empty += int(not old and not new)
        for cutoff in prefix:
            prefix[cutoff] += int(old[:int(cutoff)] == new[:int(cutoff)])
    return {"status": "EXACT_RANKING_PARITY_PASS" if identical == len(available) else "RANKING_PARITY_FAIL",
            "cohort_queries": len(cohort_ids), "available_queries": len(available),
            "predeclared_missing_queries": len(missing_ids), "identical_rankings": identical,
            "order_only_changes": order_only, "membership_changes": membership,
            "length_changes": changed_length, "both_empty_rankings": empty, "identical_prefix_counts": prefix,
            "relevance_scoring": "NOT_PERFORMED", "eligibility_validation": "SEPARATE_A03_GATE"}
