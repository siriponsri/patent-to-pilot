"""Render deterministic current-head development-only frontier artifacts."""
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
from pathlib import Path
from typing import Any


METHOD_ORDER = ("HT-B0a", "HT-B0b", "HT-B1", "HT-B2", "HT-B3", "HT-B4-offline")
COLORS = {
    "HT-B0a": "#6b7280",
    "HT-B0b": "#2563eb",
    "HT-B1": "#0f766e",
    "HT-B2": "#b45309",
    "HT-B3": "#7c3aed",
    "HT-B4-offline": "#be123c",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def stable_repo_path(path: Path) -> str:
    """Return a reproducible, non-machine-specific manifest path."""
    parts = path.resolve().parts
    for marker in ("docs", "results", "scripts"):
        if marker in parts:
            return Path(*parts[parts.index(marker) :]).as_posix()
    return f"<external>/{path.name}"


def load_rows(verification_path: Path, expected_commit: str) -> dict[str, Any]:
    raw = json.loads(verification_path.read_text(encoding="utf-8"))
    candidate = raw.get("candidate") or {}
    if candidate.get("head") != expected_commit:
        raise ValueError("verification candidate head does not match requested code commit")
    if raw.get("format") != "ptp-current-head-offline-verification-v1":
        raise ValueError("verification is not the expected current-head offline receipt")
    results = raw.get("results") or {}
    rows: list[dict[str, Any]] = []
    for method in METHOD_ORDER:
        item = results.get(method)
        if not isinstance(item, dict):
            raise ValueError(f"missing current-head result for {method}")
        row = {
            "method": method,
            "macro_recall_at_20": float(item["macro_recall_at_20"]),
            "query_calls": int(item["query_calls"]),
            "rerank_pairs": int(item["rerank_pairs"]),
            "failed_queries": int(item.get("failed_queries", 0)),
        }
        if method == "HT-B4-offline":
            row["controller_steps"] = int(item["controller_steps"])
            row["micro_recall_at_20"] = float(item["micro_recall_at_20"])
        rows.append(row)
    return {
        "candidate_head": expected_commit,
        "verification_sha256": sha256(verification_path),
        "protocol_hash": raw["frozen_inputs"]["protocol_hash"],
        "cohort_manifest_sha256": raw["frozen_inputs"]["cohort_manifest_sha256"],
        "rows": rows,
    }


def _esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def render_recall_svg(rows: list[dict[str, Any]]) -> str:
    width, height = 980, 560
    left, top, plot_width, row_height = 230, 110, 650, 52
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<text x="490" y="32" text-anchor="middle" font-family="Arial" font-size="20" font-weight="bold">Current-head development-only Recall@20</text>',
        '<text x="490" y="56" text-anchor="middle" font-family="Arial" font-size="12" fill="#4b5563">Candidate 88dc4047; descriptive frontier; no equal-total-budget superiority claim</text>',
    ]
    for tick in (0.0, 0.25, 0.5, 0.75, 1.0):
        x = left + plot_width * tick
        parts.append(f'<line x1="{x:.1f}" y1="{top - 12}" x2="{x:.1f}" y2="{top + row_height * len(rows) - 14}" stroke="#d1d5db"/>')
        parts.append(f'<text x="{x:.1f}" y="{top - 22}" text-anchor="middle" font-family="Arial" font-size="11" fill="#374151">{tick:.2f}</text>')
    for index, row in enumerate(rows):
        y = top + index * row_height
        value = row["macro_recall_at_20"]
        bar_width = plot_width * value
        color = COLORS[row["method"]]
        parts.append(f'<text x="{left - 14}" y="{y + 18}" text-anchor="end" font-family="Arial" font-size="12" fill="#111827">{_esc(row["method"])}</text>')
        parts.append(f'<rect x="{left}" y="{y}" width="{bar_width:.1f}" height="24" fill="{color}"/>')
        parts.append(f'<text x="{left + bar_width + 8:.1f}" y="{y + 17}" font-family="Arial" font-size="12" fill="#111827">{value:.6f}</text>')
        parts.append(f'<text x="{left}" y="{y + 39}" font-family="Arial" font-size="10" fill="#4b5563">queries={row["query_calls"]}; rerank_pairs={row["rerank_pairs"]}</text>')
    parts.extend([
        '<text x="490" y="530" text-anchor="middle" font-family="Arial" font-size="11" fill="#4b5563">Macro known-link Recall@20 over the frozen development cohort; unlisted pairs remain unjudged</text>',
        '</svg>',
    ])
    return "\n".join(parts) + "\n"


