"""Audit C3 on development outcomes and score only an existing frozen queue export."""

import argparse
from collections import Counter, defaultdict
from dataclasses import asdict
from datetime import date
from hashlib import sha256
import json
from pathlib import Path
import re
from unittest.mock import patch

from c3_dev_guard import nda_reader
from freeze_run import manifest, read_json
from c3_edition_applicants import collect_listings
from t1v3_run import require_closed_seal
from t2_dev_run import ROOT, _verify
from t4_power import (approved_by, composite_items, project_development_anda, project_orange,
                      projected_annotation, projected_product, select_members)
from devx_run import OB_APPROVAL, OB_HISTORICAL, without_later_approvals
import t4_power

from loe_bench import c3, dataset, moiety
from loe_bench.common import add_months, read_jsonl
from loe_bench.nber_ob import DEFAULT_NBER_DIR
from loe_bench.ob_history import DEFAULT_DIR


AUDIT_DAYS = tuple(date(year, 1, 1) for year in range(2010, 2014))
SCORED_DAYS = (date(2013, 1, 1),)
CONFIG = "FROZEN_CONFIG.json"
SPEC = "C3_SPEC.json"


def _items(fields, key):
    raw = fields.get(key, b"null")
    return () if raw == b"null" else composite_items(raw)


def project_identity(line):
    """Retain linkage metadata without decoding any unadmitted outcomes."""
    fields = dict(composite_items(line))
    app = fields.get(b"application_number", b"")
    if not re.fullmatch(rb'"ANDA[0-9]{6}"', app):
        return None
    products = []
    for _, raw in _items(fields, b"products"):
        product = dict(composite_items(raw))
        if product.get(b"approval_date") in (None, b"null"):
            products.append(projected_product(product, set()))
    payload = {b"application_number": app, b"openfda": projected_annotation(fields.get(b"openfda")),
               b"products": b"[" + b",".join(products) + b"]"}
    return json.loads(select_members(payload, payload))


def approval_metadata(line, approved):
    """Project sponsor proxy and development-dated links on the admitted action."""
    fields = dict(composite_items(line))
    when = b'"' + approved.strftime("%Y%m%d").encode("ascii") + b'"'
    documents = set()
    for _, raw in _items(fields, b"submissions"):
        sub = dict(composite_items(raw))
        if (sub.get(b"submission_type"), sub.get(b"submission_status"),
                sub.get(b"submission_status_date")) != (b'"ORIG"', b'"AP"', when):
            continue
        for _, raw_doc in _items(sub, b"application_docs"):
            doc = dict(composite_items(raw_doc))
            published = doc.get(b"applications_doc_date")
            url = doc.get(b"application_docs_url", b"null")
            if approved_by(published) and published >= when and url != b"null":
                documents.add(json.loads(url))
    return {"snapshot_sponsor": json.loads(fields.get(b"sponsor_name", b"null")),
            "admitted_document_links": sorted(documents)}


