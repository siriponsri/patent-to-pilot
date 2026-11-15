"""Paper 2 pre-check: label-free per-query action router on DAPFAM dev (CPU, local).

Spec: ../ROUTER-PREDECLARATION.md (committed before any router number was computed).
  --sanity : reproduce Stage 1 F* (0.1618) and the one-action oracle (0.2557); no router numbers.
  --run    : the single pre-declared run (refuses if outputs exist or the pre-declaration is uncommitted).
Dev only; the sealed test folder is never read. Public aggregates -> ../router-dev-result.json;
per-query rows -> the private folder only.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import random
import subprocess
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
sys.path.insert(0, str(REPO / "src"))
from patent_to_pilot.evaluation.dapfam_acquisition import POOL_DEPTH, assign_folds, positive_relations  # noqa: E402
from patent_to_pilot.evaluation.par4pc_study import paired_cluster_bootstrap, rrf  # noqa: E402

P = REPO.parent / "_private_artifacts/healthtech"
S = P / "ptp-org-adaptive-20261105"
FILES = {
    "r1": S / "stage1/rankings-r1-bm25-tac-dev.jsonl",
    "r2": S / "dense-single/rankings-dense-single-top200.jsonl",
    "q1_dense": S / "stage1/dense/rankings-q1-dense-dev.jsonl",
    "q1_bm25": S / "stage1/rankings-q1-bm25-dev.jsonl",
    "q2": S / "stage1/dense/rankings-q2-dense-dev.jsonl",
    "q3": S / "stage1/dense/rankings-q3-dense-dev.jsonl",
    "split": S / "split.json",
}
STAGE1_RESULTS = REPO / "docs/healthtech/audits/ptp-org-adaptive-stage1-20261105/stage1-dev-results.json"
QRELS = REPO / "methodology/datasets/research-only-nc/qrels_all.parquet"
OUT_PRIVATE = P / "ptp-paper2-router-dev-20261116-v1"
PUBLIC = HERE.parent / "router-dev-result.json"
PREDECL = HERE.parent / "ROUTER-PREDECLARATION.md"

ACTIONS = ("R1", "R2", "R3", "Q1", "Q2", "Q3")
DEFAULT = "R2"
FOLDS, RESAMPLES, SEED = 5, 10000, 20261105
N_ROUTERS = 3
ALPHA_FWER = 0.05
RIDGE_ALPHA = 1.0
TAU_QUANTILES = [i / 20 for i in range(21)]
GO_DELTA, GO_IN_HARM = 0.010, -0.020


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict[str, list[str]]:
    rows = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            rows[row["query_id"]] = row["families"][:POOL_DEPTH]
    return rows


def recall(pool, relevant, k=POOL_DEPTH):
    return len(set(pool[:k]) & relevant) / len(relevant)


def setup():
    stage1 = json.loads(STAGE1_RESULTS.read_text(encoding="utf-8"))
    for name, path in FILES.items():
        assert sha(path) == stage1["inputs_sha256"][name], f"hash mismatch: {name}"
    import pyarrow.parquet as pq

    split_doc = json.loads(FILES["split"].read_text(encoding="utf-8"))
    split, sections, component = split_doc["assignment"], split_doc["first_ipc_section"], split_doc["component"]
    dev = sorted(q for q, s in split.items() if s == "dev")
    positives = positive_relations(r for r in pq.read_table(QRELS).to_pylist() if str(r["query_id"]) in set(dev))
    out_rel = {q: positives.get(q, {}).get("OUT", set()) for q in dev}
    in_rel = {q: positives.get(q, {}).get("IN", set()) for q in dev}
    r1, r2 = load(FILES["r1"]), load(FILES["r2"])
    q1d, q1b, q2, q3 = (load(FILES[n]) for n in ("q1_dense", "q1_bm25", "q2", "q3"))
    actions = {
        q: {"R1": r1.get(q, []), "R2": r2.get(q, []), "R3": rrf([r1.get(q, []), r2.get(q, [])])[:POOL_DEPTH],
            "Q1": rrf([lst for lst in (q1d.get(q), q1b.get(q)) if lst])[:POOL_DEPTH],
            "Q2": q2.get(q, []), "Q3": q3.get(q, [])}
        for q in dev
    }
    out_q = [q for q in dev if out_rel[q]]
    in_q = [q for q in dev if in_rel[q]]
    folds = assign_folds({q: sections.get(q, "?") for q in out_q}, k=FOLDS)
    return stage1, dev, out_q, in_q, out_rel, in_rel, actions, folds, component


def sanity(stage1, out_q, out_rel, actions):
    per = {q: {a: recall(actions[q][a], out_rel[q]) for a in ACTIONS} for q in out_q}
    f_star = sum(per[q][DEFAULT] for q in out_q) / len(out_q)
    oracle1 = sum(max(per[q].values()) for q in out_q) / len(out_q)
    ref_f = stage1["f_star"]["out_recall_at_200"]
    ref_o = stage1["amendment_1_selection_inflation"]["single_action_oracle"]
    assert abs(f_star - ref_f) < 1e-12 and abs(oracle1 - ref_o) < 1e-12, (f_star, oracle1)
    return {"n_out": len(out_q), "f_star_out_recall_at_200": f_star, "one_action_oracle_out_recall_at_200": oracle1,
            "stage1_reference": {"f_star": ref_f, "one_action_oracle": ref_o}, "match": True}


# ---------------- label-free features (ranking lists only) ----------------
def overlap(a, b, k):
    if not a or not b:
        return 0.0
    return len(set(a[:k]) & set(b[:k])) / k


def features(acts):
    """Per-query, per-action label-free features from the six Top-200 lists."""
    nonempty = [a for a in ACTIONS if acts[a]]
    cons = {a: (sum(overlap(acts[a], acts[b], POOL_DEPTH) for b in nonempty if b != a) / max(len(nonempty) - 1, 1)
                if acts[a] else 0.0) for a in ACTIONS}
    feats = {}
    for a in ACTIONS:
        if a == DEFAULT or not acts[a]:
            continue
        feats[a] = [overlap(acts[a], acts[DEFAULT], POOL_DEPTH), overlap(acts[a], acts[DEFAULT], 50), cons[a],
                    cons[DEFAULT]]
    return cons, feats


def router_a(cons, acts):
    """A: consensus. Pick the non-empty action with the highest mean Top-200 overlap with the others.
    Ties -> R2, then canonical order. Parameter-free."""
    order = [DEFAULT] + [a for a in ACTIONS if a != DEFAULT]
    return max((a for a in order if acts[a]), key=lambda a: (cons[a], -order.index(a)))


def switch_gap(cons, acts):
    others = [a for a in ACTIONS if a != DEFAULT and acts[a]]
    best = max(others, key=lambda a: (cons[a], -ACTIONS.index(a)))
    return cons[DEFAULT] - cons[best], best


def fit_router_b(train, gaps, per):
    """B: thresholded switch. Stay on R2 unless cons(R2) - max_other cons < tau; tau from the
    training-fold quantile grid (plus 'never switch'), maximizing training OUT R@200; ties -> fewer switches."""
    values = sorted(gaps[q][0] for q in train)
    grid = [float("-inf")] + sorted(set(float(np.quantile(values, p)) for p in TAU_QUANTILES))

    def score(tau):
        chosen = [gaps[q][1] if gaps[q][0] < tau else DEFAULT for q in train]
        switches = sum(c != DEFAULT for c in chosen)
        return sum(per[q][c] for q, c in zip(train, chosen)) / len(train), -switches
    return max(grid, key=score)


def fit_router_c(train, feats, per):
    """C: ridge meta-learner. For each non-default action, ridge (alpha=1, standardized features
    fitted on training folds) predicts recall(action) - recall(R2); pick argmax prediction if > 0 else R2."""
    models = {}
    for a in ACTIONS:
        if a == DEFAULT:
            continue
        rows = [q for q in train if a in feats[q]]
        if len(rows) < 10:
            continue
        x = np.array([feats[q][a] for q in rows], dtype=float)
        y = np.array([per[q][a] - per[q][DEFAULT] for q in rows], dtype=float)
        mu, sd = x.mean(0), x.std(0)
        sd[sd == 0] = 1.0
        z = (x - mu) / sd
        y0 = y.mean()
        w = np.linalg.solve(z.T @ z + RIDGE_ALPHA * np.eye(z.shape[1]), z.T @ (y - y0))
        models[a] = (mu, sd, w, y0)
    return models


def apply_c(models, f):
    best, best_pred = DEFAULT, 0.0
    for a in ACTIONS:
        if a in models and a in f:
            mu, sd, w, y0 = models[a]
            pred = float(((np.array(f[a]) - mu) / sd) @ w + y0)
            if pred > best_pred:
                best, best_pred = a, pred
    return best


def bootstrap_quantiles(a, b, groups, resamples, seed, alpha):
    """Same resampling as paired_cluster_bootstrap, at an arbitrary two-sided level."""
    per_group = {}
    for key in a:
        per_group.setdefault(groups[key], []).append(a[key] - b[key])
    means = [sum(v) / len(v) for _, v in sorted(per_group.items())]
    n = len(means)
    rng = random.Random(seed)
    draws = sorted(sum(means[rng.randrange(n)] for _ in range(n)) / n for _ in range(resamples))
    lo = draws[int((alpha / 2) * resamples)]
    hi = draws[int((1 - alpha / 2) * resamples) - 1]
    return lo, hi


def run(stage1, dev, out_q, in_q, out_rel, in_rel, actions, folds, component):
    per = {q: {a: recall(actions[q][a], out_rel[q]) for a in ACTIONS} for q in out_q}
    feat = {q: features(actions[q]) for q in dev}
    cons = {q: feat[q][0] for q in dev}
    fts = {q: feat[q][1] for q in dev}
    gaps = {q: switch_gap(cons[q], actions[q]) for q in dev}

    choice = {"A_consensus": {q: router_a(cons[q], actions[q]) for q in dev}, "B_threshold_switch": {}, "C_ridge_gain": {}}
    fitted = {"B_threshold_switch": {}, "C_ridge_gain": {}}
    for fold in range(FOLDS):
        train = [q for q in out_q if folds[q] != fold]
        held = [q for q in out_q if folds[q] == fold]
        tau = fit_router_b(train, gaps, per)
        models = fit_router_c(train, fts, per)
        fitted["B_threshold_switch"][str(fold)] = tau
        fitted["C_ridge_gain"][str(fold)] = sorted(models)
        for q in held:
            choice["B_threshold_switch"][q] = gaps[q][1] if gaps[q][0] < tau else DEFAULT
            choice["C_ridge_gain"][q] = apply_c(models, fts[q])
    # queries without OUT labels (only used for IN harm): router fitted on all 349 OUT-eligible queries
    tau_all = fit_router_b(out_q, gaps, per)
    models_all = fit_router_c(out_q, fts, per)
    fitted["B_threshold_switch"]["all_out_queries"] = tau_all
    for q in dev:
        if q not in folds:
            choice["B_threshold_switch"][q] = gaps[q][1] if gaps[q][0] < tau_all else DEFAULT
            choice["C_ridge_gain"][q] = apply_c(models_all, fts[q])

    f_out = {q: per[q][DEFAULT] for q in out_q}
    f_in = {q: recall(actions[q][DEFAULT], in_rel[q]) for q in in_q}
    oracle1 = sum(max(per[q].values()) for q in out_q) / len(out_q)
    f_mean = sum(f_out.values()) / len(out_q)
    alpha_adj = ALPHA_FWER / N_ROUTERS
    routers = {}
    for name, ch in choice.items():
        r_out = {q: per[q][ch[q]] for q in out_q}
        r_in = {q: recall(actions[q][ch[q]], in_rel[q]) for q in in_q}
        comp_out = paired_cluster_bootstrap(r_out, f_out, {q: component[q] for q in out_q}, resamples=RESAMPLES, seed=SEED)
        lo_adj, hi_adj = bootstrap_quantiles(r_out, f_out, {q: component[q] for q in out_q}, RESAMPLES, SEED, alpha_adj)
        q_out = paired_cluster_bootstrap(r_out, f_out, {q: q for q in out_q}, resamples=RESAMPLES, seed=SEED)
        comp_in = paired_cluster_bootstrap(r_in, f_in, {q: component[q] for q in in_q}, resamples=RESAMPLES, seed=SEED)
        mean_out = sum(r_out.values()) / len(out_q)
        routers[name] = {
            "out_recall_at_200": mean_out,
            "out_minus_f_star_component_bootstrap": comp_out,
            "out_minus_f_star_component_ci_bonferroni": {"level": 1 - alpha_adj, "low": lo_adj, "high": hi_adj},
            "out_minus_f_star_query_bootstrap_descriptive": q_out,
            "in_recall_at_200": sum(r_in.values()) / len(in_q),
            "in_minus_f_star_component_bootstrap": comp_in,
            "share_of_one_action_oracle_headroom": (mean_out - f_mean) / (oracle1 - f_mean),
            "actions_chosen_out_queries": dict(Counter(ch[q] for q in out_q)),
            "actions_chosen_all_dev": dict(Counter(ch[q] for q in dev)),
            "switch_rate_out_queries": sum(ch[q] != DEFAULT for q in out_q) / len(out_q),
            "wins_losses_ties_vs_f_star": [sum(r_out[q] > f_out[q] for q in out_q), sum(r_out[q] < f_out[q] for q in out_q),
                                           sum(r_out[q] == f_out[q] for q in out_q)],
        }
    best = max(routers, key=lambda n: (routers[n]["out_recall_at_200"], n))
    b = routers[best]
    delta = b["out_minus_f_star_component_bootstrap"]["delta"]
    in_harm = b["in_minus_f_star_component_bootstrap"]["delta"]
    go = delta >= GO_DELTA and b["out_minus_f_star_component_ci_bonferroni"]["low"] > 0 and in_harm >= GO_IN_HARM
    verdict = {
        "best_router": best, "out_delta": delta, "ci_low_bonferroni": b["out_minus_f_star_component_ci_bonferroni"]["low"],
        "in_harm": in_harm, "rule": f"GO iff delta >= {GO_DELTA} and Bonferroni ({1 - alpha_adj:.4f}) component CI low > 0 and IN delta >= {GO_IN_HARM}",
        "verdict": "GO" if go else "NO_GO",
    }
    n_components = {"out": len({component[q] for q in out_q}), "in": len({component[q] for q in in_q})}
    largest = Counter(component[q] for q in out_q).most_common(1)[0][1]
    return per, choice, routers, verdict, fitted, {"f_star": f_mean, "one_action_oracle": oracle1,
                                                    "f_star_in_recall_at_200": sum(f_in.values()) / len(in_q),
                                                    "components": n_components, "largest_component_out_queries": largest}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sanity", action="store_true")
    ap.add_argument("--run", action="store_true")
    args = ap.parse_args()
    stage1, dev, out_q, in_q, out_rel, in_rel, actions, folds, component = setup()
    check = sanity(stage1, out_q, out_rel, actions)
    if args.sanity:
        print(json.dumps(check, indent=1))
        return 0
    assert args.run
    assert not PUBLIC.exists() and not OUT_PRIVATE.exists(), "already run once"
    rel = PREDECL.relative_to(REPO).as_posix()
    status = subprocess.run(["git", "status", "--porcelain", "--", rel], cwd=REPO, capture_output=True, text=True).stdout
    commit = subprocess.run(["git", "log", "-1", "--format=%H", "--", rel], cwd=REPO, capture_output=True, text=True).stdout.strip()
    assert commit and not status.strip(), "pre-declaration must be committed and unchanged"
    per, choice, routers, verdict, fitted, base = run(stage1, dev, out_q, in_q, out_rel, in_rel, actions, folds, component)
    result = {
        "format": "ptp-paper2-router-dev-v1", "split": "dev", "test_split_read": False, "model_calls": 0,
        "predeclaration": {"path": rel, "commit": commit, "sha256": sha(PREDECL)},
        "script_sha256": sha(Path(__file__)), "inputs_sha256": {n: sha(p) for n, p in FILES.items()},
        "queries": {"dev": len(dev), "out_eligible": len(out_q), "in_eligible": len(in_q)},
        "sanity": check, "baseline": base, "routers": routers, "verdict": verdict,
        "fitted": {"B_tau_per_fold": fitted["B_threshold_switch"], "C_actions_modelled_per_fold": fitted["C_ridge_gain"]},
        "folds": "Stage 1 Amendment 1: assign_folds(first-IPC section of OUT-eligible dev queries, k=5, seed 20261105)",
        "bootstrap": {"unit": "component (split.json)", "resamples": RESAMPLES, "seed": SEED,
                      "multiplicity": f"Bonferroni over {N_ROUTERS} routers, two-sided level {1 - ALPHA_FWER / N_ROUTERS:.4f}"},
    }
    OUT_PRIVATE.mkdir(parents=True)
    (OUT_PRIVATE / "per-query.json").write_text(json.dumps(
        {"out_recall_at_200": per, "choice": choice}, sort_keys=True), encoding="utf-8")
    PUBLIC.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"baseline": base, "verdict": verdict,
                      "routers": {n: {k: r[k] for k in ("out_recall_at_200", "in_recall_at_200",
                                                         "share_of_one_action_oracle_headroom", "switch_rate_out_queries")}
                                  for n, r in routers.items()}}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
