"""Default is read-only recovery preflight; live needs a new exact approval."""
import argparse
import json
import sqlite3
import sys
from contextlib import nullcontext
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from patent_to_pilot.providers import OpenRouterHTTPTransport
from patent_to_pilot.providers.env_file import EnvFileError, scoped_env_file_key
from patent_to_pilot.providers.pilot import PilotError, plan_hash
from patent_to_pilot.providers.recovery import recovery_contract, run_recovery, validate_recovery_approval


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, default=ROOT / "configs/provider-pilot-plan.json")
    parser.add_argument("--original-state", type=Path, default=ROOT / "results/development/provider-pilot/live.sqlite3")
    parser.add_argument("--state", type=Path, default=ROOT / "results/development/provider-pilot/gemini-recovery-1.sqlite3")
    parser.add_argument("--approval", type=Path)
    parser.add_argument("--env-file", type=Path)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    try:
        plan = json.loads(args.plan.read_text(encoding="utf-8"))
        contract = recovery_contract(plan, args.original_state, args.state)
        if not args.live:
            print(json.dumps(dict(status="PREFLIGHT_ONLY", contract_sha256=plan_hash(contract), contract=contract), indent=2))
            return 0
        approval = json.loads(args.approval.read_text(encoding="utf-8")) if args.approval else None
        validate_recovery_approval(contract, approval)
        credential_context = (lambda: scoped_env_file_key(args.env_file)) if args.env_file is not None else nullcontext
        result = run_recovery(plan, args.original_state, args.state, approval,
                              lambda job: OpenRouterHTTPTransport(), live=True, credential_context=credential_context)
        print(json.dumps(dict(contract_sha256=plan_hash(contract), **result), indent=2))
        return 0 if result["status"] == "RECOVERY_SUCCESS" else 2
    except (PilotError, ValueError, OSError, sqlite3.Error) as exc:
        error = dict(status="BLOCKED", error_class=type(exc).__name__)
        if isinstance(exc, EnvFileError):
            error["error_code"] = exc.code
        print(json.dumps(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
