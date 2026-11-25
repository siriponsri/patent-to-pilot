"""Rebuild or byte-verify the frozen, fictional S1 pilot. Never runs a policy."""

import argparse
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path

if __package__:
    from .s1_material import FAMILIES
    from .s1_scorer import LIMITS, check_splits
else:
    from s1_material import FAMILIES
    from s1_scorer import LIMITS, check_splits

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/evidence-scope/research"
RECEIPTS = ROOT / "docs/tracking/owner-note-22112026/receipts"
STATES = ("present", "displaced", "outside")
SEED = 20261125
P2_RT = "d3b7826783d53e958280f3c5150e0fb80a1264e9b315493e2f6e2f6f37f9a407"
P2_EV = "5e16c2f3e77fece4fc97a8d2563d34aab39a25f420de2431d6fdac19ce681da8"
P2_IDS = "3911605ec0a8351d573c4f540a96387d998c78f5cd5273f7ed56500b2f5b4b4d"
PINNED_RECEIPTS = {
    "P2-T04_frozen_protocol.md": "7f578a345cacda173fb6e202dfd8224e21f107d7",
    "P2-T04_results.md": "8f5542a30c66153901f904eac461ae81c663017c",
    "P3-T02_packets_summary.json": "43caf34e781204c468a3879ae4daaf5c2af0f602",
}


def sha(value):
    return hashlib.sha256(value).hexdigest()


def identifier(*values):
    return sha("|".join(map(str, (SEED, *values))).encode())[:18]


