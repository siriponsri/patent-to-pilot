"""Export the C9 development projection and freeze its shared CPU roster."""

import argparse
from collections import Counter, defaultdict
from datetime import date, timedelta
from importlib.metadata import version
from pathlib import Path
import os
import subprocess
from tempfile import TemporaryDirectory
from unittest.mock import patch

from c3_dev_run import ROOT, _inputs, _verify, read_json
from c9.checkpoint import model_manifest
from c9.inputs import (SPEC_SHA256, checked_bytes, file_digest, jsonl_bytes, schedule, specification,
                       write_json)
from c9.roster import prepare
from devx_run import (DEVELOPMENT_END, OB_HISTORICAL, application_identity_reader,
                      dated_brands, partition)
from l1dev_local import entity_name, gsrs_names
from t4_power import project_orange

from loe_bench import c9, dataset, l1e_prompt, moiety, ob_linkage
from loe_bench.challenge import ChallengeIdentity, court_rows
from loe_bench.challenge_patents import FilingPatentIndex, PatentChallengeHistory
from loe_bench.common import parse_yyyymmdd
from loe_bench.ob_history import DEFAULT_DIR, OBHistory
from loe_bench.piv_history import EntityMatcher, PIVHistory
from loe_bench.seal import ENV_NAME, TestSealError
from loe_bench.t2_features import AsOfBuilder


DAYS = sorted(c9.TRAIN_CUTOFFS)
PRIVATE = Path(DEFAULT_DIR).parent
CODE_PATHS = ("loe-bench/scripts/c9_dev_projection.py", "loe-bench/scripts/c3_dev_run.py")


def require_development():
    if ENV_NAME in os.environ or DEVELOPMENT_END != date(2016, 1, 1):
        raise TestSealError("C9PROJ requires the bounded development reader without test authorization")


def code_revision():
    def git(*args):
        return subprocess.check_output(["rtk", "proxy", "git", *args],
                                       cwd=ROOT.parent, text=True).strip()

    if git("status", "--porcelain", "--", *CODE_PATHS):
        raise ValueError("Commit the projection implementation before export")
    return git("rev-parse", "HEAD")


def evidence(source_id, version, sha256, locator, recorded, available):
    return dict(source_id=source_id, version=version, sha256=sha256, locator=locator,
                record_date=recorded.isoformat(), available_on=available.isoformat())


def excluded_approvals(raw, trace, metadata):
    """List excluded actions, keeping Orange Book identity leads separate from labels."""
    excluded = {app: {"application": app, "approval": metadata[app]["approval"],
                      "line": metadata[app]["line"], **groups, "orange_book_leads": []}
                for app, groups in trace["unresolved"].items()}
    for name in OB_HISTORICAL[1:]:
        with (raw / name).open("rb") as stream:
            for line, payload in enumerate(stream, 1):
                # Select only admitted products before they reach the decoder.
                row = project_orange(payload, nda=False)
                for product in (row or {}).get("products", ()):
                    app = "ANDA" + str(product.get("application_number", "")).zfill(6)
                    if app not in excluded or excluded[app]["dated_groups"]:
                        continue
                    when = parse_yyyymmdd(product.get("approval_date"))
                    if when is not None and when > date.fromisoformat(excluded[app]["approval"]):
                        continue
                    composition = trace["registry"].orange_book(product)
                    if composition.key:
                        excluded[app]["orange_book_leads"].append({
                            "file": name, "line": line, "product": product.get("product_number")
                            or row["product_number"], "key": trace["linkage"].key(composition.key),
                            "product_date": when.isoformat() if when else None,
                        })
    return [excluded[app] for app in sorted(excluded)]


def linkage_scope(excluded):
    """Give dated uncertainty to identifiable rows and a sensitivity-only pool to the rest."""
    ambiguous = defaultdict(list)
    unattributable = []
    for item in excluded:
        when = date.fromisoformat(item["approval"])
        candidates = set(item["undated_groups"]) - set(item["dated_groups"])
        candidates.update(lead["key"] for lead in item["orange_book_leads"])
        for key in candidates:
            ambiguous[key].append(when)
        if not item["dated_groups"] and not candidates:
            unattributable.append(when)
    return ambiguous, unattributable


