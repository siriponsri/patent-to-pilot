"""Owner-authorized accounting cutover, preserving known legacy spend.

This is one fixed local epoch, not a resettable allowance factory. Unknown
history remains unknown. Only USD1 of prospective exposure is released; the
rest of the nominal USD100 envelope is an uncertainty buffer, not past spend.
No keys, prompts, raw responses, or provider requests are handled here.
"""
from datetime import datetime, timezone
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import sqlite3

from .project_budget import money, policy_identity_hash
from .ledger_registry import default_registry_path, register_canonical_ledger

AUTHORIZATION_ID = 'PTP-HT-OR-E2-20261103-USD100'
LEDGER_ID = 'ptp-healthtech-openrouter-local-e2-20261103'
OWNER_DECISION = 'owner-explicit-new-api-epoch-20261103'
EPOCH_LIMIT = 1_000_000_000
PROJECT_LIMIT = 100_000_000_000
LEGACY_HASHES = {
    'live.sqlite3': 'a10f81d79a37a39b53547cb4417437499aa81b69a896048f352ff3a8ba8e9d36',
    'paired-revalidation-1.sqlite3': 'f6943c6b99b999f88e5df839e35c15bd86119cb19a89ab4507d61b40d7de9fcb',
}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def registry_path():
    return default_registry_path(AUTHORIZATION_ID)


def ledger_path():
    return registry_path().parent.parent / 'accounting' / 'project-api.sqlite3'


def active():
    return registry_path().exists() or ledger_path().exists()


def backup(db, path):
    """Consistent local recovery image, atomically published after reservations too."""
    import uuid
    path=Path(path)
    temporary=path.with_name('r-'+uuid.uuid4().hex[:12]+'.db')
    target=path.with_name('project-api.recovery.sqlite3')
    # Serialize snapshot publication with writers: an older backup cannot
    # replace a newer pending/settled state after a concurrent reservation.
    db.execute('BEGIN IMMEDIATE')
    try:
        with closing(sqlite3.connect(path.resolve().as_uri()+'?mode=ro', uri=True)) as source:
            with closing(sqlite3.connect(temporary)) as copy:source.backup(copy)
        with temporary.open('r+b') as handle:os.fsync(handle.fileno())
        os.replace(temporary,target)
        db.execute('COMMIT')
    except BaseException:
        db.execute('ROLLBACK')
        raise
    finally:
        if temporary.exists():temporary.unlink()


def policy(models, *, pricing_snapshot_sha256, pricing_snapshot_utc):
    from .round1 import build_round1_policy
    result = build_round1_policy(models, pricing_snapshot_sha256=pricing_snapshot_sha256,
                                 pricing_snapshot_utc=pricing_snapshot_utc)
    result.update(version='ptp-local-api-e2-20261103-v1', authorization_id=AUTHORIZATION_ID,
                  incremental_cap_nano_usd=PROJECT_LIMIT, admission_threshold_nano_usd=PROJECT_LIMIT,
                  phase_caps_nano_usd={'canary':250_000_000, 'paired_pilot':500_000_000, 'robustness':250_000_000},
                  prospective_epoch_cap_nano_usd=EPOCH_LIMIT, historical_completeness='UNKNOWN_OWNER_ACCEPTED_CUTOVER')
    return result


def read_epoch(db, authorization_id=AUTHORIZATION_ID, ledger_id=LEDGER_ID):
    if authorization_id != AUTHORIZATION_ID or ledger_id != LEDGER_ID:
        raise ValueError('wrong local accounting epoch identity')
    try:
        rows = db.execute('SELECT record_json, record_sha256 FROM budget_epoch').fetchall()
        if len(rows) != 1:
            raise ValueError('one durable owner epoch record required')
        record = json.loads(rows[0][0])
        if digest(record) != rows[0][1] or record['owner_decision'] != OWNER_DECISION:
            raise ValueError('epoch authorization record changed')
        if (record['authorization_id'],record['ledger_id'],record['prospective_epoch_cap_nano_usd'],record['project_nominal_cap_nano_usd'],record['lifetime_cap_guaranteed']) != (AUTHORIZATION_ID,LEDGER_ID,EPOCH_LIMIT,PROJECT_LIMIT,False):
            raise ValueError('epoch identity or accounting scope changed')
        legacy = db.execute('SELECT source_sha256,source_seq,actual_nano_usd,evidence_json FROM budget_legacy_receipts ORDER BY source_sha256,source_seq').fetchall()
        if len(legacy)!=4 or record['known_legacy_nano_usd']!=146400:
            raise ValueError('verified legacy count or total changed')
        if digest(legacy) != record['legacy_rows_sha256'] or sum(row[2] for row in legacy) != record['known_legacy_nano_usd']:
            raise ValueError('legacy provenance or actual amounts changed')
        if record['known_legacy_nano_usd'] + record['uncertainty_buffer_nano_usd'] + EPOCH_LIMIT != PROJECT_LIMIT:
            raise ValueError('epoch budget envelope changed')
        if record['history_completeness'] != 'UNKNOWN_OWNER_ACCEPTED_CUTOVER':
            raise ValueError('unknown history cannot be relabelled complete')
        return record
    except (sqlite3.Error, KeyError, TypeError, json.JSONDecodeError):
        raise ValueError('durable local epoch evidence is unavailable or invalid') from None


