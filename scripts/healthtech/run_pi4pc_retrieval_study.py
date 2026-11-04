"""PI4PC replication (protocol ptp-wpi-pi4pc-protocol-v1; inherits ptp-wpi-par4pc-protocol-v1).

--phase inputs  write label-free JSONL for remote encoding
--phase dev     score validation, apply the inherited selection rules, write the freeze file
--phase test    require an unchanged freeze, score test once, write aggregates (per-row stays private)
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
    bm25_margin, holm, paired_cluster_bootstrap, rank_by_scores,
)

PROTOCOL = ROOT / "docs/healthtech/research/PI4PC_REPLICATION_PROTOCOL_20261104_EN.md"
PARENT = ROOT / "docs/healthtech/research/PAR4PC_RETRIEVAL_PROTOCOL_20261104_EN.md"
MODULE = ROOT / "src/patent_to_pilot/evaluation/par4pc_study.py"


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


lexical = _load("lexical", "scripts/healthtech/run_panorama_lexical_baseline.py")
par4pc = _load("par4pc_runner", "scripts/healthtech/run_par4pc_retrieval_study.py")
sha_file = par4pc.sha_file


def rows_for(par_dir: Path, split: str) -> list[dict]:
    return parquet.read_table(par_dir / f"{split}.parquet").to_pylist()


def texts(row: dict) -> tuple[dict, dict, str]:
    ctx = json.loads(row["context"])
    claims = [str(x) for x in (ctx.get("claims") or [])]
    queries = {
        "full": " ".join([str(ctx.get("title") or ""), str(ctx.get("abstract") or ""), *claims]),
        "claim": " ".join([claims[row["claim_number"] - 1], str(ctx.get("title") or ""), str(ctx.get("abstract") or "")]),
    }
    options = {str(k): str(v) for k, v in json.loads(row["options"]).items()}
    return queries, options, str(row["context"])


def write_inputs(par_dir: Path, out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    receipt = {"labels_included": False}
    for split in ("validation", "test"):
        files = {name: {} for name in ("queries_full", "queries_claim", "options")}
        for index, row in enumerate(rows_for(par_dir, split)):
            claim_key = f"{row['application_number']}:{row['claim_number']}"
            key = f"{claim_key}:r{index}"  # one claim can pair with several prior-art documents
            queries, options, _ = texts(row)
            files["queries_full"].setdefault(str(row["application_number"]), queries["full"])
            files["queries_claim"].setdefault(claim_key, queries["claim"])
            for pid, text in options.items():
                files["options"][f"{key}:{pid}"] = text
        receipt[split] = {}
        for name, items in files.items():
            path = out / f"pi4pc-{split}-{name}.jsonl"
            with path.open("x", encoding="utf-8") as handle:
                for k in sorted(items):
                    handle.write(json.dumps({"id": k, "text": items[k], "text_sha256": hashlib.sha256(items[k].encode()).hexdigest()}, ensure_ascii=False) + "\n")
            receipt[split][name] = {"rows": len(items), "file_sha256": sha_file(path)}
    (out / "inputs-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt


def score_split(par_dir: Path, vec_dir: Path, split: str):
    vec = {(kind, name): _vectors(vec_dir, kind, split, name)
           for kind in ("patembed", "e5") for name in ("queries_full", "queries_claim", "options")}
    rankings, margins, labels, groups = {}, {"full": {}, "claim": {}}, {}, {}
    started = time.perf_counter()
    for index, row in enumerate(rows_for(par_dir, split)):
        app = str(row["application_number"])
        claim_key = f"{app}:{row['claim_number']}"
        key = f"{claim_key}:r{index}"
        queries, options, raw_context = texts(row)
        r = {}
        # bm25_full reproduces the existing baseline query (raw context JSON string).
        for form, text in (("full", raw_context), ("claim", queries["claim"])):
            s = par4pc.bm25_scores(text, options)
            r[f"bm25_{form}"] = rank_by_scores(s)
            margins[form][key] = bm25_margin(s)
        for form in ("full", "claim"):
            qid = app if form == "full" else claim_key
            for kind in ("patembed", "e5"):
                q = vec[(kind, f"queries_{form}")][qid]
                dense = {pid: float(np.dot(q, vec[(kind, "options")][f"{key}:{pid}"])) for pid in options}
                r[f"{kind}_{form}"] = rank_by_scores(dense)
        rankings[key], groups[key] = r, app
        labels[key] = ({str(x) for x in row["gold_answers"]}, {str(x) for x in (row["silver_answers"] or [])})
    meta = {"labels": labels, "groups": groups, "rows": len(rankings), "apps": len(set(groups.values())),
            "scoring_cpu_seconds": time.perf_counter() - started, "source_sha256": sha_file(par_dir / f"{split}.parquet")}
    return rankings, margins, meta


def _vectors(vec_dir: Path, kind: str, split: str, name: str) -> dict:
    prefix = vec_dir / f"{kind}-pi4pc-{split}-{name}"
    ids = json.loads(Path(f"{prefix}.ids.json").read_text(encoding="utf-8"))
    return dict(zip(ids, np.load(f"{prefix}.npy")))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("inputs", "dev", "test"), required=True)
    parser.add_argument("--pi4pc-dir", type=Path, required=True)
    parser.add_argument("--vectors-dir", type=Path)
    parser.add_argument("--inputs-out", type=Path)
    parser.add_argument("--freeze", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--private-dir", type=Path)
    args = parser.parse_args()
    if args.phase == "inputs":
        print(json.dumps(write_inputs(args.pi4pc_dir, args.inputs_out)))
        return 0
    if args.phase == "dev":
        if args.freeze.exists():
            parser.error("freeze exists; dev runs once")
        rankings, margins, meta = score_split(args.pi4pc_dir, args.vectors_dir, "validation")
        # Same selection logic as the parent protocol, applied to these validation scores.
        base = {n: par4pc.metrics_for({k: r[n] for k, r in rankings.items()}, meta)[0] for n in next(iter(rankings.values()))}
        mrr = {n: s["app_macro_rr"] for n, s in base.items()}
        pick = lambda fam: max((f"{fam}_full", f"{fam}_claim"), key=lambda n: (mrr[n], n == f"{fam}_full"))
        sel = {"bm25": pick("bm25"), "patembed": pick("patembed"), "e5": pick("e5")}
        sel["dense"] = max((sel["patembed"], sel["e5"]), key=lambda n: mrr[n])
        methods, _ = par4pc.build_methods(rankings, margins, sel)
        hybrid_mrr = par4pc.metrics_for(methods["hybrid"], meta)[0]["app_macro_rr"]
        form = sel["bm25"].split("_", 1)[1]
        values = sorted(margins[form].values())
        grid = sorted({values[min(int(q * len(values)), len(values) - 1)] for q in [i / 20 for i in range(21)]})
        curve = []
        for t in grid:
            m, esc = par4pc.build_methods(rankings, margins, dict(sel, tau=t))
            curve.append({"tau": t, "app_macro_rr": par4pc.metrics_for(m["cascade"], meta)[0]["app_macro_rr"],
                          "escalation_rate": sum(esc.values()) / len(esc)})
        ok = [c for c in curve if c["app_macro_rr"] >= hybrid_mrr - 0.01]
        sel["tau"] = min(ok, key=lambda c: c["tau"])["tau"] if ok else "inf"
        freeze = {"format": "ptp-wpi-pi4pc-freeze-v1", "protocol_sha256": sha_file(PROTOCOL), "parent_protocol_sha256": sha_file(PARENT),
                  "study_module_sha256": sha_file(MODULE), "runner_sha256": sha_file(Path(__file__)),
                  "validation_source_sha256": meta["source_sha256"], "validation_rows": meta["rows"], "validation_apps": meta["apps"],
                  "validation_app_macro_mrr": {**mrr, "hybrid": hybrid_mrr}, "validation_cascade_curve": curve, "selection": sel,
                  "test_scored_before_freeze": False, "frozen_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        args.freeze.write_text(json.dumps(freeze, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"selection": sel, "validation_app_macro_mrr": freeze["validation_app_macro_mrr"]}, indent=1))
        return 0
    freeze = json.loads(args.freeze.read_text(encoding="utf-8"))
    if (sha_file(PROTOCOL), sha_file(MODULE)) != (freeze["protocol_sha256"], freeze["study_module_sha256"]) or args.output.exists():
        raise SystemExit("protocol/module changed after freeze, or output exists")
    rankings, margins, meta = score_split(args.pi4pc_dir, args.vectors_dir, "test")
    sel = freeze["selection"]
    methods, escalated = par4pc.build_methods(rankings, margins, sel)
    summaries, per_row = {}, {}
    for name, ranks in methods.items():
        summaries[name], per_row[name] = par4pc.metrics_for(ranks, meta)
    rr = {n: {k: v["rr"] for k, v in rows.items()} for n, rows in per_row.items()}
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
    result = {"format": "ptp-wpi-pi4pc-test-results-v1", "freeze_sha256": sha_file(args.freeze), "test_source_sha256": meta["source_sha256"],
              "rows": meta["rows"], "apps": meta["apps"], "failed_rows": 0, "selection": sel, "methods": summaries,
              "contrasts_primary_mrr": contrasts, "C4_cascade_minus_hybrid": c4,
              "cascade_escalation_rate": sum(escalated.values()) / len(escalated),
              "scoring_cpu_seconds": meta["scoring_cpu_seconds"]}
    args.private_dir.mkdir(parents=True, exist_ok=True)
    (args.private_dir / "pi4pc-test-per-row-metrics.json").write_text(json.dumps(per_row) + "\n", encoding="utf-8")
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("contrasts_primary_mrr", "C4_cascade_minus_hybrid", "cascade_escalation_rate")}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
