"""Opt-in private, bounded diagnostic receipts for NEW attempts only.

No repair/retry and no reassessment of historical unknown calls. Invocation
markers establish entry to a Python backend, not completed inference or tokens.
Never publish the diagnostic directory or copy exception/prefix text to reports.
"""
import hashlib
import json
import os
import time
from pathlib import Path


class AttemptDiagnostics:
    def __init__(self, destination):
        self.destination = Path(destination)
        self.destination.mkdir(parents=True, exist_ok=False)
        self.started = time.monotonic()
        self.backend_invocations = 0
        self.backend_returns = 0
        self.last_prefix = None
        self.last_prefix_tokens = None
        self.validation = None
        self.telemetry_write_error = None
        self.written_bytes = 0

    def write(self, name, value):
        raw = (json.dumps(value, ensure_ascii=True, sort_keys=True) + '\n').encode()
        if self.written_bytes + len(raw) > 256 * 1024:
            raise RuntimeError('private diagnostic byte ceiling exceeded')
        with (self.destination / name).open('xb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        self.written_bytes += len(raw)

    def call_backend(self, model, **kwargs):
        if self.backend_invocations:
            raise RuntimeError('diagnostic backend may be invoked only once')
        self.write('backend-dispatch.json', {'status': 'DISPATCH_INTENT', 'retry': False})
        self.backend_invocations += 1
        result = model.generate(**kwargs)
        self.backend_returns += 1
        self.write('backend-return.json', {'status': 'BACKEND_RETURNED_NOT_VALIDATED'})
        return result

    def validator(self, validate):
        def wrapped(value):
            try:
                return validate(value)
            except Exception as error:
                self.validation = {
                    'exception_type': type(error).__name__,
                    'validator': str(getattr(error, 'validator', 'UNKNOWN'))[:100],
                    'schema_path': str(list(getattr(error, 'absolute_schema_path', [])))[:1024],
                    'instance_path': str(list(getattr(error, 'absolute_path', [])))[:1024],
                }
                raise
        return wrapped

    def grammar(self, callback, prompt_tokens):
        def wrapped(batch_id, sent):
            # Retain generated suffix only; never persist the prompt token IDs.
            count = max(0, len(sent) - prompt_tokens)
            tail = sent[max(prompt_tokens, len(sent) - 4096):]
            self.last_prefix = {'generated_tokens_seen': count,
                                'truncated': count > 4096}
            # Keep one bounded view; do not synchronize thousands of GPU scalars
            # at every decoding step. Copy once only if the attempt fails.
            self.last_prefix_tokens = tail
            try:
                return callback(batch_id, sent)
            except BaseException as error:
                self.failure(error, 'grammar-callback')
                raise
        return wrapped

    def failure(self, error, stage):
        try:
            self._persist_failure(error, stage)
        except BaseException as persistence_error:
            # Diagnostic disk/full/encoding faults must never replace the
            # original exception being propagated by the caller.
            self.telemetry_write_error = type(persistence_error).__name__
            try:
                self.write('telemetry-write-error.json', {
                    'exception_type': self.telemetry_write_error,
                    'original_exception_type': type(error).__name__, 'retry': False})
            except BaseException:
                pass

    def _persist_failure(self, error, stage):
        # Keep the earliest exception; outer layers cannot erase the diagnosis.
        if (self.destination / 'failure-private.json').exists(): return
        message = str(error)[:2048]
        prefix = None
        if self.last_prefix is not None:
            tokens = self.last_prefix_tokens
            if hasattr(tokens, 'detach'): tokens = tokens.detach().cpu().tolist()
            prefix = {**self.last_prefix, 'tail_token_ids': [int(token) for token in tokens]}
        self.write('failure-private.json', {
            'stage': stage, 'exception_type': type(error).__name__,
            'message': message, 'message_sha256': hashlib.sha256(message.encode()).hexdigest(),
            'backend_invocations_observed': self.backend_invocations,
            'backend_returns_observed': self.backend_returns,
            'inference_completed': 'UNKNOWN', 'input_output_tokens': 'UNKNOWN',
            'last_generated_prefix': prefix, 'last_schema_rejection': self.validation,
            'wall_seconds': time.monotonic() - self.started, 'retry': False,
        })


def local_executor(*, tokenizer, model_factory, device, eos_token_ids,
                   check_admission, peak_memory_bytes):
    """Factory(stage, schema, diagnostics) must use diagnostics.call_backend."""
    from .sacr_generation import GenerationLimits, run_reserved_attempt
    from .sacr_outcomes import METRICS
    def invoke(stage, destination, messages, schema):
        destination = Path(destination)
        diagnostics = AttemptDiagnostics(destination.with_name(destination.name + '-diagnostics-private'))
        start = time.monotonic()
        try:
            check_admission(stage)
            model = model_factory(stage, schema, diagnostics)
            check_admission(stage)
            result = run_reserved_attempt(destination, messages=messages, tokenizer=tokenizer,
                model=model, device=device, eos_token_ids=eos_token_ids, limits=GenerationLimits())
            if result['model_calls'] != diagnostics.backend_invocations:
                raise RuntimeError('diagnostic backend invocation binding mismatch')
            metrics = {key: 0 for key in METRICS}
            metrics.update({key: result[key] for key in ('model_calls', 'input_tokens', 'output_tokens')})
            elapsed = time.monotonic() - start
            metrics.update(operation_wall_seconds=elapsed, gpu_seconds=elapsed,
                           peak_memory_bytes=peak_memory_bytes())
            return metrics
        except BaseException as error:
            diagnostics.failure(error, 'attempt')
            raise
    return invoke
