"""Kleene tri-state evidence graph for 'can a generic/biosimilar enter within horizon?'.

Root = AND( L_excl , OR( L_pat , L_challenge ) )
  L_excl      statutory exclusivities all expire by t+h        (TRUE/FALSE from data; hard blocker)
  L_pat       all listed patents expire by t+h                 (TRUE/FALSE from data)
  L_challenge a lawful route exists despite unexpired patents  (UNKNOWN by default: needs litigation /
              settlement / licence evidence which public regulatory files do NOT contain)
Verdict TRUE  -> OPEN (clock alone suggests entry possible)
        FALSE -> BLOCKED (hard exclusivity)
        UNKNOWN -> CONTESTED (needs human evaluator or more evidence)
Legal assumptions are placeholders for a regulatory-law expert to verify. NOT legal advice.
"""
from datetime import date
from typing import Dict, Optional

from .common import add_months
from .kleene import And, Leaf, Or, T3, evaluate, rank_unknown_for_request
from .voi import voi

ROOT = And((Leaf("L_excl"), Or((Leaf("L_pat"), Leaf("L_challenge")))))
PREDICT_ENTRY = "PREDICT_ENTRY"
PREDICT_NO_ENTRY = "PREDICT_NO_ENTRY"
ABSTAIN = "ABSTAIN_REFER_TO_EVALUATOR"
DEFAULT_REVEAL_PROBABILITIES = {"L_challenge": 0.3, "L_excl": 0.5, "L_pat": 0.5}


def _clock_state(dates, end: date) -> T3:
    if not dates:
        return T3.UNKNOWN
    return T3.TRUE if all(d <= end for d in dates) else T3.FALSE


def build_assignment(snap: dict, t: date, horizon_months: int,
                     challenge_evidence: Optional[T3] = None) -> Dict[str, T3]:
    end = add_months(t, horizon_months)
    return {
        "L_excl": _clock_state(snap.get("excl_exp"), end),
        "L_pat": _clock_state(snap.get("patent_exp"), end),
        "L_challenge": challenge_evidence if challenge_evidence is not None else T3.UNKNOWN,
    }


def verdict_label(a: Dict[str, T3]) -> str:
    return {T3.TRUE: "OPEN", T3.FALSE: "BLOCKED", T3.UNKNOWN: "CONTESTED"}[evaluate(ROOT, a)]


def decide(snap: dict, t: date, horizon_months: int, p_model: float,
           lo: float = 0.25, hi: float = 0.75,
           reveal_probabilities: Optional[Dict[str, float]] = None, *,
           prior_truth_probability: float = 0.5, blocked_conflict_action: str = ABSTAIN) -> dict:
    """Use the configured conflict action for BLOCKED with p_model >= hi.

    The default refers conflicts to the evaluator. Other BLOCKED rows predict
    no entry. OPEN and CONTESTED use the probability thresholds.
    """
    if not (0 <= lo < hi <= 1 and 0 <= p_model <= 1):
        raise ValueError("require 0 <= lo < hi <= 1 and p_model in [0, 1]")
    if blocked_conflict_action not in (ABSTAIN, PREDICT_ENTRY, PREDICT_NO_ENTRY):
        raise ValueError("invalid BLOCKED conflict action")
    a = build_assignment(snap, t, horizon_months)
    v = verdict_label(a)
    conflict = v == "BLOCKED" and p_model >= hi
    if v == "BLOCKED":
        action = blocked_conflict_action if conflict else PREDICT_NO_ENTRY
    elif p_model >= hi:
        action = PREDICT_ENTRY
    elif p_model <= lo:
        action = PREDICT_NO_ENTRY
    else:
        action = ABSTAIN
    next_evidence = None
    ranked = rank_unknown_for_request(ROOT, a)
    if ranked:
        leaf, _ = ranked[0]
        rates = DEFAULT_REVEAL_PROBABILITIES if reveal_probabilities is None else reveal_probabilities
        bits = voi(ROOT, reveal_probabilities={leaf: rates.get(leaf, 0.0)}, assign=a,
                   prior_truth_probability=prior_truth_probability)
        next_evidence = {"leaf": leaf, "voi_bits": bits}
    return {"verdict": v, "action": action, "p_model": p_model, "conflict": conflict,
            "next_evidence": next_evidence,
            "trace": {k: v_.name for k, v_ in a.items()}}
