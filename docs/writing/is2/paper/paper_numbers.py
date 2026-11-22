# -*- coding: utf-8 -*-
"""Every number quoted by the IS2 paper, read from the B53 result receipts (../results/*.json).

Both content_th.py and content_en.py import from here so the two editions cannot drift apart.
Rounding: proportions and nDCG 3 decimals, percentage points 1 decimal, p-values 3 decimals ("< 0.001" below that).
"""
from __future__ import annotations

import json
from pathlib import Path

RES = Path(__file__).resolve().parent.parent / "results"
S1 = json.loads((RES / "b53-stage1-results.json").read_text(encoding="utf-8"))
S2 = json.loads((RES / "b53-stage2-results.json").read_text(encoding="utf-8"))

MINUS = "−"
CORE = ["F0", "F1", "F2", "F3", "F4"]
SECONDARY = ["F0-OUT", "F6", "F7"]
NAME = {"F0": "F0 patembed-base", "F1": "F1 BM25", "F2": "F2 RRF(F1, F0)", "F3": "F3 Arctic-embed",
        "F4": "F4 RRF(F1, F3)", "F0-OUT": "F0-OUT", "F6": "F6 patembed-large", "F7": "F7 Qwen3-Embedding"}
N_OUT = S1["cohorts"]["OUT"]          # 905
N_IN = S1["cohorts"]["IN"]            # 1217
N_ALL = S1["cohorts"]["ALL"]          # 1247
C = S2["C"]                           # 153
assert C == S1["common_exposed_k100_core"]


def f3(x: float) -> str:
    return f"{x:.3f}"


def s3(x: float, d: int = 3) -> str:
    return f"{x:+.{d}f}".replace("-", MINUS)


def pts(x: float) -> str:
    """Proportion difference -> signed percentage points, 1 decimal."""
    return s3(100 * x, 1)


def pval(p: float) -> str:
    return "< 0.001" if p < 0.001 else f"{p:.3f}"


A = S1["arms"]
B1 = S1["b53_1_contrasts"]


def count(arm: str, k: int = 100) -> int:
    return round(A[arm][f"pi{k}"] * N_OUT)


# ---- Table 1: exposure at k = 100, change vs F0, secondary endpoints. REF / NT are replaced by each edition's wording.
REF, NOT_TESTED = "REF", "NT"
T1 = []
for a in CORE + SECONDARY:
    if a == "F0":
        d, gl, hp = REF, "", ""
    else:
        r = B1[a]
        lo, hi = r["ci95"]
        d = f"{s3(r['delta_pi100_vs_F0'])} [{s3(lo)}, {s3(hi)}]"
        gl = f"{r['gained']}/{r['lost']}"
        hp = pval(r["holm_p"]) if "holm_p" in r else NOT_TESTED
    T1.append([NAME[a], f3(A[a]["pi100"]), d, gl, hp, f3(A[a]["out_recall100"]), f3(A[a]["out_ndcg100"]),
               str(A[a]["median_r1_exposed100"])])


def localise(rows, ref, nt):
    return [[ref if c == REF else nt if c == NOT_TESTED else c for c in r] for r in rows]


# ---- Stage 2
P2 = S2["B53_3_primary_on_C"]
D2 = S2["descriptive"]
M = S2["mean_ndcg100"]
SYS = ["generic", "patent_aware", "claim_focused", "scrambled", "bge", "norerank"]
T3 = [[NAME[a], f3(S2["pi100"][a])] + [f3(M[f"{a}|{s}"]) for s in SYS] for a in CORE]

deltas = [v["delta_C"] for v in P2.values()]
raw_p = min(v["p"] for v in P2.values())
holm_min = min(v["holm_p"] for v in P2.values())
n_sig = sum(v["holm_p"] < 0.05 for v in P2.values())
assert n_sig == 0 and len(P2) == 10


def rng(key: str, d: int = 3):
    xs = [D2[f"{a}|{key}-generic"]["delta_all"] for a in CORE]
    return min(xs), max(xs)


ub = [v["ci95"][1] for v in P2.values()]
qwen = [M[f"{a}|{s}"] for a in CORE for s in ("generic", "patent_aware", "claim_focused", "scrambled")]
resp = [D2[f"{a}|{s}-generic"]["response_rate_exposed"] for a in CORE for s in ("patent_aware", "claim_focused", "scrambled")]

NUM = {
    "n_out": f"{N_OUT:,}".replace(",", ","), "n_in": f"{N_IN:,}", "n_all": f"{N_ALL:,}", "C": str(C),
    "pi_F0": f3(A["F0"]["pi100"]), "n_F0": str(count("F0")),
    "d_F1": pts(B1["F1"]["delta_pi100_vs_F0"]), "ci_F1": (pts(B1["F1"]["ci95"][0]), pts(B1["F1"]["ci95"][1])),
    "d_F2": pts(B1["F2"]["delta_pi100_vs_F0"]), "ci_F2": (pts(B1["F2"]["ci95"][0]), pts(B1["F2"]["ci95"][1])),
    "d_F3": pts(B1["F3"]["delta_pi100_vs_F0"]), "d_F4": pts(B1["F4"]["delta_pi100_vs_F0"]),
    "d_F0OUT": pts(B1["F0-OUT"]["delta_pi100_vs_F0"]),
    "ci_F0OUT": (pts(B1["F0-OUT"]["ci95"][0]), pts(B1["F0-OUT"]["ci95"][1])),
    "d_F6": s3(B1["F6"]["delta_pi100_vs_F0"]), "d_F7": s3(B1["F7"]["delta_pi100_vs_F0"]),
    "gl_F1": (B1["F1"]["gained"], B1["F1"]["lost"]),
    "dmin": s3(min(deltas)), "dmax": s3(max(deltas)), "raw_p": f"{raw_p:.3f}", "holm_min": f"{holm_min:.3f}",
    "scr": (s3(rng("scrambled")[0], 4), s3(rng("scrambled")[1], 4)),
    "bge": (s3(rng("bge")[1]), s3(rng("bge")[0])),
    "norr": (s3(-rng("norerank")[1]), s3(-rng("norerank")[0])),
    "ub": (s3(min(ub)), s3(max(ub))), "qwen": (f3(min(qwen)), f3(max(qwen))),
    "resp": (round(100 * min(resp)), round(100 * max(resp))),
    "pi200_F0": f3(A["F0"]["pi200"]), "pi1000_F0": f3(A["F0"]["pi1000"]), "pi1000_F2": f3(A["F2"]["pi1000"]),
    "gain200_F0": pts((count("F0", 200) - count("F0", 100)) / N_OUT),
    "none1000_F0": N_OUT - count("F0", 1000),
    "none1000_pct": f"{100 * (N_OUT - count('F0', 1000)) / N_OUT:.1f}",
    "none100_pct": f"{100 * (N_OUT - count('F0', 100)) / N_OUT:.1f}",
    "med_F0": A["F0"]["median_r1_exposed100"],
    "pa_F0": P2["F0|patent_aware-generic"],
}

if __name__ == "__main__":
    for k, v in NUM.items():
        print(k, v if k != "pa_F0" else (v["wins"], v["losses"]))
    for t in (T1, T3):
        for r in t:
            print(r)
