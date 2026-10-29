"""Build descriptive quality-resource analysis and deterministic SVG plots."""
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
from pathlib import Path
from typing import Any


METHODS = ("HT-B0a", "HT-B0b", "HT-B1", "HT-B2", "HT-B3")
COLORS = {
    "HT-B0a": "#4c78a8",
    "HT-B0b": "#f58518",
    "HT-B1": "#54a24b",
    "HT-B2": "#e45756",
    "HT-B3": "#b279a2",
}


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _group_stats(frontier: dict[str, Any]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[float]] = {method: [] for method in METHODS}
    for row in frontier.get("groups", []):
        if not isinstance(row, dict) or row.get("k") != 20:
            continue
        method = row.get("method")
        value = row.get("macro_known_link_recall")
        if method in grouped and isinstance(value, (int, float)):
            grouped[method].append(float(value))
    result: dict[str, dict[str, Any]] = {}
    for method in METHODS:
        values = grouped[method]
        result[method] = {
            "group_count": len(values),
            "group_macro_known_link_recall_values": values,
            "group_macro_known_link_recall_min": min(values) if values else None,
            "group_macro_known_link_recall_max": max(values) if values else None,
            "group_macro_known_link_recall_range": (max(values) - min(values)) if values else None,
        }
    return result


def _enrich_rows(
    rows: list[dict[str, Any]],
    group_stats: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    enriched: list[dict[str, Any]] = []
    for row in rows:
        method = row["method"]
        stats = group_stats[method]
        enriched.append(
            {
                **row,
                **stats,
                "status": "DESCRIPTIVE_NOT_ESTIMABLE",
            }
        )
    return enriched


def _pareto_frontier(rows: list[dict[str, Any]]) -> list[str]:
    frontier: list[str] = []
    for candidate in rows:
        dominated = False
        for other in rows:
            if other["method"] == candidate["method"]:
                continue
            quality_better_or_equal = other["macro_known_link_recall_at_20"] >= candidate[
                "macro_known_link_recall_at_20"
            ]
            resource_better_or_equal = other["wall_seconds"] <= candidate["wall_seconds"]
            one_strict = (
                other["macro_known_link_recall_at_20"] > candidate["macro_known_link_recall_at_20"]
                or other["wall_seconds"] < candidate["wall_seconds"]
            )
            if quality_better_or_equal and resource_better_or_equal and one_strict:
                dominated = True
                break
        if not dominated:
            frontier.append(candidate["method"])
    return frontier


def build_analysis(
    *,
    summary: dict[str, Any],
    dev_frontier: dict[str, Any],
    holdout_frontier: dict[str, Any],
    input_hashes: dict[str, str] | None = None,
    code_commit: str | None = None,
) -> dict[str, Any]:
    development_rows = _enrich_rows(
        summary["development"]["rows"], _group_stats(dev_frontier)
    )
    holdout_rows = _enrich_rows(
        summary["final_holdout"]["rows"], _group_stats(holdout_frontier)
    )
    dev_by_method = {row["method"]: row for row in development_rows}
    holdout_by_method = {row["method"]: row for row in holdout_rows}
    holdout_minus_development = []
    for method in METHODS:
        holdout_minus_development.append(
            {
                "method": method,
                "macro_recall_delta_holdout_minus_development": holdout_by_method[method][
                    "macro_known_link_recall_at_20"
                ]
                - dev_by_method[method]["macro_known_link_recall_at_20"],
                "wall_seconds_delta_holdout_minus_development": holdout_by_method[method][
                    "wall_seconds"
                ]
                - dev_by_method[method]["wall_seconds"],
                "status": "DESCRIPTIVE_NOT_ESTIMABLE",
            }
        )

    b4_row = summary["b4_provider_shaped_mock"]["row"]
    b0b_dev = dev_by_method["HT-B0b"]
    b2_dev = dev_by_method["HT-B2"]
    b4_comparison = {
        "macro_recall_delta_vs_HT-B0b": b4_row["macro_known_link_recall_at_20"]
        - b0b_dev["macro_known_link_recall_at_20"],
        "macro_recall_delta_vs_HT-B2": b4_row["macro_known_link_recall_at_20"]
        - b2_dev["macro_known_link_recall_at_20"],
        "simulated_cost_usd": b4_row["simulated_cost_usd"],
        "paid_cost_usd": b4_row["paid_cost_usd"],
        "status": "MOCK_ONLY_NOT_PROVIDER_EVIDENCE",
    }
    development_frontier = _pareto_frontier(development_rows)
    holdout_frontier = _pareto_frontier(holdout_rows)
    for row in development_rows:
        row["pareto_frontier"] = row["method"] in development_frontier
    for row in holdout_rows:
        row["pareto_frontier"] = row["method"] in holdout_frontier

    return {
        "format": "ht-long-run-analysis-v1",
        "status": "PASS_DESCRIPTIVE_ANALYSIS_NOT_ESTIMABLE",
        "code_commit": code_commit or summary["code_commit"],
        "protocol_hash": summary["protocol_hash"],
        "cohort_manifest_hash": summary["cohort_manifest_hash"],
        "development": {
            "rows": development_rows,
            "pareto_frontier_methods": development_frontier,
        },
        "final_holdout": {
            "rows": holdout_rows,
            "pareto_frontier_methods": holdout_frontier,
        },
        "holdout_minus_development": holdout_minus_development,
        "b4_provider_shaped_mock": b4_comparison,
        "interpretation": [
            "HT-B0b is on the observed quality-resource frontier in both frozen views; this is descriptive and does not establish scientific superiority.",
            "HT-B1, HT-B2, and HT-B3 are dominated by HT-B0b on the observed wall-time/recall coordinates in these views.",
            "HT-B4 mock recall matches HT-B0b and HT-B2 on development, but the transport was mocked and therefore is not provider evidence.",
            "Small group counts, product-level disclosure labels, unjudged pairs, and the K=20 ceiling keep confirmatory uncertainty NOT_ESTIMABLE.",
        ],
        "input_hashes": input_hashes or {},
    }


def _fmt(value: Any) -> str:
    if value is None:
        return "NOT_REPORTED"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def render_analysis(analysis: dict[str, Any]) -> str:
    lines = [
        "# HealthTech long-run descriptive analysis",
        "",
        f"- Status: `{analysis['status']}`",
        f"- Code tested: `{analysis['code_commit']}`",
        f"- Protocol hash: `{analysis['protocol_hash']}`",
        f"- Cohort manifest hash: `{analysis['cohort_manifest_hash']}`",
        "- Endpoint: macro known-link recall at K=20 over product-level disclosed links.",
        "",
        "This analysis is generated from frozen local artifacts. It reports observed quality-resource relationships and holdout drift; it does not create semantic relevance labels or confirmatory statistical evidence.",
        "",
        "## Quality-resource rows",
        "",
        "| Split | Method | Macro R@20 | Wall seconds | Query calls | Group min | Group max | Pareto frontier |",
        "|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for split in ("development", "final_holdout"):
        frontier = set(analysis[split]["pareto_frontier_methods"])
        for row in analysis[split]["rows"]:
            lines.append(
                f"| {split} | {row['method']} | {_fmt(row['macro_known_link_recall_at_20'])} | {_fmt(row['wall_seconds'])} | {_fmt(row['query_calls'])} | {_fmt(row['group_macro_known_link_recall_min'])} | {_fmt(row['group_macro_known_link_recall_max'])} | {'YES' if row['method'] in frontier else 'NO'} |"
            )
    lines.extend(
        [
            "",
            "## Holdout minus development",
            "",
            "| Method | Macro recall delta | Wall-time delta seconds | Status |",
            "|---|---:|---:|---|",
        ]
    )
    for row in analysis["holdout_minus_development"]:
        lines.append(
            f"| {row['method']} | {_fmt(row['macro_recall_delta_holdout_minus_development'])} | {_fmt(row['wall_seconds_delta_holdout_minus_development'])} | {row['status']} |"
        )
    b4 = analysis["b4_provider_shaped_mock"]
    lines.extend(
        [
            "",
            "## B4 provider-shaped mock comparison",
            "",
            f"The B4 mock recall delta versus HT-B0b is `{_fmt(b4['macro_recall_delta_vs_HT-B0b'])}` and versus HT-B2 is `{_fmt(b4['macro_recall_delta_vs_HT-B2'])}`. Simulated debit is `${b4['simulated_cost_usd']:.4f}` and paid cost is `${b4['paid_cost_usd']:.4f}`. Status: `{b4['status']}`.",
            "",
            "## Interpretation",
            "",
        ]
    )
    lines.extend(f"- {statement}" for statement in analysis["interpretation"])
    return "\n".join(lines) + "\n"


def _svg_text(value: Any) -> str:
    return html.escape(str(value))


def _quality_cost_svg(rows: list[dict[str, Any]], title: str) -> str:
    width, height = 760, 430
    left, right, top, bottom = 70, 30, 55, 70
    plot_width = width - left - right
    plot_height = height - top - bottom
    max_x = max(float(row["wall_seconds"]) for row in rows) or 1.0
    max_x *= 1.05
    max_y = 1.05
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        f'<rect width="{width}" height="{height}" fill="white"/>',
        f'<text x="{width / 2:.1f}" y="28" text-anchor="middle" font-family="Arial" font-size="18" font-weight="bold">{_svg_text(title)}</text>',
        f'<line x1="{left}" y1="{top + plot_height}" x2="{left + plot_width}" y2="{top + plot_height}" stroke="#444"/>',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_height}" stroke="#444"/>',
        f'<text x="{left + plot_width / 2:.1f}" y="{height - 18}" text-anchor="middle" font-family="Arial" font-size="12">Wall seconds</text>',
        f'<text x="18" y="{top + plot_height / 2:.1f}" text-anchor="middle" font-family="Arial" font-size="12" transform="rotate(-90 18 {top + plot_height / 2:.1f})">Macro known-link R@20</text>',
    ]
    for tick in (0.0, 0.5, 1.0):
        y = top + plot_height - (tick / max_y) * plot_height
        parts.append(f'<line x1="{left - 4}" y1="{y:.1f}" x2="{left}" y2="{y:.1f}" stroke="#444"/>')
        parts.append(f'<text x="{left - 8}" y="{y + 4:.1f}" text-anchor="end" font-family="Arial" font-size="11">{tick:.1f}</text>')
    for row in rows:
        x = left + (float(row["wall_seconds"]) / max_x) * plot_width
        y = top + plot_height - (float(row["macro_known_link_recall_at_20"]) / max_y) * plot_height
        method = _svg_text(row["method"])
        color = COLORS[row["method"]]
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6" fill="{color}"/>')
        parts.append(f'<text x="{x + 8:.1f}" y="{y - 8:.1f}" font-family="Arial" font-size="11" fill="{color}">{method}</text>')
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def _recall_svg(dev_rows: list[dict[str, Any]], holdout_rows: list[dict[str, Any]]) -> str:
    width, height = 820, 460
    left, right, top, bottom = 70, 30, 55, 85
    plot_width = width - left - right
    plot_height = height - top - bottom
    group_width = plot_width / len(METHODS)
    bar_width = group_width * 0.28
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        f'<rect width="{width}" height="{height}" fill="white"/>',
        f'<text x="{width / 2:.1f}" y="28" text-anchor="middle" font-family="Arial" font-size="18" font-weight="bold">Development vs final-holdout macro R@20</text>',
        f'<line x1="{left}" y1="{top + plot_height}" x2="{left + plot_width}" y2="{top + plot_height}" stroke="#444"/>',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_height}" stroke="#444"/>',
    ]
    for tick in (0.0, 0.5, 1.0):
        y = top + plot_height - tick * plot_height
        parts.append(f'<line x1="{left - 4}" y1="{y:.1f}" x2="{left}" y2="{y:.1f}" stroke="#444"/>')
        parts.append(f'<text x="{left - 8}" y="{y + 4:.1f}" text-anchor="end" font-family="Arial" font-size="11">{tick:.1f}</text>')
    dev_by_method = {row["method"]: row for row in dev_rows}
    holdout_by_method = {row["method"]: row for row in holdout_rows}
    for index, method in enumerate(METHODS):
        base_x = left + index * group_width + group_width * 0.18
        for offset, value, color in (
            (0.0, dev_by_method[method]["macro_known_link_recall_at_20"], "#1f77b4"),
            (bar_width * 1.1, holdout_by_method[method]["macro_known_link_recall_at_20"], "#ff7f0e"),
        ):
            bar_height = float(value) * plot_height
            y = top + plot_height - bar_height
            parts.append(f'<rect x="{base_x + offset:.1f}" y="{y:.1f}" width="{bar_width:.1f}" height="{bar_height:.1f}" fill="{color}"/>')
        parts.append(f'<text x="{base_x + bar_width:.1f}" y="{top + plot_height + 20}" text-anchor="middle" font-family="Arial" font-size="11">{_svg_text(method)}</text>')
    parts.extend(
        [
            f'<rect x="{width - 190}" y="{height - 45}" width="12" height="12" fill="#1f77b4"/><text x="{width - 172}" y="{height - 34}" font-family="Arial" font-size="11">development</text>',
            f'<rect x="{width - 90}" y="{height - 45}" width="12" height="12" fill="#ff7f0e"/><text x="{width - 72}" y="{height - 34}" font-family="Arial" font-size="11">holdout</text>',
            "</svg>",
        ]
    )
    return "\n".join(parts) + "\n"


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_outputs(output: Path, analysis: dict[str, Any]) -> None:
    output.mkdir(parents=True)
    (output / "analysis.json").write_text(
        json.dumps(analysis, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    rows = analysis["development"]["rows"] + analysis["final_holdout"]["rows"]
    _write_csv(output / "quality_cost_frontier.csv", rows)
    (output / "ANALYSIS.md").write_text(render_analysis(analysis), encoding="utf-8")
    (output / "quality_cost_development.svg").write_text(
        _quality_cost_svg(analysis["development"]["rows"], "Development quality vs wall time"),
        encoding="utf-8",
    )
    (output / "quality_cost_holdout.svg").write_text(
        _quality_cost_svg(analysis["final_holdout"]["rows"], "Final holdout quality vs wall time"),
        encoding="utf-8",
    )
    (output / "recall_comparison.svg").write_text(
        _recall_svg(analysis["development"]["rows"], analysis["final_holdout"]["rows"]),
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--dev-frontier", type=Path, required=True)
    parser.add_argument("--holdout-frontier", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--code-commit", required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output already exists; choose a fresh directory")
    input_hashes = {
        str(path): _sha256(path)
        for path in (args.summary, args.dev_frontier, args.holdout_frontier)
    }
    summary = _read_json(args.summary)
    analysis = build_analysis(
        summary=summary,
        dev_frontier=_read_json(args.dev_frontier),
        holdout_frontier=_read_json(args.holdout_frontier),
        input_hashes=input_hashes,
        code_commit=args.code_commit,
    )
    write_outputs(args.output, analysis)
    print(
        json.dumps(
            {
                "status": analysis["status"],
                "output": str(args.output),
                "development_frontier": analysis["development"]["pareto_frontier_methods"],
                "holdout_frontier": analysis["final_holdout"]["pareto_frontier_methods"],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
