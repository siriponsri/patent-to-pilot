"""Re-run the offline backend on supplied Abbott dossier snapshots for UI checks.

No acquisition or embedding is performed. Raw outputs belong in private local
storage; only the caller's sanitized summary should enter the public audit.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
from patent_to_pilot.healthtech.abbott import promote_disclosed_links
from patent_to_pilot.healthtech.contracts import DossierVersion, content_hash
from patent_to_pilot.healthtech.engine import DossierInput, PatentInput, run_dossier, serialize_dossier, export_markdown
from patent_to_pilot.healthtech.history import save_version, append_user_edits, source_view
from patent_to_pilot.healthtech.provenance import check_evidence
from patent_to_pilot.healthtech.rights import RightsBoundaryError


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dossier", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--code-commit", required=True)
    args = parser.parse_args()
    originals = [DossierVersion.model_validate_json(p.read_text(encoding="utf-8")) for p in args.dossier]
    # The first supplied case must cover its complete patent-source universe.
    # IDs are copied from canonical candidates, never guessed from source URLs.
    base = originals[0]
    candidates = {c.source_id: c for c in base.candidates}
    patent_sources = [s for s in base.sources if s.source.source_type == "patent_document"]
    if not patent_sources or any(s.source.source_id not in candidates for s in patent_sources):
        parser.error("first dossier must identify every patent source with a candidate")
    patents = [PatentInput(
        patent_id=candidates[s.source.source_id].patent_id_raw,
        title=candidates[s.source.source_id].patent_id_canonical, source=s,
    ) for s in patent_sources]
    args.output.mkdir(parents=True, exist_ok=False)
    cases = []
    for original in originals:
        query_id = original.query.query_id
        if not query_id.replace("-", "").isalnum():
            parser.error("unsafe query ID")
        data = DossierInput(
            query=original.query,
            sources=[s for s in original.sources if s.source.source_type != "patent_document"],
            patents=patents, evidence=original.evidence,
        )
        dossier, events, manifest = run_dossier(data, run_id=f"ui-{query_id}", code_commit=args.code_commit)
        dossier = promote_disclosed_links(dossier, data)
        out = args.output / query_id
        out.mkdir()
        save_version(out / "history", dossier)
        dossier = append_user_edits(out / "history", {"integration_note": "Current backend edit retained in UI TH/EN"}, expected_parent_version=1)
        for e in dossier.evidence:
            source = next(s for s in dossier.sources if s.source.source_id == e.source_id)
            check_evidence(e, source)
        source_view(dossier, dossier.query.selected_comparator_source_id)
        (out / "dossier.json").write_text(json.dumps(serialize_dossier(dossier), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (out / "manifest.json").write_text(manifest.model_dump_json(indent=2) + "\n", encoding="utf-8")
        (out / "acquisition_events.jsonl").write_text("".join(e.model_dump_json() + "\n" for e in events), encoding="utf-8")
        for lang in ("th", "en"):
            (out / f"dossier.{lang}.md").write_text(export_markdown(dossier, language=lang), encoding="utf-8")
        try:
            serialize_dossier(dossier, purpose="product_display")
        except RightsBoundaryError:
            display = "BLOCKED_EXPECTED_LOCAL_RESEARCH_ONLY"
        else:
            display = "ALLOWED_BY_RECORDED_POLICY"
        cases.append({"query_id": query_id, "source_dossier_sha256": content_hash(original.model_dump(mode="json")),
                      "dossier_sha256": content_hash(serialize_dossier(dossier)), "patent_inputs": len(patents),
                      "candidates": len(dossier.candidates), "disclosed_links": sum(c.association_status == "disclosed_link" for c in dossier.candidates),
                      "history_versions": [1, 2], "events": len(events), "search_calls": manifest.actual_search_calls,
                      "product_display": display})
    summary = {"status": "PASS_CURRENT_BACKEND_LOCAL_CASES", "generated_at": datetime.now(timezone.utc).isoformat(),
               "cases": cases, "provider_calls": 0, "paid_cost_usd": 0,
               "retrieval": "current offline lexical backend; original patent IDs used as title labels; no new dense encoding or scientific comparison"}
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
