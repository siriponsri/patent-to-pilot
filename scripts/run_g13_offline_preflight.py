"""Offline-only G13 preparation. No key loading or provider transport."""
import argparse
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from patent_to_pilot.evaluation.pilot_readiness import build_preflight

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan',type=Path,default=ROOT/'configs/g13-offline-plan-v1.json')
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args()
    result=build_preflight(json.loads(args.plan.read_text(encoding='utf-8')),args.output_dir)
    print(json.dumps({k:result[k] for k in ['status','scientific_live_ready','public_case_count','public_state_count','mock_call_records','provider_calls','api_cost_usd']},indent=2))
    return 0 if result['status']=='PASS' else 1

if __name__=='__main__':raise SystemExit(main())