def _inputs(raw):
    """Verify raw bytes and build the same development-scoped moiety linkage as FREEZE."""
    source = read_json("S0_INPUT_MANIFEST.json")
    hashes = {row["raw_file"]: row["sha256"] for row in source["files"]}
    names = ("df_nda.jsonl", "df_anda.jsonl", *OB_HISTORICAL)
    for name in names:
        _verify(raw / name, hashes[name])
    gsrs = raw.resolve().parent / "moiety" / moiety.GSRS_FILE
    registry = moiety.registry_for(raw, gsrs)
    records, identities, metadata = [], [], {}
    with (raw / "df_anda.jsonl").open("rb") as handle:
        for line_number, line in enumerate(handle, 1):
            record = project_development_anda(line)
            identity = record if record is not None else project_identity(line)
            if identity is not None:
                identities.append(identity)
            if record is not None:
                day, _ = next(dataset._final_originals(record))
                app = record["application_number"]
                if app in metadata:
                    raise ValueError(f"Duplicate admitted application {app}")
                records.append((record, day))
                metadata[app] = {"approval": day.isoformat(), "line": line_number,
                                 **approval_metadata(line, day)}

    def reader(path):
        path = Path(path)
        if path.name == "df_anda.jsonl":
            yield from identities
        elif path.name in ("ob_nda.jsonl", "df_nda.jsonl"):
            yield from nda_reader(path, read_jsonl, projector=t4_power, redact_dates=without_later_approvals)
        elif path.name in OB_HISTORICAL:
            with path.open("rb") as handle:
                for line in handle:
                    dates = OB_APPROVAL.findall(line)
                    if (dates and all(approved_by(b'"' + when + b'"') for when in dates)
                            or not dates and path.name == "ob_anda_pre1982.jsonl"):
                        record = project_orange(line, nda=False)
                        if record is not None:
                            yield record
        else:
            raise ValueError(f"Source outside C3 development allowlist: {path.name}")

    with (patch.object(moiety, "ORANGE_FILES", OB_HISTORICAL),
          patch.object(moiety, "read_jsonl", reader), patch.object(dataset, "read_jsonl", reader)):
        orange = moiety.orange_products(raw)
        linkage = dataset.build_moiety_linkage(raw, registry, orange)
        # Reuse the same linkage object for the roster and every approval.
        with patch.object(dataset, "build_moiety_linkage", return_value=linkage):
            entities = dataset.build_entities(raw, gsrs_path=gsrs, include_anda_outcomes=False)

    approvals, unlinked = [], 0
    for record, day in records:
        app = record["application_number"]
        groups = [(group, approved) for group, approved, _ in
                  dataset._original_compositions(record, day, registry, orange, linkage) if approved]
        unlinked += not groups
        for group, approved in groups:
            if group not in entities:
                continue
            proof = c3.Evidence(
                source="openFDA Drugs@FDA df_anda.jsonl", version=source["fetched_at_utc"],
                sha256=hashes["df_anda.jsonl"],
                locator=f"line {metadata[app]['line']}, {app}, ORIG/AP {day.isoformat()}",
            )
            approvals.append(c3.Approval(group, app, approved, proof))
            entity = entities[group]
            entity.anda_first = min(entity.anda_first or approved, approved)
    return entities, approvals, metadata, unlinked, {name: hashes[name] for name in names}, source["fetched_at_utc"]


def _history(path, digest, metadata):
    if path is None:
        return c3.ApplicantIndex()
    _verify(path, digest)
    history, aliases = [], []
    payload = dict(composite_items(path.read_bytes()))
    for field, constructor, result in ((b"history", c3.ApplicantHistory, history),
                                       (b"aliases", c3.NameAlias, aliases)):
        for _, raw in _items(payload, field):
            if field == b"history":
                app = dict(composite_items(raw)).get(b"application", b"")
                if not re.fullmatch(rb'"ANDA[0-9]{6}"', app) or app[1:-1].decode("ascii") not in metadata:
                    raise ValueError("Applicant history must refer to admitted development approvals")
            row = json.loads(raw)
            row["evidence"] = c3.Evidence(**row["evidence"])
            for name in ("start", "end"):
                row[name] = date.fromisoformat(row[name])
            result.append(constructor(**row))
    return c3.ApplicantIndex(history, aliases)


