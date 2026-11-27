"""Fail closed before a retrospective runner can evaluate a protected cutoff."""
import hmac
import json
import os
import re
from datetime import date
from pathlib import Path

TEST_FIRST = date(2017, 1, 1)
LOCK_PATH = Path(__file__).resolve().parents[1] / "data" / "PREREG_LOCK.json"
ENV_NAME = "LOE_PREREG_SHA256"


class TestSealError(PermissionError):
    """The preregistration lock has not authorized protected evaluation."""


def require_cutoffs(cutoffs):
    """Require the canonical lock's lowercase `sha256` for any protected cutoff."""
    if not any(cutoff >= TEST_FIRST for cutoff in cutoffs):
        return
    try:
        expected = json.loads(LOCK_PATH.read_text(encoding="utf-8"))["sha256"]
    except (OSError, ValueError, KeyError, TypeError):
        expected = None
    supplied = os.environ.get(ENV_NAME, "")
    if (not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected)
            or not re.fullmatch(r"[0-9a-f]{64}", supplied)
            or not hmac.compare_digest(expected, supplied)):
        raise TestSealError("cutoffs from 2017-01-01 require the matching preregistration SHA-256")


def require_rows(rows):
    """Check row cutoffs before stripping metadata for numerical metrics."""
    require_cutoffs(row["t"] for row in rows)
