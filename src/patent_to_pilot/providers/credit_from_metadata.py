"""Join a scoped account observation to fresh, presence-preserving key metadata.

No credentials, network, ledger mutations or admission authority. Account/key
binding must be asserted by the observation source; matching usage is not proof.
"""
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json

from .credit import FORMAT, MAX_AGE_SECONDS, normalize_credit, utc_time, available_money
from .metadata_observation import availability_summary


def credit_from_metadata(metadata, account, *, now=None):
    now = now or datetime.now(timezone.utc)
    if not isinstance(metadata, dict) or metadata.get('format') != 'ptp-openrouter-metadata-observation-v2':
        raise ValueError('presence-preserving v2 key observation required')
    unsigned = {k:v for k,v in metadata.items() if k != 'receipt_sha256'}
    digest = hashlib.sha256(json.dumps(unsigned,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    if metadata.get('receipt_sha256') != digest:
        raise ValueError('metadata observation hash mismatch')
    endpoint = metadata.get('key_endpoint', {})
    if metadata.get('provider') != 'openrouter' or metadata.get('currency') != 'USD' or endpoint.get('status') != 'OBSERVED' or endpoint.get('http_status') != 200:
        raise ValueError('successful OpenRouter key observation required')
    # A signed observation may display the same instant with a local offset.
    # Canonicalize after checking its hash; do not re-date the observation.
    value = metadata.get('started_at_utc')
    if not isinstance(value, str):
        raise ValueError('key observation timestamp must include timezone')
    try:
        key_at = datetime.fromisoformat(value.replace('Z','+00:00'))
    except ValueError:
        raise ValueError('invalid key observation timestamp') from None
    if key_at.tzinfo is None or key_at.utcoffset() is None:
        raise ValueError('key observation timestamp must include timezone')
    key_at = key_at.astimezone(timezone.utc)
    age = (now-key_at).total_seconds()
    if not 0 <= age <= MAX_AGE_SECONDS:
        raise ValueError('key observation is future-dated or stale')
    # This equality is necessary but does not infer account ownership. The
    # account observation source must have established the named binding.
    if not isinstance(account,dict) or account.get('key_scope') != metadata.get('key_scope'):
        raise ValueError('account observation must bind the exact dispatch key')
    if account.get('format') != FORMAT:
        raise ValueError('v2 scoped account observation required')
    state = availability_summary(metadata)
    if state['key_limit_state'] not in {'LIMITED','UNLIMITED'} or not state['applicable_budgets_observed']:
        raise ValueError('key/budget observation unavailable or blocking')
    remaining = state['observed_key_or_budget_remaining_usd']
    if remaining is not None:
        if Decimal(remaining) <= 0:
            raise ValueError('key or applicable budget is exhausted')
        available_money(remaining)
    # Retain the older timestamp so intervening exposure is conservatively
    # counted by the existing transactional reservation guard.
    account_at = utc_time(account.get('as_of_utc'))
    values = {k:account.get(k) for k in ('format','provider','source','remaining_credits_usd',
               'authorization_id','account_scope','key_scope','currency')}
    values.update(as_of_utc=min(key_at,account_at).isoformat(),key_remaining_usd=remaining,
                  key_limit_unlimited=remaining is None)
    if account_at > now:
        raise ValueError('account observation is future-dated')
    return normalize_credit(values,now=now,require_current=True)


def main():
    import argparse
    from pathlib import Path
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--key-observation',type=Path,required=True)
    parser.add_argument('--account-observation',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    try:
        result=credit_from_metadata(json.loads(args.key_observation.read_text(encoding='utf-8')),
                                    json.loads(args.account_observation.read_text(encoding='utf-8')))
        with args.output.open('x',encoding='utf-8') as handle:
            json.dump(result,handle,indent=2,allow_nan=False);handle.write('\n')
    except Exception:
        raise SystemExit('CREDIT_JOIN_FAILED_NO_RAW_DETAILS') from None
    print('SCOPED_CREDIT_SNAPSHOT_WRITTEN_NOT_DISPATCHED')


if __name__=='__main__':
    main()
