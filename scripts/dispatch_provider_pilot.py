"""Explicitly approved/funded engineering pilot. Default is offline plan view."""
import argparse, json, sys
from contextlib import nullcontext
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from patent_to_pilot.providers import MockHTTPResponse, MockHTTPTransport, OpenRouterHTTPTransport
from patent_to_pilot.providers.pilot import PilotError, dispatch, plan_hash, validate_plan, validate_approval
from patent_to_pilot.providers.env_file import EnvFileError, scoped_env_file_key

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, default=ROOT / 'configs/provider-pilot-plan.json')
    parser.add_argument('--state', type=Path, default=ROOT / 'results/development/provider-pilot/state.sqlite3')
    parser.add_argument('--phase', choices=['smoke', 'pilot'], default='smoke')
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument('--mock', action='store_true')
    modes.add_argument('--live', action='store_true')
    parser.add_argument('--approval', type=Path)
    parser.add_argument('--reconcile', type=Path)
    parser.add_argument('--env-file', type=Path, help='explicit plaintext local key file; read only after live approval; inherited environment wins')
    args = parser.parse_args()
    try:
        plan = json.loads(args.plan.read_text(encoding='utf-8'))
        validate_plan(plan)
        digest = plan_hash(plan)
        if not args.mock and (not args.live):
            print(json.dumps(dict(status='READY_AWAITING_FUNDING_AND_BUDGET_APPROVAL', live='NOT_RUN', plan_sha256=digest, plan=plan), indent=2))
            return 0
        approval = json.loads(args.approval.read_text(encoding='utf-8')) if args.approval else None
        receipt = json.loads(args.reconcile.read_text(encoding='utf-8')) if args.reconcile else None
        if args.live:
            validate_approval(plan, args.phase, approval, args.state)

        def factory(job):
            if args.live:
                return OpenRouterHTTPTransport()
            payload = {'model': job['model'], 'provider': plan['models'][job['model']]['routing_only'][0], 'choices': [{'message': {'content': json.dumps(dict(ack='ready', case_id=job['id']))}}], 'usage': dict(prompt_tokens=100, completion_tokens=12, total_tokens=112, cost=0.0001)}
            return MockHTTPTransport(MockHTTPResponse(200, payload))
        credential_context = scoped_env_file_key(args.env_file) if args.live and args.env_file is not None else nullcontext()
        with credential_context:
            result = dispatch(plan, args.state, args.phase, factory, live=args.live, approval=approval, reconcile=receipt)
        print(json.dumps(dict(plan_sha256=digest, mode='live' if args.live else 'mock', **result), indent=2))
        return 0 if result['status'] == 'PHASE_COMPLETE' else 2
    except (PilotError, ValueError, OSError) as exc:
        failure = dict(status='BLOCKED', error_class=type(exc).__name__)
        if isinstance(exc, EnvFileError):
            failure['error_code'] = exc.code
        print(json.dumps(failure), file=sys.stderr)
        return 2
if __name__ == '__main__':
    raise SystemExit(main())
