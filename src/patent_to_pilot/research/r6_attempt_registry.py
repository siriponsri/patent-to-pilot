"""Durable no-replay claims, independent of run names and output directories.

The controller must pin one preinitialized registry path and identity in its
declaration. This module cannot prove that a caller mounted that same database;
the production isolation/admission receipt must establish that separately.
Claims are never released, even when a process dies before its first call.
"""
import hashlib
import json
import sqlite3
from contextlib import closing, contextmanager
from pathlib import Path

from .mtm_runtime import InputBoundaryError


def _encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def _hash(value):
    if (type(value) is not str or len(value) != 64
            or any(c not in '0123456789abcdef' for c in value)):
        raise InputBoundaryError('registry requires lowercase sha256 identity')
    return value


def initialize(path, identity):
    """Explicit controller setup only; never called by a worker on open failure."""
    path = Path(path)
    _hash(identity)
    with path.open('xb'):
        pass
    with closing(sqlite3.connect(path)) as db, db:
        db.execute('PRAGMA synchronous=FULL')
        db.execute('CREATE TABLE identity (id TEXT PRIMARY KEY)')
        db.execute('INSERT INTO identity VALUES (?)', (identity,))
        db.execute('CREATE TABLE attempts (key TEXT PRIMARY KEY, binding TEXT NOT NULL, '
                   'status TEXT NOT NULL, result_sha256 TEXT)')


class AttemptRegistry:
    def __init__(self, path, identity):
        self.path = Path(path).resolve(strict=True)
        self.identity = _hash(identity)
        # mode=rw cannot silently replace a missing database with an empty one.
        with self._open() as db:
            if db.execute('SELECT id FROM identity').fetchall() != [(identity,)]:
                raise InputBoundaryError('registry identity mismatch')

    @contextmanager
    def _open(self):
        db = sqlite3.connect(self.path.as_uri() + '?mode=rw', uri=True, timeout=5)
        try:
            db.execute('PRAGMA synchronous=FULL')
            if db.execute('SELECT id FROM identity').fetchall() != [(self.identity,)]:
                raise InputBoundaryError('registry identity mismatch')
            with db:
                yield db
        finally:
            db.close()

    def claim(self, *, namespace, benchmark, split, configuration_sha256,
              query_id, source_sha256, manifest_sha256, execution_sha256, destination=None):
        for value in (namespace, benchmark, split, query_id):
            if type(value) is not str or not value.strip():
                raise InputBoundaryError('registry key fields required')
        key = _encoded([namespace, benchmark, split, _hash(configuration_sha256), query_id])
        binding = _encoded({'source_sha256': _hash(source_sha256),
                            'manifest_sha256': _hash(manifest_sha256),
                            'execution_sha256': _hash(execution_sha256),
                            'destination': str(Path(destination).resolve()) if destination is not None else None})
        with self._open() as db:
            db.execute('BEGIN IMMEDIATE')
            # Any earlier claim blocks: changed source is not a new native attempt.
            if db.execute('SELECT key FROM attempts WHERE key=?', (key,)).fetchone():
                raise InputBoundaryError('native attempt already claimed; replay forbidden')
            db.execute('INSERT INTO attempts VALUES (?, ?, ?, NULL)', (key, binding, 'CLAIMED'))
        return {'key': key, 'binding': binding, 'registry_identity': self.identity}

    def begin_dispatch(self, claim):
        """Consume a claim once, before any backend invocation (also crash-safe)."""
        if claim.get('registry_identity') != self.identity:
            raise InputBoundaryError('claim registry identity mismatch')
        with self._open() as db:
            db.execute('BEGIN IMMEDIATE')
            changed = db.execute('UPDATE attempts SET status=? '
                                 'WHERE key=? AND binding=? AND status=?',
                                 ('DISPATCHED_UNRESOLVED', claim['key'], claim['binding'], 'CLAIMED'))
            if changed.rowcount != 1:
                raise InputBoundaryError('claim already consumed or identity mismatch')

    def settle(self, claim, result):
        """Controller calls only after validating durable result and artifact bytes."""
        if claim.get('registry_identity') != self.identity:
            raise InputBoundaryError('claim registry identity mismatch')
        result_hash = hashlib.sha256(_encoded(result).encode()).hexdigest()
        with self._open() as db:
            db.execute('BEGIN IMMEDIATE')
            changed = db.execute('UPDATE attempts SET status=?, result_sha256=? '
                                 'WHERE key=? AND binding=? AND status=?',
                                 ('COMPLETE', result_hash, claim['key'], claim['binding'], 'DISPATCHED_UNRESOLVED'))
            if changed.rowcount != 1:
                raise InputBoundaryError('unknown, altered or already settled claim')
        return result_hash

    def verify_completed(self, claim, result):
        """Verify cached outcome identity; this never grants a dispatch token."""
        if claim.get('registry_identity') != self.identity:
            raise InputBoundaryError('claim registry identity mismatch')
        result_hash = hashlib.sha256(_encoded(result).encode()).hexdigest()
        with self._open() as db:
            row = db.execute('SELECT binding, status, result_sha256 FROM attempts WHERE key=?',
                             (claim['key'],)).fetchone()
        if row != (claim['binding'], 'COMPLETE', result_hash):
            raise InputBoundaryError('cached result is unresolved, changed or unregistered')
        return result_hash


