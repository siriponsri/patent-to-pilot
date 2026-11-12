"""Conservatively charge bounded CPU-only work once, without resetting history.

The cumulative CPU cap is 28800s unless the single owner-approved amendment
record (28800 -> 57600s, 12 Nov 2026) is present in the same journal ledger.
GPU-stage host CPU is telemetry and is never charged here (owner definition).
"""
import json
import math
from .r6_dispatch_journal import DispatchJournal, document_hash, encoded
from .r6_admission import digest
from .mtm_runtime import InputBoundaryError

BASE_CAP_SECONDS = 28800
AMENDED_CAP_SECONDS = 57600
CPU_KEYS = ('cpu_prior_upper_bound_seconds', 'local_cpu_conservative_charged_seconds',
            'local_cpu_measured_seconds', 'remote_cpu_charged_seconds',
            'local_cpu_reserved_seconds', 'remote_cpu_reserved_seconds')
GPU_STAGE_HOST_CPU = 'TELEMETRY_NOT_CHARGED_TO_CPU_CAP'


def require(value, message):
    if not value: raise InputBoundaryError(message)


def cpu_cap(cpu):
    """Return the cap only when it is the original value or the recorded amendment."""
    cap, amendments = cpu.get('cpu_cap_seconds'), cpu.get('cap_amendments')
    if cap == BASE_CAP_SECONDS and amendments is None:
        return cap
    require(cap == AMENDED_CAP_SECONDS and type(amendments) is list and len(amendments) == 1
            and amendments[0].get('from_seconds') == BASE_CAP_SECONDS
            and amendments[0].get('to_seconds') == AMENDED_CAP_SECONDS
            and digest(amendments[0].get('owner_approval_sha256'))
            and digest(amendments[0].get('receipt_sha256')), 'CPU cap not backed by amendment record')
    return cap


def cpu_used(cpu):
    require(all(type(cpu.get(k)) in (int, float) and math.isfinite(cpu[k]) and cpu[k] >= 0
                for k in CPU_KEYS), 'CPU cumulative accounting incomplete')
    return sum(cpu[k] for k in CPU_KEYS)


def book_cpu(journal: DispatchJournal, *, expected_generation, receipt, receipt_sha256):
    require(digest(receipt_sha256) and document_hash(receipt) == receipt_sha256, 'CPU booking pin changed')
    require(receipt.get('model_calls') == 0 and receipt.get('gpu_seconds') == 0
            and digest(receipt.get('owner_approval_sha256'))
            and digest(receipt.get('evidence_sha256')), 'CPU authority/evidence missing')
    seconds = receipt.get('conservative_cpu_seconds'); name = receipt.get('booking_id')
    require(type(seconds) is int and 0 < seconds <= 1200 and type(name) is str and name,
            'bounded CPU booking required')
    with journal.transaction() as (db, head):
        require(head[1] == expected_generation and head[4] is None, 'stale or active journal')
        ledger = json.loads(head[2])
        require(document_hash(ledger) == receipt.get('prior_ledger_sha256'), 'CPU accounting baseline changed')
        cpu = ledger['r6_phase0_cpu']
        require(cpu_used(cpu) + seconds <= cpu_cap(cpu), 'CPU cumulative allowance exceeded')
        db.execute('CREATE TABLE IF NOT EXISTS automatic_cpu_bookings (id TEXT PRIMARY KEY, receipt TEXT)')
        require(not db.execute('SELECT id FROM automatic_cpu_bookings WHERE id=?',(name,)).fetchone(), 'CPU booking replay')
        require(receipt.get('location') in ('local','remote'), 'CPU location required')
        field = 'local_cpu_conservative_charged_seconds' if receipt['location']=='local' else 'remote_cpu_charged_seconds'
        cpu[field] += seconds
        db.execute('INSERT INTO automatic_cpu_bookings VALUES (?,?)',(name,encoded(receipt)))
        db.execute('UPDATE head SET generation=?,ledger=?',(head[1]+1,encoded(ledger)))
    return {'status':'CPU_UPPER_BOUND_CHARGED_NO_REFUND','generation':expected_generation+1,'ledger':ledger}