def nda_evidence(raw, trace):
    records = defaultdict(list)
    for row in trace["reader"](raw / "df_nda.jsonl"):
        originals = list(dataset._final_originals(row))
        first = min((when for when, _ in originals), default=None)
        for key, when, _ in dataset._original_compositions(
            row, first, trace["registry"], trace["orange"], trace["linkage"]
        ):
            if when is not None:
                records[key].append((when, row["application_number"], row))
    return records


def nda_proofs(records, cutoff, hashes, snapshot):
    proofs = []
    for approved, app, row in records:
        if approved > cutoff:
            continue
        for when, submission in dataset._final_originals(row):
            if when <= cutoff:
                tags = submission.get("submission_class_code")
                proofs.append(evidence("openFDA df_nda.jsonl", snapshot, hashes["df_nda.jsonl"],
                                       f"{app}, submissions ORIG/AP {when}, class {tags}", when, when))
        for product in row.get("products") or ():
            when = parse_yyyymmdd(product.get("approval_date"))
            if when is not None and max(when, approved) <= cutoff and product.get("route"):
                locator = f"{app}, products {product.get('product_number')}, approval {when}, route"
                proofs.append(evidence("openFDA df_nda.jsonl", snapshot, hashes["df_nda.jsonl"],
                                       locator, when, max(when, approved)))
    return proofs


def predictor_builder(raw, entities, trace, gsrs):
    """Rebuild the C2 feature inputs on all declared C9 dates with the guarded linker."""
    lock = read_json("FROZEN_CONFIG.json")["input_sha256"]
    for key in ("ob_manifest", "piv_manifest", "court_manifest"):
        pin = lock[key]
        checked_bytes(ROOT / "data" / pin["file"], pin["sha256"], lf=True)

    def linker_reader(path):
        return (application_identity_reader(path) if Path(path).name == "df_anda.jsonl"
                else trace["reader"](path))

    with (patch.object(moiety, "ORANGE_FILES", OB_HISTORICAL),
          patch.object(moiety, "read_jsonl", trace["reader"]),
          patch.object(ob_linkage, "read_jsonl", linker_reader),
          patch("e7_dev_run.read_jsonl", trace["reader"])):
        linker = ob_linkage.HistoricalMoietyLinker(raw, entities, gsrs_path=gsrs)
        identity = ChallengeIdentity(linker, dated_brands(raw, linker))
    history = OBHistory.from_records(read_json("OB_EDITIONS.json"), DEFAULT_DIR)
    piv = PIVHistory(ROOT / "data/PIV_EDITIONS.json", PRIVATE / "piv", EntityMatcher([]))
    sources = read_json("E7_sources.json")
    rai = sources["rai"]
    rai_path = PRIVATE / "challenge" / rai["file"]
    _verify(rai_path, rai["sha256"])
    # C2's filing-date rule is used for the filing itself. A later document
    # cannot establish the case-type or name admission at an earlier cutoff.
    corroboration = []
    for case in sources["corroborated_cases"]:
        document = sources["corroborating_documents"][case["document"]]
        if date.fromisoformat(document["version"][:10]) <= DAYS[-1]:
            _verify(PRIVATE / "challenge" / document["file"], document["sha256"])
            corroboration.append({**case, **document})
    challenge = PatentChallengeHistory(
        piv, identity, court_rows(rai_path, DAYS[-1] + timedelta(days=1)),
        rai, corroboration, FilingPatentIndex(history, linker),
    )
    builder = AsOfBuilder(history, linker=linker, challenge=challenge)
    for source in {builder.select_edition(day)[0] for day in DAYS} - {None}:
        _verify(Path(DEFAULT_DIR) / source.identity["file"], source.identity["sha256"])
    return builder, {key: lock[key] for key in ("ob_manifest", "piv_manifest", "court_manifest")}


