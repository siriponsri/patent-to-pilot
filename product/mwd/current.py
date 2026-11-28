"""Materialize the two Track A queues and their shared as-of dossiers offline."""

import argparse
from collections import Counter
from datetime import date
from hashlib import sha256
from itertools import groupby
import json
from math import isfinite
from pathlib import Path
import re
import sys
from tempfile import TemporaryDirectory

from .audit import audit_dossier
from .build import Dossier, add_listings, orange_source
from .contract import (BENCH, CURRENT, ROOT, SECTIONS, TRACK_A_DISCLAIMER, TRACK_A_LABEL,
                       read_json, write_json)
from .inputs import PRIVATE, gsrs_names, verify

T0 = date(2026, 11, 27)
HORIZONS = (12, 24)
CORE = "TRACKA_CORE_MANIFEST.json"
BASE = "https://github.com/siriponsri/patent-to-pilot/blob/5861d077/loe-bench/data/"
PRIOR_ARMS = ("P1-RSF-OPEN", "P2-COX-OPEN")


def core_module():
    sys.path[:0] = [str(ROOT / "loe-bench"), str(ROOT / "loe-bench" / "scripts")]
    import tracka_core
    return tracka_core


def verified_package(package):
    pins = {}
    for line in (package / "SHA256SUMS").read_text(encoding="ascii").splitlines():
        digest, name = line.split("  ", 1)
        path = package / name
        if (not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", name)
                or name.casefold() in {item.casefold() for item in pins}
                or path.resolve().parent != package.resolve() or path.is_symlink()
                or not re.fullmatch(r"[a-f0-9]{64}", digest)):
            raise ValueError("Invalid Track A SHA256SUMS entry")
        verify(path, digest)
        pins[name] = digest
    if pins.get(CORE) != sha256((BENCH / CORE).read_bytes().replace(b"\r\n", b"\n")).hexdigest():
        raise ValueError("Track A core manifest differs from the published pin")
    manifest = read_json(package / CORE)
    prior = read_json(BENCH / "PRIORARMS_MANIFEST.json")
    if (manifest["t0"] != T0.isoformat() or prior["t0"] != T0.isoformat()
            or prior["tracka_core_manifest_sha256"] != pins[CORE]
            or any(pins.get(name) != digest for name, digest in
                   (manifest["files_sha256"] | prior["files_sha256"]).items())):
        raise ValueError("Track A package differs from the core or prior-arm pins")
    return pins, manifest


def jsonl(path):
    with path.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream]


def aligned_rows(rows, horizon, keys, arms=None):
    identity = {"t0": T0.isoformat(), "horizon_months": horizon}
    fields = identity.keys() | {"key"} | ({"arms"} if arms else set())
    if ([row["key"] for row in rows] != keys
            or any(row.keys() != fields or any(row[k] != v for k, v in identity.items()) for row in rows)
            or (arms and any(set(row["arms"]) != set(arms) for row in rows))):
        raise ValueError(f"Invalid {horizon}-month Track A rows")
    return rows


def score(value):
    if type(value) not in (int, float) or not isfinite(value) or not 0 <= value <= 1:
        raise ValueError("Invalid native score")
    return value


def ranked_rows(rows, priors, names):
    """Rank equal native scores together and share the remaining capacity uniformly."""
    ordered = sorted(rows, key=lambda row: (-score(row["arms"]["M3"]["native"]), row["key"]))
    capacity = len(ordered) // 5
    ranked, boundary = [], dict(capacity=capacity, boundary_native_score=None, above_boundary=0,
                                boundary_rows=0, slots_at_boundary=0, boundary_inclusion_probability=None)
    for native, group in groupby(ordered, key=lambda row: row["arms"]["M3"]["native"]):
        tied = list(group)
        above = len(ranked)
        probability = max(0, min(capacity - above, len(tied))) / len(tied)
        if above < capacity <= above + len(tied):
            boundary.update(boundary_native_score=native, above_boundary=above, boundary_rows=len(tied),
                            slots_at_boundary=capacity - above, boundary_inclusion_probability=probability)
        for row in tied:
            key, arms = row["key"], row["arms"]
            if probability != arms["M3"]["queue_inclusion_probability"]:
                raise ValueError("M3 inclusion probability differs from pinned prediction")
            ranked.append(dict(
                key=key, display_name=names[key], m3_rank=above + 1, m3_p=native,
                b1_p=score(arms["B1"]["native"]), m1_p=score(arms["M1"]["native"]),
                p1_p=score(priors[key]["P1-RSF-OPEN"]["native"]),
                p2_p=score(priors[key]["P2-COX-OPEN"]["native"]),
                queue_inclusion_probability=probability, in_queue=probability == 1,
            ))
    return ranked, boundary