def credit_scope(db, raw):
    from .credit import normalize_credit
    record = read_epoch(db)
    snapshot = normalize_credit(raw, require_current=True)
    if snapshot['authorization_id'] != AUTHORIZATION_ID or snapshot['key_scope'] != record['key_scope']:
        raise ValueError('credit scope differs from authorized epoch key')
    observed = (snapshot['account_scope'], snapshot['key_scope'])
    existing = db.execute('SELECT account_scope,key_scope FROM budget_epoch_scope WHERE singleton=1').fetchone()
    if existing is None:
        # Called inside ProjectBudget.reserve's transaction. Invalid credit or
        # a failed reservation rolls this first binding back with the attempt.
        db.execute('INSERT INTO budget_epoch_scope VALUES(1,?,?)', observed)
    elif tuple(existing) != observed:
        raise ValueError('epoch account/key scope is immutable')
    return {'account_scope':observed[0], 'key_scope':observed[1]}


def read_legacy_sources(directory):
    result=[]
    for name, expected in LEGACY_HASHES.items():
        source=Path(directory)/name
        before=hashlib.sha256(source.read_bytes()).hexdigest()
        if before != expected or Path(str(source)+'-wal').exists():
            raise ValueError('legacy journal changed or has an active WAL; inspect before import')
        with closing(sqlite3.connect(source.resolve().as_uri()+'?mode=ro&immutable=1', uri=True)) as db:
            if db.execute('SELECT mode FROM meta').fetchone() != ('live',):
                raise ValueError('legacy source is not live history')
            for seq, reservation, finished in db.execute('SELECT seq,reservation,finished FROM attempts ORDER BY seq'):
                item=json.loads(reservation)
                if not finished or item.get('reservation_status') != 'settled' or item.get('observed_cost_usd') is None:
                    raise ValueError('unresolved legacy source requires separate recovery')
                evidence={'source_locator':name, 'source_sha256':before, 'source_seq':seq,
                          'status':item.get('status'), 'billing_state':'settled',
                          'original_reserved_nano_usd':money(item['reserved_cost_usd']),
                          'actual_nano_usd':money(item['observed_cost_usd'])}
                result.append((before,seq,evidence['actual_nano_usd'],canonical(evidence)))
        if hashlib.sha256(source.read_bytes()).hexdigest()!=before:
            raise ValueError('legacy source changed during read')
    result.sort(key=lambda row:(row[0],row[1]))
    if len(result)!=4 or sum(row[2] for row in result)!=146400:
        raise ValueError('legacy source totals differ from verified four calls')
    return result


