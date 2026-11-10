"""Prospective deterministic solo-review mechanics; no automatic semantic oracle.

All IDs/artifacts and the cumulative ledger remain private. Caller must supply
only curated dev population and freeze config/source manifests before outcomes.
"""
import hashlib

from patent_to_pilot.research.mtm_runtime import InputBoundaryError, identifier


def _population(benchmark, ids):
    if benchmark not in {"DAPFAM", "MTM"}:
        raise InputBoundaryError("unknown benchmark")
    values = list(ids)
    for key in values:
        identifier(key)
    if len(set(values)) != len(values) or not values:
        raise InputBoundaryError("empty or duplicate fidelity population")
    return values


def fixed_sample(benchmark, dev_ids):
    values = _population(benchmark, dev_ids)
    return sorted(values, key=lambda q: (hashlib.sha256(
        f"sacr-v0-fidelity-20261110|{benchmark}|{q}".encode("utf-8")).hexdigest(), q))[:100]


def required_cards(benchmark, config_digest, sample, escalations, unassessable=()):
    values = _population(benchmark, sample)
    if len(values) > 100 or len(config_digest) != 64 or any(c not in "0123456789abcdef" for c in config_digest):
        raise InputBoundaryError("invalid fixed sample/configuration")
    risks, unknown = set(escalations), set(unassessable)
    if not risks <= set(values) or not unknown <= set(values):
        raise InputBoundaryError("screen result outside fixed sample")
    risks |= unknown  # Missing/invalid/disagreeing automation cannot silently pass.
    if len(risks) > 20:
        raise InputBoundaryError("REVIEW_CAP_EXCEEDED")
    unflagged = set(values) - risks
    sentinels = sorted(unflagged, key=lambda q: (hashlib.sha256(
        f"sacr-solo-sentinel-20261110|{benchmark}|{q}".encode("utf-8")).hexdigest(), q))[:10]
    return [{"benchmark": benchmark, "configuration_digest": config_digest, "query_id": q, "category": category}
            for category, ids in (("escalation", sorted(risks)), ("sentinel", sentinels)) for q in ids]


def admit_cards(previously_issued, required):
    """Validate complete reservation against cumulative issued/unfinished cards.

    Caller must durably persist this complete reservation before showing cards.
    This function never deletes/refunds prior reservations or auto-adjudicates.
    """
    prior, new = list(previously_issued), list(required)
    keys = set()
    counts = {b: {"escalation": 0, "sentinel": 0} for b in ("DAPFAM", "MTM")}
    for card in prior + new:
        if set(card) != {"benchmark", "configuration_digest", "query_id", "category"}:
            raise InputBoundaryError("invalid card reservation")
        benchmark, category = card["benchmark"], card["category"]
        if benchmark not in counts or category not in counts[benchmark]:
            raise InputBoundaryError("invalid card category")
        identifier(card["query_id"])
        d = card["configuration_digest"]
        if not isinstance(d, str) or len(d) != 64 or any(c not in "0123456789abcdef" for c in d):
            raise InputBoundaryError("invalid configuration digest")
        key = (benchmark, d, card["query_id"])
        if key in keys:
            raise InputBoundaryError("duplicate card; adjudicate existing card without reissuing")
        keys.add(key)
        counts[benchmark][category] += 1
    if len(keys) > 60 or any(c["escalation"] > 20 or c["sentinel"] > 10 or sum(c.values()) > 30 for c in counts.values()):
        raise InputBoundaryError("HUMAN_BUDGET_EXHAUSTED")
    return {"issued_total": len(keys), "by_benchmark": counts, "reservation": new}


def review_gate(required, judgments, *, automatic_screen_complete, confirmed_automatic_critical=False):
    """Gate only after complete screening; no overall fidelity guarantee."""
    keys = {(c["benchmark"], c["configuration_digest"], c["query_id"]) for c in required}
    if len(keys) != len(required) or not keys:
        raise InputBoundaryError("nonempty unique required review set")
    if not set(judgments) <= keys or any(v not in {"faithful", "unsupported", "ambiguous", "unassessable"} for v in judgments.values()):
        raise InputBoundaryError("invalid human judgments")
    if confirmed_automatic_critical or "unsupported" in judgments.values():
        return "FAIL_STOP_CONFIGURATION_REVIEW_REQUIRED"
    if not automatic_screen_complete or set(judgments) != keys or any(v != "faithful" for v in judgments.values()):
        return "INCOMPLETE_NO_PASS"
    return "SOLO_SCREEN_AND_SENTINEL_GATE_PASS"


def admit_paper1_cards(previously_issued, required):
    """Owner amendment: DAPFAM SACR30 + shared S/G30; MTM unallocated.

    Each pool cumulatively allows20 escalation and10 sentinel cards across all
    configurations. A single S/G extraction configuration is shared, not30 each.
    """
    prior, new = list(previously_issued), list(required)
    pools = {'SACR': [], 'SG': []}
    for card in prior + new:
        if type(card) is not dict or card.get('review_pool') not in pools or card.get('benchmark') != 'DAPFAM':
            raise InputBoundaryError('unallocated review pool or benchmark')
        pools[card['review_pool']].append({k: v for k, v in card.items() if k != 'review_pool'})
    counts = {}
    for pool, cards in pools.items():
        status = admit_cards([], cards)
        counts[pool] = status['by_benchmark']['DAPFAM']
    return {'issued_total': len(prior) + len(new), 'by_pool': counts, 'reservation': new}
