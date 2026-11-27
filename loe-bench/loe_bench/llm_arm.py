"""T10 LLM one-shot arm: label-free prompt builder and strict-JSON parser (standard library only).

The prompt is built from (entity, t0, horizon_months) plus an allowlisted set of features that exist at t0.
Outcome or label fields, and the outputs of other models (p_model, verdict, action), are never admitted.
"""
import json

ACTIONS = ("PREDICT_ENTRY", "PREDICT_NO_ENTRY", "ABSTAIN_REFER_TO_EVALUATOR")
ALLOWED_FEATURES = ("rule_baseline",)
FORBIDDEN_FIELDS = frozenset({
    "label", "y", "outcome", "entry", "entered", "event", "event_date", "entry_date", "first_entry_date",
    "censored", "time_to_event", "p_model", "verdict", "action", "next_evidence"})

SYSTEM = ("You are a careful regulatory analyst forecasting first final FDA generic drug approvals. "
          "Answer with one JSON object only, no prose, no code fence.")

TEMPLATE = """Question: will the first final FDA ANDA approval for the reference product below occur within {h} months after the forecast date {t0}?

Reference product (active ingredient): {entity}
Forecast date t0: {t0}
Horizon: {h} months
{features}
Count only final FDA approval of an Abbreviated New Drug Application (ANDA). Exclude tentative approvals.
Use only knowledge you hold with confidence about records dated on or before t0. If the evidence is insufficient, abstain.

Return a JSON object with exactly these fields:
- "p_entry": probability of the stated approval event, a number between 0 and 1.
- "action": one of "PREDICT_ENTRY", "PREDICT_NO_ENTRY", or "ABSTAIN_REFER_TO_EVALUATOR".
- "missing_evidence": a JSON array of short strings, or [] if empty."""


def _unique_fields(pairs):
    fields = dict(pairs)
    if len(fields) != len(pairs):
        raise ValueError("duplicate JSON key")
    return fields


def build_prompt(row):
    """row: mapping with entity, t0, horizon_months and optional allowlisted features. Returns (system, user)."""
    bad = sorted(k for k in row if k.lower() in FORBIDDEN_FIELDS and row[k] not in (None, ""))
    # Other-model outputs are ignored (not an error); true outcome-like fields are an error.
    leak = [k for k in bad if k.lower() not in {"p_model", "verdict", "action", "next_evidence"}]
    if leak:
        raise ValueError("label-like fields present: %s" % leak)
    lines = ["%s: %s" % (k, row[k]) for k in ALLOWED_FEATURES if row.get(k) not in (None, "")]
    feat = ("Evidence features available at t0:\n" + "\n".join(lines) + "\n") if lines else ""
    return SYSTEM, TEMPLATE.format(entity=row["entity"], t0=row["t0"], h=row["horizon_months"], features=feat)


def parse_response(text):
    """Strict-JSON parse with fallback to ABSTAIN. Returns dict(p_entry, action, missing_evidence, valid, error)."""
    fb = {"p_entry": None, "action": "ABSTAIN_REFER_TO_EVALUATOR", "missing_evidence": [], "valid": False}
    if not isinstance(text, str):
        return dict(fb, error="not_text")
    try:
        obj = json.loads(text, object_pairs_hook=_unique_fields)
    except (ValueError, RecursionError):
        return dict(fb, error="invalid_json")
    if not isinstance(obj, dict):
        return dict(fb, error="invalid_json")
    if obj.keys() != {"p_entry", "action", "missing_evidence"}:
        return dict(fb, error="bad_fields")
    p, a, me = obj["p_entry"], obj["action"], obj["missing_evidence"]
    if isinstance(p, bool) or not isinstance(p, (int, float)) or not 0.0 <= p <= 1.0:
        return dict(fb, error="bad_p_entry")
    if a not in ACTIONS:
        return dict(fb, error="bad_action")
    if not isinstance(me, list) or not all(isinstance(x, str) for x in me):
        return dict(fb, error="bad_missing_evidence")
    return {"p_entry": float(p), "action": a, "missing_evidence": me, "valid": True, "error": None}


def run_rows(rows, generate):
    """generate(system, user) -> text. Returns one result per row (deterministic if generate is)."""
    out = []
    for r in rows:
        s, u = build_prompt(r)
        res = parse_response(generate(s, u))
        res.update(entity=r["entity"], t0=r["t0"], horizon_months=r["horizon_months"])
        out.append(res)
    return out
