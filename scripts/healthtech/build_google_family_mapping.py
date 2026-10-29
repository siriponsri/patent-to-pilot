"""Build a sourced Google Patents family mapping from local raw pages.

The mapping is evaluator-side metadata only. It never reads evaluator
relations, never adds family labels to runtime.json, and records only source
metadata plus hashes in the generated artifact.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import Any

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from patent_to_pilot.healthtech.contracts import canonical_patent_id


FAMILY_SECTION = re.compile(r'<section\s+itemprop=["\']family["\'][^>]*>', re.IGNORECASE)
FAMILY_ID = re.compile(r"<h2>ID=([^<]+)</h2>", re.IGNORECASE)


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_google_family_id(html: str) -> str:
    """Return the page's explicit Google Patents family-section identifier."""
    marker = FAMILY_SECTION.search(html)
    if marker is None:
        raise ValueError("Google Patents page lacks a family section")
    section = html[marker.end(): marker.end() + 100_000]
    match = FAMILY_ID.search(section)
    if match is None:
        raise ValueError("Google Patents family section lacks an ID heading")
    raw_id = match.group(1).strip()
    if not re.fullmatch(r"[0-9]+", raw_id):
        raise ValueError("Google Patents family ID is not numeric")
    return f"google-docdb-{raw_id}"


def _manifest_raw_files(cohort: Path, manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = manifest.get("raw_files")
    if not isinstance(rows, list) or not rows:
        raise ValueError("manifest raw_files must be a nonempty list")
    indexed: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("path"), str):
            raise ValueError("manifest raw_files contains an invalid row")
        relative = row["path"].replace("\\", "/")
        path = (cohort / relative).resolve()
        if cohort.resolve() not in path.parents:
            raise ValueError(f"raw file escapes cohort root: {relative}")
        if relative in indexed:
            raise ValueError(f"manifest raw_files repeats {relative}")
        if not path.is_file():
            raise ValueError(f"manifest raw file is missing: {relative}")
        expected_size = row.get("size_bytes", row.get("bytes"))
        expected_sha = row.get("sha256")
        if not isinstance(expected_size, int) or not isinstance(expected_sha, str):
            raise ValueError(f"manifest raw file lacks size/hash: {relative}")
        actual = path.read_bytes()
        if len(actual) != expected_size or hashlib.sha256(actual).hexdigest() != expected_sha:
            raise ValueError(f"manifest raw file hash/size mismatch: {relative}")
        indexed[relative] = {**row, "path": relative, "absolute_path": path}
    return indexed


def build_cohort_mapping(cohort_dir: str | Path) -> dict[str, Any]:
    cohort = Path(cohort_dir).resolve()
    manifest = _read_json(cohort / "manifest.json")
    runtime = _read_json(cohort / str(manifest.get("runtime_path", "runtime.json")))
    registry = _read_json(cohort / str(manifest.get("source_registry", "source_registry.json")))
    devices = runtime.get("devices")
    patents = runtime.get("patents")
    registry_rows = registry.get("sources")
    if not isinstance(devices, list) or not isinstance(patents, list):
        raise ValueError("runtime must contain devices and patents")
    if not isinstance(registry_rows, list):
        raise ValueError("source registry must contain sources")
    registry_by_id = {row.get("source_id"): row for row in registry_rows if isinstance(row, dict)}
    raw_files = _manifest_raw_files(cohort, manifest)
    mappings: list[dict[str, Any]] = []
    seen: set[str] = set()
    for patent in patents:
        if not isinstance(patent, dict):
            raise ValueError("runtime patents must be objects")
        patent_id = canonical_patent_id(str(patent.get("patent_id_canonical", "")))
        if patent_id in seen:
            raise ValueError(f"runtime patents repeat {patent_id}")
        seen.add(patent_id)
        source_id = patent.get("source_id")
        registry_row = registry_by_id.get(source_id)
        if not isinstance(source_id, str) or not isinstance(registry_row, dict):
            raise ValueError(f"patent lacks a registered source: {patent_id}")
        if registry_row.get("source_type") != "patent_document":
            raise ValueError(f"family source is not a patent document: {source_id}")
        if registry_row.get("rights_policy_id") != "google-patents-pages":
            raise ValueError(f"family source lacks the Google Patents local-use policy: {source_id}")
        raw_candidates = [
            row for row in raw_files.values()
            if Path(str(row["path"])).stem.upper() == patent_id and str(row["path"]).lower().endswith(".html")
        ]
        if len(raw_candidates) != 1:
            raise ValueError(f"expected one raw Google page for {patent_id}")
        raw = raw_candidates[0]
        raw_path = Path(raw["absolute_path"])
        raw_sha = _sha256(raw_path)
        if registry_row.get("raw_html_sha256") != raw_sha:
            raise ValueError(f"registry raw hash disagrees for {patent_id}")
        family_id = parse_google_family_id(raw_path.read_text(encoding="utf-8", errors="ignore"))
        mappings.append({
            "patent_id_canonical": patent_id,
            "family_id": family_id,
            "family_mapping_type": "google_docdb_family_section_id",
            "family_source_id": source_id,
            "family_source_url": str(registry_row.get("url", patent.get("source_url", ""))),
            "family_source_revision": str(registry_row.get("revision", patent.get("source_revision", ""))),
            "family_source_sha256": raw_sha,
            "family_locator": "HTML section itemprop=family; h2 ID=...",
        })
    mappings.sort(key=lambda row: row["patent_id_canonical"])
    return {
        "cohort_id": cohort.name,
        "patent_count": len(mappings),
        "family_count": len({row["family_id"] for row in mappings}),
        "mappings": mappings,
    }


def build_mapping(cohort_dirs: list[str | Path]) -> dict[str, Any]:
    source_cohorts = [build_cohort_mapping(path) for path in cohort_dirs]
    merged: dict[str, dict[str, Any]] = {}
    for cohort in source_cohorts:
        for row in cohort["mappings"]:
            previous = merged.get(row["patent_id_canonical"])
            if previous is not None and previous["family_id"] != row["family_id"]:
                raise ValueError(f"conflicting family mapping for {row['patent_id_canonical']}")
            merged[row["patent_id_canonical"]] = row
    mappings = [merged[key] for key in sorted(merged)]
    mapping_hash = hashlib.sha256(
        json.dumps(mappings, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "format": "ht-google-docdb-family-mapping-v1",
        "status": "SOURCED_LOCAL_EVALUATOR_MAPPING",
        "source_policy": "google-patents-pages / ALLOWED_LOCAL_RESEARCH",
        "source_cohorts": [
            {key: cohort[key] for key in ("cohort_id", "patent_count", "family_count")}
            for cohort in source_cohorts
        ],
        "counts": {
            "patents_mapped": len(mappings),
            "families_observed": len({row["family_id"] for row in mappings}),
            "unmapped_patents": 0,
        },
        "mapping_sha256": mapping_hash,
        "mappings": mappings,
        "limitations": [
            "The mapping is derived from the explicit Google Patents family-section ID in each cached page.",
            "It is evaluator-side metadata and is not added to runtime inputs or controller observations.",
            "Google-derived pages remain local-research only under the recorded rights policy.",
            "Family membership does not establish semantic relevance, patent validity, FTO, clinical suitability, or investment merit.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cohort", action="append", required=True, help="local cohort directory; repeat for multiple cohorts")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output already exists; choose a fresh path")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    payload = build_mapping(args.cohort)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": payload["status"],
        "patents_mapped": payload["counts"]["patents_mapped"],
        "families_observed": payload["counts"]["families_observed"],
        "mapping_sha256": payload["mapping_sha256"],
        "output": str(args.output),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
