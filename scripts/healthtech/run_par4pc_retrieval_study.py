"""PAR4PC lexical/dense/hybrid/cascade study (protocol ptp-wpi-par4pc-protocol-v1).

--phase dev   scores validation, applies the frozen selection rules, writes the freeze file.
--phase test  requires an unchanged freeze file, scores test once, writes results.
Rankers read only context/options; labels are read by the evaluator after ranking.
Per-row outputs stay in the private output directory; the public summary has aggregates only.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np  # noqa: E402
import pyarrow.parquet as parquet  # noqa: E402

from patent_to_pilot.evaluation.par4pc_study import (  # noqa: E402
    app_macro, bm25_margin, cascade, holm, paired_cluster_bootstrap, rank_by_scores, row_metrics, rrf,
)

PROTOCOL = ROOT / "docs/healthtech/research/PAR4PC_RETRIEVAL_PROTOCOL_20261104_EN.md"
_spec = importlib.util.spec_from_file_location("lexical", ROOT / "scripts/healthtech/run_panorama_lexical_baseline.py")
lexical = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lexical)


def sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bm25_scores(query: str, options: dict[str, str]) -> dict[str, float]:
    q = lexical.tokens(query)
    docs = {k: lexical.tokens(v) for k, v in options.items()}
    df = lexical.Counter()
    for doc in docs.values():
        df.update(set(doc))
    avg = sum(len(d) for d in docs.values()) / max(len(docs), 1)
    return {k: lexical.bm25(q, d, df, len(docs), avg) for k, d in docs.items()}


def load_vectors(directory: Path, kind: str, split: str, name: str) -> dict[str, np.ndarray]:
    prefix = directory / f"{kind}-{split}-{name}"
    ids = json.loads(Path(f"{prefix}.ids.json").read_text(encoding="utf-8"))
    matrix = np.load(f"{prefix}.npy")
    return dict(zip(ids, matrix))


def score_split(par4pc_dir: Path, vectors_dir: Path, split: str) -> tuple[dict, dict, dict]:
    """Return per-method rankings, BM25 margins and labels (labels kept separate)."""
    rows = parquet.read_table(par4pc_dir / f"{split}.parquet").to_pylist()
    vec = {(kind, name): load_vectors(vectors_dir, kind, split, name)
           for kind in ("patembed", "e5") for name in ("queries_full", "queries_claim", "options")}
    rankings, margins, labels, groups = {}, {"full": {}, "claim": {}}, {}, {}
    started = time.perf_counter()
    for row in rows:
        app, claim = str(row["application_number"]), row["claim_number"]
        key = f"{app}:{claim}"
        ctx = row["context"]
        options = {letter: str(o["patent_id"]) for letter, o in row["options"].items()}
        option_text = {letter: " ".join([str(o.get("title") or ""), str(o.get("abstract") or ""), *[str(x) for x in (o.get("claims") or [])]])
                       for letter, o in row["options"].items()}
        queries = {
            "full": " ".join([str(ctx.get("title") or ""), str(ctx.get("abstract") or ""), *[str(x) for x in (ctx.get("claims") or [])]]),
            "claim": " ".join([str(ctx["claims"][claim - 1]), str(ctx.get("title") or ""), str(ctx.get("abstract") or "")]),
        }
        r = {}
        for form, text in queries.items():
            s = bm25_scores(text, option_text)
            r[f"bm25_{form}"] = rank_by_scores(s)
            margins[form][key] = bm25_margin(s)
            qid = app if form == "full" else key
            for kind in ("patembed", "e5"):
                q = vec[(kind, f"queries_{form}")][qid]
                dense = {letter: float(np.dot(q, vec[(kind, "options")][pid])) for letter, pid in options.items()}
                r[f"{kind}_{form}"] = rank_by_scores(dense)
        rankings[key] = r
        groups[key] = app
        labels[key] = (set(row["gold_answers"]), set(row["silver_answers"]))
    cpu_seconds = time.perf_counter() - started
    return rankings, margins, {"labels": labels, "groups": groups, "rows": len(rows), "apps": len(set(groups.values())),
                               "scoring_cpu_seconds": cpu_seconds, "source_sha256": sha_file(par4pc_dir / f"{split}.parquet")}


def metrics_for(method_rankings: dict[str, list[str]], meta: dict) -> tuple[dict, dict]:
    per_row = {k: row_metrics(rank, *meta["labels"][k]) for k, rank in method_rankings.items()}
    summary = {}
    for metric in ("rr", "hit1", "recall3", "ndcg8"):
        values = {k: v[metric] for k, v in per_row.items()}
        summary[f"app_macro_{metric}"] = app_macro(values, meta["groups"])
        summary[f"row_micro_{metric}"] = sum(values.values()) / len(values)
    return summary, per_row


def build_methods(rankings: dict, margins: dict, selection: dict) -> tuple[dict, dict]:
    methods = {name: {k: r[name] for k, r in rankings.items()} for name in next(iter(rankings.values()))}
    bm, dense = selection["bm25"], selection["dense"]
    methods["hybrid"] = {k: rrf([r[bm], r[dense]]) for k, r in rankings.items()}
    escalated = {}
    if selection.get("tau") is not None:
        tau = float("inf") if selection["tau"] == "inf" else selection["tau"]
        form = bm.split("_", 1)[1]
        cas = {}
        for k, r in rankings.items():
            cas[k], escalated[k] = cascade(r[bm], methods["hybrid"][k], margins[form][k], tau)
        methods["cascade"] = cas
    return methods, escalated


def dev_phase(args) -> dict:
    rankings, margins, meta = score_split(args.par4pc_dir, args.vectors_dir, "validation")
    base = {name: metrics_for({k: r[name] for k, r in rankings.items()}, meta)[0] for name in next(iter(rankings.values()))}
    mrr = {name: s["app_macro_rr"] for name, s in base.items()}
    pick = lambda fam: max((f"{fam}_full", f"{fam}_claim"), key=lambda n: (mrr[n], n == f"{fam}_full"))
    selection = {"bm25": pick("bm25"), "patembed": pick("patembed"), "e5": pick("e5")}
    selection["dense"] = max((selection["patembed"], selection["e5"]), key=lambda n: mrr[n])
    methods, _ = build_methods(rankings, margins, selection)
    hybrid_mrr = metrics_for(methods["hybrid"], meta)[0]["app_macro_rr"]
    form = selection["bm25"].split("_", 1)[1]
    values = sorted(margins[form].values())
    grid = sorted({values[min(int(q * len(values)), len(values) - 1)] for q in [i / 20 for i in range(21)]})
    curve, tau = [], "inf"
    for t in grid:
        selection_t = dict(selection, tau=t)
        m, esc = build_methods(rankings, margins, selection_t)
        s = metrics_for(m["cascade"], meta)[0]["app_macro_rr"]
        curve.append({"tau": t, "app_macro_rr": s, "escalation_rate": sum(esc.values()) / len(esc)})
    qualifying = [c for c in curve if c["app_macro_rr"] >= hybrid_mrr - 0.01]
    if qualifying:
        tau = min(qualifying, key=lambda c: c["tau"])["tau"]
    selection["tau"] = tau
    freeze = {
        "format": "ptp-wpi-par4pc-freeze-v1",
        "protocol": str(PROTOCOL.relative_to(ROOT)).replace("\\", "/"),
        "protocol_sha256": sha_file(PROTOCOL),
        "study_module_sha256": sha_file(ROOT / "src/patent_to_pilot/evaluation/par4pc_study.py"),
        "runner_sha256": sha_file(Path(__file__)),
        "validation_source_sha256": meta["source_sha256"],
        "validation_rows": meta["rows"], "validation_apps": meta["apps"],
        "validation_app_macro_mrr": {**mrr, "hybrid": hybrid_mrr},
        "validation_cascade_curve": curve,
        "selection": selection,
        "test_scored_before_freeze": False,
        "frozen_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    return freeze


def test_phase(args, freeze: dict) -> dict:
    if sha_file(PROTOCOL) != freeze["protocol_sha256"] or sha_file(ROOT / "src/patent_to_pilot/evaluation/par4pc_study.py") != freeze["study_module_sha256"]:
        raise SystemExit("protocol or study module changed after freeze")
    rankings, margins, meta = score_split(args.par4pc_dir, args.vectors_dir, "test")
    methods, escalated = build_methods(rankings, margins, freeze["selection"])
    summaries, per_row = {}, {}
    for name, ranks in methods.items():
        summaries[name], per_row[name] = metrics_for(ranks, meta)
    rr = {name: {k: v["rr"] for k, v in rows.items()} for name, rows in per_row.items()}
    sel = freeze["selection"]
    contrasts = {
        "C1_dense_minus_bm25_full": paired_cluster_bootstrap(rr[sel["dense"]], rr["bm25_full"], meta["groups"]),
        "C2_hybrid_minus_bm25_full": paired_cluster_bootstrap(rr["hybrid"], rr["bm25_full"], meta["groups"]),
        "C3_hybrid_minus_dense": paired_cluster_bootstrap(rr["hybrid"], rr[sel["dense"]], meta["groups"]),
    }
    adjusted = holm({k: v["p_bootstrap"] for k, v in contrasts.items()})
    for k in contrasts:
        contrasts[k]["p_holm"] = adjusted[k]
    c4 = paired_cluster_bootstrap(rr["cascade"], rr["hybrid"], meta["groups"])
    c4["within_tolerance_minus_0_01"] = c4["ci95_low"] >= -0.01
    escalation_rate = sum(escalated.values()) / len(escalated)
    return {
        "format": "ptp-wpi-par4pc-test-results-v1",
        "freeze_sha256": sha_file(args.freeze), "test_source_sha256": meta["source_sha256"],
        "rows": meta["rows"], "apps": meta["apps"], "failed_rows": 0,
        "selection": sel, "methods": summaries, "contrasts_primary_mrr": contrasts,
        "C4_cascade_minus_hybrid": c4, "cascade_escalation_rate": escalation_rate,
        "dense_query_encodings_needed": {"always": meta["rows"], "cascade": sum(escalated.values())},
        "scoring_cpu_seconds": meta["scoring_cpu_seconds"],
    }, per_row


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("dev", "test"), required=True)
    parser.add_argument("--par4pc-dir", type=Path, required=True)
    parser.add_argument("--vectors-dir", type=Path, required=True)
    parser.add_argument("--freeze", type=Path, required=True)
    parser.add_argument("--output", type=Path, help="public aggregate output (test phase)")
    parser.add_argument("--private-dir", type=Path, help="per-row outputs (test phase)")
    args = parser.parse_args()
    if args.phase == "dev":
        if args.freeze.exists():
            parser.error("freeze file already exists; the dev phase runs once")
        freeze = dev_phase(args)
        args.freeze.write_text(json.dumps(freeze, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"selection": freeze["selection"], "validation_app_macro_mrr": freeze["validation_app_macro_mrr"]}, indent=1))
        return 0
    if args.output is None or args.private_dir is None or args.output.exists():
        parser.error("test phase needs fresh --output and --private-dir")
    freeze = json.loads(args.freeze.read_text(encoding="utf-8"))
    result, per_row = test_phase(args, freeze)
    args.private_dir.mkdir(parents=True, exist_ok=True)
    (args.private_dir / "test-per-row-metrics.json").write_text(json.dumps(per_row) + "\n", encoding="utf-8")
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("contrasts_primary_mrr", "C4_cascade_minus_hybrid", "cascade_escalation_rate")}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
