"""Generate explicitly authored Thai development packets and a separate reference key."""
import argparse
import json
import random
from pathlib import Path

SEED = 2026112603
LAYOUTS = ("valid-bundle", "stale-bundle", "direct", "unresolved")


def make_packet(group, layout, rng):
    family = f"controlled-family-{group}"
    dossier = f"case-{rng.getrandbits(64):016x}"
    identity = {
        "applicant": f"ผู้ยื่นสมมติ-{rng.getrandbits(64):016x}",
        "application": f"ตัวอย่าง-{group}-{rng.randrange(1000, 9999)}",
        "round": "2", "sequence": "0004",
    }
    stale = identity | {"sequence": "0003"}
    other = identity | {"applicant": f"ผู้ยื่นรายอื่น-{group}"}
    requested = ["assay", "stability"]
    documents = {}
    visible = []

    def report(topics, scope, preview, exposed=True):
        tag = f"d-{rng.getrandbits(64):016x}"
        documents[tag] = json.dumps({
            "kind": "report", "role": "applicant_result", "scope": scope,
            "results": {topic: f"ผลประกอบการทดสอบสมมติ {topic}" for topic in topics},
            "title": "เอกสารผลทดสอบจำลองเพื่อทดสอบการส่งต่อ",
        }, ensure_ascii=False, sort_keys=True)
        card = {"id": tag, "kind": "report", "advertises": topics, "scope": preview}
        if exposed:
            visible.append(card)
        return card

    def locator(follow):
        tag = f"d-{rng.getrandbits(64):016x}"
        documents[tag] = json.dumps({
            "kind": "locator", "follow": follow, "title": "สารบัญเอกสารแนบจำลอง",
        }, ensure_ascii=False, sort_keys=True)
        visible.append({"id": tag, "kind": "locator", "advertises": requested, "scope": None})

    # Reference facts come from the independently declared layout, without reading document bytes.
    if layout == "unresolved":
        report(["assay"], other, None)
        report(["stability"], stale, None)
        locator(None)
        valid = {"assay": [], "stability": []}
    else:
        first = report(["assay"], identity, identity)
        if layout == "direct":
            second = report(["stability"], identity, identity)
            valid = {"assay": [first["id"]], "stability": [second["id"]]}
        elif layout == "valid-bundle":
            report(["stability"], stale, None)
            bundle = report(requested, identity, identity, exposed=False)
            locator(bundle)
            valid = {"assay": [first["id"], bundle["id"]], "stability": [bundle["id"]]}
        elif layout == "stale-bundle":
            second = report(["stability"], identity, None)
            locator(report(requested, stale, stale, exposed=False))
            valid = {"assay": [first["id"]], "stability": [second["id"]]}
        else:
            raise ValueError(f"unknown layout: {layout}")
    rng.shuffle(visible)
    packet = {"id": dossier, "family": family, "request": identity, "rows": requested,
              "title": "ขอหลักฐานผลทดสอบของผู้ยื่นตามรอบและลำดับที่กำหนด",
              "catalog": visible, "documents": documents}
    key = {"family": family, "layout": layout, "valid": {
        row: {doc: f"/results/{row}" for doc in docs} for row, docs in valid.items()
    }}
    return packet, key


def generate(output):
    output.mkdir(parents=True, exist_ok=False)
    rng = random.Random(SEED)
    generated = [make_packet(group, layout, rng) for group in range(1, 4) for layout in LAYOUTS]
    rng.shuffle(generated)
    data = {"runtime.json": [packet for packet, _ in generated],
            "key.json": {packet["id"]: key for packet, key in generated}}
    for name, obj in data.items():
        with (output / name).open("x", encoding="utf-8", newline="\n") as dest:
            json.dump(obj, dest, ensure_ascii=False, indent=2, sort_keys=True)
            dest.write("\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    generate(parser.parse_args().output)
