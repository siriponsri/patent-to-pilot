"""Run leave-one-company-out sensitivity on the frozen HealthTech cohort."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
COMPOSE_SCRIPT = ROOT / "scripts" / "healthtech" / "compose_multicompany_cohort.py"
BASELINE_SCRIPT = ROOT / "scripts" / "healthtech" / "run_real_baselines.py"
DEFAULT_HOLDOUTS = (
    "BOSTON SCIENTIFIC CORP",
    "STRYKER NEUROVASCULAR",
    "Cook Medical",
    "PHILIPS IMAGE GUIDED THERAPY",
)


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _repo_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path.resolve())


def _record_command(command: list[str], paths: Iterable[Path]) -> list[str]:
    replacements = {str(path): _repo_path(path) for path in paths}
    replacements[str(COMPOSE_SCRIPT)] = _repo_path(COMPOSE_SCRIPT)
    replacements[str(BASELINE_SCRIPT)] = _repo_path(BASELINE_SCRIPT)
    recorded: list[str] = []
    for value in command:
        if value == sys.executable:
            recorded.append("python")
            continue
        if value in replacements:
            recorded.append(replacements[value])
            continue
        embedded = next(
            (f"{value[:value.index('=') + 1]}{replacement}"
             for path, replacement in replacements.items()
             if value.startswith(path + "=")),
            None,
        )
        recorded.append(embedded or value)
    return recorded


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
    if not slug:
        raise ValueError(f"holdout company has no usable slug: {value!r}")
    return slug


def _parse_additional_cohort(value: str) -> tuple[str, Path]:
    alias, separator, raw_path = value.partition("=")
    alias = alias.strip()
    raw_path = raw_path.strip()
    if not separator or not alias or not raw_path:
        raise ValueError("additional cohorts must use ALIAS=PATH")
    return alias, Path(raw_path).resolve()


def build_compose_command(
    *,
    boston_cohort: Path,
    stryker_cohort: Path,
    additional_cohorts: Iterable[tuple[str, Path]],
    holdout_company: str,
    family_mapping: Path | None,
    output: Path,
) -> list[str]:
    command = [
        sys.executable,
        str(COMPOSE_SCRIPT),
        "--boston-cohort",
        str(boston_cohort),
        "--stryker-cohort",
        str(stryker_cohort),
        "--holdout-company",
        holdout_company,
        "--output",
        str(output),
    ]
    for alias, path in additional_cohorts:
        command.extend(["--additional-cohort", f"{alias}={path}"])
    if family_mapping is not None:
        command.extend(["--family-mapping", str(family_mapping)])
    return command


def build_baseline_command(
    *,
    runtime: Path,
    references: Path,
    groups: Path,
    model_root: Path,
    output: Path,
    code_commit: str,
    protocol_hash: str,
    cohort_manifest_hash: str,
    candidate_depth: int,
    rerank_depth: int,
) -> list[str]:
    return [
        sys.executable,
        str(BASELINE_SCRIPT),
        "--runtime",
        str(runtime),
        "--references",
        str(references),
        "--groups",
        str(groups),
        "--model-root",
        str(model_root),
        "--output",
        str(output),
        "--code-commit",
        code_commit,
        "--protocol-hash",
        protocol_hash,
        "--cohort-manifest-hash",
        cohort_manifest_hash,
        "--candidate-depth",
        str(candidate_depth),
        "--rerank-depth",
        str(rerank_depth),
    ]


def _directory_bytes(root: Path) -> int:
    return sum(path.stat().st_size for path in root.rglob("*") if path.is_file())


def _run(command: list[str]) -> None:
    subprocess.run(command, cwd=ROOT, check=True)


def summarize_baseline(output: Path) -> dict[str, Any]:
    receipt_path = output / "receipt.json"
    frontier_path = output / "frontier_diagnostics.json"
    receipt = _read_json(receipt_path)
    frontier = _read_json(frontier_path)
    by_method = frontier.get("by_method")
    if not isinstance(by_method, dict):
        raise ValueError(f"baseline frontier lacks by_method: {frontier_path}")
    metrics: dict[str, dict[str, Any]] = {}
    for method, row in sorted(by_method.items()):
        if not isinstance(row, dict):
            raise ValueError(f"baseline method row is invalid: {method}")
        metrics[str(method)] = {
            "macro_known_link_recall_at_20": row.get("macro_known_link_recall_at_20"),
            "failed_device_count": row.get("failed_device_count"),
            "query_calls": row.get("query_calls"),
            "rerank_pairs": row.get("rerank_pairs"),
            "returned_candidates": row.get("returned_candidates"),
        }
    return {
        "status": receipt.get("status"),
        "devices": receipt.get("devices"),
        "patents": receipt.get("patents"),
        "reference_pairs": receipt.get("reference_pairs"),
        "provider_calls": receipt.get("provider_calls"),
        "paid_cost_usd": receipt.get("paid_cost_usd"),
        "receipt_sha256": _sha256(receipt_path),
        "frontier_sha256": _sha256(frontier_path),
        "metrics": metrics,
    }


def run_sensitivity(
    *,
    boston_cohort: Path,
    stryker_cohort: Path,
    additional_cohorts: list[tuple[str, Path]],
    holdouts: list[str],
    family_mapping: Path | None,
    model_root: Path,
    output: Path,
    code_commit: str,
    protocol_hash: str,
    candidate_depth: int,
    rerank_depth: int,
    max_output_bytes: int,
) -> dict[str, Any]:
    if output.exists():
        raise ValueError(f"output already exists; choose a fresh directory: {output}")
    if not holdouts:
        raise ValueError("at least one holdout company is required")
    if len({_slug(value) for value in holdouts}) != len(holdouts):
        raise ValueError("holdout company slugs must be unique")
    for path in [boston_cohort, stryker_cohort, model_root, *[item[1] for item in additional_cohorts]]:
        if not path.exists():
            raise FileNotFoundError(path)
    if family_mapping is not None and not family_mapping.exists():
        raise FileNotFoundError(family_mapping)
    if candidate_depth < 1 or rerank_depth < 1 or max_output_bytes < 1:
        raise ValueError("depths and max_output_bytes must be positive")

    output = output.resolve()
    output.mkdir(parents=True)
    commands: list[dict[str, Any]] = []
    runs: list[dict[str, Any]] = []
    for holdout_company in holdouts:
        slug = _slug(holdout_company)
        run_root = output / slug
        cohort_root = run_root / "cohort"
        compose_command = build_compose_command(
            boston_cohort=boston_cohort,
            stryker_cohort=stryker_cohort,
            additional_cohorts=additional_cohorts,
            holdout_company=holdout_company,
            family_mapping=family_mapping,
            output=cohort_root,
        )
        _run(compose_command)
        commands.append({
            "kind": "compose",
            "holdout_company": holdout_company,
            "argv": _record_command(
                compose_command,
                [boston_cohort, stryker_cohort, *[item[1] for item in additional_cohorts], output, cohort_root, family_mapping] if family_mapping is not None else [boston_cohort, stryker_cohort, *[item[1] for item in additional_cohorts], output, cohort_root],
            ),
        })
        manifest_path = cohort_root / "manifest.json"
        manifest = _read_json(manifest_path)
        manifest_hash = _sha256(manifest_path)
        split_summaries: dict[str, Any] = {}
        for split in ("development", "final_holdout"):
            view_root = cohort_root / "views" / split
            baseline_root = run_root / "baselines" / split
            baseline_command = build_baseline_command(
                runtime=view_root / "runtime.json",
                references=view_root / "references.json",
                groups=view_root / "groups.json",
                model_root=model_root,
                output=baseline_root,
                code_commit=code_commit,
                protocol_hash=protocol_hash,
                cohort_manifest_hash=manifest_hash,
                candidate_depth=candidate_depth,
                rerank_depth=rerank_depth,
            )
            _run(baseline_command)
            commands.append({
                "kind": "baseline",
                "holdout_company": holdout_company,
                "split": split,
                "argv": _record_command(
                    baseline_command,
                    [view_root / "runtime.json", view_root / "references.json", view_root / "groups.json", model_root, baseline_root],
                ),
            })
            split_summaries[split] = summarize_baseline(baseline_root)
        runs.append({
            "holdout_company": holdout_company,
            "slug": slug,
            "cohort_manifest_sha256": manifest_hash,
            "cohort_status": manifest.get("status"),
            "development_query_count": len(manifest.get("development_query_ids", [])),
            "final_holdout_query_count": len(manifest.get("final_holdout_query_ids", [])),
            "final_holdout_company_groups": manifest.get("final_holdout_company_groups", []),
            "family_group_count": manifest.get("family_group_count"),
            "splits": split_summaries,
        })
        if _directory_bytes(run_root) > max_output_bytes:
            raise ValueError(f"output cap exceeded after {holdout_company}: {max_output_bytes} bytes")

    summary = {
        "format": "ht-company-holdout-sensitivity-v1",
        "status": "PASS_OFFLINE_COMPANY_HOLDOUT_SENSITIVITY",
        "code_commit": code_commit,
        "protocol_hash": protocol_hash,
        "model_root": _repo_path(model_root),
        "candidate_depth": candidate_depth,
        "rerank_depth": rerank_depth,
        "holdout_count": len(runs),
        "holdouts": runs,
        "commands": commands,
        "provider_calls": 0,
        "paid_cost_usd": 0,
        "limitations": [
            "Product-level disclosure relationships are known-link proxies, not semantic relevance gold.",
            "Leave-one-company-out rows reuse the same four local cohorts and are sensitivity analyses, not independent samples.",
            "Unlisted device-patent pairs remain unjudged and are never recoded as negatives.",
            "No live/provider HT-B4 call or external payload was used.",
        ],
    }
    _write_json(output / "summary.json", summary)
    _write_json(output / "commands.json", {"format": "ht-command-log-v1", "commands": commands})
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--boston-cohort", type=Path, required=True)
    parser.add_argument("--stryker-cohort", type=Path, required=True)
    parser.add_argument("--additional-cohort", action="append", default=[], help="ALIAS=PATH; repeatable")
    parser.add_argument("--holdout-company", action="append", dest="holdouts", default=None, help="repeatable; defaults to all four frozen company names")
    parser.add_argument("--family-mapping", type=Path)
    parser.add_argument("--model-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--code-commit", required=True)
    parser.add_argument("--protocol-hash", required=True)
    parser.add_argument("--candidate-depth", type=int, default=31)
    parser.add_argument("--rerank-depth", type=int, default=31)
    parser.add_argument("--max-output-bytes", type=int, default=600_000_000)
    args = parser.parse_args()
    additional = [_parse_additional_cohort(value) for value in args.additional_cohort]
    summary = run_sensitivity(
        boston_cohort=args.boston_cohort.resolve(),
        stryker_cohort=args.stryker_cohort.resolve(),
        additional_cohorts=additional,
        holdouts=list(args.holdouts or DEFAULT_HOLDOUTS),
        family_mapping=args.family_mapping.resolve() if args.family_mapping else None,
        model_root=args.model_root.resolve(),
        output=args.output,
        code_commit=args.code_commit,
        protocol_hash=args.protocol_hash,
        candidate_depth=args.candidate_depth,
        rerank_depth=args.rerank_depth,
        max_output_bytes=args.max_output_bytes,
    )
    print(json.dumps({
        "status": summary["status"],
        "output": str(args.output.resolve()),
        "holdouts": [row["holdout_company"] for row in summary["holdouts"]],
        "provider_calls": 0,
        "paid_cost_usd": 0,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
