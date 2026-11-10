"""Exclusive dev stage journal with durable receipts; injected callbacks only."""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import time

from patent_to_pilot.research.mtm_runtime import InputBoundaryError
from patent_to_pilot.research.sacr_components import digest
from patent_to_pilot.research.sacr_execution import bind_execution
from patent_to_pilot.research.sacr_anchor import bind_anchor_bundle
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

    def __init__(self, destination, manifest, *, expected_manifest_sha256,
                 execution=None, expected_execution_sha256=None, anchor_bundle_raw=None):
        validate_plan(manifest, expected_manifest_sha256=expected_manifest_sha256)
        self.execution = None
        self.execution_expected = expected_execution_sha256
        if execution is not None or expected_execution_sha256 is not None:
            self.execution = bind_execution(
                execution, manifest, expected_execution_sha256=expected_execution_sha256,
                expected_plan_sha256=expected_manifest_sha256)
        self.anchor_bundle = None
        if self.execution is not None and self.execution['format'] == 'sacr-dev-execution-v2':
            self.anchor_bundle = bind_anchor_bundle(anchor_bundle_raw, self.execution)
        elif anchor_bundle_raw is not None:
            raise InputBoundaryError('anchor bundle requires predeclared execution v2')
        self.manifest = deepcopy(manifest)
        self.expected = expected_manifest_sha256
        self.slots = {s['attempt_id']: s for s in self.manifest['slots']}
        self.destination = Path(destination)
        self.destination.mkdir(parents=True, exist_ok=False)
        _write(self.destination / 'manifest.json', self.manifest)
        if self.execution is not None:
            _write(self.destination / 'execution.json', self.execution)
        if self.anchor_bundle is not None:
            with (self.destination / 'anchor-bundle.json').open('xb') as handle:
                handle.write(anchor_bundle_raw)
                handle.flush()
                os.fsync(handle.fileno())

    def _check_bindings(self):
        manifest, _ = _read(self.destination / 'manifest.json')
        if digest(manifest) != self.expected or digest(self.manifest) != self.expected:
            raise InputBoundaryError('persisted or in-memory plan changed')
        if self.slots != {s['attempt_id']: s for s in manifest['slots']}:
            raise InputBoundaryError('in-memory attempt slots changed')
        if self.execution is not None:
            execution, _ = _read(self.destination / 'execution.json')
            bind_execution(execution, manifest, expected_execution_sha256=self.execution_expected,
                           expected_plan_sha256=self.expected)
            if digest(self.execution) != self.execution_expected:
                raise InputBoundaryError('in-memory execution declaration changed')
            if self.execution['format'] == 'sacr-dev-execution-v2':
                bound = bind_anchor_bundle((self.destination / 'anchor-bundle.json').read_bytes(), self.execution)
                if bound != self.anchor_bundle:
                    raise InputBoundaryError('in-memory original anchor bundle changed')

    def _reserve(self, attempt_id):
        self._check_bindings()
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

    def read_completed_output(self, attempt_id):
        """Read a sealed dependency, never infer completion from a reservation."""
        receipt, output = self.read_terminal_attempt(attempt_id)
        if receipt['status'] != 'COMPLETED':
            raise InputBoundaryError('dependency is not a bound completed attempt')
        return output

    def read_terminal_attempt(self, attempt_id):
        """Read verified terminal evidence; unsealed attempts are never classified."""
        self._check_bindings()
        if attempt_id not in self.slots:
            raise InputBoundaryError('dependency is not declared')
        path = self.destination / digest(attempt_id)
        if not (path / 'seal.json').is_file():
            raise InputBoundaryError('dependency is unsealed; inspect process state')
        slot = self.slots[attempt_id]
        reservation, _ = _read(path / 'reservation.json')
        receipt, receipt_hash = _read(path / 'receipt.json')
        seal, _ = _read(path / 'seal.json')
        if (reservation != {'manifest_sha256': self.expected, **slot} or
                receipt_hash != seal['receipt_sha256'] or
                any(receipt.get(key) != value for key, value in slot.items()) or
                receipt.get('status') not in ('COMPLETED', 'FAILED', 'INTERRUPTED', 'SKIPPED')):
            raise InputBoundaryError('dependency is not a bound terminal attempt')
        if receipt['status'] == 'COMPLETED' and seal['output_sha256'] is None:
            raise InputBoundaryError('completed dependency lacks bound output')
        output = None
        if seal['output_sha256'] is not None:
            output, output_hash = _read(path / 'output.json')
            if output_hash != seal['output_sha256']:
                raise InputBoundaryError('dependency output bytes changed')
        return receipt, output

    def read_completed_metrics(self, attempt_id):
        """Check the sealed event as well as the output before replaying costs."""
        receipt, _ = self.read_terminal_attempt(attempt_id)
        if receipt['status'] != 'COMPLETED':
            raise InputBoundaryError('completed cost event required')
        path = self.destination / digest(attempt_id)
        seal, _ = _read(path / 'seal.json')
        event, observed = _read(path / 'event.json')
        slot = self.slots[attempt_id]
        if (observed != seal['event_sha256'] or event.get('event_id') != attempt_id or
                event.get('query_id') != slot['query_id'] or event.get('stage') != slot['stage'] or
                event.get('status') != 'COMPLETED'):
            raise InputBoundaryError('completed cost event differs from seal or slot')
        summarize_costs([event])
        return deepcopy(event['metrics'])

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
        self._check_bindings()
        manifest, _ = _read(self.destination / 'manifest.json')
        if digest(manifest) != self.expected:
            raise InputBoundaryError('persisted manifest changed')
        attempts, events = [], []
        profile_outputs = {}
        selection_outputs = {}
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
                output, output_hash = _read(path / 'output.json')
                if output_hash != seal['output_sha256']:
                    raise InputBoundaryError('output bytes changed')
                if (slot['stage'] == 'profile' and type(output) is dict and
                        output.get('format') == 'sacr-profile-stage-v1'):
                    if self.execution is not None:
                        sources = {s['query_id']: s['source_sha256'] for s in self.execution['sources']}
                        source = output.get('source')
                        if (type(source) is not str or hashlib.sha256(source.encode()).hexdigest() !=
                                sources[slot['query_id']]):
                            raise InputBoundaryError('typed profile source differs from execution binding')
                    profile_outputs[slot['query_id']] = output
                if (slot['stage'] == 'selection' and type(output) is dict and
                        output.get('format') == 'sacr-selection-stage-v1'):
                    selection_outputs[slot['query_id']] = output
        report = reconcile_run(manifest, attempts, events, outcomes, expected_manifest_sha256=self.expected,
                               profile_outputs=profile_outputs, selection_outputs=selection_outputs)
        if self.anchor_bundle is not None:
            anchors = {row['query_id']: row['ranking'] for row in self.anchor_bundle['rows']}
            for outcome in outcomes:
                if outcome['anchor_fallback'] and any(r != anchors[outcome['query_id']]
                                                      for r in outcome['rankings'].values()):
                    raise InputBoundaryError('fallback outcome differs from pinned original anchor')
            report['anchor_reuse'] = {
                'bundle_sha256': self.execution['anchor_bundle_sha256'],
                'baseline_receipt_sha256': self.anchor_bundle['baseline_receipt_sha256'],
                'queries': sum(o['anchor_fallback'] for o in outcomes),
                'baseline_costs': 'EXTERNAL_BASELINE_COSTS_NOT_INCLUDED',
                'baseline_parity': 'REQUIRES_EXTERNAL_VERIFICATION'}
        outcomes_hash = _write(self.destination / 'outcomes.json', outcomes)
        report_hash = _write(self.destination / 'reconciliation.json', report)
        _write(self.destination / 'completion.json', {'manifest_sha256': self.expected,
                                                     'execution_sha256': self.execution_expected,
                                                     'outcomes_sha256': outcomes_hash,
                                                     'reconciliation_sha256': report_hash})
        return report
