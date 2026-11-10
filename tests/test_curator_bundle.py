import hashlib
import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("curator_bundle", Path(__file__).resolve().parents[1] /
                                            "scripts/healthtech/build_curator_bundle.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_exact_historical_bytes_restored_without_changing_source():
    lf = b'def example():\n    return "original"\n'
    crlf = lf.replace(b"\n", b"\r\n")
    digest = hashlib.sha256(crlf).hexdigest()
    assert module.restore_bound_bytes(lf, digest) == crlf
    assert module.restore_bound_bytes(crlf, digest) == crlf
    assert module.restore_bound_bytes(crlf, hashlib.sha256(lf).hexdigest()) == lf


def test_semantic_change_cannot_be_relabelled_as_newline_repair():
    expected = hashlib.sha256(b'return "original"\r\n').hexdigest()
    with pytest.raises(ValueError, match="cannot be reconstructed"):
        module.restore_bound_bytes(b'return "changed"\n', expected)
