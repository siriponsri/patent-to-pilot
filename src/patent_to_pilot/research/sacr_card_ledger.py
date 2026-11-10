"""Private durable, cumulative fidelity-card reservations across accounts.

Open an existing ledger explicitly; missing/corrupt files never reset budgets.
OS file locks serialize reservations. Hash links detect accidental corruption,
not deliberate rewriting by an actor with host filesystem privileges.
"""
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path

from patent_to_pilot.research.mtm_runtime import InputBoundaryError, _unique_object
from patent_to_pilot.research.sacr_solo_fidelity import admit_cards

HEADER = {'format': 'ptp-solo-card-ledger-v1', 'total_limit': 60,
          'benchmark_limit': 30, 'escalation_limit_per_benchmark': 20,
          'sentinel_limit_per_benchmark': 10, 'refunds': False}


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')


def sha(value):
    return hashlib.sha256(encoded(value)).hexdigest()


@contextmanager
def locked(path):
    # r+b intentionally refuses absent ledgers. Never unlink the lock inode.
    with Path(path).open('r+b') as f:
        if os.name == 'nt':
            import msvcrt
            f.seek(0)
            msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield f
        finally:
            f.seek(0)
            if os.name == 'nt':
                msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)


def read_chain(f):
    f.seek(0)
    raw = f.read()
    if not raw.endswith(b'\n'):
        raise InputBoundaryError('incomplete card ledger; manual recovery required')
    try:
        lines = [json.loads(line, object_pairs_hook=_unique_object) for line in raw.splitlines()]
    except (ValueError, UnicodeError):
        raise InputBoundaryError('invalid card ledger serialization') from None
    if not lines or lines[0] != HEADER:
        raise InputBoundaryError('card ledger policy mismatch')
    prior, previous = [], sha(HEADER)
    for number, event in enumerate(lines[1:], 1):
        if type(event) is not dict or set(event) != {'sequence', 'previous', 'cards', 'sha256'}:
            raise InputBoundaryError('invalid card ledger event')
        body = {k: v for k, v in event.items() if k != 'sha256'}
        if event['sequence'] != number or event['previous'] != previous or event['sha256'] != sha(body):
            raise InputBoundaryError('card ledger chain changed')
        if type(event['cards']) is not list or not event['cards']:
            raise InputBoundaryError('invalid empty card reservation')
        admit_cards(prior, event['cards'])
        prior.extend(event['cards'])
        previous = event['sha256']
    return prior, previous, len(lines) - 1


class CardLedger:
    def __init__(self, path):
        self.path = Path(path)
        with locked(self.path) as f:
            read_chain(f)

    @classmethod
    def create(cls, path):
        path = Path(path)
        with path.open('xb') as f:
            f.write(encoded(HEADER) + b'\n')
            f.flush()
            os.fsync(f.fileno())
        return cls(path)

    def snapshot(self):
        with locked(self.path) as f:
            prior, head, count = read_chain(f)
            status = admit_cards(prior, [])
            return {'issued_total': status['issued_total'], 'by_benchmark': status['by_benchmark'],
                    'head_sha256': head, 'events': count}

    def reserve(self, cards, *, expected_head):
        # Canonical detached snapshot prevents mutation during validation/write.
        cards = json.loads(encoded(cards))
        if type(cards) is not list or not cards:
            raise InputBoundaryError('complete nonempty card reservation required')
        with locked(self.path) as f:
            prior, head, count = read_chain(f)
            if head != expected_head:
                raise InputBoundaryError('stale card ledger; reread before reserving')
            status = admit_cards(prior, cards)
            body = {'sequence': count + 1, 'previous': head, 'cards': cards}
            event = {**body, 'sha256': sha(body)}
            f.seek(0, os.SEEK_END)
            f.write(encoded(event) + b'\n')
            f.flush()
            os.fsync(f.fileno())
            return {'issued_total': status['issued_total'], 'by_benchmark': status['by_benchmark'],
                    'head_sha256': event['sha256'], 'events': count + 1}