def artifact_manifest(directory):
    """Bind exact retained bundle files; no sources or file bytes leave this API."""
    root = Path(directory).resolve(strict=True)
    result = {}
    for path in sorted(root.rglob('*')):
        if path.is_symlink():
            raise InputBoundaryError('bundle artifact symlink forbidden')
        if path.is_file():
            if not path.resolve(strict=True).is_relative_to(root):
                raise InputBoundaryError('bundle artifact outside destination')
            result[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    if 'input.json' not in result or 'result.json' not in result:
        raise InputBoundaryError('completed bundle requires input and result artifacts')
    return result


def completed_bundle(directory, *, query_id, source_sha256, execution, result):
    """Validate durable input/result before settling or reusing a native bundle."""
    root = Path(directory)
    artifacts = artifact_manifest(root)
    input_record = json.loads((root/'input.json').read_bytes())
    durable = json.loads((root/'result.json').read_bytes())
    if (input_record.get('query_id') != query_id
            or input_record.get('source_sha256') != source_sha256
            or input_record.get('execution') != execution
            or input_record.get('retry') is not False
            or durable != result or result.get('query_id') != query_id
            or result.get('status') not in ('UNASSESSABLE', 'AUTOMATIC_METHOD_FLAG',
                                          'AUTOMATIC_UNFLAGGED_NOT_FIDELITY_PASS')
            or result.get('retry') is not False):
        raise InputBoundaryError('durable native bundle identity mismatch')
    return {'query_id': query_id, 'source_sha256': source_sha256,
            'execution': execution, 'result': result, 'artifacts': artifacts}


def run_registered_bundle(*, registry, namespace, configuration_sha256,
                          manifest_sha256, bundle_arguments):
    """Native worker entry: a new directory/run never grants a second attempt.

    The controller must validate the namespace/configuration against its frozen
    declaration. Synthetic fixtures use the unregistered core runner separately.
    """
    from copy import deepcopy
    from .sacr_r6_bundle_runner import run_bundle
    args = dict(bundle_arguments)
    execution = deepcopy(args['execution'])
    args['execution'] = deepcopy(execution)
    source_hash = hashlib.sha256(args['source'].encode()).hexdigest()
    claim = registry.claim(namespace=namespace, benchmark='DAPFAM', split='dev',
        configuration_sha256=configuration_sha256, query_id=args['query_id'],
        source_sha256=source_hash, manifest_sha256=manifest_sha256,
        execution_sha256=hashlib.sha256(_encoded(execution).encode()).hexdigest(),
        destination=args['destination'])
    registry.begin_dispatch(claim)
    result = run_bundle(**args)
    binding = completed_bundle(args['destination'], query_id=args['query_id'],
        source_sha256=source_hash, execution=execution, result=result)
    registry.settle(claim, binding)
    return {'claim': claim, 'binding': binding}