def initialize(*, legacy_directory, key_scope, owner_decision, model_provider_map,
               pricing_snapshot_sha256, pricing_snapshot_utc):
    if owner_decision != OWNER_DECISION:
        raise ValueError('explicit owner epoch decision required')
    import re
    if not isinstance(key_scope,str) or not re.fullmatch(r'sha256:[a-f0-9]{64}',key_scope):
        raise ValueError('observed dispatch key fingerprint required; never a secret')
    pol=policy(model_provider_map,pricing_snapshot_sha256=pricing_snapshot_sha256,pricing_snapshot_utc=pricing_snapshot_utc)
    ph=policy_identity_hash(pol); path=ledger_path().resolve()
    rows=read_legacy_sources(legacy_directory)
    record={'owner_decision':OWNER_DECISION,'authorization_id':AUTHORIZATION_ID,'ledger_id':LEDGER_ID,
            'recorded_utc':datetime.now(timezone.utc).isoformat(),'key_scope':key_scope,
            'known_legacy_nano_usd':sum(row[2] for row in rows),
            'uncertainty_buffer_nano_usd':PROJECT_LIMIT-EPOCH_LIMIT-sum(row[2] for row in rows),
            'prospective_epoch_cap_nano_usd':EPOCH_LIMIT,'project_nominal_cap_nano_usd':PROJECT_LIMIT,
            'history_completeness':'UNKNOWN_OWNER_ACCEPTED_CUTOVER','lifetime_cap_guaranteed':False,
            'legacy_rows_sha256':digest(rows),'model_provider_map':model_provider_map}
    path.parent.mkdir(parents=True,exist_ok=True)
    # O_EXCL prevents two initializers from minting different copies/allowances.
    try:
        fd=os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600);os.close(fd);created=True
    except FileExistsError:
        created=False
    db=sqlite3.connect(path,timeout=10,isolation_level=None)
    try:
        db.execute('PRAGMA synchronous=FULL');db.execute('PRAGMA busy_timeout=10000')
        if created:
            db.executescript('BEGIN IMMEDIATE;'
              'CREATE TABLE budget_meta(policy_hash TEXT NOT NULL);'
              'CREATE TABLE budget_ledger_meta(singleton INTEGER PRIMARY KEY CHECK(singleton=1),ledger_id TEXT NOT NULL,authorization_id TEXT,namespace TEXT NOT NULL,canonical_path TEXT NOT NULL,policy_hash TEXT NOT NULL,pricing_snapshot_sha256 TEXT,pricing_snapshot_utc TEXT);'
              'CREATE TABLE budget_epoch(record_json TEXT NOT NULL,record_sha256 TEXT NOT NULL);'
              'CREATE TABLE budget_legacy_receipts(source_sha256 TEXT NOT NULL,source_seq INTEGER NOT NULL,actual_nano_usd INTEGER NOT NULL,evidence_json TEXT NOT NULL,PRIMARY KEY(source_sha256,source_seq));'
              'CREATE TABLE budget_epoch_scope(singleton INTEGER PRIMARY KEY CHECK(singleton=1),account_scope TEXT NOT NULL,key_scope TEXT NOT NULL);')
            db.execute('INSERT INTO budget_meta VALUES(?)',(ph,))
            db.execute('INSERT INTO budget_ledger_meta VALUES(1,?,?,?,?,?,?,?)',(LEDGER_ID,AUTHORIZATION_ID,'canonical',str(path),ph,pricing_snapshot_sha256,pricing_snapshot_utc))
            db.execute('INSERT INTO budget_epoch VALUES(?,?)',(canonical(record),digest(record)))
            db.executemany('INSERT INTO budget_legacy_receipts VALUES(?,?,?,?)',rows)
            db.execute('COMMIT')
        else:
            existing=read_epoch(db)
            if existing['legacy_rows_sha256']!=record['legacy_rows_sha256'] or existing['key_scope']!=key_scope or existing['model_provider_map']!=model_provider_map:
                raise ValueError('existing epoch differs; initialization cannot reset history')
        meta=db.execute('SELECT policy_hash,canonical_path FROM budget_ledger_meta WHERE singleton=1').fetchone()
        if meta!=(ph,str(path)):
            raise ValueError('existing epoch policy/path cannot be substituted')
    finally:
        db.close()
    register_canonical_ledger(path,authorization_id=AUTHORIZATION_ID,policy_hash=ph,
        pricing_snapshot_sha256=pricing_snapshot_sha256,pricing_snapshot_utc=pricing_snapshot_utc,ledger_id=LEDGER_ID)
    # The existing canonical class creates missing operational tables and all
    # later calls use its original reserve/settle/transaction transport path.
    from .project_budget import ProjectBudget
    budget=ProjectBudget(path,policy=pol,ledger_id=LEDGER_ID,authorization_id=AUTHORIZATION_ID,
        namespace='canonical',canonical_path=path,pricing_snapshot_sha256=pricing_snapshot_sha256,pricing_snapshot_utc=pricing_snapshot_utc)
    try:
        state=budget.snapshot()
        backup_path=path.parent/'project-api.initial-backup.sqlite3'
        if not backup_path.exists():
            with closing(sqlite3.connect(backup_path)) as target:budget.db.backup(target)
    finally:budget.close()
    return state