def predictor_proofs(builder, row):
    key, cutoff = builder.linker.canonical(row["key"]), row["t"]
    source, coverage = builder.select_edition(cutoff)
    if source is not None:
        index = builder._indexes[source]
        products = index.linked_products.get(key, ())
        patents, exclusivities = index.records(key)
        locators = [entry["locator"] for entry in (*products, *(patents or ()), *(exclusivities or ()))]
        locator = "; ".join(locators) or f"products table, no linked NDA presentation for {key}"
        name = source.identity["file"]
        proof = coverage["availability_proof"]
        yield evidence(name, source.edition_date.isoformat(), source.identity["sha256"],
                       f"{locator}; availability {proof['url']}", source.edition_date,
                       date.fromisoformat(proof["date"]))
    for witness in row["asof"].challenge.witnesses:
        available = witness.date
        if witness.source == "FDA_PIV":
            available = builder.challenge.piv.edition_asof(cutoff).captured.date()
        elif witness.source == "RAI_COURT":
            available = date.fromisoformat(witness.corroboration["version"][:10])
        elif witness.source == "RAI_OB_PATENT":
            for match in witness.corroboration["matches"]:
                listing = match["orange_book"]
                proof = listing["availability_proof"]
                yield evidence(listing["file"], listing["edition_date"], listing["sha256"],
                               f"{listing['locator']}; availability {proof['url']}",
                               date.fromisoformat(listing["edition_date"]), date.fromisoformat(proof["date"]))
        yield evidence(witness.source, witness.version, witness.sha256, witness.locator,
                       witness.date, available)
    piv_coverage = builder.challenge._piv(cutoff)[1]
    if piv_coverage["status"] == "FRESH":
        piv_edition = piv_coverage["edition"]
        yield evidence("FDA_PIV", piv_edition["version"], piv_edition["sha256"],
                       f"{piv_edition['file']}, PIV list, identity lookup for {key}; {piv_edition['wayback_url']}",
                       date.fromisoformat(piv_edition["version"]),
                       builder.challenge.piv.edition_asof(cutoff).captured.date())


def sensitivity(rows, unlinked):
    prior = sum(any(when <= row["t"] for when in unlinked) for row in rows)
    window = sum(any(row["t"] < when <= row["t_end"] for when in unlinked) for row in rows)
    both = sum(any(when <= row["t_end"] for when in unlinked) for row in rows)
    negatives = sum(not row["y"] and any(row["t"] < when <= row["t_end"] for when in unlinked)
                    for row in rows)
    return dict(prior_eligibility=prior, within_window=window, union=both, negative_labels=negatives)


def counts(rows):
    positive = sum(rows)
    return {"positive": positive, "negative": len(rows) - positive}


