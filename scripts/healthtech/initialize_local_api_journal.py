"""Initialize the one owner-approved local accounting epoch, never dispatch."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'src'))
from patent_to_pilot.providers.local_epoch import initialize
from patent_to_pilot.healthtech.api_generation import pricing_from_snapshot


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--legacy-directory',type=Path,required=True)
    parser.add_argument('--key-scope',required=True,help='non-secret SHA-256 fingerprint, never the key')
    parser.add_argument('--model-snapshot',type=Path,required=True)
    parser.add_argument('--owner-decision',required=True)
    args=parser.parse_args()
    pricing=pricing_from_snapshot(json.loads(args.model_snapshot.read_text(encoding='utf-8')))
    state=initialize(legacy_directory=args.legacy_directory,key_scope=args.key_scope,
        owner_decision=args.owner_decision,model_provider_map={pricing.model:pricing.upstream_provider},
        pricing_snapshot_sha256=pricing.snapshot_sha256,pricing_snapshot_utc=pricing.snapshot_utc)
    print(json.dumps(state,sort_keys=True))
    return 0


if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as exc:
        raise SystemExit('INITIALIZATION_FAILED_'+type(exc).__name__+'; preserve journal and inspect locally') from None