class CurrentEvidence:
    def __init__(self, private, work, core, manifest):
        config = read_json(BENCH / "FROZEN_CONFIG.json")
        _, gsrs, entities, builder, inputs = core.source_inputs(private, config, work)
        if inputs != manifest["inputs"]:
            raise ValueError("Replayed Track A source pins differ")
        selected, coverage = builder.select_edition(T0)
        edition_audit = core.verify_editions(builder, {T0})[T0.isoformat()]
        if edition_audit != manifest["edition_audit"][T0.isoformat()]:
            raise ValueError("Replayed Track A edition selection differs")
        roster, summary = core.forecast_roster(entities)
        if summary != manifest["eligibility"]:
            raise ValueError("Replayed Track A eligibility differs")
        self.keys = [row["key"] for row in roster]
        self.names = gsrs_names(gsrs, self.keys)
        self.ob_entries = {entry["sha256"]: entry for entry in read_json(BENCH / "OB_EDITIONS.json")["editions"]}
        self.builder = builder
        self.orange = selected.identity, coverage["availability_proof"], selected.edition_date.isoformat()
        self.by_key = {}
        self.piv_status = edition_audit["paragraph_iv"]["status"]
        for row in roster:
            key = row["key"]
            self.by_key[key] = builder.build(key, T0, 24, row["x"])
        actual = dict(Counter(item.challenge.state.name for item in self.by_key.values()))
        if any(actual != manifest["horizons"][str(h)]["challenge_state"] for h in HORIZONS):
            raise ValueError("Replayed Track A challenge states differ")
        self.index = builder._indexes[selected]
        self.root = private

    def listing(self, cutoff, key):
        canonical = self.builder.linker.canonical(key)
        patents, exclusivities = self.index.records(canonical)
        return self.orange, self.index.linked_products[canonical], patents or [], exclusivities or []


def add_current_challenges(report, evidence, cutoff, key, scope):
    from c9_dev_projection import corroboration_date
    from loe_bench.challenge_patents import normalize_patent_number

    challenge = evidence.by_key[key].challenge
    report.claim(
        "piv-coverage", "patents",
        "ยังไม่ทราบสถานะจากรายการ Paragraph IV ของ FDA เพราะไม่มีฉบับที่ผ่านเกณฑ์ ณ วันตัดข้อมูล",
        "FDA Paragraph IV list status is unknown because no edition met the as-of coverage rule.",
        [scope], "unknown",
    )
    if not challenge.witnesses:
        report.claim("challenge-unknown", "patents", "ยังไม่ทราบสถานะการท้าทายในชุดหลักฐานที่ตรวจ",
                     "Challenge status is unknown within the admitted evidence.", [scope], "unknown")
    challenged = {}
    for i, witness in enumerate(challenge.witnesses, 1):
        ref = f"challenge-{i}"
        report.source(ref, "U.S. district court filings, indexed by Rai et al.",
                      "Patent litigation docket", witness.version, witness.date.isoformat(),
                      witness.locator, witness.url, witness.sha256)
        refs = [ref]
        if witness.source == "RAI_OB_PATENT":
            for j, match in enumerate(witness.corroboration["matches"], 1):
                ob = match["orange_book"]
                verify(evidence.root / "ob_editions" / ob["file"], ob["sha256"])
                match_ref = orange_source(report, evidence, f"{ref}-ob-{j}", ob, ob["availability_proof"],
                                          ob["edition_date"], ob["locator"])
                refs.append(match_ref)
                challenged.setdefault(normalize_patent_number(match["patent"]), []).extend([ref, match_ref])
            numbers = ", ".join(sorted({match["patent"] for match in witness.corroboration["matches"]}))
            lead = f"links to listed patent(s) {numbers}"
            lead_th = f"เชื่อมโยงกับสิทธิบัตรในรายการ {numbers}"
        elif witness.source == "RAI_COURT":
            doc = witness.corroboration
            day = corroboration_date(doc)
            locator = doc["locator"]
            if day is None:
                day = date(int(doc["version"].rsplit(", ", 1)[1]), 12, 31)
                locator += "; edition year upper bound"
            refs.append(report.source(f"{ref}-doc", "U.S. court or FDA", "Court case identity corroboration",
                                      doc["version"], day.isoformat(), locator, doc["url"], doc["sha256"]))
            lead = f"links to the NDA brand {doc['brand']}"
            lead_th = f"เชื่อมโยงกับยาต้นแบบ {doc['brand']}"
        else:
            raise ValueError(f"Unexpected Track A challenge source: {witness.source}")
        report.claim(ref, "patents",
                     f"คดี {witness.document_id} ยื่นวันที่ {witness.date} {lead_th} "
                     "ใช้วันที่ยื่นเป็นวันเปิดเผยโดยประมาณ ผลคดียังต้องตรวจสอบ",
                     f"Docket {witness.document_id}, filed {witness.date}, {lead}. "
                     "The replay uses filing as a proxy for public availability. Verify the disposition.",
                     refs)
    return challenged


