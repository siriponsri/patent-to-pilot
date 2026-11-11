"""One-shot census worker. External isolation/approval is required for real data.

Cooperative deadlines do not replace the outer hard supervisor. Receipts contain
aggregate counts only; no source text or exception messages are published.
"""
import hashlib
import json
import math
from pathlib import Path
import time

from .mtm_runtime import InputBoundaryError
from .sg_relations_v2 import CONFIG, extract_family_v2
from .sg_signature_census import SignatureCensus


def config_hash():
    return hashlib.sha256(json.dumps(CONFIG, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def run_census(source, destination, *, expected_sha256, expected_families,
               expected_config_sha256, max_seconds, max_input_bytes,
               max_line_bytes=8*1024*1024, clock=time.monotonic):
    for value in (expected_families, max_input_bytes, max_line_bytes):
        if type(value) is not int or value <= 0:
            raise InputBoundaryError('invalid census integer bound')
    if (type(max_seconds) not in (int, float) or not math.isfinite(max_seconds)
            or max_seconds <= 0):
        raise InputBoundaryError('invalid census deadline')
    for digest in (expected_sha256, expected_config_sha256):
        if type(digest) is not str or len(digest) != 64 or any(c not in '0123456789abcdef' for c in digest):
            raise InputBoundaryError('invalid census digest')
    # Exclusive creation is a replay guard for this attempt, not cross-path authority.
    out = Path(destination)
    out.mkdir(exist_ok=False)
    start = clock()
    census = SignatureCensus(max_families=expected_families, max_records=expected_families*8)
    receipt = {'status': 'INCOMPLETE', 'model_calls': 0, 'gpu_seconds': 0,
               'expected_input_sha256': expected_sha256,
               'config_sha256': expected_config_sha256, 'rows_read': 0,
               'bytes_hashed': 0, 'retry': False}
    phase = 'preflight'

    def deadline():
        if clock() - start >= max_seconds:
            raise TimeoutError('census deadline')

    try:
        if config_hash() != expected_config_sha256:
            raise InputBoundaryError('extractor config mismatch')
        with Path(source).open('rb') as stream:
            phase = 'input_identity'
            digest = hashlib.sha256()
            while True:
                deadline()
                chunk = stream.read(min(1024*1024, max_input_bytes-receipt['bytes_hashed']+1))
                if not chunk:
                    break
                receipt['bytes_hashed'] += len(chunk)
                if receipt['bytes_hashed'] > max_input_bytes:
                    raise InputBoundaryError('input size cap')
                digest.update(chunk)
            receipt['observed_input_sha256'] = digest.hexdigest()
            if digest.hexdigest() != expected_sha256:
                raise InputBoundaryError('input identity mismatch')
            stream.seek(0)
            phase = 'extraction'
            second_digest = hashlib.sha256()
            while True:
                deadline()
                raw = stream.readline(max_line_bytes+1)
                if not raw:
                    break
                if len(raw) > max_line_bytes:
                    raise InputBoundaryError('line size cap')
                second_digest.update(raw)
                row = json.loads(raw)
                result = extract_family_v2(row)
                deadline()
                census.add_family(result['family_id'], result['records'])
                receipt['rows_read'] += 1
            phase = 'completion_validation'
            if second_digest.hexdigest() != expected_sha256:
                raise InputBoundaryError('input changed during extraction')
            if receipt['rows_read'] != expected_families:
                raise InputBoundaryError('incomplete family count')
            deadline()
        receipt['status'] = 'COMPLETE_SIGNATURE_CENSUS_NOT_FIDELITY'
    except BaseException as error:
        receipt['failure_phase'] = phase
        receipt['failure_type'] = type(error).__name__
        raise
    finally:
        receipt['elapsed_seconds'] = max(0, clock()-start)
        receipt['partial_counts'] = census.summary()
        with (out/'receipt.json').open('x', encoding='utf-8') as handle:
            json.dump(receipt, handle, indent=2)
            handle.write('\n')
    return receipt
