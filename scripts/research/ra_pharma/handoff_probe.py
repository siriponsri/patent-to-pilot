"""Capture one exposed Thai FDA structure and the author-written handoff probes."""
import argparse
import hashlib
import json
import re
from io import BytesIO
from pathlib import Path
from time import perf_counter, process_time
from xml.etree import ElementTree
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[3]
PACKET = ROOT / "docs/ra-pharma/research/handoff-conformance"
ISSUER_HASH = "cf7a4e45068858898004c37139e3799c7551aa8beea6b7c32c9f54b1f8a2b2e6"
PATENT_TRACE_HASH = "d816042c9e42e874c00dfa4c455c60139c3d268e5672a09a04724c81103b1156"
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
FIELDS = ("applicant", "application", "round", "sequence", "role", "issuer")
ARMS = ("fixed_exact", "versioned_handoff", "id_only")
READ_CAP = 2


def digest(data):
    return hashlib.sha256(data).hexdigest()


def verified_bytes(path, expected):
    data = path.read_bytes()
    if digest(data) != expected:
        raise ValueError(f"source digest mismatch: {path.name}")
    return data


def cell_text(cell):
    return "\n".join("".join(node.text or "" for node in paragraph.findall(".//w:t", NS))
                     for paragraph in cell.findall("./w:p", NS)).strip()


def issuer_binding(path):
    data = verified_bytes(path, ISSUER_HASH)
    with ZipFile(BytesIO(data)) as docx:
        member = docx.getinfo("word/document.xml")
        if member.file_size > 1024 * 1024:
            raise ValueError("unexpected document size")
        root = ElementTree.fromstring(docx.read(member))
    table = root.find(".//w:tbl", NS)
    rows = [[cell_text(cell) for cell in row.findall("./w:tc", NS)]
            for row in table.findall("./w:tr", NS)]
    if len(rows) != 6 or any(len(row) != 3 for row in rows[:4]):
        raise ValueError("unexpected tracking table shape")
    initial, first, second = rows[1:4]
    rounds = [re.findall(r"[0-9]+", row[2]) for row in (first, second)]
    if not first[0] or initial[0] == first[0] or first[0] != second[0] or rounds != [["1"], ["2"]]:
        raise ValueError("unexpected issuer application/round structure")
    if (first[1], second[1]) != ("0000", "0001"):
        raise ValueError("unexpected issuer sequence strings")
    return {
        "source_id": "Thai FDA THAIRIMS media 673722105321365504",
        "edition": "2024-09-10", "authority": "Thai FDA Medicines Regulation Division",
        "sha256": ISSUER_HASH, "raw_bytes": len(data), "table": 1, "rows_including_header": 6,
        "initial_row": 2, "initial_application_distinct": True,
        "same_application_rows": [3, 4],
        "round_and_sequence": {"3": ["1", first[1]], "4": ["2", second[1]]},
    }


def patent_reference(path):
    original = json.loads(verified_bytes(path, PATENT_TRACE_HASH))
    packet = original["traces"]["full"]["shared"]
    item = packet["evidence"]["3"]
    return {key: item[key] for key in ("source_id", "edition", "issuer", "source_sha256", "locator")}


def scope_key(scope):
    return tuple(scope[field] for field in FIELDS)


def run_case(case, arm, binding, patent):
    request = case["request"]
    expected = scope_key(request)
    catalog = case["catalog"]
    if arm == "versioned_handoff":
        by_scope = {}
        for candidate in catalog:
            by_scope.setdefault(scope_key(candidate["scope"]), []).append(candidate)
        options = by_scope.get(expected, [])
    elif arm == "fixed_exact":
        options = [item for item in catalog if scope_key(item["scope"]) == expected]
    elif arm == "id_only":
        options = [item for item in catalog if item["scope"]["application"] == request["application"]]
    else:
        raise ValueError(f"unknown arm: {arm}")
    chosen = min(options, key=lambda item: (item["rank"], item["id"]), default=None)
    differences = [field for field in FIELDS if chosen and chosen["scope"][field] != request[field]]
    accepted = chosen if not differences else None
    supported = accepted is not None and scope_key(accepted["scope"]) == expected
    chart = patent if case["patent_context"] else None
    text = (f'อ้างอิงเอกสารผลทดสอบของผู้ยื่นที่ {chosen["locator"]}' if supported else
            f'ขอเอกสารผลทดสอบของผู้ยื่นสำหรับรอบ {request["round"]} ลำดับ {request["sequence"]}')
    trace_id = f'{case["id"]}/{arm}'
    return {
        "trace_id": trace_id,
        "schema_version": "ra-pharma/1",
        "issuer_example_locator": {"sha256": binding["sha256"], "table": 1, "row": 4},
        "handoffs": {
            "patent": {"role": "claim_limitation", "source": chart},
            "regulatory": {"role": "applicant_result", "binding": request,
                           "read_source": chosen["id"] if chosen else None,
                           "selected_mismatches": differences,
                           "verified_scope": accepted["scope"] if accepted else None,
                           "source_edition": chosen["edition"] if chosen else None,
                           "source_record_sha256": digest(json.dumps(chosen, sort_keys=True).encode()) if chosen else None},
            "correspondence": {
                "status": "supported" if supported else "missing",
                "applicant_source": chosen["id"] if supported else None,
                "reply_locator": chosen["locator"] if supported else None,
                "request_binding": None if supported else request,
                "patent_context": chart, "thai_draft": text,
            },
        },
        "catalog_descriptors_inspected": len(catalog), "read_cap": READ_CAP,
        "reads": [chosen["id"]] if chosen else [],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("issuer_docx", type=Path)
    parser.add_argument("patent_original", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    if args.output.name != "original.json":
        parser.error("use the frozen original.json filename in the private output directory")
    lock_bytes = (PACKET / "freeze.json").read_bytes()
    for name, expected in json.loads(lock_bytes)["capture_inputs"].items():
        verified_bytes(ROOT / name, expected)
    start, cpu = perf_counter(), process_time()
    binding = issuer_binding(args.issuer_docx)
    patent = patent_reference(args.patent_original)
    cases = json.loads((PACKET / "runtime.json").read_bytes())
    for case in cases:
        if [case["request"]["round"], case["request"]["sequence"]] != binding["round_and_sequence"]["4"]:
            raise ValueError("stand-in request does not bind to the issuer key structure")
    traces = {case["id"]: {arm: run_case(case, arm, binding, patent) for arm in ARMS} for case in cases}
    record = {"freeze_sha256": digest(lock_bytes), "issuer_structure": binding, "traces": traces,
              "wall_seconds": perf_counter() - start, "cpu_seconds": process_time() - cpu}
    with args.output.open("x", encoding="utf-8", newline="\n") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()