def add_registry_tasks(report, name, patents, refs):
    patent_terms = sorted({f"US {p['patent_no']}" for p in patents if p["patent_no"]})
    report.claim("thai-status", "thai_asean",
                 "ยังไม่ทราบสถานะสิทธิบัตรและทะเบียนยาในไทยและประเทศอาเซียนเป้าหมาย",
                 "Patent and drug registration status in Thailand and target ASEAN jurisdictions is unknown.",
                 refs, "unknown")
    for id, agency, url, owner, terms, th, en in (
        ("th-dip", "Thai DIP", "https://patentsearch.ipthailand.go.th/", "FTO evaluator", [name, *patent_terms],
         "ค้นเลข WO และเลขคำขอที่ใช้อ้างสิทธิครั้งแรก แล้วตรวจเลขคำขอในไทย ข้อถือสิทธิ และสถานะที่กรมทรัพย์สินทางปัญญา",
         "Find WO and priority numbers, then verify Thai application IDs, claims and legal status with DIP."),
        ("asean-ip", "ASEAN IP Register and national IP offices", "https://ip-register.aseanip.org/",
         "FTO evaluator", [name, *patent_terms],
         "ใช้เลข WO และเลขคำขอที่ใช้อ้างสิทธิครั้งแรกตรวจตระกูลสิทธิบัตรและสถานะกับสำนักงานของประเทศเป้าหมาย",
         "Use WO and priority numbers to verify national family members and legal status in each target country."),
        ("th-fda", "Thai FDA NDI", "https://ndi.fda.moph.go.th/drug_info", "R&D", [name],
         "ค้นตัวยาสำคัญและรูปแบบยาในทะเบียนของ อย. ไทย แล้วตรวจเลขทะเบียนและสถานะ",
         "Search by active ingredient and dosage form, then verify registration IDs and status with Thai FDA."),
        ("asean-drug", "Target national medicines regulators", None, "R&D", [name],
         "ระบุประเทศเป้าหมายและตรวจเลขทะเบียนยาและสถานะกับหน่วยงานกำกับดูแลของแต่ละประเทศ",
         "Specify target markets and verify drug registration IDs and status with each national regulator."),
    ):
        report.task(id, f"{agency} · {th} (ยังไม่ทราบสถานะ)", f"{agency} · {en} Status unknown.", owner, refs)
        report.checklist[-1].update(agency=agency, lookup_url=url, state="unknown",
                                    search_terms=list(dict.fromkeys(terms)), wo_numbers=[], priority_numbers=[])


