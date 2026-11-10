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
from patent_to_pilot.research.sacr_solo_fidelity import admit_cards, admit_paper1_cards

HEADER = {'format': 'ptp-solo-card-ledger-v1', 'total_limit': 60,
          'benchmark_limit': 30, 'escalation_limit_per_benchmark': 20,
          'sentinel_limit_per_benchmark': 10, 'refunds': False}
PAPER1_POLICY = {'format': 'ptp-paper1-card-allocation-v2', 'total_limit': 60,
                 'DAPFAM_SACR': 30, 'DAPFAM_SG_SHARED': 30, 'MTM': 0,
                 'escalation_per_pool': 20, 'sentinel_per_pool': 10, 'refunds': False}


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
    prior, previous, policy = [], sha(HEADER), 'legacy'
    for number, event in enumerate(lines[1:], 1):
        if type(event) is not dict or set(event) not in ({'sequence', 'previous', 'cards', 'sha256'},
                                                       {'sequence', 'previous', 'policy', 'sha256'}):
            raise InputBoundaryError('invalid card ledger event')
        body = {k: v for k, v in event.items() if k != 'sha256'}
        if event['sequence'] != number or event['previous'] != previous or event['sha256'] != sha(body):
            raise InputBoundaryError('card ledger chain changed')
        if 'policy' in event:
            if prior or policy != 'legacy' or event['policy'] != PAPER1_POLICY:
                raise InputBoundaryError('unsupported card allocation amendment')
            policy = 'paper1'
            previous = event['sha256']
            continue
        if type(event['cards']) is not list or not event['cards']:
            raise InputBoundaryError('invalid empty card reservation')
        (admit_paper1_cards if policy == 'paper1' else admit_cards)(prior, event['cards'])
        prior.extend(event['cards'])
        previous = event['sha256']
    return prior, previous, len(lines) - 1, policy


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
            prior, head, count, policy = read_chain(f)
            status = (admit_paper1_cards if policy == 'paper1' else admit_cards)(prior, [])
            return {k: v for k, v in {**status, 'head_sha256': head, 'events': count}.items() if k != 'reservation'}

    def adopt_paper1_allocation(self, *, expected_head):
        """Explicit owner-approved amendment; never remap/refund issued cards."""
        with locked(self.path) as f:
            prior, head, count, policy = read_chain(f)
            if head != expected_head or prior or policy != 'legacy':
                raise InputBoundaryError('allocation amendment requires current empty legacy ledger')
            body = {'sequence': count + 1, 'previous': head, 'policy': PAPER1_POLICY}
            event = {**body, 'sha256': sha(body)}
            f.seek(0, os.SEEK_END)
            f.write(encoded(event) + b'\n')
            f.flush()
            os.fsync(f.fileno())
        return self.snapshot()

    def reserve(self, cards, *, expected_head):
        # Canonical detached snapshot prevents mutation during validation/write.
        cards = json.loads(encoded(cards))
        if type(cards) is not list or not cards:
            raise InputBoundaryError('complete nonempty card reservation required')
        with locked(self.path) as f:
            prior, head, count, policy = read_chain(f)
            if head != expected_head:
                raise InputBoundaryError('stale card ledger; reread before reserving')
            status = (admit_paper1_cards if policy == 'paper1' else admit_cards)(prior, cards)
            body = {'sequence': count + 1, 'previous': head, 'cards': cards}
            event = {**body, 'sha256': sha(body)}
            f.seek(0, os.SEEK_END)
            f.write(encoded(event) + b'\n')
            f.flush()
            os.fsync(f.fileno())
            return {k: v for k, v in {**status, 'head_sha256': event['sha256'], 'events': count + 1}.items()
                    if k != 'reservation'}
