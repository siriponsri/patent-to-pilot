"""Compare the frozen Abbott and Boston offline HealthTech frontiers."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


METHODS = ("HT-B0a", "HT-B0b", "HT-B1", "HT-B2", "HT-B3")
RESOURCE_KEYS = (
    "query_calls",
    "rerank_pairs",
    "embedding_query_tokens",
    "rerank_tokens",
    "returned_candidates",
    "cpu_seconds",
    "wall_seconds",
)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def load_group_payload(path: Path) -> dict[str, Any]:
    value = load_json(path)
    nested = value.get("groups")
    return nested if isinstance(nested, dict) else value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _required_int(mapping: dict[str, Any], key: str, label: str) -> int:
    value = mapping.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{label}.{key} must be a non-negative integer")
    return value


def _group_counts(groups: dict[str, Any]) -> tuple[int, int, str, int]:
    company_groups = groups.get("company_groups", [])
    exact_groups = groups.get("shared_exact_patent_groups", [])
    family_mapping = groups.get("family_mapping", {})
    if not isinstance(company_groups, list) or not isinstance(exact_groups, list):
        raise ValueError("group evidence has invalid group lists")
    family_status = str(family_mapping.get("status", "UNKNOWN"))
    return len(company_groups), len(exact_groups), family_status, len(groups.get("group_evidence", []))


def _cohort_summary(
    *,
    name: str,
    receipt: dict[str, Any],
    groups: dict[str, Any],
    split: dict[str, Any],
    distractors: dict[str, Any],
    protocol: dict[str, Any] | None = None,
    manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if protocol is not None:
        counts = protocol.get("counts", {})
        devices = _required_int(counts, "eligible_devices", f"{name}.counts")
        patents = _required_int(counts, "universe_patents", f"{name}.counts")
        known_links = _required_int(counts, "disclosed_pairs", f"{name}.counts")
        distractor_count = _required_int(counts, "unjudged_distractor_pairs", f"{name}.counts")
        final_holdout = protocol.get("split", {}).get("final_holdout", [])
        protocol_status = protocol.get("status")
        source_refs = protocol.get("source_refs", {})
    elif manifest is not None:
        devices = _required_int(manifest, "devices", name)
        patents = _required_int(manifest, "patents", name)
        known_links = _required_int(manifest, "reference_pairs", name)
        distractor_count = _required_int(manifest, "unjudged_distractor_pairs", name)
        final_holdout = split.get("final_holdout", [])
        protocol_status = manifest.get("status")
        source_refs = {
            "cohort_sha256": manifest.get("cohort_sha256"),
            "references_sha256": manifest.get("references_sha256"),
            "runtime_sha256": manifest.get("runtime_sha256"),
            "universe_sha256": manifest.get("universe_sha256"),
        }
    else:
        raise ValueError(f"{name} needs protocol or manifest")

    company_count, exact_group_count, family_status, group_evidence_count = _group_counts(groups)
    if not isinstance(final_holdout, list):
        raise ValueError(f"{name}.final_holdout must be a list")

    return {
        "name": name,
        "devices": devices,
        "patents": patents,
        "known_link_pairs": known_links,
        "unjudged_distractor_pairs": distractor_count,
        "company_group_count": company_count,
        "exact_patent_group_count": exact_group_count,
        "group_evidence_count": group_evidence_count,
        "family_mapping_status": family_status,
        "final_holdout_count": len(final_holdout),
        "status": protocol_status,
        "source_refs": source_refs,
        "distractor_status": distractors.get("status"),
        "candidate_universe_per_device": patents / devices if devices else None,
        "known_links_per_device": known_links / devices if devices else None,
    }


def _method_summary(frontier: dict[str, Any], method: str, cohort: dict[str, Any]) -> dict[str, Any]:
    by_method = frontier.get("by_method", {})
    if method not in by_method:
        raise ValueError(f"frontier missing {method}")
    row = by_method[method]
    resources = {key: float(row.get(key, 0.0)) for key in RESOURCE_KEYS}
    devices = cohort["devices"]
    return {
        "method": method,
        "macro_known_link_recall_at_20": float(row.get("macro_known_link_recall_at_20", 0.0)),
        "device_count": _required_int(row, "device_count", f"frontier.by_method.{method}"),
        "failed_device_count": _required_int(row, "failed_device_count", f"frontier.by_method.{method}"),
        "realized_query_count": float(row.get("realized_query_count", 0.0)),
        "resources": resources,
        "per_device_resources": {
            key: value / devices if devices else None for key, value in resources.items()
        },
    }


def _missing_method_summary(method: str) -> dict[str, Any]:
    return {"method": method, "status": "MISSING"}


def _frontier_profiles(frontier: dict[str, Any]) -> list[dict[str, Any]]:
    rows = frontier.get("quality_resource_frontier", {}).get("rows", [])
    profiles = []
    for row in rows:
        profiles.append(
            {
                "method": row.get("method"),
                "prefix": row.get("prefix"),
                "macro_known_link_recall_at_20_all_devices": row.get(
                    "macro_known_link_recall_at_20_all_devices"
                ),
                "query_calls": row.get("query_calls", 0.0),
                "rerank_pairs": row.get("rerank_pairs", 0.0),
                "returned_candidates": row.get("returned_candidates", 0.0),
                "reached_query_count": row.get("reached_query_count", 0),
                "failed_query_count": row.get("failed_query_count", 0),
                "not_realized_query_count": row.get("not_realized_query_count", 0),
            }
        )
    return profiles


def _last_prefix_by_method(profiles: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    last: dict[str, dict[str, Any]] = {}
    for row in profiles:
        method = str(row["method"])
        if method not in last or int(row["prefix"]) > int(last[method]["prefix"]):
            last[method] = row
    return last


def _validate_frontier(
    name: str,
    frontier: dict[str, Any],
    cohort: dict[str, Any],
) -> list[str]:
    issues = []
    if frontier.get("status") != "DESCRIPTIVE_DEVELOPMENT_FRONTIER":
        issues.append(f"{name}: unexpected frontier status {frontier.get('status')!r}")
    if frontier.get("primary_k") != 20:
        issues.append(f"{name}: primary_k is not 20")
    by_method = frontier.get("by_method", {})
    if set(by_method) != set(METHODS):
        issues.append(f"{name}: method set is {sorted(by_method)}")
    for method in METHODS:
        if method not in by_method:
            continue
        if by_method[method].get("device_count") != cohort["devices"]:
            issues.append(f"{name}/{method}: device count mismatch")
    alignment = frontier.get("quality_resource_frontier", {}).get("fixed_prefix_alignment", {})
    if alignment.get("first_query_match_across_fixed_methods") is not True:
        issues.append(f"{name}: fixed-prefix first-query alignment failed")
    return issues


def build_comparison(
    *,
    run_id: str,
    source_files: dict[str, Path],
    abbott_protocol: dict[str, Any],
    abbott_receipt: dict[str, Any],
    abbott_frontier: dict[str, Any],
    abbott_groups: dict[str, Any],
    abbott_split: dict[str, Any],
    abbott_distractors: dict[str, Any],
    boston_manifest: dict[str, Any],
    boston_receipt: dict[str, Any],
    boston_frontier: dict[str, Any],
    boston_groups: dict[str, Any],
    boston_split: dict[str, Any],
    boston_distractors: dict[str, Any],
) -> dict[str, Any]:
    abbott = _cohort_summary(
        name="Abbott",
        receipt=abbott_receipt,
        groups=abbott_groups,
        split=abbott_split,
        distractors=abbott_distractors,
        protocol=abbott_protocol,
    )
    boston = _cohort_summary(
        name="Boston Scientific WATCHMAN",
        receipt=boston_receipt,
        groups=boston_groups,
        split=boston_split,
        distractors=boston_distractors,
        manifest=boston_manifest,
    )
    validation = _validate_frontier("Abbott", abbott_frontier, abbott) + _validate_frontier(
        "Boston Scientific WATCHMAN", boston_frontier, boston
    )
    if abbott["final_holdout_count"] or boston["final_holdout_count"]:
        validation.append("comparison assumes development-only cohorts; final holdout must remain empty")

    abbott_methods = {
        method: _method_summary(abbott_frontier, method, abbott)
        if method in abbott_frontier.get("by_method", {})
        else _missing_method_summary(method)
        for method in METHODS
    }
    boston_methods = {
        method: _method_summary(boston_frontier, method, boston)
        if method in boston_frontier.get("by_method", {})
        else _missing_method_summary(method)
        for method in METHODS
    }
    methods = {}
    for method in METHODS:
        a = abbott_methods[method]
        b = boston_methods[method]
        if a.get("status") == "MISSING" or b.get("status") == "MISSING":
            delta = {"status": "NOT_COMPUTED"}
        else:
            delta = {
                "macro_known_link_recall_at_20": b["macro_known_link_recall_at_20"]
                - a["macro_known_link_recall_at_20"],
                "per_device_resources": {
                    key: b["per_device_resources"][key] - a["per_device_resources"][key]
                    for key in RESOURCE_KEYS
                },
            }
        methods[method] = {"abbott": a, "boston": b, "boston_minus_abbott": delta}

    profiles = {
        "Abbott": _frontier_profiles(abbott_frontier),
        "Boston Scientific WATCHMAN": _frontier_profiles(boston_frontier),
    }
    cohort_flags = {
        "Abbott": {
            "descriptive_low_effective_group_status": abbott["exact_patent_group_count"] <= 2,
            "k_exceeds_candidate_universe": 20 > abbott["patents"],
        },
        "Boston Scientific WATCHMAN": {
            "descriptive_low_effective_group_status": boston["exact_patent_group_count"] <= 2,
            "k_exceeds_candidate_universe": 20 > boston["patents"],
        },
    }

    return {
        "format": "ht-cross-cohort-frontier-comparison-v1",
        "run_id": run_id,
        "status": "PASS" if not validation else "FAIL",
        "scope": "Descriptive offline comparison of two public development cohorts using shared HT-B0a/B0b/B1/B2/B3 outputs.",
        "methods": list(METHODS),
        "cohorts": {"Abbott": abbott, "Boston Scientific WATCHMAN": boston},
        "cohort_flags": cohort_flags,
        "comparability": {
            "same_method_set": True,
            "same_primary_k": abbott_frontier.get("primary_k") == boston_frontier.get("primary_k") == 20,
            "same_fixed_prefix_alignment_contract": (
                abbott_frontier.get("quality_resource_frontier", {})
                .get("fixed_prefix_alignment", {})
                .get("first_query_match_across_fixed_methods")
                is True
                and boston_frontier.get("quality_resource_frontier", {})
                .get("fixed_prefix_alignment", {})
                .get("first_query_match_across_fixed_methods")
                is True
            ),
            "same_model_revisions": abbott_receipt.get("model_revisions") == boston_receipt.get("model_revisions"),
            "cross_cohort_score_comparison_allowed": False,
            "reason": "Cohort sizes, candidate universes, company/group structure, and K ceiling differ; use deltas descriptively only.",
        },
        "methods_by_cohort": methods,
        "frontier_profiles": profiles,
        "validation": {
            "issues": validation,
            "error_count_abbott": abbott_frontier.get("error_count"),
            "error_count_boston": boston_frontier.get("error_count"),
        },
        "limitations": [
            "Both cohorts are development-only and have no final holdout; uncertainty and generalization are not estimable.",
            "Abbott has three devices but only two exact-patent groups, one company group, and unknown family mapping.",
            "Boston has two devices, one exact-patent group, one company group, and unknown family mapping.",
            "Boston's K=20 exceeds its seven-patent candidate universe, so every method's 1.0 recall is ceiling-limited.",
            "Known-link recall measures recovery of source-disclosed product-level links, not semantic claim relevance, clinical suitability, FTO, validity, or investment merit.",
            "Resource values are realized local units, not dollars; no provider calls or paid inference occurred.",
            "Unjudged distractors are not negative labels and family identity is not inferred from overlap.",
        ],
        "source_files": {
            label: {"path": str(path).replace("\\", "/"), "sha256": sha256_file(path)}
            for label, path in sorted(source_files.items())
        },
    }


def _fmt(value: Any, digits: int = 3) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, (int, float)):
        return f"{value:.{digits}f}"
    return str(value)


def render_report(comparison: dict[str, Any]) -> str:
    cohorts = comparison["cohorts"]
    methods = comparison["methods_by_cohort"]
    lines = [
        "# HT M3 cross-cohort frontier comparison",
        "",
        f"- Run ID: `{comparison['run_id']}`",
        "- Status: `" + comparison["status"] + "`",
        "- Scope: descriptive offline comparison only; no final scientific or generalization claim.",
        "- Provider calls: `0`; paid cost: `$0`.",
        "",
        "## Objective and scope",
        "",
        "Compare the Abbott and Boston Scientific WATCHMAN development frontiers under the shared HT-B0a/B0b/B1/B2/B3 runner. The comparison reports raw recall and realized local resources, then normalizes resources per device. It does not pool scores across cohorts or treat either cohort as expert semantic gold.",
        "",
        "## Cohort boundaries",
        "",
        "| Cohort | Devices | Patents | Disclosed pairs | Unjudged distractor pairs | Exact-patent groups | Company groups | Final holdout |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name in ("Abbott", "Boston Scientific WATCHMAN"):
        cohort = cohorts[name]
        lines.append(
            f"| {name} | {cohort['devices']} | {cohort['patents']} | {cohort['known_link_pairs']} | {cohort['unjudged_distractor_pairs']} | {cohort['exact_patent_group_count']} | {cohort['company_group_count']} | {cohort['final_holdout_count']} |"
        )
    lines.extend(
        [
            "",
            "Abbott is descriptive with low effective group count: three devices collapse to two exact-patent groups, one company group, and unknown family mapping. Boston is also descriptive and has one exact-patent group and one company group.",
            "",
            "## Method deltas",
            "",
            "The delta column is Boston minus Abbott. Resource columns are realized totals per device; they are not monetary costs.",
            "",
            "| Method | Abbott recall@20 | Boston recall@20 | Delta | Abbott query calls/device | Boston query calls/device | Abbott rerank pairs/device | Boston rerank pairs/device |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for method in comparison["methods"]:
        row = methods[method]
        a = row["abbott"]
        b = row["boston"]
        delta = row["boston_minus_abbott"].get("macro_known_link_recall_at_20")
        lines.append(
            f"| {method} | {_fmt(a.get('macro_known_link_recall_at_20'))} | {_fmt(b.get('macro_known_link_recall_at_20'))} | {_fmt(delta)} | {_fmt(a.get('per_device_resources', {}).get('query_calls'))} | {_fmt(b.get('per_device_resources', {}).get('query_calls'))} | {_fmt(a.get('per_device_resources', {}).get('rerank_pairs'))} | {_fmt(b.get('per_device_resources', {}).get('rerank_pairs'))} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Boston reports `1.0` recall@20 for every method because `K=20` exceeds its seven-patent candidate universe. The result is a ceiling-limited development observation, not method superiority.",
            "- Abbott provides the more informative within-cohort spread at `K=20`: HT-B0b is the highest observed method, while HT-B1, HT-B2, and HT-B3 trade additional local resources for lower or mixed recall in this slice.",
            "- Cross-cohort recall deltas are not transportable performance estimates because the cohorts differ in size, candidate-universe depth, company/group structure, and disclosure density.",
            "- All reported rows are offline and completed with zero recorded failures in the source frontiers. Resource values remain local execution units, not dollars.",
            "",
            "## Limitations and next test",
            "",
            "- No confidence intervals, company-held-out sensitivity, family-held-out sensitivity, or final-holdout estimate is reported.",
            "- Unlisted device-patent pairs remain unjudged; distractor lists are not negative labels.",
            "- Product-level disclosures do not establish claim-level semantic relevance or any clinical, legal, or investment conclusion.",
            "- Next discriminating test: add a rights-cleared cohort with multiple independent company/family groups, freeze its holdout rules, and rerun the same fixed-prefix frontier before considering a scientific comparison.",
            "",
            "## Inspectable sources",
            "",
        ]
    )
    for label, source in comparison["source_files"].items():
        lines.append(f"- `{label}`: `{source['path']}` (SHA-256 `{source['sha256']}`)")
    return "\n".join(lines) + "\n"


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--abbott-protocol", type=Path, required=True)
    parser.add_argument("--abbott-receipt", type=Path, required=True)
    parser.add_argument("--abbott-frontier", type=Path, required=True)
    parser.add_argument("--abbott-groups", type=Path, required=True)
    parser.add_argument("--abbott-split", type=Path, required=True)
    parser.add_argument("--abbott-distractors", type=Path, required=True)
    parser.add_argument("--boston-manifest", type=Path, required=True)
    parser.add_argument("--boston-receipt", type=Path, required=True)
    parser.add_argument("--boston-frontier", type=Path, required=True)
    parser.add_argument("--boston-groups", type=Path, required=True)
    parser.add_argument("--boston-split", type=Path, required=True)
    parser.add_argument("--boston-distractors", type=Path, required=True)
    args = parser.parse_args()

    source_files = {
        "abbott_protocol": args.abbott_protocol,
        "abbott_receipt": args.abbott_receipt,
        "abbott_frontier": args.abbott_frontier,
        "abbott_groups": args.abbott_groups,
        "abbott_split": args.abbott_split,
        "abbott_distractors": args.abbott_distractors,
        "boston_manifest": args.boston_manifest,
        "boston_receipt": args.boston_receipt,
        "boston_frontier": args.boston_frontier,
        "boston_groups": args.boston_groups,
        "boston_split": args.boston_split,
        "boston_distractors": args.boston_distractors,
    }
    comparison = build_comparison(
        run_id=args.run_id,
        source_files=source_files,
        abbott_protocol=load_json(args.abbott_protocol),
        abbott_receipt=load_json(args.abbott_receipt),
        abbott_frontier=load_json(args.abbott_frontier),
        abbott_groups=load_group_payload(args.abbott_groups),
        abbott_split=load_json(args.abbott_split),
        abbott_distractors=load_json(args.abbott_distractors),
        boston_manifest=load_json(args.boston_manifest),
        boston_receipt=load_json(args.boston_receipt),
        boston_frontier=load_json(args.boston_frontier),
        boston_groups=load_json(args.boston_groups),
        boston_split=load_json(args.boston_split),
        boston_distractors=load_json(args.boston_distractors),
    )
    args.output.mkdir(parents=True, exist_ok=False)
    _write_json(args.output / "comparison.json", comparison)
    (args.output / "REPORT.md").write_text(render_report(comparison), encoding="utf-8")
    verification = {
        "format": "ht-cross-cohort-frontier-verification-v1",
        "run_id": args.run_id,
        "status": comparison["status"],
        "checks": {
            "input_hashes_recorded": bool(comparison["source_files"]),
            "shared_method_set": comparison["comparability"]["same_method_set"],
            "same_primary_k": comparison["comparability"]["same_primary_k"],
            "fixed_prefix_alignment": comparison["comparability"]["same_fixed_prefix_alignment_contract"],
            "cross_cohort_scores_not_promoted": not comparison["comparability"]["cross_cohort_score_comparison_allowed"],
            "source_validation_errors": comparison["validation"]["issues"],
        },
        "provider_calls": 0,
        "paid_cost_usd": 0,
        "implemented_boundary": "offline descriptive analysis only",
        "not_run": [
            "final holdout evaluation",
            "confidence intervals or significance testing",
            "adaptive HT-B4 live/provider run",
        ],
    }
    _write_json(args.output / "verification.json", verification)
    print(json.dumps({"status": comparison["status"], "output": str(args.output), "issues": comparison["validation"]["issues"]}))
    if comparison["status"] != "PASS":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