def _scores(path, digest, config_digest, roster, frozen_cutoffs):
    _verify(path, digest)
    fields = dict(composite_items(path.read_bytes()))
    source = json.loads(select_members(fields, {b"status", b"prediction_horizon_months", b"frozen_config_sha256"}))
    if (source["status"], source["prediction_horizon_months"], source["frozen_config_sha256"]) != (
            "DEVELOPMENT_ONLY", 24, config_digest):
        raise ValueError("Scores must come from the pinned frozen development queue")
    approved = {json.dumps(day).encode("ascii"): day for day in frozen_cutoffs
                if date.fromisoformat(day) < c3.FIRST_TEST}
    results = {arm: {} for arm in c3.ARMS}
    seen = set()
    counts = Counter()
    for _, raw in _items(fields, b"rows"):
        cutoff = dict(composite_items(raw)).get(b"cutoff")
        if cutoff not in approved:
            raise ValueError("Frozen score export contains an inadmissible cutoff")
        row = json.loads(raw)
        if set(row) != {"key", "cutoff", *c3.ARMS}:
            raise ValueError("Frozen score exports must contain only identifiers and native scores")
        key = row["key"], date.fromisoformat(row["cutoff"])
        if key in seen:
            raise ValueError("Frozen score export contains a duplicate row")
        seen.add(key)
        counts[approved[cutoff]] += 1
        if key[1] in SCORED_DAYS:
            if key not in roster:
                raise ValueError("Frozen score export contains an unexpected C3 row")
            for arm in c3.ARMS:
                results[arm][key] = row[arm]
    if dict(counts) != frozen_cutoffs or results["M3"].keys() != roster:
        raise ValueError("Frozen score export does not cover the full development rosters")
    return results


def _audit(roster, labels, metadata):
    decisions = Counter(labels[row].event for row in roster)
    applications = {app for row in roster for app in labels[row].applications}
    unresolved = {app for row in roster for app in labels[row].unresolved_applications}
    return {"rows": len(roster), "known_event_rows": decisions[True], "known_negative_rows": decisions[False],
            "unknown_rows": decisions[None],
            "event_drugs": len({key for key, day in roster if labels[key, day].event is True}),
            "unknown_drugs": len({key for key, day in roster if labels[key, day].event is None}),
            "recorded_window_applications": len(applications), "unresolved_applications": len(unresolved),
            "unresolved_with_snapshot_sponsor": sum(bool(metadata[app]["snapshot_sponsor"]) for app in unresolved),
            "unresolved_with_admitted_document_link": sum(
                bool(metadata[app]["admitted_document_links"]) for app in unresolved)}


def _fixtures(roster, labels, metadata):
    """Select by application count and canonical key before looking up applicant evidence."""
    selected = defaultdict(list)
    for key, day in sorted(roster):
        label = labels[key, day]
        count = len(label.applications)
        if count in (2, 3) and len(selected[count]) < 3:
            selected[count].append({
                "key": key, "cutoff": day.isoformat(), "applicant_bounds": [label.lower, label.upper],
                "event": label.event, "confirmed_applicants": label.confirmed_applicants,
                "unresolved_applications": label.unresolved_applications,
                "records": [{"application": app, **metadata[app]} for app in label.applications],
            })
    return dict(selected)


def _unique(names):
    return next(iter(names)) if len(names) == 1 else None


class WindowApplicants:
    """A pre-resolved index of applicant names for the audited applications."""

    def __init__(self, names):
        self.names = names

    def at_approval(self, approval):
        return self.names.get(approval.application)


def _historical_identity(approval, history, listings):
    direct = history.approval_records(approval)
    if direct:
        names = history.canonical_names((record.name for record in direct), approval.approved)
        evidence = [{**asdict(record.evidence), "name": record.name,
                     "effective_start": record.start.isoformat(), "effective_end": record.end.isoformat()}
                    for record in direct]
        return {"name": _unique(names), "source_kind": "approval_day", "evidence": evidence, "edition": None}
    eligible = [item for item in listings if approval.approved <= item.date <= add_months(approval.approved, 12)]
    if not eligible:
        return {"name": None, "source_kind": "no_listing", "evidence": [], "edition": None}
    first = min(item.date for item in eligible)
    selected = [item for item in eligible if item.date == first]
    names = history.canonical_names((item.name for item in selected if item.name), first)
    evidence = [{**asdict(item.evidence), "name": item.name, "source_kind": item.kind} for item in selected]
    kinds = "+".join(sorted({item.kind for item in selected}))
    return {"name": _unique(names), "source_kind": kinds, "evidence": evidence, "edition": first.isoformat()}


