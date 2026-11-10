"""Legacy byte compatibility and bounded hashing for authored arrays only."""
import hashlib
import json

import numpy as np
import pytest

from patent_to_pilot.research import sacr_components


def legacy(matrix):
    return hashlib.sha256(json.dumps(list(matrix.shape)).encode() + b'\n' +
                          np.ascontiguousarray(matrix, dtype='<f4').tobytes()).hexdigest()


@pytest.mark.parametrize('matrix', [
    np.arange(60, dtype=np.float32).reshape(10, 6),
    np.asfortranarray(np.arange(60, dtype=np.float32).reshape(10, 6)),
    np.arange(60, dtype=np.float64).reshape(10, 6).T,
    np.arange(60, dtype=np.float32).reshape(10, 6)[::-2, ::2],
    np.arange(60, dtype='>f4').reshape(10, 6),
    np.arange(60, dtype=np.int64).reshape(10, 6),
    np.array([0., -0., np.inf, -np.inf, np.nan], dtype=np.float32),
    np.empty((0, 4), dtype=np.float32),
    np.empty((2, 0), dtype=np.float32),
    np.array(3.25, dtype=np.float64),
])
def test_legacy_byte_compatibility(matrix):
    assert sacr_components.vector_digest(matrix) == legacy(matrix)


@pytest.mark.parametrize('layout', ['contiguous', 'fortran', 'strided', 'conversion'])
def test_large_input_is_hashed_in_bounded_chunks(monkeypatch, layout):
    matrix = np.arange(1024 * 1024, dtype=np.float32).reshape(1024, 1024)
    if layout == 'fortran':
        matrix = np.asfortranarray(matrix)
    elif layout == 'strided':
        matrix = matrix[::-1, ::2]
    elif layout == 'conversion':
        matrix = matrix.astype('>f8')
    expected = legacy(matrix)
    sha256 = hashlib.sha256
    lengths = []

    class TrackedHash:
        def __init__(self):
            self.inner = sha256()

        def update(self, data):
            lengths.append(len(data))
            self.inner.update(data)

        def hexdigest(self):
            return self.inner.hexdigest()

    monkeypatch.setattr(sacr_components.hashlib, 'sha256', TrackedHash)
    assert sacr_components.vector_digest(matrix) == expected
    assert max(lengths) <= 1024 * 1024
    assert sum(lengths) == len(json.dumps(list(matrix.shape)).encode()) + 1 + matrix.size * 4
    assert len(lengths) > 2