def amend_cpu_cap_and_book_preparation(journal: DispatchJournal, *, expected_generation, receipt, receipt_sha256):
    """One-time owner amendment: cap 28800->57600 plus a physical upper-bound
    booking for an unmeasured local window (wall seconds x logical CPUs)."""
    require(digest(receipt_sha256) and document_hash(receipt) == receipt_sha256, 'amendment pin changed')
    require(receipt.get('kind') == 'CPU_CAP_AMENDMENT_AND_PREPARATION_UPPER_BOUND'
            and receipt.get('from_seconds') == BASE_CAP_SECONDS
            and receipt.get('to_seconds') == AMENDED_CAP_SECONDS
            and receipt.get('basis') == 'UPPER_BOUND_NOT_MEASURED'
            and receipt.get('gpu_stage_host_cpu') == GPU_STAGE_HOST_CPU
            and receipt.get('model_calls') == 0 and receipt.get('gpu_seconds') == 0
            and receipt.get('location') == 'local'
            and digest(receipt.get('owner_approval_sha256'))
            and digest(receipt.get('evidence_sha256')), 'owner amendment receipt incomplete')
    start, end, cpus = receipt.get('window_start_unix'), receipt.get('window_end_unix'), receipt.get('logical_cpus')
    name, seconds = receipt.get('booking_id'), receipt.get('upper_bound_seconds')
    require(all(type(v) in (int, float) and math.isfinite(v) for v in (start, end))
            and 0 < end - start <= 6 * 3600 and type(cpus) is int and 0 < cpus <= 256,
            'invalid unmeasured window')
    require(type(seconds) is int and seconds == math.ceil(end - start) * cpus,
            'upper bound must equal ceil(window) x logical CPUs')
    require(type(name) is str and name, 'booking identity required')
    with journal.transaction() as (db, head):
        require(head[1] == expected_generation and head[4] is None, 'stale or active journal')
        ledger = json.loads(head[2])
        require(document_hash(ledger) == receipt.get('prior_ledger_sha256'), 'CPU accounting baseline changed')
        cpu = ledger['r6_phase0_cpu']
        require(cpu.get('cpu_cap_seconds') == BASE_CAP_SECONDS and 'cap_amendments' not in cpu,
                'CPU cap already amended')
        require(cpu_used(cpu) + seconds <= AMENDED_CAP_SECONDS, 'upper bound exceeds amended cap')
        db.execute('CREATE TABLE IF NOT EXISTS automatic_cpu_bookings (id TEXT PRIMARY KEY, receipt TEXT)')
        require(not db.execute('SELECT id FROM automatic_cpu_bookings WHERE id=?', (name,)).fetchone(),
                'CPU booking replay')
        cpu['cpu_cap_seconds'] = AMENDED_CAP_SECONDS
        cpu['cap_amendments'] = [{'from_seconds': BASE_CAP_SECONDS, 'to_seconds': AMENDED_CAP_SECONDS,
                                  'owner_approval_sha256': receipt['owner_approval_sha256'],
                                  'receipt_sha256': receipt_sha256, 'generation': head[1] + 1}]
        cpu['local_cpu_conservative_charged_seconds'] += seconds
        cpu['upper_bound_bookings'] = cpu.get('upper_bound_bookings', []) + [
            {'booking_id': name, 'seconds': seconds, 'basis': receipt['basis'],
             'window_start_unix': start, 'window_end_unix': end, 'logical_cpus': cpus}]
        cpu['gpu_stage_host_cpu'] = GPU_STAGE_HOST_CPU
        db.execute('INSERT INTO automatic_cpu_bookings VALUES (?,?)', (name, encoded(receipt)))
        db.execute('CREATE TABLE IF NOT EXISTS automatic_transitions '
                   '(generation INTEGER PRIMARY KEY, kind TEXT, receipt TEXT)')
        db.execute('INSERT INTO automatic_transitions VALUES (?,?,?)',
                   (head[1] + 1, 'CPU_CAP_AMENDMENT', encoded(receipt)))
        db.execute('UPDATE head SET generation=?,ledger=?', (head[1] + 1, encoded(ledger)))
    return {'status': 'CPU_CAP_AMENDED_UPPER_BOUND_CHARGED', 'generation': expected_generation + 1,
            'ledger': ledger, 'remaining_seconds': AMENDED_CAP_SECONDS - cpu_used(cpu)}
