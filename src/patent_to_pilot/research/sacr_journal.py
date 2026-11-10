"""Exclusive dev stage journal with durable receipts; injected callbacks only."""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import time

from patent_to_pilot.research.mtm_runtime import InputBoundaryError
from patent_to_pilot.research.sacr_components import digest
from patent_to_pilot.research.sacr_outcomes import METRICS, summarize_costs
from patent_to_pilot.research.sacr_run_reconcile import reconcile_run, validate_plan


def _write(path, value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False).encode('utf-8')
    with path.open('xb') as handle:
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())
    return hashlib.sha256(raw).hexdigest()


def _read(path):
    raw = path.read_bytes()
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


class DevStageJournal:
    """Not an isolation boundary, GPU launcher or model-budget controller.

    Callbacks return (JSON-serializable private output, complete metric mapping).
    Caller controls declared stage dependencies and model-specific caps. A crash
    with no final seal cannot be resumed/reclassified automatically. Directory
    exclusivity is not protection against another process modifying artifacts.
    """

    def __init__(self, destination, manifest, *, expected_manifest_sha256):
        validate_plan(manifest, expected_manifest_sha256=expected_manifest_sha256)
        self.manifest = deepcopy(manifest)
        self.expected = expected_manifest_sha256
        self.slots = {s['attempt_id']: s for s in self.manifest['slots']}
        self.destination = Path(destination)
        self.destination.mkdir(parents=True, exist_ok=False)
        _write(self.destination / 'manifest.json', self.manifest)

    def _reserve(self, attempt_id):
        if attempt_id not in self.slots:
            raise InputBoundaryError('attempt is not declared')
        path = self.destination / digest(attempt_id)
        path.mkdir(exist_ok=False)
        slot = self.slots[attempt_id]
        _write(path / 'reservation.json', {'manifest_sha256': self.expected, **slot})
        return path, slot

    def _terminal(self, path, slot, status, reason, metrics, output_hash=None):
        receipt_hash = _write(path / 'receipt.json', {**slot, 'status': status, 'reason': reason})
        event_hash = None
        if metrics is not None:
            event = {'event_id': slot['attempt_id'], 'query_id': slot['query_id'],
                     'stage': slot['stage'], 'status': status, 'metrics': metrics}
            summarize_costs([event])
            event_hash = _write(path / 'event.json', event)
        _write(path / 'seal.json', {'receipt_sha256': receipt_hash,
                                   'event_sha256': event_hash, 'output_sha256': output_hash})

    def skip(self, attempt_id, *, reason):
        if type(reason) is not str or not reason.strip():
            raise InputBoundaryError('skip reason required')
        path, slot = self._reserve(attempt_id)
        self._terminal(path, slot, 'SKIPPED', reason, None)

    def execute(self, attempt_id, callback):
        path, slot = self._reserve(attempt_id)
        start = time.monotonic()
        try:
            output, metrics = callback()
            metrics = deepcopy(metrics)
            metrics['operation_wall_seconds'] = time.monotonic() - start
            summarize_costs([{'event_id': attempt_id, 'query_id': slot['query_id'],
                             'stage': slot['stage'], 'status': 'COMPLETED', 'metrics': metrics}])
            output_hash = _write(path / 'output.json', output)
        except BaseException as error:
            metrics = {key: None for key in METRICS}
            metrics['operation_wall_seconds'] = time.monotonic() - start
            status = 'INTERRUPTED' if isinstance(error, (KeyboardInterrupt, SystemExit)) else 'FAILED'
            self._terminal(path, slot, status, type(error).__name__, metrics)
            raise
        self._terminal(path, slot, 'COMPLETED', None, metrics, output_hash)
        return output

    def finalize(self, outcomes):
        manifest, _ = _read(self.destination / 'manifest.json')
        if digest(manifest) != self.expected:
            raise InputBoundaryError('persisted manifest changed')
        attempts, events = [], []
        for attempt_id, slot in self.slots.items():
            path = self.destination / digest(attempt_id)
            if not (path / 'seal.json').is_file():
                raise InputBoundaryError('unsealed attempt; inspect process state, never infer stopped')
            reservation, _ = _read(path / 'reservation.json')
            if reservation != {'manifest_sha256': self.expected, **slot}:
                raise InputBoundaryError('reservation identity changed')
            seal, _ = _read(path / 'seal.json')
            receipt, receipt_hash = _read(path / 'receipt.json')
            if receipt_hash != seal['receipt_sha256']:
                raise InputBoundaryError('receipt bytes changed')
            attempts.append({**receipt, 'receipt_sha256': receipt_hash})
            if seal['event_sha256'] is not None:
                event, event_hash = _read(path / 'event.json')
                if event_hash != seal['event_sha256']:
                    raise InputBoundaryError('event bytes changed')
                events.append(event)
            if receipt['status'] == 'COMPLETED' and seal['output_sha256'] is None:
                raise InputBoundaryError('completed attempt lacks output binding')
            if seal['output_sha256'] is not None:
                _, output_hash = _read(path / 'output.json')
                if output_hash != seal['output_sha256']:
                    raise InputBoundaryError('output bytes changed')
        report = reconcile_run(manifest, attempts, events, outcomes, expected_manifest_sha256=self.expected)
        outcomes_hash = _write(self.destination / 'outcomes.json', outcomes)
        report_hash = _write(self.destination / 'reconciliation.json', report)
        _write(self.destination / 'completion.json', {'manifest_sha256': self.expected,
                                                     'outcomes_sha256': outcomes_hash,
                                                     'reconciliation_sha256': report_hash})
        return report
