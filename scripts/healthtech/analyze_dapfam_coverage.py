"""Screen DAPFAM text for an explicit, non-semantic medical-device lexicon.

The DAPFAM inputs are research-only parquet files. This analyzer writes only
aggregate counts, hashes, and the declared screening policy; it never copies
raw text or row-level relations into the result directory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]

LEXICON: dict[str, tuple[str, ...]] = {
    "medical_device": (
        "balloon",
        "catheter",
        "cardiac",
        "cardiovascular",
        "delivery system",
        "embol",
        "endovascular",
        "graft",
        "guidewire",
        "implant",
        "medical device",
        "occluder",
        "prosthesis",
        "stent",
        "surgical",
        "thrombectomy",
        "valve",
        "vascular",
    ),
    "pharma_biologics": (
        "antibody",
        "cell",
        "compound",
        "drug",
        "enzyme",
        "gene",
        "peptide",
        "pharmaceutical",
        "protein",
        "vaccine",
    ),
}


def sql_literal(value: str | Path) -> str:
    return str(value).replace("\\", "/").replace("'", "''")


def sql_regex_literal(pattern: str) -> str:
    return sql_literal(pattern)


def screening_pattern(terms: tuple[str, ...]) -> str:
    if not terms:
        raise ValueError("screening terms must not be empty")
    escaped = "|".join(re.escape(term) for term in terms)
    return f"(?i)({escaped})"


def screening_expression(alias: str, terms: tuple[str, ...]) -> str:
    if not alias or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", alias):
        raise ValueError("alias must be a simple SQL identifier")
    pattern = screening_pattern(terms)
    text = f"lower(coalesce({alias}.title_en, '') || ' ' || coalesce({alias}.abstract_en, ''))"
    return f"regexp_matches({text}, '{sql_regex_literal(pattern)}')"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def git_revision() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()


def git_worktree_dirty() -> bool:
    result = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return bool(result.stdout.strip())


def duckdb_json(duckdb: Path, sql: str) -> list[dict[str, Any]]:
    result = subprocess.run(
        [str(duckdb), "-no-agent", "-json", "-c", sql],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"DuckDB returned non-JSON output: {result.stdout[:200]}") from exc
    if not isinstance(payload, list) or not all(isinstance(row, dict) for row in payload):
        raise RuntimeError("DuckDB JSON output must be a list of objects")
    return payload


def duckdb_version(duckdb: Path) -> str:
    result = subprocess.run(
        [str(duckdb), "-no-agent", "--version"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result.stdout.strip()


def build_counts_sql(corpus: Path, queries: Path, qrels: Path) -> str:
    return f"""
        SELECT 'corpus' AS dataset, count(*) AS row_count, count(DISTINCT relevant_id) AS unique_id_count
        FROM read_parquet('{sql_literal(corpus)}')
        UNION ALL
        SELECT 'queries' AS dataset, count(*) AS row_count, count(DISTINCT query_id) AS unique_id_count
        FROM read_parquet('{sql_literal(queries)}')
        UNION ALL
        SELECT 'qrels' AS dataset, count(*) AS row_count,
               count(DISTINCT query_id || '|' || relevant_id) AS unique_id_count
        FROM read_parquet('{sql_literal(qrels)}')
    """


def build_screening_sql(path: Path, alias: str, dataset: str) -> str:
    expressions = [
        f"count(*) FILTER (WHERE {screening_expression(alias, terms)}) AS {name}_rows"
        for name, terms in LEXICON.items()
    ]
    missing = [
        f"count(*) FILTER (WHERE {alias}.title_en IS NULL OR trim({alias}.title_en) = '') AS missing_title_rows",
        f"count(*) FILTER (WHERE {alias}.abstract_en IS NULL OR trim({alias}.abstract_en) = '') AS missing_abstract_rows",
        f"count(*) FILTER (WHERE ({alias}.title_en IS NULL OR trim({alias}.title_en) = '') AND ({alias}.abstract_en IS NULL OR trim({alias}.abstract_en) = '')) AS missing_both_rows",
    ]
    return f"""
        SELECT '{dataset}' AS dataset, count(*) AS row_count,
               {', '.join(expressions + missing)}
        FROM read_parquet('{sql_literal(path)}') AS {alias}
    """


def build_qrel_sql(corpus: Path, queries: Path, qrels: Path) -> str:
    target_flags = ", ".join(
        f"{screening_expression('c', terms)} AS {name}_target"
        for name, terms in LEXICON.items()
    )
    query_flags = ", ".join(
        f"{screening_expression('q', terms)} AS {name}_query"
        for name, terms in LEXICON.items()
    )
    category_columns = []
    for name in LEXICON:
        category_columns.extend(
            [
                f"count(*) FILTER (WHERE {name}_query) AS {name}_query_screened_positive_pairs",
                f"count(*) FILTER (WHERE {name}_target) AS {name}_target_screened_positive_pairs",
                f"count(*) FILTER (WHERE {name}_query AND {name}_target) AS {name}_both_screened_positive_pairs",
                f"count(DISTINCT query_id) FILTER (WHERE {name}_query) AS {name}_screened_queries",
                f"count(DISTINCT relevant_id) FILTER (WHERE {name}_target) AS {name}_screened_targets",
            ]
        )
    return f"""
        WITH corpus_flags AS (
            SELECT relevant_id, {target_flags}
            FROM read_parquet('{sql_literal(corpus)}') AS c
        ), query_flags AS (
            SELECT query_id, {query_flags}
            FROM read_parquet('{sql_literal(queries)}') AS q
        ), positive AS (
            SELECT query_id, relevant_id, coalesce(domain_rel, 'UNKNOWN') AS domain_rel
            FROM read_parquet('{sql_literal(qrels)}')
            WHERE relevance_score > 0
        )
        SELECT domain_rel, count(*) AS positive_pairs, {', '.join(category_columns)}
        FROM positive
        JOIN query_flags USING (query_id)
        JOIN corpus_flags USING (relevant_id)
        GROUP BY domain_rel
        ORDER BY domain_rel
    """


def render_report(summary: dict[str, Any]) -> str:
    counts = summary["counts"]
    screens = {row["dataset"]: row for row in summary["screening"]}
    lines = [
        "# DAPFAM lexical coverage screen",
        "",
        "This is a deterministic substring screen over DAPFAM title and abstract fields.",
        "It is a corpus-coverage diagnostic, not semantic device relevance gold.",
        "",
        "## Inputs",
        "",
        f"- Corpus rows: `{counts['corpus']['row_count']}`; queries: `{counts['queries']['row_count']}`; qrels: `{counts['qrels']['row_count']}`.",
        f"- DuckDB: `{summary['runtime']['duckdb_version']}`.",
        "- Raw parquet files remain in the research-only input boundary; no row-level text or relation is written here.",
        "",
        "## Screen policy",
        "",
        "- Matching is case-insensitive substring matching over `title_en + abstract_en`.",
        "- `medical_device` and `pharma_biologics` are lexical buckets only; a hit does not establish device identity, clinical use, or patent relevance.",
        "- Positive qrel analysis uses supplied `relevance_score > 0`; unlisted pairs remain unjudged.",
        "",
        "## Aggregate coverage",
        "",
        "| Dataset | Rows | Medical-device hits | Pharma/biologics hits | Missing title | Missing abstract |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for dataset in ("corpus", "queries"):
        row = screens[dataset]
        lines.append(
            f"| {dataset} | {row['row_count']} | {row['medical_device_rows']} | {row['pharma_biologics_rows']} | {row['missing_title_rows']} | {row['missing_abstract_rows']} |"
        )
    lines.extend(
        [
            "",
            "## Positive qrel screen",
            "",
            "| Domain | Positive pairs | Device-query hits | Device-target hits | Both hits |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for row in summary["positive_qrels"]:
        lines.append(
            f"| {row['domain_rel']} | {row['positive_pairs']} | {row['medical_device_query_screened_positive_pairs']} | {row['medical_device_target_screened_positive_pairs']} | {row['medical_device_both_screened_positive_pairs']} |"
        )
    lines.extend(
        [
            "",
            "## Limits",
            "",
            "- DAPFAM remains a separate citation-based patent-family retrieval diagnostic under its recorded research-only license.",
            "- Lexical coverage cannot replace owner-authorized semantic device-patent judgments, source locators, adjudicator roles, or an untouched company/family holdout.",
            "- This package does not change HT-T1 denominators, family/company grouping, frozen controls, or the `UNJUDGED` policy.",
        ]
    )
    return "\n".join(lines) + "\n"


def run(args: argparse.Namespace) -> dict[str, Any]:
    output = args.output.resolve()
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"output directory is not empty: {output}")
    output.mkdir(parents=True, exist_ok=True)

    paths = {
        "corpus": args.corpus.resolve(),
        "queries": args.queries.resolve(),
        "qrels": args.qrels.resolve(),
    }
    for path in paths.values():
        if not path.is_file():
            raise FileNotFoundError(path)

    summary: dict[str, Any] = {
        "status": "PASS",
        "task": "DAPFAM lexical medical-device coverage screen",
        "screening_policy": {
            "match": "case-insensitive substring over title_en + abstract_en",
            "lexicon": {name: list(terms) for name, terms in LEXICON.items()},
            "semantic_claim": False,
            "unjudged_policy": "unlisted query-target pairs remain unjudged",
        },
        "counts": {
            row["dataset"]: row
            for row in duckdb_json(args.duckdb, build_counts_sql(paths["corpus"], paths["queries"], paths["qrels"]))
        },
        "screening": duckdb_json(
            args.duckdb,
            " UNION ALL ".join(
                [
                    build_screening_sql(paths["corpus"], "c", "corpus"),
                    build_screening_sql(paths["queries"], "q", "queries"),
                ]
            ),
        ),
        "positive_qrels": duckdb_json(
            args.duckdb,
            build_qrel_sql(paths["corpus"], paths["queries"], paths["qrels"]),
        ),
        "rights_boundary": {
            "license": "CC-BY-NC-SA-4.0",
            "intended_use": "separate local research diagnostic only",
            "raw_payload_exported": False,
        },
        "runtime": {
            "duckdb_version": duckdb_version(args.duckdb),
            "python": sys.version,
            "code_revision": git_revision(),
            "working_tree_dirty": git_worktree_dirty(),
        },
    }
    summary["input_files"] = {
        name: {
            "path": display_path(path),
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        for name, path in paths.items()
    }
    (output / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output / "REPORT.md").write_text(render_report(summary), encoding="utf-8")
    manifest = {
        "run_id": output.name,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "entrypoint": display_path(Path(__file__).resolve()),
        "entrypoint_sha256": sha256_file(Path(__file__).resolve()),
        "code_revision": git_revision(),
        "inputs": summary["input_files"],
        "outputs": {"summary": display_path(output / "summary.json"), "report": display_path(output / "REPORT.md")},
        "raw_payload_exported": False,
        "provider_calls": 0,
        "network_calls": 0,
        "paid_cost_usd": 0.0,
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--duckdb", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--qrels", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args)
    print(
        json.dumps(
            {
                "status": result["status"],
                "output": display_path(args.output.resolve()),
                "corpus_rows": result["counts"]["corpus"]["row_count"],
                "query_rows": result["counts"]["queries"]["row_count"],
                "positive_qrel_rows": sum(row["positive_pairs"] for row in result["positive_qrels"]),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
