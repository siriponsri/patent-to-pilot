"""CPU-only roster, trainer supervision and paired scoring rules for C9.

The dated evidence projection and C2 renderer are upstream. This module reads
no files and does not load a model, fetch outcomes or build a model prompt.
"""
import hashlib
import json
import math
from datetime import date
from itertools import cycle, islice

import numpy as np

from .common import add_months
from .llm_arm import parse_response
from .metrics import brier, paired_cluster_bootstrap_ci
from .review_metrics import ReviewQueue


S0 = date(2026, 11, 27)
PROTECTED_START = date(2017, 1, 1)
HORIZON_MONTHS = 24
TRAIN_CUTOFFS = frozenset(date(year, 1, 1) for year in range(1995, 2015))
PROMPTS_PER_BATCH = 8
PROMPT_BATCHES = 32
TRAIN_SLOTS = PROMPTS_PER_BATCH * PROMPT_BATCHES
SEED = 20261127
MALFORMED_REWARD = -1.25
MALFORMED_PROBABILITY = 0.5
MALFORMED_RANK = -1.0
BOOTSTRAP_DRAWS = 2000


def _binary_label(label):
    if type(label) is not int or label not in (0, 1):
        raise ValueError("C9 requires a resolved binary label")
    return label


def _training_end(cutoff):
    end = add_months(cutoff, HORIZON_MONTHS)
    if cutoff not in TRAIN_CUTOFFS or end >= PROTECTED_START:
        raise ValueError("C9 training window is outside the declared development calendar")
    return end


def resolve_training_label(cutoff, first_final_anda, covered_through):
    """Trainer-only outcome rule for an otherwise eligible drug-cutoff row."""
    end = _training_end(cutoff)
    if covered_through is None or end > min(S0, covered_through):
        return None
    if first_final_anda is None or first_final_anda > end:
        return 0
    if first_final_anda <= cutoff:
        raise ValueError("prior final ANDA makes the row ineligible")
    return 1


def training_order(eligible_resolved_keys):
    """Order an outcome-blind sequence of (drug key, cutoff) pairs for both arms."""
    keys = list(eligible_resolved_keys)
    if len(set(keys)) != len(keys) or len(keys) < PROMPTS_PER_BATCH:
        raise ValueError("C9 needs at least one full batch of unique training rows")

    def order(key):
        drug, cutoff = key
        _training_end(cutoff)
        row_id = json.dumps([SEED, drug, cutoff.isoformat()], ensure_ascii=False,
                            separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(row_id).digest(), cutoff, drug

    return list(islice(cycle(sorted(keys, key=order)), TRAIN_SLOTS))


def sft_target(label):
    """Supervisor-only assistant target. The C2 prompt stays separate."""
    y = _binary_label(label)
    return json.dumps({"p_entry": float(y),
                       "action": "PREDICT_ENTRY" if y else "PREDICT_NO_ENTRY",
                       "missing_evidence": []}, separators=(",", ":"))


def grpo_reward(completion, label):
    y = _binary_label(label)
    answer = parse_response(completion)
    if not answer["valid"]:
        return MALFORMED_REWARD
    return -((answer["p_entry"] - y) ** 2)


def _prediction(completion):
    answer = parse_response(completion)
    if not answer["valid"]:
        return MALFORMED_PROBABILITY, MALFORMED_RANK
    return answer["p_entry"], answer["p_entry"]


def _brier(predictions, labels):
    return brier([probability for probability, _ in predictions], labels)


def _recall20(predictions, labels):
    events = sum(labels)
    if not events:
        return math.nan
    ranking = [rank for _, rank in predictions]
    fractions, _ = ReviewQueue(ranking, np.zeros(len(ranking))).allocation(np.ones(len(ranking)))
    return float(fractions @ labels / events)


def score_pair(roster, grpo, sft, labels, *, covered_through):
    """Evaluator-only score after verified Track A coverage, keyed by frozen drug ID."""
    if covered_through is None or covered_through < add_months(S0, HORIZON_MONTHS):
        raise ValueError("Track A 24-month follow-up is incomplete")
    drugs = sorted(roster)
    if not drugs or any(set(drugs) != set(panel) for panel in (grpo, sft, labels)):
        raise ValueError("C9 requires one completion and resolved label per frozen drug in both arms")
    if len(set(drugs)) != len(drugs):
        raise ValueError("C9 requires a unique frozen drug roster")
    if any(not isinstance(arm[drug], str) for arm in (grpo, sft) for drug in drugs):
        raise ValueError("C9 requires captured model text for every completion")

    outcomes = [_binary_label(labels[drug]) for drug in drugs]
    left, right = [[_prediction(arm[drug]) for drug in drugs] for arm in (grpo, sft)]
    report = {"drugs": len(drugs), "events": sum(outcomes), "slots": len(drugs) // 5,
              "malformed": {"grpo": sum(rank == MALFORMED_RANK for _, rank in left),
                            "sft": sum(rank == MALFORMED_RANK for _, rank in right)}}
    for name, metric in (("brier", _brier), ("recall20", _recall20)):
        a, b = metric(left, outcomes), metric(right, outcomes)
        lo, hi, invalid = paired_cluster_bootstrap_ci(
            metric, left, right, outcomes, drugs, n_boot=BOOTSTRAP_DRAWS, seed=SEED)
        report[name] = {"grpo": a if math.isfinite(a) else None,
                        "sft": b if math.isfinite(b) else None,
                        "difference": a - b if math.isfinite(a - b) else None,
                        "ci95": [lo, hi] if math.isfinite(lo) and math.isfinite(hi) else None,
                        "undefined_draws": invalid}
    return report
