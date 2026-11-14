"""Owner-approved cumulative disk cap amendment (append-only, no reset).

The declared-upper-bound disk accounting (each GPU job declares 256 MiB, CPU jobs 16 MiB) is checked by
automatic_live_admission against ledger['disk_limit_bytes_combined_incremental']. Owner approval 14 Nov 2026:
40 GiB -> 52 GiB (owner-disk-cap-approval.json). Only the exact chain below is accepted; GPU/fidelity/full-dev/CPU
caps and all charged amounts are untouched. The closed R6 admission path keeps its own fixed 40 GiB check.
"""
import json
from .r6_dispatch_journal import DispatchJournal, document_hash, encoded
from .r6_admission import digest
from .mtm_runtime import InputBoundaryError

GIB = 1024**3
DISK_CAP_CHAIN = ((40 * GIB, 52 * GIB),)  # owner approval 2026-11-14


def require(value, message):
    if not value: raise InputBoundaryError(message)


def amend_disk_cap(journal: DispatchJournal, *, expected_generation, receipt, receipt_sha256):
    """Raise the cumulative disk cap to the next owner-approved link; nothing else in the ledger changes."""
    require(digest(receipt_sha256) and document_hash(receipt) == receipt_sha256, 'amendment pin changed')
    require(receipt.get('kind') == 'DISK_CAP_AMENDMENT' and digest(receipt.get('owner_approval_sha256'))
            and receipt.get('model_calls') == 0 and receipt.get('gpu_seconds') == 0, 'owner amendment receipt incomplete')
    with journal.transaction() as (db, head):
        require(head[1] == expected_generation and head[4] is None, 'stale or active journal')
        ledger = json.loads(head[2])
        require(document_hash(ledger) == receipt.get('prior_ledger_sha256'), 'accounting baseline changed')
        links = ledger.get('disk_cap_amendments') or []
        require(len(links) < len(DISK_CAP_CHAIN)
                and (receipt.get('from_bytes'), receipt.get('to_bytes')) == DISK_CAP_CHAIN[len(links)]
                and ledger.get('disk_limit_bytes_combined_incremental') == receipt['from_bytes'], 'amendment outside approved chain')
        ledger['disk_cap_amendments'] = links + [{'from_bytes': receipt['from_bytes'], 'to_bytes': receipt['to_bytes'],
            'owner_approval_sha256': receipt['owner_approval_sha256'], 'receipt_sha256': receipt_sha256, 'generation': head[1] + 1}]
        ledger['disk_limit_bytes_combined_incremental'] = receipt['to_bytes']
        db.execute('CREATE TABLE IF NOT EXISTS automatic_transitions (generation INTEGER PRIMARY KEY, kind TEXT, receipt TEXT)')
        db.execute('INSERT INTO automatic_transitions VALUES (?,?,?)', (head[1] + 1, 'DISK_CAP_AMENDMENT', encoded(receipt)))
        db.execute('UPDATE head SET generation=?,ledger=?', (head[1] + 1, encoded(ledger)))
    return {'status': 'DISK_CAP_AMENDED', 'generation': expected_generation + 1, 'ledger': ledger}
