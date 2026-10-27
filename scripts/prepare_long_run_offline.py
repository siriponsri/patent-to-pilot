"""Prepare synthetic fixtures/contracts and an honest blocked live-readiness report.

No provider transport, credential loader, network client or live switch is used.
"""
import argparse
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from patent_to_pilot.evaluation.synthetic_corpus import write_corpus
from patent_to_pilot.product.contracts import ProjectBrief, EvidenceCard, ReviewDecision, JobStatus
from patent_to_pilot.providers.project_budget import POLICY, MODELS


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, default=ROOT / "configs/long-run-offline-v2.json")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--corpus-dir", type=Path, required=True)
    args = parser.parse_args()
    data = args.plan.read_bytes()
    plan = json.loads(data)
    if plan["incremental_cap_usd"] != 5 or plan["phase_caps_usd"] != {"calibration": 1, "subsequent": 4} or {m:r["provider"] for m,r in plan["models"].items()} != MODELS or plan["owner_reference"] != POLICY["owner_reference"] or plan["live_enabled"] is not False:
        raise ValueError("offline plan must preserve owner cap/routes and disable live")
    candidate = plan["calibration_candidate"]
    if candidate["maximum_attempts_total"] != 2 or candidate["retries"] != 0 or candidate["max_output_tokens"] != 1500:
        raise ValueError("bounded calibration candidate changed")
    if args.output_dir.exists() or args.corpus_dir.exists():
        raise FileExistsError("fresh output and corpus directories required")
    args.output_dir.mkdir(parents=True, exist_ok=False)
    corpus = write_corpus(args.corpus_dir, **plan["synthetic"])
    schemas = {c.__name__: c.model_json_schema() for c in (ProjectBrief, EvidenceCard, ReviewDecision, JobStatus)}
    (args.output_dir / "product-schemas.json").write_text(json.dumps(schemas, indent=2), encoding="utf-8")
    estimated = {m: str((Decimal(r["historical_context_length"]) * Decimal(r["historical_input_per_million"]) + Decimal(1500) * Decimal(r["historical_output_per_million"])) / Decimal(1_000_000)) for m,r in plan["models"].items()}
    report = {"status": "OFFLINE_PREPARATION_PASS", "scientific_live_ready": False, "provider_calls": 0, "api_cost_usd": 0,
        "owner_budget_approved_usd": 5, "calibration_candidate_attempts": 2,
        "plan_sha256": hashlib.sha256(data).hexdigest(), "synthetic_coverage": corpus["coverage"],
        "historical_full_context_reservation_estimate_usd": estimated,
        "historical_pair_total_usd": str(sum(Decimal(x) for x in estimated.values())),
        "pricing_status": "HISTORICAL_ONLY_NOT_A_VERIFIED_CURRENT_UPPER_BOUND",
        "blocked_gates": [k for k,v in plan["technical_gates"].items() if v is not True],
        "subsequent_release": "NOT_READY; exact matrix required after calibration",
        "worker_isolation": "NOT_IMPLEMENTED; file hashes/schema checks alone do not isolate filesystem",
        "ui_http_api": "NOT_IMPLEMENTED; schemas only"}
    (args.output_dir / "preflight.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__": main()
