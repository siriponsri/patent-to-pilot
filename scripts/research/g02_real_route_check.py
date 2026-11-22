"""G02 real-model route check: the Workbench's openai_compatible embedding adapter against a real model.

Prerequisite: an OpenAI-compatible embedding endpoint reachable on loopback (for the G02 receipt: Qwen3-Embedding-0.6B
served on dr-train CPU by scripts/research/st_openai_embed_server.py, forwarded with ``ssh -L 18000:127.0.0.1:18000``).
Runs in a fresh temporary store under the loopback-only socket guard, then writes a JSON receipt.

    .venv\\Scripts\\python.exe scripts\\research\\g02_real_route_check.py --endpoint http://127.0.0.1:18000/v1 --out RECEIPT.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from patent_to_pilot.workbench import core as C  # noqa: E402
from patent_to_pilot.workbench.guard import loopback_only  # noqa: E402


def cells(core, pid):
    return {f"{c['candidate_id']}/{c['requirement_id']}": {"outcome": c["outcome"], "citation": c["citation"] and
            f"{c['citation']['source_id']}@{c['citation']['version_id']}#{c['citation']['passage_id']}"}
            for c in core.comparison(pid)["cells"]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--endpoint", default="http://127.0.0.1:18000/v1")
    ap.add_argument("--model", default="Qwen/Qwen3-Embedding-0.6B")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    rec: dict = {"program_id": "PTP-2026-11-21", "goal_id": "G02", "check": "real_embedding_route",
                 "endpoint": args.endpoint, "model": args.model, "started": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    attempts: list = []
    with tempfile.TemporaryDirectory(prefix="ptp-g02-real-") as tmp, loopback_only(attempts):
        core = C.EvidenceCore(Path(tmp) / "store")
        core.registry.save({"profile_id": "qwen3-embed", "role": "embedding", "adapter": "openai_compatible",
                            "model_id": args.model, "endpoint": args.endpoint, "max_batch": 8, "timeout_s": 120,
                            "query_prefix": "Instruct: Given a requirement, retrieve passages that state it\nQuery: "})
        t = time.monotonic()
        d = core.registry.check("qwen3-embed")
        rec["connection_check"] = {"status": d["status"], "items": d["last_check"]["items"],
                                   "facts": d["last_check"]["facts"], "seconds": round(time.monotonic() - t, 2)}
        if d["status"] != "ready":
            rec["result"] = "FAIL: profile not ready"
            Path(args.out).write_text(json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")
            return 1
        pid = core.bootstrap_sample()["project_id"]
        core.run_comparison(pid)
        rec["lexical_cells"] = cells(core, pid)
        t = time.monotonic()
        b = core.build_index(pid, "qwen3-embed")
        rec["build_index"] = {**b["generation"], "seconds": round(time.monotonic() - t, 2)}
        m = core.set_retrieval_mode(pid, "hybrid")
        rec["switch_to_hybrid"] = {k: m["result"].get(k) for k in ("reacquired", "revalidated_by_search", "retrieval")}
        run = core.run_comparison(pid)
        searches = [a for a in run["actions"] if a["action_type"] == "search_current_sources"]
        rec["hybrid_run"] = {"status": run["status"], "counters": run["counters"],
                             "setup": run["actions"][0]["detail"],
                             "hits": {f"{a['candidate_id']}/{a['requirement_id']}": a["detail"]["hits"] for a in searches}}
        rec["hybrid_cells"] = cells(core, pid)
        t = time.monotonic()
        ch = core.apply_change(pid, "CHANGE-S2-V2")
        rec["source_revision_under_hybrid"] = {"seconds": round(time.monotonic() - t, 2),
                                               **{k: ch["result"].get(k) for k in ("reacquired", "revalidated_by_search",
                                                                                   "outside_changed_scope", "retrieval")}}
        st = core.retrieval_status(pid)
        rec["generations"] = [{k: g[k] for k in ("generation_id", "status", "n_vectors", "dimension", "reused_vectors",
                                                 "embedded_vectors", "embedding_space_id")} for g in st["generations"]]
        rec["after_revision_cells"] = cells(core, pid)
        # Thai query against the Thai passage: dense channel only, to show the multilingual route works
        client = core.registry.client("qwen3-embed")
        qv = client.embed(["โมดูลเปลี่ยนแยกได้อย่างอิสระหรือไม่"], "query")[0]
        rec["thai_query_dense_top"] = core.generations.search(st["active_generation_id"], qv, "CONCEPT-A", 3)
        rec["ledger_requests"] = core.registry.usage_count("qwen3-embed")
        rec["usage_sample"] = core.registry.usage("qwen3-embed", limit=3)
    rec["remote_attempts_blocked"] = attempts
    rec["result"] = "PASS" if not attempts and rec["hybrid_run"]["counters"].get("retrieval_effective") == "hybrid" else "FAIL"
    Path(args.out).write_text(json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")
    print(rec["result"], json.dumps({k: rec[k] for k in ("connection_check",)}, ensure_ascii=False)[:600])
    return 0 if rec["result"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
