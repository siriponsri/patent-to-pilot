"""Shared, standard-library-only boundary for L1 development inputs."""
from hashlib import sha256
import json


CUTOFFS = {12: ('2012-01-01', '2013-01-01', '2014-01-01', '2015-01-01'),
           24: ('2013-01-01', '2014-01-01')}
ROWS = 3244
GATE_ROWS = 200
MINIMUM_VALID = 180
SEED = 20261127
BATCH_SIZE = 8
MAX_NEW_TOKENS = 160
MEMORY_FRACTION = 0.90
FIELDS = {"entity", "t0", "horizon_months"}


def unique_fields(pairs):
    obj = dict(pairs)
    if len(obj) != len(pairs):
        raise ValueError("duplicate field in forecast row")
    return obj


def validate_input(data, expected_sha, *, expected_rows=ROWS):
    """Verify exact bytes and every row before transfer or GPU generation."""
    if sha256(data).hexdigest() != expected_sha:
        raise ValueError("forecast input SHA-256 mismatch")
    rows = []
    for line in data.splitlines():
        row = json.loads(line, object_pairs_hook=unique_fields)
        if not isinstance(row, dict) or row.keys() != FIELDS:
            raise ValueError("forecast row must have exactly the three allowed fields")
        h, day, entity = row["horizon_months"], row["t0"], row["entity"]
        if (type(h) is not int or h not in CUTOFFS or day not in CUTOFFS[h]
                or not isinstance(entity, str) or not entity.strip() or not entity.isprintable()):
            raise ValueError("forecast row must have a frozen validation cutoff and ingredient name")
        rows.append(row)
    if len(rows) != expected_rows:
        raise ValueError("unexpected forecast row count")
    if len({(r['horizon_months'], r['t0'], r['entity']) for r in rows}) != len(rows):
        raise ValueError("display names are ambiguous within a cutoff and horizon")
    return rows
