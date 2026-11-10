"""Evaluator-only access to a curator-staged development qrel bundle."""
from pathlib import Path

from patent_to_pilot.research.mtm_runtime import (
    InputBoundaryError, exact_fields, identifier, read_bound_rows,
)


def load_dev_qrels(root: Path, *, query_ids: set[str]) -> dict[str, set[str]]:
    rows = read_bound_rows(root, expected_format="ptp-mtm-qrels-v1", filename="qrels.jsonl")
    result = {}
    for row in rows:
        exact_fields(row, {"id", "targets"})
        identifier(row["id"])
        targets = row["targets"]
        if type(targets) is not list or not targets:
            raise InputBoundaryError("invalid development targets")
        for target in targets:
            identifier(target)
        if len(set(targets)) != len(targets) or row["id"] in result:
            raise InputBoundaryError("duplicate development query or target")
        result[row["id"]] = set(targets)
    if set(result) != query_ids:
        raise InputBoundaryError("development population mismatch")
    return result
