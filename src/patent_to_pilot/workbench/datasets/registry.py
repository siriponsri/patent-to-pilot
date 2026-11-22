"""G02 dataset metadata registry: load, validate, and decide local availability from file metadata only.

``availability()`` never opens a data row. It looks for a pinned dataset under caller-supplied search
roots by directory and marker-file existence, and reads at most a small JSON sidecar
(``PTP_DATASET_MANIFEST.json``) or the Hugging Face cache snapshot directory name for the revision.
Gated or private assets are never reported as available, even when files exist locally.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Iterable

REGISTRY_PATH = Path(__file__).with_name("registry.json")
SIDECAR_NAME = "PTP_DATASET_MANIFEST.json"

NOT_DOWNLOADED = "not_downloaded"
GATED_ACCEPTANCE_REQUIRED = "gated_acceptance_required"
LOCAL_COPY_FOUND = "local_copy_found"

_HEX40 = re.compile(r"^[0-9a-f]{40}$")
_ACCESS_KINDS = {"public", "auto_gated", "manual_gated", "private", "bundled_fixture"}
_REQUIRED_DATASET_KEYS = ("dataset_id", "revision", "license", "role", "development_use", "exposure", "access",
                          "native_configs", "sources", "field_name_status", "local_markers")
_REQUIRED_SOURCED = ("license", "role", "exposure", "access", "native_configs")
_FIELD_CLASSES = ("runtime_fields", "evaluator_fields", "withheld_fields", "dropped_fields")


class RegistryError(ValueError):
    """The registry document violates the G02 contract."""


@dataclass(frozen=True)
class Availability:
    dataset_id: str
    status: str
    path: str | None = None
    recorded_revision: str | None = None
    pinned_revision: str | None = None
    detail: str = ""

    @property
    def available(self) -> bool:
        return self.status == LOCAL_COPY_FOUND

    @property
    def revision_matches(self) -> bool | None:
        if self.recorded_revision is None or self.pinned_revision is None:
            return None
        return self.recorded_revision == self.pinned_revision


def load_registry(path: Path | str = REGISTRY_PATH) -> dict:
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    validate_registry(doc)
    return doc


def validate_registry(doc: dict) -> None:
    errors: list[str] = []
    if doc.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    seen: set[str] = set()
    for ds in doc.get("datasets", []):
        did = ds.get("dataset_id", "<missing id>")
        for key in _REQUIRED_DATASET_KEYS:
            if key not in ds:
                errors.append(f"{did}: missing {key}")
        if did in seen:
            errors.append(f"{did}: duplicate dataset_id")
        seen.add(did)
        sources = ds.get("sources", {})
        for key in _REQUIRED_SOURCED:
            if not sources.get(key):
                errors.append(f"{did}: fact {key!r} has no source")
        if ds.get("hf_repo"):
            if not _HEX40.match(str(ds.get("revision") or "")):
                errors.append(f"{did}: hf dataset needs a pinned 40-hex revision")
            if not sources.get("revision"):
                errors.append(f"{did}: fact 'revision' has no source")
            if ds.get("development_use") is not False:
                errors.append(f"{did}: benchmark datasets must declare development_use false")
        access = ds.get("access", {})
        if access.get("kind") not in _ACCESS_KINDS:
            errors.append(f"{did}: unknown access kind {access.get('kind')!r}")
        if access.get("kind") in ("auto_gated", "manual_gated") and access.get("acceptance_performed") and not access.get("acceptance_record"):
            errors.append(f"{did}: gated acceptance claimed without an acceptance_record")
        configs = ds.get("native_configs", [])
        if not configs:
            errors.append(f"{did}: no native_configs")
        for cfg in configs:
            name = f"{did}:{cfg.get('config')}"
            sets = {k: set(cfg.get(k, [])) for k in _FIELD_CLASSES}
            for i, a in enumerate(_FIELD_CLASSES):
                for b in _FIELD_CLASSES[i + 1:]:
                    overlap = sets[a] & sets[b]
                    if overlap:
                        errors.append(f"{name}: fields in both {a} and {b}: {sorted(overlap)}")
            if cfg.get("evaluator_only") and (sets["runtime_fields"] or sets["withheld_fields"]):
                errors.append(f"{name}: evaluator_only config declares runtime or withheld fields")
            if not cfg.get("evaluator_only") and not sets["runtime_fields"]:
                errors.append(f"{name}: runtime config declares no runtime fields")
            rows = cfg.get("rows")
            if rows is not None and (not isinstance(rows, int) or rows < 0):
                errors.append(f"{name}: rows must be a non-negative int or null")
        status = ds.get("field_name_status", {})
        if set(status.get("verified", [])) & set(status.get("assumed", [])):
            errors.append(f"{did}: a field name is both verified and assumed")
    if errors:
        raise RegistryError("; ".join(errors))


def get_dataset(dataset_id: str, registry: dict | None = None) -> dict:
    reg = registry or load_registry()
    for ds in reg["datasets"]:
        if ds["dataset_id"] == dataset_id:
            return ds
    raise KeyError(f"unknown dataset_id {dataset_id!r}")


def get_config(dataset_id: str, config: str, registry: dict | None = None) -> dict:
    for cfg in get_dataset(dataset_id, registry)["native_configs"]:
        if cfg["config"] == config:
            return cfg
    raise KeyError(f"{dataset_id}: unknown config {config!r}")


def is_gated_or_private(ds: dict) -> bool:
    access = ds.get("access", {})
    kind = access.get("kind")
    if kind == "private":
        return True
    if kind in ("auto_gated", "manual_gated"):
        return not (access.get("acceptance_performed") and access.get("acceptance_record"))
    return False


def _candidate_dirs(ds: dict, root: Path) -> list[tuple[Path, str | None]]:
    """Directories that could hold a local copy, with a revision implied by the layout (HF cache)."""
    out: list[tuple[Path, str | None]] = []
    repo = ds.get("hf_repo")
    if repo:
        org, name = repo.split("/", 1)
        for cand in (root / repo, root / f"{org}__{name}", root / f"{org}--{name}", root / name):
            out.append((cand, None))
        snapshots = root / f"datasets--{org}--{name}" / "snapshots"
        if snapshots.is_dir():
            for snap in sorted(p for p in snapshots.iterdir() if p.is_dir()):
                out.append((snap, snap.name))
    else:
        out.append((root, None))
        out.append((root / ds["dataset_id"], None))
    return out


def _has_markers(directory: Path, markers: Iterable[str]) -> bool:
    markers = list(markers)
    return bool(markers) and directory.is_dir() and all((directory / m).exists() for m in markers)


def _sidecar_revision(directory: Path) -> str | None:
    sidecar = directory / SIDECAR_NAME
    if not sidecar.is_file() or sidecar.stat().st_size > 64_000:
        return None
    try:
        meta = json.loads(sidecar.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    rev = meta.get("revision") if isinstance(meta, dict) else None
    return str(rev) if rev else None


def availability(dataset_id: str, search_roots: Iterable[Path | str] = (), registry: dict | None = None) -> Availability:
    """Report not_downloaded | gated_acceptance_required | local_copy_found from file existence only."""
    reg = registry or load_registry()
    ds = get_dataset(dataset_id, reg)
    pinned = ds.get("revision")
    found: tuple[Path, str | None] | None = None
    roots = [Path(r) for r in search_roots]
    if ds.get("access", {}).get("kind") == "bundled_fixture" and ds.get("bundled_path"):
        roots.insert(0, (REGISTRY_PATH.parent / ds["bundled_path"]).resolve())
    for root in roots:
        for cand, layout_rev in _candidate_dirs(ds, root):
            if _has_markers(cand, ds.get("local_markers", [])):
                found = (cand, _sidecar_revision(cand) or layout_rev)
                break
        if found:
            break
    if is_gated_or_private(ds):
        detail = "access is gated/private and owner acceptance is not recorded; never reported available"
        if found:
            detail += "; files exist locally but must not be used until acceptance is recorded in the registry"
        return Availability(dataset_id, GATED_ACCEPTANCE_REQUIRED, None, None, pinned, detail)
    if not found:
        return Availability(dataset_id, NOT_DOWNLOADED, None, None, pinned, "no directory with the registry markers under the search roots")
    path, rev = found
    detail = "markers present"
    if pinned and rev and rev != pinned:
        detail += f"; recorded revision {rev} differs from pinned {pinned}"
    elif pinned and not rev:
        detail += "; no recorded revision (add PTP_DATASET_MANIFEST.json before use)"
    return Availability(dataset_id, LOCAL_COPY_FOUND, str(path), rev, pinned, detail)