def render_budget_svg(rows: list[dict[str, Any]]) -> str:
    width, height = 980, 560
    left, top, plot_width, row_height = 230, 110, 650, 52
    max_query = max(row["query_calls"] for row in rows)
    max_rerank = max(row["rerank_pairs"] for row in rows)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<text x="490" y="32" text-anchor="middle" font-family="Arial" font-size="20" font-weight="bold">Current-head realized retrieval units</text>',
        '<text x="490" y="56" text-anchor="middle" font-family="Arial" font-size="12" fill="#4b5563">Same inputs and per-call depths; totals are observed, not equalized</text>',
        '<text x="390" y="82" text-anchor="middle" font-family="Arial" font-size="12" fill="#1d4ed8">Query calls (0 to 9)</text>',
        '<text x="770" y="82" text-anchor="middle" font-family="Arial" font-size="12" fill="#b45309">Rerank pairs (0 to 369)</text>',
    ]
    for index, row in enumerate(rows):
        y = top + index * row_height
        color = COLORS[row["method"]]
        query_x = left + 150 * row["query_calls"] / max_query
        rerank_x = left + 390 + 220 * row["rerank_pairs"] / max_rerank
        parts.append(f'<text x="{left - 14}" y="{y + 18}" text-anchor="end" font-family="Arial" font-size="12" fill="#111827">{_esc(row["method"])}</text>')
        parts.append(f'<line x1="{left}" y1="{y + 12}" x2="{left + 150}" y2="{y + 12}" stroke="#dbeafe" stroke-width="10"/>')
        parts.append(f'<circle cx="{query_x:.1f}" cy="{y + 12}" r="7" fill="{color}"/>')
        parts.append(f'<text x="{left + 160}" y="{y + 17}" font-family="Arial" font-size="11" fill="#1d4ed8">{row["query_calls"]}</text>')
        parts.append(f'<line x1="{left + 390}" y1="{y + 12}" x2="{left + 610}" y2="{y + 12}" stroke="#fef3c7" stroke-width="10"/>')
        parts.append(f'<circle cx="{rerank_x:.1f}" cy="{y + 12}" r="7" fill="{color}"/>')
        parts.append(f'<text x="{left + 620}" y="{y + 17}" font-family="Arial" font-size="11" fill="#b45309">{row["rerank_pairs"]}</text>')
    parts.extend([
        '<text x="490" y="530" text-anchor="middle" font-family="Arial" font-size="11" fill="#4b5563">HT-B4 controller steps are reported separately and are not interchangeable with query/rerank units</text>',
        '</svg>',
    ])
    return "\n".join(parts) + "\n"


def write_artifacts(verification_path: Path, output: Path, code_commit: str) -> dict[str, Any]:
    if output.exists():
        raise ValueError("output already exists; choose a fresh directory")
    data = load_rows(verification_path, code_commit)
    output.mkdir(parents=True)
    rows = data["rows"]
    with (output / "current_head_frontier.csv").open("w", encoding="utf-8", newline="") as handle:
        fields = ["method", "macro_recall_at_20", "query_calls", "rerank_pairs", "failed_queries", "micro_recall_at_20", "controller_steps"]
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    (output / "current_head_recall.svg").write_text(render_recall_svg(rows), encoding="utf-8")
    (output / "current_head_budget.svg").write_text(render_budget_svg(rows), encoding="utf-8")
    manifest = {
        "format": "ptp-current-head-frontier-figures-v1",
        "status": "DESCRIPTIVE_DEVELOPMENT_ONLY",
        "candidate_head": code_commit,
        "verification_path": stable_repo_path(verification_path),
        "verification_sha256": data["verification_sha256"],
        "protocol_hash": data["protocol_hash"],
        "cohort_manifest_sha256": data["cohort_manifest_sha256"],
        "rows": rows,
        "outputs": ["current_head_frontier.csv", "current_head_recall.svg", "current_head_budget.svg"],
        "limitations": [
            "Development-only cohort with no current-head final holdout.",
            "Product-level disclosed links are not semantic relevance gold.",
            "Observed query/rerank totals are not an equal-total-budget comparison.",
            "Figures do not include paid API or external business validation evidence.",
        ],
    }
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verification", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--code-commit", required=True)
    args = parser.parse_args()
    manifest = write_artifacts(args.verification, args.output, args.code_commit)
    print(json.dumps({"status": manifest["status"], "output": str(args.output), "rows": len(manifest["rows"]), "candidate_head": manifest["candidate_head"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
