"""Stop only the owned continuation when its verified frozen flag bound exceeds20.

Never changes criteria, retries a query, or declares a semantic error. Retains
the trigger before stopping and leaves actual GPU charging to terminal closeout.
"""
from pathlib import Path
import datetime
import hashlib
import json
import subprocess

JOB=Path(__file__).resolve().parent
NAME='ptp-native-sacr-continuation-20261111-v1'
START='2026-11-10T23:31:56.42988521Z'
HELPER_SHA='c1d6ac6bf83156c82b462b855efcabae647dbbacd11cc1b299e94d36fc54d2f5'


def inspect():
    return json.loads(subprocess.run(['docker','inspect',NAME],check=True,capture_output=True,text=True,timeout=10).stdout)[0]['State']


def validate_bound(bound):
    c=bound['counts']
    keys=('checked_completed','rejected_profiles','compact_unavailable','compact_lexical_flagged','compact_unflagged_only')
    if any(type(c.get(k)) is not int or not 0<=c[k]<=100 for k in keys):
        raise ValueError('invalid risk observation')
    flags=c['rejected_profiles']+c['compact_unavailable']+c['compact_lexical_flagged']
    if (flags+c['compact_unflagged_only']!=c['checked_completed'] or
            bound.get('flagged_queries_lower_bound')!=flags or bound.get('full_sample')!=100 or
            bound.get('cap')!=20 or flags<=20):
        raise ValueError('frozen stop threshold not established')
    return flags


def main():
    if JOB.name!=NAME or (JOB/'gate-stop-trigger.json').exists():
        raise ValueError('wrong job or existing stop record; inspect instead of replay')
    helper=JOB/'compact-risk-lower-bound.py'
    if hashlib.sha256(helper.read_bytes()).hexdigest()!=HELPER_SHA:
        raise ValueError('risk observer changed')
    bound=json.loads(subprocess.run(['python3',str(helper)],check=True,capture_output=True,text=True,timeout=30).stdout)
    validate_bound(bound)
    before=inspect()
    if before['StartedAt']!=START:
        raise ValueError('different owned attempt; refusing stop')
    receipt={'reason':'FROZEN_REVIEW_CAP_EXCEEDED','bound':bound,'observer_sha256':HELPER_SHA,
             'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'before':before,
             'semantic_errors_proven':False,'retry':False}
    with (JOB/'gate-stop-trigger.json').open('x') as f:json.dump(receipt,f,indent=2)
    if before['Running']:
        subprocess.run(['docker','stop','--time=5',NAME],check=True,capture_output=True,timeout=15)
    after=inspect()
    if after['Running']:
        subprocess.run(['docker','kill',NAME],check=True,capture_output=True,timeout=10)
        after=inspect()
    if after['Running'] or after['StartedAt']!=START:
        raise RuntimeError('termination not verified; do not restart')
    receipt['after']=after
    receipt['status']='OWNED_CONTINUATION_STOPPED_FOR_FROZEN_GATE'
    with (JOB/'gate-stop-result.json').open('x') as f:json.dump(receipt,f,indent=2)
    print(json.dumps(receipt))


if __name__=='__main__':main()
