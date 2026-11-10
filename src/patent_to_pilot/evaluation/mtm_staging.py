"""Trusted curator operation. Never import this module into retrieval runtime.

Staging reads mixed protected source labels. Do not execute against real source
data in a development/agent environment. Separate destinations are necessary
but not sufficient for physical isolation; the curator controls mounts/access.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from patent_to_pilot.research.mtm_runtime import (
    InputBoundaryError, decode_json, exact_fields, identifier, validate_metadata,
)


def _write_bundle(root: Path, rows: list[dict], split: str, kind: str) -> dict:
    root.mkdir(parents=True, exist_ok=False)
    filename = "metadata.jsonl" if kind == "runtime" else "qrels.jsonl"
    raw = b"".join((json.dumps(row, sort_keys=True) + "\n").encode("utf-8") for row in rows)
    with (root / filename).open("xb") as handle:
        handle.write(raw)
    manifest = {"format": f"ptp-mtm-{kind}-v1", "split": split,
                "queries": len(rows), "sha256": hashlib.sha256(raw).hexdigest()}
    with (root / "manifest.json").open("x", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)
        handle.write("\n")
    return manifest


def stage_metadata(source: Path, runtime_root: Path, dev_eval_root: Path, protected_root: Path) -> dict:
    """Validate all source rows before writing; existing destinations fail closed.

    No return value contains IDs or targets. On an I/O failure, incomplete new
    directories remain for inspection; the completion receipt is written last.
    Do not resume or overwrite a partial staging attempt.
    """
    roots = [p.resolve() for p in (runtime_root, dev_eval_root, protected_root)]
    source = source.resolve(strict=True)
    for i, root in enumerate(roots):
        if root.exists() or source.is_relative_to(root):
            raise InputBoundaryError("staging destination already exists or contains source")
        for other in roots[i + 1:]:
            if root.is_relative_to(other) or other.is_relative_to(root):
                raise InputBoundaryError("staging destinations must be disjoint")
    raw = source.read_bytes()
    runtime = {"dev": [], "test": []}
    qrels = {"dev": [], "test": []}
    ids, families = set(), set()
    for line in raw.splitlines():
        row = decode_json(line)
        exact_fields(row, {"id", "family_id", "priority", "c3", "split", "targets"})
        if type(row["split"]) is not str or row["split"] not in runtime:
            raise InputBoundaryError("unknown source split")
        clean = validate_metadata({key: row[key] for key in ("id", "family_id", "priority", "c3")})
        if clean["id"] in ids or clean["family_id"] in families:
            raise InputBoundaryError("duplicate query or cross-split family")
        targets = row["targets"]
        if type(targets) is not list or not targets:
            raise InputBoundaryError("invalid target list")
        for target in targets:
            identifier(target)
        if len(set(targets)) != len(targets):
            raise InputBoundaryError("duplicate target")
        ids.add(clean["id"])
        families.add(clean["family_id"])
        runtime[row["split"]].append(clean)
        qrels[row["split"]].append({"id": clean["id"], "targets": list(targets)})
    if not all(runtime.values()):
        raise InputBoundaryError("both source splits must be nonempty")
    runtime_root, dev_eval_root, protected_root = roots
    # Protected payload is never written into the runtime or dev evaluator tree.
    protected = _write_bundle(protected_root, qrels["test"], "test", "qrels")
    dev = _write_bundle(dev_eval_root, qrels["dev"], "dev", "qrels")
    runtime_root.mkdir(parents=True, exist_ok=False)
    bundles = {s: _write_bundle(runtime_root / s, runtime[s], s, "runtime") for s in runtime}
    receipt = {"format": "ptp-mtm-staging-v1", "status": "STAGED_NOT_ISOLATION_ATTESTED",
               "source_sha256": hashlib.sha256(raw).hexdigest(), "runtime": bundles,
               "dev_evaluation": dev, "protected_evaluation": protected,
               "physical_isolation": "CURATOR_ATTESTATION_REQUIRED"}
    # This receipt is an evaluator artifact, not a runtime feature.
    with (dev_eval_root / "staging-receipt.json").open("x", encoding="utf-8") as handle:
        json.dump(receipt, handle, indent=2)
        handle.write("\n")
    return receipt