def _applicant_inputs(args, approvals, roster, history, metadata, snapshot_version):
    unresolved = c3.build_labels(roster, approvals, c3.ApplicantIndex(), observed_through=c3.DEVELOPMENT_END)
    used = {app for label in unresolved.values() for app in label.applications}
    by_app = {approval.application: approval for approval in approvals if approval.application in used}
    listings, inventory = collect_listings({app: approval.approved for app, approval in by_app.items()},
                                           args.ob_dir, args.nber_dir)
    snapshot_date = date.fromisoformat(snapshot_version.split("T")[0])
    records = {}
    for app, approval in sorted(by_app.items()):
        sponsor = metadata[app]["snapshot_sponsor"]
        names = history.canonical_names((sponsor,), snapshot_date) if sponsor and sponsor.strip() else set()
        records[app] = {
            "approval": approval.approved.isoformat(), "approval_evidence": asdict(approval.evidence),
            "primary": _historical_identity(approval, history, listings.get(app, ())),
            "sensitivity": {"name": _unique(names), "listed_name": sponsor,
                            "evidence": {**asdict(approval.evidence), "locator": f"line {metadata[app]['line']}, sponsor_name"}},
        }
    return records, inventory


def _comparison(roster, primary, sensitivity, records):
    applications = {app for row in roster for app in primary[row].applications}
    resolved_sources = Counter()
    unresolved_sources = Counter()
    comparable = agreements = 0
    for app in applications:
        left, right = (records[app][rule] for rule in ("primary", "sensitivity"))
        source = "/".join(part for part in (left["source_kind"], left["edition"]) if part)
        if left["name"] is None:
            unresolved_sources[source] += 1
        else:
            resolved_sources[source] += 1
        if left["name"] is not None and right["name"] is not None:
            comparable += 1
            agreements += left["name"] == right["name"]
    transitions = Counter()
    for row in roster:
        left, right = primary[row].event, sensitivity[row].event
        if left != right:
            transitions[left, right] += 1
    return {
        "comparable_applications": comparable, "agreeing_applications": agreements,
        "applicant_agreement": agreements / comparable if comparable else None,
        "resolved_by_source": dict(resolved_sources), "unresolved_by_source": dict(unresolved_sources),
        "determinate_threshold_label_differences": transitions[True, False] + transitions[False, True],
        "label_status_differences": sum(transitions.values()),
        "label_transitions": {f"{left} -> {right}": count for (left, right), count in transitions.items()},
    }


def _evaluate(rule, roster, panel, approvals, applicant_records, metadata, scores):
    index = WindowApplicants({app: record[rule]["name"] for app, record in applicant_records.items()})
    labels = c3.build_labels(roster, approvals, index, observed_through=c3.DEVELOPMENT_END)
    panel_labels = {row: labels[row].event for row in panel}
    panel_audit = _audit(panel, labels, metadata)
    irrecoverable = bool(panel_audit["recorded_window_applications"] and
                         panel_audit["recorded_window_applications"] == panel_audit["unresolved_applications"])
    irrecoverable |= any(labels[row].event is None and not labels[row].confirmed_applicants for row in panel)
    ranking = (c3.score(panel_labels, scores, observed_through=c3.DEVELOPMENT_END, history_irrecoverable=irrecoverable)
               if scores is not None else {"status": "BLOCKED_FROZEN_QUEUE_UNAVAILABLE", "event_rows": None,
                                           "recall": None, "delta": None, "ci95": None, "capture_bounds": None})
    return labels, {
        "history_irrecoverable": irrecoverable,
        "audit": _audit(roster, labels, metadata),
        "by_cutoff": {day.isoformat(): _audit({row for row in roster if row[1] == day}, labels, metadata)
                      for day in AUDIT_DAYS},
        "frozen_queue_panel": panel_audit, "ranking": ranking,
    }