def build_dossier(key, horizon_rows, evidence, pins, version, status):
    day = T0.isoformat()
    report = Dossier()
    forecasts = {}
    scope = report.source("tracka-scope", "LOE-Bench", "Track A evidence coverage",
                          pins[CORE], None, f"{CORE}, eligibility and edition_audit[{day}]",
                          BASE + CORE, pins[CORE])
    report.sources[scope]["evidence_cutoff"] = day
    for horizon, row in horizon_rows.items():
        file = f"core_predictions_{horizon}m.jsonl"
        ref = report.source(f"score-{horizon}", "LOE-Bench", "Track A native forecast scores", pins[file], None,
                            f"{file}, key={key}, t0={day}, horizon_months={horizon}, arms M3 and B1",
                            BASE + CORE, pins[file])
        report.sources[ref]["evidence_cutoff"] = day
        probability = row["queue_inclusion_probability"]
        slots = row["queue_size"]
        rank = row["m3_rank"]
        report.claim(f"queue-{horizon}", "decision",
                     f"{horizon} เดือน · ลำดับ {rank} ตามคะแนน M3 · โอกาสเข้าคิวตรวจ {probability:.2%} "
                     f"จากโควตาตรวจ {slots} รายการ หากคะแนนตรงเส้นตัดเท่ากัน จะให้โอกาสเข้าคิวเท่ากัน",
                     f"{horizon} months · M3 rank {rank} · {probability:.2%} inclusion probability "
                     f"with {slots} expected slots. Boundary ties share the remaining slots uniformly.",
                     [ref], kind="estimate")
        report.claim(f"entry-{horizon}", "market",
                     f"คะแนน M3 สำหรับการอนุมัติ ANDA ขั้นสุดท้ายครั้งแรกในสหรัฐฯ ภายใน {horizon} เดือน "
                     f"เท่ากับ {row['m3_p']:.4g} วันอนุมัติและวันวางจำหน่ายเป็นคนละเหตุการณ์",
                     f"M3 native score {row['m3_p']:.4g} for first final US ANDA approval within {horizon} "
                     "months. Approval and commercial launch are separate events.", [ref], kind="estimate")
        forecasts[horizon] = dict(horizon_months=horizon, m3_p_entry=row["m3_p"], b1_p_entry=row["b1_p"],
                                  m3_rank=rank, queue_size=slots, in_queue=row["in_queue"], status=status,
                                  queue_inclusion_probability=probability)
    report.claim("at-risk", "competition",
                 "ไม่พบการอนุมัติ ANDA ต้นฉบับขั้นสุดท้ายถึงวันตัดข้อมูลในประวัติที่เชื่อมโยงได้ "
                 "จำนวนผู้ผลิตที่วางจำหน่ายยังไม่ทราบ",
                 "The Track A roster contains linked histories with no first final original ANDA approval "
                 "through t0. Marketed producer count is unknown.", [scope])
    forms, refs = add_listings(report, evidence, day, key, scope, challenge_adder=add_current_challenges)
    _, _, patents, _ = evidence.listing(day, key)
    add_registry_tasks(report, evidence.names[key], patents, refs)
    report.task("review-spec", "ระบุรูปแบบยา ความแรง ข้อบ่งใช้ และวันเปิดตัวเป้าหมาย",
                "Specify dosage form, strength, indication and target launch date.", "R&D", [scope])
    return dict(schema_version="mwd.dossier.v1", as_of=day, jurisdiction="US",
                molecule=dict(key=key, display_name=evidence.names[key], dosage_forms=forms),
                forecast=forecasts[24], forecast_12m=forecasts[12], version=version, label=TRACK_A_LABEL,
                disclaimer=TRACK_A_DISCLAIMER, challenge_state=evidence.by_key[key].challenge.state.name,
                fda_piv_coverage=evidence.piv_status,
                sections=[dict(id=id, title_th=th, title_en=en) for id, th, en in SECTIONS],
                claims=report.claims, sources=list(report.sources.values()), checklist=report.checklist)


def freeze_version(core, pins, tag=None, manifest_path=None):
    version = {"freeze": "pending", "core_manifest_sha256": pins[CORE]}
    if tag is not None:
        # The planner supplies the externally verified release tag and its tagged manifest path.
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]*", tag) or not re.fullmatch(
                r"loe-bench/data/[A-Za-z0-9_-]+\.json", manifest_path):
            raise ValueError("Invalid Track A release tag or manifest path")
        manifest = core.git("show", f"refs/tags/{tag}:{manifest_path}")
        release = json.loads(manifest)
        # The freeze must bind the exact two inputs to the current queue (directly or via manifests).
        values = set(re.findall(r'"([0-9a-f]{64})"', manifest.decode("utf-8")))
        prior = read_json(BENCH / "PRIORARMS_MANIFEST.json")
        prior_hash = sha256((BENCH / "PRIORARMS_MANIFEST.json").read_bytes().replace(b"\r\n", b"\n")).hexdigest()
        if (not isinstance(release, dict) or pins[CORE] not in values
                or (prior_hash not in values and not set(prior["files_sha256"].values()) <= values)):
            raise ValueError("Tagged freeze manifest does not bind the core and prior-arm data")
        version.update(freeze="verified", tag=tag, manifest_sha256=sha256(manifest).hexdigest())
    return version