def export(raw, code_commit):
    require_development()
    spec = specification()
    s0 = read_json("S0_INPUT_MANIFEST.json")
    if date.fromisoformat(s0["t0"]) != c9.S0 or DEVELOPMENT_END > c9.S0:
        raise ValueError("S0 does not cover the development outcomes")
    gsrs = raw.resolve().parent / "moiety" / moiety.GSRS_FILE
    _verify(gsrs, moiety.GSRS_SHA256)
    trace = {}
    entities, approvals, metadata, unlinked, hashes, snapshot = _inputs(raw, trace=trace)
    excluded = excluded_approvals(raw, trace, metadata)
    if sum(not item["dated_groups"] for item in excluded) != unlinked:
        raise ValueError("excluded application count differs from C3")
    ambiguous, unattributable = linkage_scope(excluded)
    builder, feature_manifests = predictor_builder(raw, entities, trace, gsrs)
    candidates = sorted(partition(entities, builder, DAYS, c9.HORIZON_MONTHS),
                        key=lambda row: (row["t"], row["key"]))
    rows = [row for row in candidates
            if not any(when <= row["t_end"] for when in ambiguous.get(row["key"], ()))]
    names = gsrs_names(gsrs, {part[2:] for row in rows for part in row["key"].split("|")
                             if part.startswith("U:")})
    nda = nda_evidence(raw, trace)
    first = {}
    for approval in sorted(approvals, key=lambda item: (item.approved, item.application)):
        first.setdefault(approval.group, approval)
    projections = []
    for row in rows:
        key, cutoff, end = row["key"], row["t"], row["t_end"]
        entity = entities[key]
        as_of = nda_proofs(nda[key], cutoff, hashes, snapshot)
        as_of.extend(predictor_proofs(builder, row))
        outcome = [evidence("openFDA df_anda.jsonl", snapshot, hashes["df_anda.jsonl"],
                            f"S0 pinned ANDA partition, first ORIG/AP lookup for {key} through {end}",
                            end, c9.S0)]
        event = first[key] if row["y"] else None
        if event:
            proof = event.evidence
            outcome.append(evidence(proof.source, proof.version, proof.sha256, proof.locator,
                                    event.approved, c9.S0))
        projections.append(dict(
            drug_key=key, original_nda=entity.nda_first.isoformat(), type1=entity.flag_dates["nme"].isoformat(),
            covered_through=end.isoformat(), resolved_linkage=True,
            first_final_anda=event.approved.isoformat() if event else None,
            forecast=dict(entity=entity_name(key, names), t0=cutoff.isoformat(), horizon_months=c9.HORIZON_MONTHS,
                          as_of_evidence=l1e_prompt.from_m3(row)),
            provenance=dict(as_of=as_of, outcome=outcome),
        ))
    report = dict(code_commit=code_commit, spec_lf_sha256=SPEC_SHA256, snapshot=snapshot,
                  observed_through=DEVELOPMENT_END.isoformat(), s0_raw_sha256=hashes,
                  gsrs_sha256=moiety.GSRS_SHA256, feature_manifests=feature_manifests,
                  admitted_anda_applications=len(metadata),
                  excluded_no_dated_group_count=unlinked,
                  fully_unattributable_count=len(unattributable), excluded_or_ambiguous_anda=excluded,
                  omitted_ambiguous_rows=len(candidates) - len(rows),
                  sensitivity_upper_bounds=sensitivity(rows, unattributable),
                  eligible_rows=len(rows), class_counts=counts([row["y"] for row in rows]),
                  eligible_by_cutoff=dict(sorted(Counter(row["t"].isoformat() for row in rows).items())))
    require_development()
    return dict(schema="c9-development-v1", s0_manifest_lf_sha256=spec["s0"]["manifest_lf_sha256"],
                rows=projections), report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=PRIVATE / "raw-20261127")
    parser.add_argument("--out", type=Path, default=PRIVATE / "c9")
    parser.add_argument("--checkpoint", type=Path, default=PRIVATE / "c9/checkpoint")
    parser.add_argument("--manifest-dir", type=Path, default=ROOT / "data")
    args = parser.parse_args()
    out, manifests = args.out.resolve(), args.manifest_dir.resolve()
    if out.is_relative_to(ROOT.parent):
        parser.error("private outputs must be outside the repository")
    paths = (out / "c9_dev_projection.json", out / "c9_dev_roster.jsonl",
             manifests / "C9_DEV_PROJECTION_MANIFEST.json", manifests / "C9_DEV_ROSTER_MANIFEST.json")
    if any(path.exists() for path in paths):
        parser.error("output paths must be fresh")
    projection, roster, projection_manifest, roster_manifest = paths
    revision = code_revision()
    checkpoint = model_manifest(args.checkpoint, dry=False)
    envelope, report = export(args.raw, revision)
    spec = specification()
    with TemporaryDirectory(dir=out) as staging:
        staged = Path(staging) / projection.name
        write_json(staged, envelope)
        sha = file_digest(staged)
        rows, _, _, freeze = prepare(args.checkpoint, staged, sha, spec, dry=False)
    batches, width, updates = schedule(spec)
    if len(rows) != batches * width:
        raise ValueError("shared roster does not match the frozen batch schedule")
    write_json(projection, envelope)
    if file_digest(projection) != sha:
        raise ValueError("published projection differs from the roster input")
    write_json(projection_manifest, report | {"path": projection.as_posix(), "sha256": sha})
    with roster.open("xb") as stream:
        stream.write(jsonl_bytes(rows))
    write_json(roster_manifest, freeze | {
        "code_commit": revision, "path": roster.as_posix(), "sha256": file_digest(roster),
        "checkpoint": checkpoint, "checkpoint_manifest_sha256": file_digest(args.checkpoint / "checkpoint.json"),
        "batches": batches, "prompts_per_batch": width,
        "updates_per_batch": updates, "arms": ["sft", "grpo"],
        "distinct_rows": len({(row["drug_key"], row["t0"]) for row in rows}),
        "class_counts": counts([row["label"] for row in rows]),
        "tokenizer_library": f"transformers {version('transformers')}; tokenizers {version('tokenizers')}",
    })


if __name__ == "__main__":
    main()