def jsonline(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def encoded(rows):
    return ("\n".join(jsonline(row) for row in rows) + "\n").encode("utf-8")


def materialize(f):
    slug = f["key"]
    fam = "s1-" + slug
    lang = f["language"]
    local_sources = {}
    indexes = []
    for i, branch in enumerate(f["branches"]):
        for j in (0, 2):
            loc, text = branch[j:j + 2]
            # Claims and examples in one publication. Thai enclosures are separate sources.
            doc = "main" if lang == "en" or j == 0 else "attachment"
            local_sources.setdefault(doc, []).append((loc, text))
            indexes.append((doc, loc))
    for i, text in enumerate(f["background"], 1):
        loc = f"Note {i}" if lang == "en" else f"หมายเหตุ {i}"
        local_sources["main"].append((loc, text))
        indexes.append(("main", loc))
    units, docs = {}, []
    for doc, passages in local_sources.items():
        sid = fam + "-" + doc
        body = "\n".join(f"{loc}\n{text}" for loc, text in passages)
        checksum = sha(body.encode())
        docs.append(dict(source_id=sid, version="1", sha256=checksum, text=body,
                         fictional=True, family_id=fam, language=lang))
        for loc, text in passages:
            start = body.index(f"{loc}\n{text}") + len(loc) + 1
            uid = identifier(sid, loc)
            units[doc, loc] = dict(unit_id=uid, source_id=sid, family_id=fam, version="1",
                                   sha256=checksum, locator=loc, char_start=start,
                                   char_end=start+len(text), unit_sha256=sha(text.encode()),
                                   text=text, language=lang)
    u = [units[k] for k in indexes]
    kinds = {"reed": "amendment", "fern": "amendment", "loom": "exception",
             "bell": "table_scope", "tray": "inherits_claim", "fold": "embodiment",
             "frame": "embodiment", "dial": "embodiment", "spool": "diagram_reference"}
    edges = []
    for a, b in ((0, 1), (2, 3)):
        kind = kinds.get(slug, "cross_reference")
        if a == 2 and kind in {"amendment", "exception"}:
            kind = "cross_reference"
        edges.append(dict(**{"from": u[a]["unit_id"], "to": u[b]["unit_id"]},
                          kind=kind, basis=u[a]["text"], inferred=False))
    return docs, u, edges


def cases(f, units):
    family = units[0]["family_id"]
    ids = [u["unit_id"] for u in units]
    public, labels, pairs = [], [], []
    all_case_ids = []
    for index, state in enumerate(STATES):
        case_ids = []
        for wording, question in enumerate(f["requests"][:3]):
            branch = int(wording == 2)
            required = ids[branch*2:branch*2+2]
            other = ids[(1-branch)*2:(1-branch)*2+2]
            # Preserve the exact seed and available corpus across paraphrases.
            position = identifier(family, "rank")
            witness = sorted(required, key=lambda uid: identifier(position, uid))
            rivals = sorted(other, key=lambda uid: identifier(position, uid))
            noise = sorted(ids[4:], key=lambda uid: identifier(position, uid))
            if state == "present":
                pool = witness + rivals
            elif state == "displaced":
                pool = rivals + witness
            else:
                # One reference header and an answer-bearing unit from the other branch.
                # Both questions see exactly the same incompatible initial evidence.
                partial = [ids[0], ids[3]] if int(position, 16) % 2 else [ids[1], ids[2]]
                pool = sorted([*partial, *noise],
                              key=lambda uid: identifier(position, uid))
            cid = identifier(family, index, wording)
            case_ids.append(cid)
            public.append(dict(case_id=cid, family_id=family, question=question,
                               language=f["language"], seed_pool=pool))
            labels.append(dict(case_id=cid, family_id=family, state=state, status="ANSWERABLE",
                               decision=f["answers"][branch],
                               witness_assignments=[dict(required=required, permitted=required)]))
        all_case_ids.append(case_ids)
    for index, case_ids in enumerate(all_case_ids):
        # Keep corpus, pool membership AND ranking fixed across both edits.
        alternate_index = (1, 0, 2)[index]
        for role, ends in (("invariant", case_ids[:2]),
                           ("changing", [case_ids[0], all_case_ids[alternate_index][2]])):
            if (FAMILIES.index(f) + index) % 2:
                ends = ends[::-1]
            pairs.append(dict(pair_id=identifier(family, index, role), edit=role, cases=ends,
                              rationale="wording preserves the referenced scope" if role == "invariant"
                              else "changed request selects a different documented scope"))
    cid = identifier(family, "closed")
    public.append(dict(case_id=cid, family_id=family, question=f["requests"][3],
                       language=f["language"], seed_pool=sorted(ids, key=lambda x: identifier(cid,x))[:4]))
    labels.append(dict(case_id=cid, family_id=family, state=None, status="FINITE_UNANSWERABLE",
                       decision="ABSTAIN", witness_assignments=[]))
    return public, labels, pairs


def packet():
    from collections import defaultdict
    output, files = {}, defaultdict(list)
    splits, totals = [], Counter()
    for f in FAMILIES:
        lane = f["lane"]
        docs, units, edges = materialize(f)
        requests, labels, pairs = cases(f, units)
        splits.append(dict(family_id=units[0]["family_id"], lane=lane,
                           lineages=["original-" + f["key"], "template-" + f["key"]]))
        for name, rows in (("sources", docs), ("units", units), ("edges", edges), ("requests", requests)):
            files[f"runtime/{lane}/{name}.jsonl"].extend(rows)
        files[f"evaluator/{lane}/labels.jsonl"].extend(labels)
        files[f"evaluator/{lane}/pairs.jsonl"].extend(pairs)
        for label in labels:
            totals[(lane, f["language"], label["state"] or "finite_unanswerable")] += 1
    check_splits(splits)
    files["evaluator/splits.jsonl"] = splits
    for key, rows in files.items():
        # Stable, opaque dispatch order; never group requests by evaluator state.
        output[key] = encoded(sorted(rows, key=lambda row: row.get("case_id", jsonline(row))))
    counts = [dict(lane=lane, language=lang, state=state, count=n)
              for (lane, lang, state), n in sorted(totals.items())]
    manifest = dict(revision="S1-v1", seed=SEED, limits=LIMITS, counts=counts,
                    files={name: dict(bytes=len(data), sha256=sha(data))
                           for name, data in sorted(output.items())})
    manifests = ["scripts/research/s1_scorer.py", "scripts/research/s1_material.py",
                 "scripts/research/s1_packet.py", "docs/evidence-scope/research/MEASUREMENT.md",
                 "docs/evidence-scope/research/RIGHTS.md"]
    manifest["protocol_lf_sha256"] = {
        name: sha((ROOT / name).read_bytes().replace(b"\r\n", b"\n")) for name in manifests}
    output["manifest.json"] = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
    return output


def verify_private():
    import sys
    summary = json.loads((RECEIPTS / "P3-T02_packets_summary.json").read_bytes())
    private = ROOT.parent / "_private_artifacts"
    allow = {}
    for item, folder in (("statute", "nitibench-statute@069e774f"),
                         ("wangchanx", "WangchanX-Legal-ThaiCCL-RAG@654e1a10")):
        row = summary["inputs"][item]
        fname = {"statute": "ccl", "wangchanx": "train"}[item] + "-00000-of-00001.parquet"
        assert row["file"] == "data/" + fname
        allow["thai-data/" + folder + "/data/" + fname] = row["sha256"]
    for name in ("requests", "sources"):
        rel = "dev/" + name + ".jsonl"
        allow["thai-data/packets-v1/" + rel] = summary["outputs_sha256"][rel]
    prefix = "p2t04-preflight-20261124/freeze-cutoff-v1/"
    allow[prefix + "runtime-cutoff-v1.json"] = P2_RT
    allow[prefix + "evaluator-cutoff-v1.json"] = P2_EV
    for path, expected in allow.items():
        file = private / path
        h = hashlib.sha256()
        with file.open("rb") as reader:
            for block in iter(lambda: reader.read(1024 * 1024), b""):
                h.update(block)
        if h.hexdigest() != expected:
            sys.exit("private hash mismatch: " + path)
        print(path, file.stat().st_size, expected)
    ids = json.loads((private / (prefix + "runtime-cutoff-v1.json")).read_bytes())["query_ids"]
    if sha(jsonline(ids).encode()) != P2_IDS:
        sys.exit("historical cohort hash mismatch")
    print("P2 ordered cohort", len(ids), P2_IDS)
    for name, expected in PINNED_RECEIPTS.items():
        rel = (RECEIPTS / name).relative_to(ROOT).as_posix()
        actual = subprocess.check_output(["git", "rev-parse", f"HEAD:{rel}"], cwd=ROOT, text=True).strip()
        if actual != expected:
            sys.exit("Git blob mismatch: " + rel)
        print(name, actual)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("build", "verify", "verify-private"))
    mode = parser.parse_args().mode
    if mode == "verify-private":
        verify_private()
    else:
        blobs = packet()
        for name, content in blobs.items():
            path = OUT / name
            if mode == "build":
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
            elif path.read_bytes() != content:
                raise SystemExit("byte mismatch: " + name)
        print(mode, len(blobs), "files; corpus and protocol only")