def materialize(private, out, *, tag=None, manifest_path=None, core=None):
    package = private / "trackA"
    pins, manifest = verified_package(package)
    core = core or core_module()
    version = freeze_version(core, pins, tag, manifest_path)
    status = "TRACK_A_FROZEN" if tag else "TRACK_A_PENDING"
    roster = jsonl(package / "roster.jsonl")
    if out.exists():
        raise FileExistsError(f"Choose a new output directory: {out}")
    out.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".track-a-", dir=out.parent) as stage:
        evidence = CurrentEvidence(private, Path(stage), core, manifest)
        keys = evidence.keys
        if len(keys) != 651 or len(roster) != len(keys) * len(HORIZONS):
            raise ValueError("Unexpected Track A roster size")
        staged = Path(stage) / "current"
        indexed, by_horizon = [], {}
        paths = {key: f"dossier-{re.sub(r'[^A-Za-z0-9_-]+', '-', key)}-{T0}.json" for key in keys}
        if len({path.casefold() for path in paths.values()}) != len(keys):
            raise ValueError("Track A dossier path collision")
        for horizon in HORIZONS:
            aligned_rows([r for r in roster if r["horizon_months"] == horizon], horizon, keys)
            filename = f"core_predictions_{horizon}m.jsonl"
            rows = aligned_rows(jsonl(package / filename), horizon, keys, core.ARMS)
            priors = aligned_rows(jsonl(package / f"priorarms_predictions_{horizon}m.jsonl"),
                                  horizon, keys, PRIOR_ARMS)
            ranked, boundary = ranked_rows(rows, {r["key"]: r["arms"] for r in priors}, evidence.names)
            if boundary != manifest["horizons"][str(horizon)]["arms"]["M3"]["queue"]:
                raise ValueError(f"Track A {horizon}-month queue boundary differs from core manifest")
            name = f"queue-{T0}-{horizon}m.json"
            slots = boundary["capacity"]
            for row in ranked:
                row.update(dossier_path=paths[row["key"]], queue_size=slots)
            queue = dict(schema_version="mwd.queue.v1", as_of=T0.isoformat(), horizon_months=horizon,
                         window_end=date(T0.year + horizon // 12, T0.month, T0.day).isoformat(),
                         queue_size=slots, status=status, label=TRACK_A_LABEL, version=version,
                         ranked_rows=ranked, score_export_sha256=pins[filename], boundary=boundary,
                         secondary_score_export_sha256=pins[f"priorarms_predictions_{horizon}m.jsonl"],
                         tie_rule="Rank by descending native M3. Boundary ties share remaining slots uniformly. "
                                  "Ascending key controls display order within a tie.",
                         disclaimer=TRACK_A_DISCLAIMER)
            write_json(staged / name, queue)
            indexed.append(dict(path=name, as_of=T0.isoformat(), horizon_months=horizon))
            by_horizon[horizon] = {row["key"]: row for row in ranked}
        dossiers = []
        for key, path in paths.items():
            dossier = build_dossier(key, {h: by_horizon[h][key] for h in HORIZONS}, evidence, pins, version, status)
            audit = audit_dossier(dossier)
            if audit["errors"]:
                raise ValueError(f"Track A dossier audit failed for {key}: {audit['errors']}")
            write_json(staged / path, dossier)
            dossiers.append(dict(key=key, display_name=evidence.names[key], path=path, horizons=list(HORIZONS)))
        write_json(staged / "index.json", dict(schema="mwd.index.v1", as_of=T0.isoformat(), fixture=False,
                                               status=status, jurisdiction="US", label=TRACK_A_LABEL,
                                               version=version, disclaimer=TRACK_A_DISCLAIMER,
                                               queues=indexed, dossiers=dossiers))
        if out.exists():
            raise FileExistsError(f"Concurrent Track A output directory: {out}")
        staged.rename(out)
    return len(keys)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--private-root", type=Path, default=PRIVATE)
    parser.add_argument("--out", type=Path, default=CURRENT)
    parser.add_argument("--verified-freeze-tag")
    parser.add_argument("--verified-freeze-manifest", help="Repository-relative manifest path in the tag")
    args = parser.parse_args()
    if (args.verified_freeze_tag is None) != (args.verified_freeze_manifest is None):
        parser.error("Supply both verified freeze arguments")
    core = core_module()
    sys.addaudithook(core.network_guard)
    count = materialize(args.private_root, args.out, tag=args.verified_freeze_tag,
                        manifest_path=args.verified_freeze_manifest, core=core)
    print(f"Built {count} dossiers and two queues at {args.out}")


if __name__ == "__main__":
    main()
