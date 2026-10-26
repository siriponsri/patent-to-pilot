"""Offline-by-default CLI for the isolated two-model paired revalidation."""

import argparse
import json
import sys
from contextlib import nullcontext
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from patent_to_pilot.providers import MockHTTPResponse, MockHTTPTransport, OpenRouterHTTPTransport
from patent_to_pilot.providers.env_file import EnvFileError, scoped_env_file_key
from patent_to_pilot.providers.paired import PairError, body_hash, config_for, plan_hash, request_for, run_paired, validate_pair_plan


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, default=ROOT / "configs/provider-paired-revalidation-plan.json")
    parser.add_argument("--state", type=Path, default=ROOT / "results/development/provider-pilot/paired-revalidation-1.sqlite3")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--mock", action="store_true")
    modes.add_argument("--live", action="store_true")
    parser.add_argument("--approval", type=Path)
    parser.add_argument("--env-file", type=Path)
    args = parser.parse_args()
    try:
        plan = json.loads(args.plan.read_text(encoding="utf-8"))
        validate_pair_plan(plan)
        digest = plan_hash(plan)
        if not args.mock and not args.live:
            print(json.dumps({"status": "READY_FOR_OWNER_APPROVAL", "live": "NOT_RUN", "plan_sha256": digest, "payload_sha256": {job["id"]: body_hash(config_for(plan, job, live=True), request_for(plan, job)) for job in plan["jobs"]}}, indent=2))
            return 0
        approval = json.loads(args.approval.read_text(encoding="utf-8")) if args.approval else None

        def factory(job):
            if args.live:
                return OpenRouterHTTPTransport()
            provider = job["provider_only"]
            payload = {
                "model": job["model"],
                "provider": provider,
                "choices": [{"message": {"content": json.dumps({"ack": "ready", "case_id": job["case_id"]})}}],
                "usage": {"prompt_tokens": 32, "completion_tokens": 25, "total_tokens": 57, "cost": 0.0000132 if provider == "google-ai-studio" else 0.00006},
            }
            return MockHTTPTransport(MockHTTPResponse(200, payload))

        def credential_context():
            if args.live and args.env_file is not None:
                return scoped_env_file_key(args.env_file)
            return nullcontext()

        result = run_paired(plan, args.state, approval, factory, live=args.live, credential_context=credential_context)
        print(json.dumps({"plan_sha256": digest, "mode": "live" if args.live else "mock", **result}, indent=2))
        return 0 if result["status"] == "PAIR_COMPLETE" else 2
    except (PairError, ValueError, OSError, EnvFileError) as exc:
        failure = {"status": "BLOCKED", "error_class": type(exc).__name__}
        if isinstance(exc, EnvFileError):
            failure["error_code"] = exc.code
        print(json.dumps(failure), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
