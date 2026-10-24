#!/usr/bin/env python3
"""Streaming-only G03 checks for PLS CSV and EnterpriseRAG questions/ZIPs."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import zipfile
import re
import shutil
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW = DATA / "raw"
DERIVED = DATA / "derived"
RECEIPTS = DATA / "manifests"

try:
    csv.field_size_limit(sys.maxsize)
except OverflowError:
    csv.field_size_limit(2**31 - 1)


def csv_report(path: Path) -> dict:
    rows = 0
    widths: Counter[str] = Counter()
    duplicate_keys: Counter[str] = Counter()
    missing: Counter[str] = Counter()
    family_values: Counter[str] = Counter()
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        header = reader.fieldnames or []
        if not header:
            raise ValueError(f"no CSV header: {path}")
        key_candidates = [
            x for x in header
            if any(token in x.lower() for token in ("family", "publication", "patent", "id"))
        ]
        family_candidates = [x for x in header if "family" in x.lower()]
        for record in reader:
            rows += 1
            widths[str(len(record))] += 1
            for field in header:
                value = record.get(field, "")
                if value is None or not value.strip():
                    missing[field] += 1
            key = "|".join((record.get(field) or "").strip() for field in key_candidates)
            if key and key.strip("|"):
                duplicate_keys[key] += 1
            for field in family_candidates:
                value = (record.get(field) or "").strip()
                if value:
                    family_values[value] += 1
    duplicate_groups = sum(1 for n in duplicate_keys.values() if n > 1)
    duplicate_rows = sum(n - 1 for n in duplicate_keys.values() if n > 1)
    return {
        "file": str(path.relative_to(ROOT)),
        "classification": "EVALUATOR_ONLY_ANALYSIS",
        "agent_view": "not_for_agent_input",
        "rows": rows,
        "field_count": len(header),
        "fields": header,
        "row_widths": dict(widths),
        "missing_by_field": dict(missing),
        "duplicate_key_fields": key_candidates,
        "duplicate_groups": duplicate_groups,
        "duplicate_rows_after_first": duplicate_rows,
        "family_fields": family_candidates,
        "family_value_count_observed": len(family_values),
        "family_values_with_multiple_rows": sum(1 for n in family_values.values() if n > 1),
    }


def question_report(path: Path) -> dict:
    count = 0
    fields: Counter[str] = Counter()
    source_types: Counter[str] = Counter()
    by_source = Counter()
    selected = []
    with path.open("r", encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            item = json.loads(line)
            count += 1
            fields.update(item.keys())
            types = tuple(item.get("source_types", []))
            source_types.update(types)
            by_source["+".join(types) or "<none>"] += 1
            if "github" in types and len(selected) < 10:
                selected.append({
                    "question_id": item.get("question_id"),
                    "question_type": item.get("question_type"),
                    "expected_doc_ids": item.get("expected_doc_ids", []),
                    "question": item.get("question"),
                })
    return {
        "file": str(path.relative_to(ROOT)),
        "rows": count,
        "field_presence": dict(fields),
        "source_type_counts": dict(source_types),
        "source_combination_counts": dict(by_source),
        "github_examples": selected,
        "excluded_from_agent_view": ["expected_doc_ids", "gold_answer", "answer_facts"],
    }


def zip_report(path: Path, expected: set[str]) -> dict:
    names = set()
    total_uncompressed = 0
    member_ids = set()
    with zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            if not info.is_dir():
                names.add(info.filename)
                total_uncompressed += info.file_size
                member_ids.update(re.findall(r"dsid_[0-9a-f]+", info.filename))
    matched = sorted(x for x in expected if x in member_ids)
    return {
        "file": str(path.relative_to(ROOT)),
        "members": len(names),
        "uncompressed_bytes": total_uncompressed,
        "expected_ids_requested": sorted(expected),
        "expected_ids_found_by_path_or_basename": matched,
        "expected_ids_missing": sorted(expected - set(matched)),
        "member_doc_ids": len(member_ids),
    }


def extract_closed_enterprise_sample() -> dict:
    question_path = RAW / "enterprise" / "questions.jsonl"
    archives = [RAW / "enterprise" / x for x in ("github_slice_0001.zip", "github_slice_0002.zip")]
    member_by_id = {}
    for archive_path in archives:
        with zipfile.ZipFile(archive_path) as archive:
            for info in archive.infolist():
                if info.is_dir():
                    continue
                match = re.search(r"(dsid_[0-9a-f]+)", info.filename)
                if match:
                    member_by_id[match.group(1)] = (archive_path, info.filename, info.file_size)
    selected = []
    with question_path.open(encoding="utf-8") as stream:
        for line in stream:
            item = json.loads(line)
            expected = set(item.get("expected_doc_ids", []))
            if "github" in item.get("source_types", []) and expected and expected.issubset(member_by_id):
                selected.append({
                    "question_id": item.get("question_id"),
                    "question_type": item.get("question_type"),
                    "source_types": item.get("source_types", []),
                    "question": item.get("question"),
                    "expected_doc_ids": item.get("expected_doc_ids", []),
                })
    out_dir = DATA / "processed" / "enterprise" / "github_closed_sample"
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    docs = []
    copied_ids = set()
    agent_questions = []
    for item in selected:
        for doc_id in item["expected_doc_ids"]:
            if doc_id in copied_ids:
                continue
            archive_path, member_name, member_size = member_by_id[doc_id]
            target = out_dir / f"{doc_id}.txt"
            digest = hashlib.sha256()
            total = 0
            with zipfile.ZipFile(archive_path) as archive, archive.open(member_name) as source, target.open("wb") as output:
                for block in iter(lambda: source.read(1024 * 1024), b""):
                    output.write(block)
                    digest.update(block)
                    total += len(block)
            docs.append({
                "doc_id": doc_id,
                "source_archive": str(archive_path.relative_to(ROOT)),
                "source_member": member_name,
                "expected_uncompressed_bytes": member_size,
                "actual_bytes": total,
                "sha256": digest.hexdigest(),
                "processed_path": str(target.relative_to(ROOT)),
            })
            copied_ids.add(doc_id)
        agent_questions.append({
            "question_id": item.get("question_id"),
            "question_type": item.get("question_type"),
            "source_types": item.get("source_types", []),
            "question": item.get("question"),
        })
    (out_dir / "selected_questions.jsonl").write_text(
        "".join(json.dumps(x, ensure_ascii=False) + "\n" for x in selected),
        encoding="utf-8",
    )
    (out_dir / "agent_questions.jsonl").write_text(
        "".join(json.dumps(x, ensure_ascii=False) + "\n" for x in agent_questions),
        encoding="utf-8",
    )
    (out_dir / "agent_view_manifest.json").write_text(
        json.dumps({
            "record": "G03-ENTERPRISE-AGENT-VIEW-001",
            "status": "AGENT_FACING_ALLOWLIST_VIEW",
            "source_file": "selected_questions.jsonl",
            "source_classification": "EVALUATOR_ONLY",
            "agent_file": "agent_questions.jsonl",
            "allowed_fields": ["question_id", "question_type", "source_types", "question"],
            "excluded_fields": ["expected_doc_ids", "gold_answer", "answer_facts"],
            "rows": len(agent_questions),
            "document_ids_are_not_exposed": True,
        }, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    manifest = {
        "record": "G03-ENTERPRISE-CLOSED-SAMPLE-001",
        "status": "CLOSED_SAMPLE_READY_FOR_REVIEW",
        "source_release": "EnterpriseRAG-Bench v1.0.0",
        "source_type": "github",
        "questions_selected": len(selected),
        "unique_documents_extracted": len(docs),
        "questions_with_missing_expected_docs": 0,
        "excluded_github_questions": 60 - len(selected),
        "gold_answer_fields_copied": False,
        "selected_questions_classification": "EVALUATOR_ONLY",
        "agent_questions_path": "data/processed/enterprise/github_closed_sample/agent_questions.jsonl",
        "agent_view_allowlist": ["question_id", "question_type", "source_types", "question"],
        "agent_view_excluded_fields": ["expected_doc_ids", "gold_answer", "answer_facts"],
        "documents": docs,
    }
    (out_dir / "sample-manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pls", action="store_true")
    parser.add_argument("--questions", action="store_true")
    parser.add_argument("--zips", action="store_true")
    parser.add_argument("--extract-closed", action="store_true")
    args = parser.parse_args()
    DERIVED.mkdir(parents=True, exist_ok=True)
    result = {"record": "G03-ANALYSIS-001", "streaming": True, "reports": []}
    if args.pls:
        for name in ("atazanavir.csv", "ritonavir.csv"):
            result["reports"].append(csv_report(RAW / "pls" / name))
    if args.questions:
        result["reports"].append(question_report(RAW / "enterprise" / "questions.jsonl"))
    if args.zips:
        qpath = RAW / "enterprise" / "questions.jsonl"
        expected_by_zip = {}
        with qpath.open(encoding="utf-8") as stream:
            for line in stream:
                item = json.loads(line)
                if "github" in item.get("source_types", []):
                    for doc_id in item.get("expected_doc_ids", []):
                        expected_by_zip.setdefault("all_github", set()).add(doc_id)
        zip_reports = []
        for name in ("github_slice_0001.zip", "github_slice_0002.zip"):
            report = zip_report(RAW / "enterprise" / name, expected_by_zip.get("all_github", set()))
            zip_reports.append(report)
        result["reports"].extend(zip_reports)
        result["enterprise_closure"] = {
            "github_expected_doc_ids": len(expected_by_zip.get("all_github", set())),
            "github_doc_ids_found_in_selected_slices": len(set().union(*(set(x["expected_ids_found_by_path_or_basename"]) for x in zip_reports))),
            "fully_closed_github_questions": 0,
            "selected_question_ids": [],
        }
        with qpath.open(encoding="utf-8") as stream:
            for line in stream:
                item = json.loads(line)
                expected = set(item.get("expected_doc_ids", []))
                if "github" in item.get("source_types", []) and expected and expected.issubset(set().union(*(set(x["expected_ids_found_by_path_or_basename"]) for x in zip_reports))):
                    result["enterprise_closure"]["fully_closed_github_questions"] += 1
                    result["enterprise_closure"]["selected_question_ids"].append(item.get("question_id"))
    if args.extract_closed:
        result["closed_enterprise_sample"] = extract_closed_enterprise_sample()
    out = DERIVED / "g03-analysis-report.json"
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
