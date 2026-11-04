"""Owner-side dashboard capture; one read-only /key request, never paid dispatch.

Run interactively on Windows. Do not paste credentials. Existing ledger is only
read; each capture uses a fresh directory in the existing local evidence root.
"""
from datetime import datetime, timezone
from pathlib import Path
import json, os, re, sqlite3, uuid

from .credit import FORMAT, available_money
from .credit_from_metadata import credit_from_metadata
from .local_epoch import AUTHORIZATION_ID, ledger_path, read_epoch
from .metadata_observation import run as observe_key


class CaptureError(ValueError):
    """Only fixed non-secret diagnostic codes."""


def read_binding(path):
    with sqlite3.connect(Path(path).resolve().as_uri()+'?mode=ro',uri=True) as db:
        epoch=read_epoch(db)
        scopes=db.execute('SELECT account_scope,key_scope FROM budget_epoch_scope WHERE singleton=1').fetchall()
    if len(scopes)>1:
        raise ValueError('multiple account bindings')
    if scopes and scopes[0][1]!=epoch['key_scope']:
        raise ValueError('epoch scope mismatch')
    # This is a stable OWNER-ASSERTED account alias, not a provider account ID.
    account=scopes[0][0] if scopes else 'owner-asserted-account:'+epoch['key_scope'].split(':')[-1]
    return {'key_scope':epoch['key_scope'],'account_scope':account}


def capture(key_file, directory, binding, *, ask=input, clock=None, observer=observe_key):
    clock=clock or (lambda:datetime.now(timezone.utc))
    if ask('Can you verify this .env key belongs to the OpenRouter account whose balance you will view? Type SAME ACCOUNT or press Enter to stop: ').strip()!='SAME ACCOUNT':
        raise CaptureError('ACCOUNT_NOT_CONFIRMED_NO_REQUEST')
    print('Refresh OpenRouter Settings > Credits now. Enter remaining AVAILABLE CREDIT in USD, not usage, purchased total, key cap or MCP cap. Do not paste a key.')
    observed_at=clock()
    balance=ask('Fresh remaining credit (USD number only): ').strip()
    if not re.fullmatch(r'\d+(?:\.\d{1,9})?',balance):
        raise CaptureError('INVALID_BALANCE_NO_REQUEST')
    available_money(balance)
    # Fail before any request when the human observation is already too old.
    if not 0 <= (clock()-observed_at).total_seconds() <= 300:
        raise CaptureError('DASHBOARD_STALE_NO_REQUEST')
    directory=Path(directory)
    directory.mkdir(parents=True,exist_ok=False)
    account={'format':FORMAT,'provider':'openrouter','source':'owner_sanitized_snapshot',
             'as_of_utc':observed_at.isoformat(),'remaining_credits_usd':balance,'currency':'USD',
             'authorization_id':AUTHORIZATION_ID,**binding}
    def save(name,value):
        with (directory/name).open('x',encoding='utf-8') as f:
            json.dump(value,f,indent=2,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
    save('account-observation.json',account)
    save('owner-attestation.json',{'format':'ptp-owner-dashboard-attestation-v1','as_of_utc':observed_at.isoformat(),
         'same_account_confirmation':'SAME ACCOUNT','account_scope_basis':'existing ledger binding or stable owner-asserted alias; not a provider-verified account ID',
         'key_scope':binding['key_scope'],'account_scope':binding['account_scope'],
         'source':'owner checked dashboard in the account holding the local .env key',
         'automated_balance_verification':False,'paid_dispatch':False})
    key_path=directory/'key-observation.json'
    if observer(key_file,key_path)!='OBSERVED':
        raise CaptureError('KEY_ENDPOINT_NOT_OBSERVED_NO_RETRY')
    metadata=json.loads(key_path.read_text(encoding='utf-8'))
    try:
        snapshot=credit_from_metadata(metadata,account,now=clock())
    except ValueError:
        raise CaptureError('CREDIT_JOIN_REJECTED_CHECK_SCOPE_TIME_AND_BUDGETS') from None
    save('credit-snapshot.json',snapshot)
    return directory/'credit-snapshot.json'


def main():
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--key-file',type=Path,required=True)
    args=parser.parse_args()
    root=ledger_path().parent.parent/'evidence'/'owner-credit'
    directory=root/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8])
    try:
        binding=read_binding(ledger_path())
        path=capture(args.key_file,directory,binding)
    except (Exception,KeyboardInterrupt) as error:
        code=str(error) if isinstance(error,CaptureError) else 'LOCAL_INPUT_OR_STORAGE_ERROR'
        print('CAPTURE_STOPPED:',code)
        print('No paid call or ledger change. If a capture directory exists, preserve it; do not retry an uncertain paid job.')
        print('Capture directory:',directory)
        raise SystemExit(1) from None
    print('READY_FOR_EXISTING_ADMISSION_CHECKS; NOT_DISPATCHED')
    print('Credit snapshot:',path)
    print('Use promptly with current pricing and the existing E2 runner; expires 300 seconds from dashboard observation. Never edit its timestamp.')


if __name__=='__main__':
    main()
