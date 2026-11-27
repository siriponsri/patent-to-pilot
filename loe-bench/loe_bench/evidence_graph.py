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
from .kleene import And, Leaf, Or, T3, analyze, evaluate
from .voi import voi

ROOT = And((Leaf("L_excl"), Or((Leaf("L_pat"), Leaf("L_challenge")))))


def build_assignment(snap: dict, t: date, horizon_months: int,
                     challenge_evidence: Optional[T3] = None) -> Dict[str, T3]:
    end = add_months(t, horizon_months)
    excl = snap.get("excl_exp", [])
    pat = snap.get("patent_exp", [])
    a = {
        "L_excl": T3.TRUE if all(d <= end for d in excl) else T3.FALSE,
        "L_pat": T3.TRUE if all(d <= end for d in pat) else T3.FALSE,
        "L_challenge": challenge_evidence if challenge_evidence is not None else T3.UNKNOWN,
    }
    return a


def verdict_label(a: Dict[str, T3]) -> str:
    return {T3.TRUE: "OPEN", T3.FALSE: "BLOCKED", T3.UNKNOWN: "CONTESTED"}[evaluate(ROOT, a)]


def decide(snap: dict, t: date, horizon_months: int, p_model: float,
           lo: float = 0.25, hi: float = 0.75, p_leaf: Optional[Dict[str, float]] = None) -> dict:
    """Selective decision: structure first, then calibrated probability, abstain in the grey zone.
    CONTESTED verdicts are always routed to 'ABSTAIN_REFER' unless the model is confident
    (p<=lo or p>=hi). BLOCKED is final unless exclusivity data are wrong (flag for audit)."""
    a = build_assignment(snap, t, horizon_months)
    res = analyze(ROOT, a)
    v = verdict_label(a)
    if v == "BLOCKED":
        action = "PREDICT_NO_ENTRY"
    elif p_model >= hi:
        action = "PREDICT_ENTRY"
    elif p_model <= lo:
        action = "PREDICT_NO_ENTRY"
    else:
        action = "ABSTAIN_REFER_TO_EVALUATOR"
    next_evidence = None
    if res["unknown_leaves"]:
        pl = p_leaf or {"L_challenge": 0.3, "L_excl": 0.5, "L_pat": 0.5}
        next_evidence = {"leaf": res["unknown_leaves"][0], "voi_bits": voi(ROOT, pl, a, 0.5)}
    return {"verdict": v, "action": action, "p_model": p_model, "next_evidence": next_evidence,
            "trace": {k: v_.name for k, v_ in a.items()}}