def run(args):
    require_closed_seal()
    c3.window_ends(AUDIT_DAYS, c3.DEVELOPMENT_END)
    c3.window_ends(SCORED_DAYS, c3.DEVELOPMENT_END)
    spec = read_json(SPEC)
    spec_digest = manifest(SPEC)["sha256"]
    if (ROOT / "data/C3_SPEC.sha256").read_text(encoding="ascii").split()[0] != spec_digest:
        raise ValueError("C3 specification digest mismatch")
    config_digest = manifest(CONFIG)["sha256"]
    if config_digest != spec["frozen_queue"]["config_sha256"]:
        raise ValueError("C3 requires the canonical frozen configuration")
    entities, approvals, metadata, unlinked, hashes, snapshot_version = _inputs(args.raw)
    roster = {(row["key"], row["t"]): row for row in dataset.build_samples(
        entities, list(AUDIT_DAYS), c3.HORIZON, c3.DEVELOPMENT_END)}
    panel = {row for row in roster if row[1] in SCORED_DAYS}
    checks = read_json("FREEZE_dev_report.json")["horizons"]["24"]["cutoffs"]
    expected = {date.fromisoformat(row["cutoff"]): row["rows"] for row in checks if
                date.fromisoformat(row["cutoff"]) in SCORED_DAYS}
    if dict(Counter(day for _, day in panel)) != expected:
        raise ValueError("C3 development roster count differs from FREEZE")
    frozen_cutoffs = {row["cutoff"]: row["rows"] for row in checks}
    scores = (_scores(args.frozen_scores, args.scores_sha256, config_digest, panel, frozen_cutoffs)
              if args.frozen_scores is not None else None)
    history = _history(args.history, args.history_sha256, metadata)
    applicant_records, inventory = _applicant_inputs(args, approvals, roster, history, metadata, snapshot_version)
    primary, primary_report = _evaluate("primary", roster, panel, approvals, applicant_records, metadata, scores)
    sensitivity, sensitivity_report = _evaluate(
        "sensitivity", roster, panel, approvals, applicant_records, metadata, scores)
    require_closed_seal()
    return {
        "status": "DEVELOPMENT_ONLY", "spec_sha256": spec_digest, "s0_raw_sha256": hashes,
        "gsrs_sha256": moiety.GSRS_SHA256, "history_sha256": args.history_sha256,
        "frozen_scores_sha256": args.scores_sha256,
        "admitted_original_final_andas": len(metadata), "admitted_without_linked_group": unlinked,
        "observation_end": c3.DEVELOPMENT_END.isoformat(),
        **primary_report, "sensitivity": sensitivity_report,
        "applicant_comparison": {
            "pooled": _comparison(roster, primary, sensitivity, applicant_records),
            "by_cutoff": {day.isoformat(): _comparison({row for row in roster if row[1] == day},
                                                       primary, sensitivity, applicant_records) for day in AUDIT_DAYS},
        },
        "applicant_evidence": applicant_records, "edition_inventory": inventory,
        "frozen_queue_cutoffs": [day.isoformat() for day in SCORED_DAYS],
        "frozen_queue_slots": {day.isoformat(): rows // 5 for day, rows in expected.items()},
        "fixtures": _fixtures(panel, primary, metadata),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=Path(DEFAULT_DIR).parent / "raw-20261127")
    parser.add_argument("--history", type=Path)
    parser.add_argument("--history-sha256")
    parser.add_argument("--ob-dir", type=Path, default=Path(DEFAULT_DIR))
    parser.add_argument("--nber-dir", type=Path, default=Path(DEFAULT_NBER_DIR))
    parser.add_argument("--frozen-scores", type=Path)
    parser.add_argument("--scores-sha256")
    parser.add_argument("--output", type=Path, required=True, help="Development-only report path")
    args = parser.parse_args()
    for path, digest in ((args.history, args.history_sha256), (args.frozen_scores, args.scores_sha256)):
        if (path is None) != (digest is None) or (digest is not None and not re.fullmatch(r"[0-9a-f]{64}", digest)):
            parser.error("Optional evidence and score artifacts each require a pinned SHA-256")
    report = run(args)
    raw = (json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")
    with args.output.open("xb") as handle:
        handle.write(raw)
    print(f"{args.output} {sha256(raw).hexdigest()}")


if __name__ == "__main__":
    main()
