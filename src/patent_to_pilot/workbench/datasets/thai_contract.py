"""P3-T01 Thai data contract: pinned releases, rights, exposure and separate scoreboards (stdlib only).

This module reads the ``thai_contract`` blocks of ``registry.json`` and answers three questions from
metadata alone:

* Is the contract complete and self-consistent? (``validate_thai_contract``)
* Which scoreboard does a result row belong to, and does a table mix scoreboards? (``scoreboard_of``,
  ``assert_single_scoreboard``)
* May an agent do X with resource Y right now? (``permitted_use``)

It never downloads, opens a data row, accepts a gate or calls a provider. A download, a gate acceptance,
a paid call or a rights decision is an owner action; ``permitted_use`` reports it as blocked until the
registry carries the owner's record.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .registry import REGISTRY_PATH, is_gated_or_private, load_registry

SCOREBOARDS = (
    "thai_gazette_retrieval",
    "nitibench_original",
    "nitibench_plus",
    "supplied_document_tasks",
    "fresh_structural_packets",
    "ocr_diagnostics",
)
BLOCK_KINDS = ("download", "gate_acceptance", "paid_call", "rights_review", "owner_decision")
PURPOSES = (
    "metadata_read",        # public cards / API metadata; record any auto-preview as exposure
    "synthetic_fixture",    # fictional rows imitating column names only
    "gate_acceptance",      # accepting access conditions: owner only
    "download",             # fetching data files
    "development",          # tuning or designing a method on the rows
    "method_selection",     # choosing a method, prompt or threshold from the rows
    "training",             # updating weights on the rows
    "held_out_evaluation",  # scoring a frozen method
    "product_bundle",       # shipping rows inside the Workbench product
)
PLANNED_STATUSES = ("NOT_COLLECTED", "NOT_DEFINED", "COLLECTED")

_REQUIRED_CONTRACT = ("scoreboard", "release", "rights", "gating", "evaluation_unit", "native_metric", "splits",
                      "development_use", "held_out_use", "prior_exposure", "training_overlap_risk",
                      "download_approval", "blocked_pending_owner")
_REQUIRED_RIGHTS = ("license", "license_scope", "attribution_required", "share_alike", "redistribution_in_product",
                    "terms_url")
_REQUIRED_PLANNED = ("resource_id", "scoreboard", "status", "rights", "evaluation_unit", "development_use",
                     "held_out_use", "prior_exposure", "blocked_pending_owner")
_APPROVAL_KEYS = ("approved_by", "date", "scope", "record")


class ContractError(ValueError):
    """The Thai data contract in the registry is incomplete or inconsistent."""


class ScoreboardMixError(ValueError):
    """A result table mixes scoreboards, mislabels a row, or uses a non-native NitiBench+ setting."""


@dataclass(frozen=True)
class UseDecision:
    resource_id: str
    purpose: str
    allowed: bool
    reason: str


def _blocked_kinds(entry: dict) -> set[str]:
    return {b.get("kind") for b in entry.get("blocked_pending_owner", []) if isinstance(b, dict)}


def _check_blocked(rid: str, entry: dict, errors: list[str]) -> None:
    blocked = entry.get("blocked_pending_owner")
    if not isinstance(blocked, list):
        errors.append(f"{rid}: blocked_pending_owner must be a list")
        return
    for b in blocked:
        if not isinstance(b, dict) or b.get("kind") not in BLOCK_KINDS or not b.get("item") or not b.get("why"):
            errors.append(f"{rid}: blocked item needs kind in {BLOCK_KINDS}, item and why: {b!r}")


def _approval_ok(approval) -> bool:
    return isinstance(approval, dict) and all(isinstance(approval.get(k), str) and approval.get(k) for k in _APPROVAL_KEYS)


def validate_thai_contract(registry: dict) -> None:
    errors: list[str] = []
    top = registry.get("thai_contract")
    if not isinstance(top, dict):
        raise ContractError("registry has no top-level thai_contract")
    boards = top.get("scoreboards", {})
    if set(boards) != set(SCOREBOARDS):
        errors.append(f"scoreboards must be exactly {sorted(SCOREBOARDS)}; got {sorted(boards)}")

    owner_of: dict[str, str] = {}   # resource -> scoreboard it actually declares
    for ds in registry.get("datasets", []):
        did = ds.get("dataset_id")
        contract = ds.get("thai_contract")
        if ds.get("language") != "th":
            if contract is not None:
                errors.append(f"{did}: thai_contract on a non-Thai dataset")
            continue
        if not isinstance(contract, dict):
            errors.append(f"{did}: Thai dataset has no thai_contract")
            continue
        for key in _REQUIRED_CONTRACT:
            if key not in contract:
                errors.append(f"{did}: thai_contract missing {key}")
        if not ds.get("sources", {}).get("thai_contract"):
            errors.append(f"{did}: fact 'thai_contract' has no source")
        owner_of[did] = contract.get("scoreboard")
        rights = contract.get("rights", {})
        for key in _REQUIRED_RIGHTS:
            if key not in rights:
                errors.append(f"{did}: rights missing {key}")
        if rights.get("license") != ds.get("license"):
            errors.append(f"{did}: rights.license {rights.get('license')!r} differs from registry license {ds.get('license')!r}")
        if contract.get("release", {}).get("dataset_revision") != ds.get("revision"):
            errors.append(f"{did}: release.dataset_revision differs from the pinned revision")
        if ds.get("hf_repo"):
            if rights.get("redistribution_in_product") is not False or ds.get("product_bundle_allowed") is not False:
                errors.append(f"{did}: external Thai benchmarks may not be bundled into the product")
            if ds.get("development_use") is not False:
                errors.append(f"{did}: external Thai benchmarks must declare development_use false")
        if not contract.get("training_overlap_risk"):
            errors.append(f"{did}: training_overlap_risk must record at least one finding (or its absence)")
        _check_blocked(did, contract, errors)
        approval = contract.get("download_approval")
        if approval is None:
            if "download" not in _blocked_kinds(contract):
                errors.append(f"{did}: no download approval recorded, so a 'download' block is required")
        elif not _approval_ok(approval):
            errors.append(f"{did}: download_approval needs non-empty {_APPROVAL_KEYS}")
        if is_gated_or_private(ds) and "gate_acceptance" not in _blocked_kinds(contract):
            errors.append(f"{did}: gated without a recorded acceptance, so a 'gate_acceptance' block is required")

    for res in top.get("planned_resources", []):
        rid = res.get("resource_id", "<missing id>")
        for key in _REQUIRED_PLANNED:
            if key not in res:
                errors.append(f"{rid}: planned resource missing {key}")
        if res.get("status") not in PLANNED_STATUSES:
            errors.append(f"{rid}: status must be one of {PLANNED_STATUSES}")
        if res.get("status") != "COLLECTED" and not res.get("blocked_pending_owner"):
            errors.append(f"{rid}: an uncollected resource must say what is blocked")
        _check_blocked(rid, res, errors)
        if rid in owner_of:
            errors.append(f"{rid}: duplicate resource id")
        owner_of[rid] = res.get("scoreboard")

    seen_members: dict[str, str] = {}
    for board, spec in boards.items():
        for member in spec.get("members", []):
            if member in seen_members:
                errors.append(f"{member}: listed in both {seen_members[member]} and {board}")
            seen_members[member] = board
            if member not in owner_of:
                errors.append(f"{board}: member {member!r} is not a registered dataset or planned resource")
            elif owner_of[member] != board:
                errors.append(f"{member}: declares scoreboard {owner_of[member]!r} but is listed under {board!r}")
    for rid, board in owner_of.items():
        if board not in boards:
            errors.append(f"{rid}: unknown scoreboard {board!r}")
        elif rid not in seen_members:
            errors.append(f"{rid}: not listed as a member of {board!r}")
    if errors:
        raise ContractError("; ".join(errors))


def load_thai_contract(path: Path | str = REGISTRY_PATH) -> dict:
    """Load the registry, validate the G02 contract and the P3-T01 Thai contract, return the registry."""
    reg = load_registry(path)
    validate_thai_contract(reg)
    return reg


def _lookup(resource_id: str, registry: dict) -> tuple[str, dict, dict | None]:
    """Return (kind, contract, dataset) where kind is 'dataset' or 'planned'."""
    for ds in registry.get("datasets", []):
        if ds.get("dataset_id") == resource_id and isinstance(ds.get("thai_contract"), dict):
            return "dataset", ds["thai_contract"], ds
    for res in registry.get("thai_contract", {}).get("planned_resources", []):
        if res.get("resource_id") == resource_id:
            return "planned", res, None
    raise KeyError(f"{resource_id!r} is not a Thai resource in the contract")


def thai_resource_ids(registry: dict | None = None) -> list[str]:
    reg = registry or load_thai_contract()
    ids = [d["dataset_id"] for d in reg["datasets"] if isinstance(d.get("thai_contract"), dict)]
    return ids + [r["resource_id"] for r in reg["thai_contract"].get("planned_resources", [])]


def scoreboard_of(resource_id: str, registry: dict | None = None) -> str:
    reg = registry or load_thai_contract()
    return _lookup(resource_id, reg)[1]["scoreboard"]


def assert_single_scoreboard(rows: Iterable[dict], registry: dict | None = None) -> str:
    """Check that every result row belongs to one scoreboard; return it.

    Each row names its resource in ``dataset_id`` and may also state ``scoreboard`` and ``setting``. A stated
    scoreboard must match the resource's contract. A NitiBench+ row's setting must be a native named setting.
    """
    reg = registry or load_thai_contract()
    boards: set[str] = set()
    for i, row in enumerate(rows):
        rid = row.get("dataset_id")
        try:
            kind, contract, ds = _lookup(rid, reg)
        except KeyError as exc:
            raise ScoreboardMixError(f"row {i}: {exc}") from None
        board = contract["scoreboard"]
        stated = row.get("scoreboard")
        if stated is not None and stated != board:
            raise ScoreboardMixError(f"row {i}: {rid} belongs to {board!r}, not {stated!r}")
        setting = row.get("setting")
        if ds is not None and setting is not None and ds.get("allowed_named_settings") is not None:
            if setting not in ds["allowed_named_settings"]:
                raise ScoreboardMixError(f"row {i}: setting {setting!r} is not a native named setting of {rid}")
        boards.add(board)
    if not boards:
        raise ValueError("no result rows")
    if len(boards) > 1:
        raise ScoreboardMixError(f"one table mixes scoreboards {sorted(boards)}; report each in its own table")
    return boards.pop()


def permitted_use(resource_id: str, purpose: str, registry: dict | None = None) -> UseDecision:
    """What an agent may do with a Thai resource under the current registry (no side effects)."""
    if purpose not in PURPOSES:
        raise ValueError(f"unknown purpose {purpose!r}; known: {PURPOSES}")
    reg = registry or load_thai_contract()
    kind, contract, ds = _lookup(resource_id, reg)

    def decide(allowed: bool, reason: str) -> UseDecision:
        return UseDecision(resource_id, purpose, allowed, reason)

    if purpose == "metadata_read":
        return decide(True, "public card/API metadata only; record any auto-previewed rows as exposure")
    if purpose == "synthetic_fixture":
        return decide(True, "fictional rows imitating column names only; never copy native rows or card examples")
    if purpose == "gate_acceptance":
        return decide(False, "owner action only: the agent never accepts access conditions or terms")
    if purpose == "product_bundle":
        ok = contract.get("rights", {}).get("redistribution_in_product") is True
        return decide(ok, "rights allow product redistribution" if ok else
                      "research data ships separately from the product; adapter support is not bundling")

    if kind == "planned":
        if contract.get("status") != "COLLECTED":
            return decide(False, f"{contract.get('status')}: nothing collected; " + _blocked_summary(contract))
        if purpose == "download":
            return decide(False, "each new source needs its own per-item owner approval in the packet manifest")
        if purpose in ("development", "method_selection"):
            return decide(True, "development families only: " + str(contract.get("development_use")))
        if purpose == "training":
            return decide(False, "training on packets is not part of the contract")
        return decide(True, "held-out families only, with judgments isolated from policy design")

    gated = is_gated_or_private(ds)
    approval = contract.get("download_approval")
    if purpose == "download":
        if gated:
            return decide(False, "gated: owner acceptance not recorded")
        if approval is None:
            return decide(False, "no per-item owner download approval recorded")
        return decide(True, f"approved by {approval['approved_by']} on {approval['date']} for {approval['scope']}")
    if purpose in ("development", "method_selection", "training"):
        return decide(False, str(contract.get("development_use")))
    # held_out_evaluation
    if gated:
        return decide(False, "gated: owner acceptance not recorded")
    if approval is None:
        return decide(False, "data not downloaded: no per-item owner download approval recorded")
    return decide(True, "frozen method only; report as " + str(contract.get("held_out_use")))


def _blocked_summary(entry: dict) -> str:
    return "blocked: " + "; ".join(f"{b['kind']} ({b['item']})" for b in entry.get("blocked_pending_owner", []))
