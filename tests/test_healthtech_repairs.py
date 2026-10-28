from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from concurrent.futures import ThreadPoolExecutor
import json
import threading

import pytest

from patent_to_pilot.evaluation.healthtech.local_retrieval import (
    PatentRecord,
    _OnnxTokenizer,
)
from patent_to_pilot.evaluation.healthtech.provenance import (
    CohortProvenanceError,
    verify_cohort_provenance,
)
from patent_to_pilot.healthtech.engine import DossierInput, export_markdown, run_dossier
from patent_to_pilot.healthtech import history as history_module
from patent_to_pilot.healthtech.abbott import (
    build_abbott_case_inputs,
    build_abbott_development_protocol,
    promote_disclosed_links,
)
from patent_to_pilot.healthtech.history import (
    DossierHistoryError,
    append_user_edits,
    load_versions,
    recover_staging_files,
    save_version,
)
from patent_to_pilot.healthtech.rights import RightsBoundaryError
from scripts.healthtech.fetch_boston_watchman_cohort import PRODUCTS, _validate_product_rows
from scripts.healthtech.fetch_public_device_cohort import _rights_policy_id, _source_registry_row
from scripts.healthtech import run_real_baselines as baselines


ROOT = Path(__file__).resolve().parents[1]
TOKENIZER = ROOT / "data/raw/healthtech/models/sentence-transformers-all-MiniLM-L6-v2/tokenizer.json"


@pytest.mark.skipif(not TOKENIZER.exists(), reason="pinned local tokenizer artifact is unavailable")
def test_onnx_tokenizer_uses_native_masks_types_and_deterministic_padding():
    tokenizer = _OnnxTokenizer(str(TOKENIZER), max_length=256)
    short = "mitral valve"
    long = " ".join(["valve"] * 400)

    first = tokenizer.encode_texts([short, long])
    second = tokenizer.encode_texts([short, long])
    ids, masks, types, token_count = first

    assert ids.shape == (2, 256)
    assert masks.shape == types.shape == ids.shape
    assert int(masks[0].sum()) == 5
    assert int(masks[1].sum()) == 256
    assert token_count == int(masks.sum())
    assert int(masks[0][ids[0] == tokenizer.pad_id].sum()) == 0
    assert (ids == second[0]).all()
    assert (masks == second[1]).all()
    assert (types == second[2]).all()

    pair_ids, pair_masks, pair_types, pair_tokens = tokenizer.encode_pairs([("query", "document")])
    assert pair_ids.shape == pair_masks.shape == pair_types.shape == (1, 256)
    assert pair_tokens == int(pair_masks.sum())
    assert int(pair_masks[0].sum()) == 5
    assert 1 in set(pair_types[0].tolist())
    assert int(pair_masks[0][pair_ids[0] == tokenizer.pad_id].sum()) == 0


def _device():
    return SimpleNamespace(
        query_id="q1",
        company="Example Co",
        technical_description="first fixed query",
        features_of_interest=["second fixed query"],
    )


def _patents():
    return [
        PatentRecord(
            "US000001A1", "US000001A1", "US-grant", "US", "One", "One", "claim", "one",
            "source", "v1", "urn:one", "a" * 64, "b" * 64, "2026-01-01", "Example Co", "source",
        ),
        PatentRecord(
            "US000002A1", "US000002A1", "US-grant", "US", "Two", "Two", "claim", "two",
            "source", "v1", "urn:two", "c" * 64, "d" * 64, "2026-01-01", "Example Co", "source",
        ),
    ]


class _FakeRetriever:
    def __init__(self, fail_on: int | None = None):
        self.calls: list[str] = []
        self.fail_on = fail_on

    def fixed_bundle(self, query: str, *, candidate_depth: int, rerank_depth: int):
        self.calls.append(query)
        if self.fail_on == len(self.calls):
            raise RuntimeError(f"failure on action {len(self.calls)}")
        return {
            "query": query,
            "query_hash": baselines.stable_json_hash(query),
            "reranked": [{"patent_id_canonical": "US000001A1", "score": 1.0, "rank": 1}],
            "resources": {
                "query_calls": 1,
                "rerank_pairs": 1,
                "returned_candidates": 1,
                "embedding_query_tokens": 5,
                "rerank_tokens": 7,
            },
            "observables": {"lexical_dense_disagreement": 0.0},
        }


def test_baseline_preserves_completed_attempt_before_later_failure():
    result = baselines._run_method(
        _device(), _patents(), method="HT-B2", lexical=None, retriever=_FakeRetriever(fail_on=2),
        candidate_depth=2, rerank_depth=2,
    )

    assert result["status"] == "failed"
    assert [attempt["status"] for attempt in result["attempts"]] == ["completed", "failed"]
    assert [attempt["query"] for attempt in result["attempts"]] == ["first fixed query", "second fixed query"]
    assert result["resources"]["query_calls"] == 2
    assert result["resources"]["rerank_pairs"] == 1
    assert result["final_ranking"][0]["patent_id_canonical"] == "US000001A1"


def test_baseline_records_failure_before_dispatch_with_zero_query_calls(monkeypatch):
    def fail_before_schedule(_device):
        raise RuntimeError("pre-dispatch failure")

    monkeypatch.setattr(baselines, "_fixed_queries", fail_before_schedule)
    result = baselines._run_method(
        _device(), _patents(), method="HT-B2", lexical=None, retriever=_FakeRetriever(),
        candidate_depth=2, rerank_depth=2,
    )

    assert result["status"] == "failed"
    assert len(result["attempts"]) == 1
    assert result["attempts"][0]["status"] == "failed"
    assert result["attempts"][0]["query"] == "first fixed query"
    assert result["attempts"][0]["resources"]["query_calls"] == 0


def test_b1_and_fixed_multiquery_methods_share_first_query_text():
    b1_retriever = _FakeRetriever()
    b2_retriever = _FakeRetriever()
    b1 = baselines._run_method(_device(), _patents(), method="HT-B1", lexical=None, retriever=b1_retriever, candidate_depth=2, rerank_depth=2)
    baselines._run_method(_device(), _patents(), method="HT-B2", lexical=None, retriever=b2_retriever, candidate_depth=2, rerank_depth=2)
    assert b1["prefix_diagnostics"]["first_query"] == b2_retriever.calls[0]
    assert b1_retriever.calls[0] == b2_retriever.calls[0] == "first fixed query"


def test_frontier_reports_prefix_quality_resources_and_nonrealized_queries():
    def attempt(attempt_id: int, ranking: list[str], *, query_calls: int = 1):
        return {
            "attempt_id": attempt_id,
            "status": "completed",
            "query": f"query-{attempt_id}",
            "ranking": [
                {"patent_id_canonical": patent_id, "score": 1.0, "rank": rank}
                for rank, patent_id in enumerate(ranking, 1)
            ],
            "resources": {
                "query_calls": query_calls,
                "returned_candidates": len(ranking),
                "rerank_pairs": len(ranking),
            },
        }

    rows = []
    for method in baselines.METHODS:
        for query_id, first_query_hash, attempts in (
            ("q1", "shared-q1", [attempt(1, ["US000002A1", "US000001A1"]), attempt(2, ["US000001A1", "US000002A1"])]),
            ("q2", "shared-q2", [attempt(1, ["US000001A1", "US000002A1"])]) if method == "HT-B3" else
            ("q2", "shared-q2", [attempt(1, ["US000002A1", "US000001A1"]), attempt(2, ["US000001A1", "US000002A1"])]),
        ):
            rows.append({
                "method": method,
                "query_id": query_id,
                "status": "completed",
                "attempts": attempts,
                "prefix_diagnostics": {"first_query_hash": first_query_hash, "scheduled_queries": ["a", "b"]},
            })

    frontier = baselines._quality_resource_frontier(
        rows,
        {"q1": ["US000001A1"], "q2": ["US000002A1"]},
        ["US000001A1", "US000002A1"],
        [["q1", "q2"]],
        ["q1", "q2"],
    )

    b2_rows = [row for row in frontier["rows"] if row["method"] == "HT-B2"]
    b3_rows = [row for row in frontier["rows"] if row["method"] == "HT-B3"]
    assert [row["prefix"] for row in b2_rows] == [1, 2]
    assert b2_rows[1]["query_calls"] == 4
    assert b3_rows[1]["not_realized_query_count"] == 1
    assert frontier["fixed_prefix_alignment"]["first_query_match_across_fixed_methods"] is True
    assert frontier["uncertainty"]["status"] == "NOT_ESTIMABLE"


def test_history_rejects_stale_parent_and_export_includes_user_edits(tmp_path):
    example = json.loads((ROOT / "examples/healthtech/synthetic-device/input.json").read_text(encoding="utf-8"))
    dossier, _, _ = run_dossier(DossierInput.model_validate(example), run_id="repair-history", code_commit="test")
    history = tmp_path / "history"
    save_version(history, dossier)
    edited = append_user_edits(history, {"audit-note": "keep this in export"}, expected_parent_version=1)

    with pytest.raises(DossierHistoryError, match="expected parent version"):
        append_user_edits(history, {"stale": "writer"}, expected_parent_version=1)
    with pytest.raises(DossierHistoryError, match="version already exists"):
        save_version(history, dossier)

    markdown = export_markdown(edited, language="en")
    assert "## User edits" in markdown
    assert "keep this in export" in markdown
    assert "Dossier version: 2" in markdown
    assert "Parent version: 1" in markdown
    assert "Validation scope: source_integrity_only" in markdown
    assert "type regulatory_record" in markdown
    assert "type patent_document" in markdown
    assert "synthetic true" in markdown

    thai = export_markdown(edited, language="th")
    assert "Dossier version: 2" in thai
    assert "Parent version: 1" in thai
    assert "## Source manifest" in thai
    assert "sha256" in thai


def test_history_two_simultaneous_writers_have_one_commit_and_one_conflict(tmp_path):
    example = json.loads((ROOT / "examples/healthtech/synthetic-device/input.json").read_text(encoding="utf-8"))
    dossier, _, _ = run_dossier(DossierInput.model_validate(example), run_id="concurrent-history", code_commit="test")
    history = tmp_path / "history"
    save_version(history, dossier)
    barrier = threading.Barrier(2)

    def writer(key: str):
        barrier.wait()
        try:
            version = append_user_edits(history, {key: f"pending-{key}"}, expected_parent_version=1)
            return {"status": "committed", "key": key, "version": version.version}
        except DossierHistoryError as exc:
            return {"status": "conflict", "key": key, "pending_text": f"pending-{key}", "error": str(exc)}

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(writer, ["writer-a", "writer-b"]))

    assert sorted(item["status"] for item in results) == ["committed", "conflict"]
    assert [item.version for item in load_versions(history)] == [1, 2]
    assert any(item.get("pending_text") == "pending-writer-a" for item in results) or any(item.get("pending_text") == "pending-writer-b" for item in results)


def test_history_reader_never_sees_partial_published_version(tmp_path, monkeypatch):
    example = json.loads((ROOT / "examples/healthtech/synthetic-device/input.json").read_text(encoding="utf-8"))
    dossier, _, _ = run_dossier(DossierInput.model_validate(example), run_id="atomic-reader", code_commit="test")
    history = tmp_path / "history"
    save_version(history, dossier)
    updated = dossier.model_copy(update={"version": 2, "parent_version": 1})
    staged = threading.Event()
    release = threading.Event()
    original_fdopen = history_module.os.fdopen

    def paused_fdopen(*args, **kwargs):
        staged.set()
        assert release.wait(5)
        return original_fdopen(*args, **kwargs)

    monkeypatch.setattr("patent_to_pilot.healthtech.history.os.fdopen", paused_fdopen)
    errors = []

    def writer():
        try:
            save_version(history, updated)
        except BaseException as exc:
            errors.append(exc)

    thread = threading.Thread(target=writer, daemon=True)
    thread.start()
    assert staged.wait(5)
    assert not (history / "version-0002.json").exists()
    assert [item.version for item in load_versions(history)] == [1]
    assert list(history.glob(".version-*.staging"))
    release.set()
    thread.join(5)
    assert not thread.is_alive()
    assert errors == []
    assert [item.version for item in load_versions(history)] == [1, 2]


def test_history_interruption_before_publish_preserves_last_committed_chain(tmp_path, monkeypatch):
    example = json.loads((ROOT / "examples/healthtech/synthetic-device/input.json").read_text(encoding="utf-8"))
    dossier, _, _ = run_dossier(DossierInput.model_validate(example), run_id="atomic-before", code_commit="test")
    history = tmp_path / "history"
    save_version(history, dossier)
    updated = dossier.model_copy(update={"version": 2, "parent_version": 1})

    def interrupt(_source, _destination):
        raise KeyboardInterrupt("interrupted before publication")

    monkeypatch.setattr("patent_to_pilot.healthtech.history.os.link", interrupt)
    with pytest.raises(KeyboardInterrupt, match="before publication"):
        save_version(history, updated)
    assert [item.version for item in load_versions(history)] == [1]
    assert not (history / "version-0002.json").exists()
    assert list(history.glob(".version-*.staging")) == []


def test_history_interruption_after_payload_fsync_before_publish_cleans_staging(tmp_path, monkeypatch):
    example = json.loads((ROOT / "examples/healthtech/synthetic-device/input.json").read_text(encoding="utf-8"))
    dossier, _, _ = run_dossier(DossierInput.model_validate(example), run_id="atomic-fsync", code_commit="test")
    history = tmp_path / "history"
    save_version(history, dossier)
    updated = dossier.model_copy(update={"version": 2, "parent_version": 1})
    fsync_calls = []
    original_fsync = history_module.os.fsync

    def track_fsync(descriptor):
        fsync_calls.append(descriptor)
        return original_fsync(descriptor)

    def fail_publish(_source, _destination):
        assert fsync_calls
        raise OSError("injected publication interruption")

    monkeypatch.setattr("patent_to_pilot.healthtech.history.os.fsync", track_fsync)
    monkeypatch.setattr("patent_to_pilot.healthtech.history.os.link", fail_publish)
    with pytest.raises(DossierHistoryError, match="could not publish version atomically"):
        save_version(history, updated)
    assert [item.version for item in load_versions(history)] == [1]
    assert not (history / "version-0002.json").exists()
    assert list(history.glob(".version-*.staging")) == []


def test_history_interruption_after_publish_leaves_recoverable_staging(tmp_path, monkeypatch):
    example = json.loads((ROOT / "examples/healthtech/synthetic-device/input.json").read_text(encoding="utf-8"))
    dossier, _, _ = run_dossier(DossierInput.model_validate(example), run_id="atomic-after", code_commit="test")
    history = tmp_path / "history"
    save_version(history, dossier)
    updated = dossier.model_copy(update={"version": 2, "parent_version": 1})
    original_unlink = history_module.os.unlink

    def interrupt_cleanup(path, *args, **kwargs):
        if str(path).endswith(".staging"):
            raise OSError("interrupted after publication")
        return original_unlink(path, *args, **kwargs)

    monkeypatch.setattr("patent_to_pilot.healthtech.history.os.unlink", interrupt_cleanup)
    save_version(history, updated)
    monkeypatch.setattr("patent_to_pilot.healthtech.history.os.unlink", original_unlink)
    assert [item.version for item in load_versions(history)] == [1, 2]
    abandoned = list(history.glob(".version-*.staging"))
    assert len(abandoned) == 1
    recovered = recover_staging_files(history, older_than_seconds=0)
    assert recovered == abandoned
    assert list(history.glob(".version-*.staging")) == []
    assert [item.version for item in load_versions(history)] == [1, 2]


def test_abbott_adapter_builds_real_public_linked_inputs_without_evaluator_reads():
    cohort = ROOT / "results/healthtech/ht-public-cohort-20261028-r1"
    cases = build_abbott_case_inputs(cohort)
    assert sorted(cases) == ["HT-DEV-MITRACLIP", "HT-DEV-TENDYNE", "HT-DEV-TRICLIP"]
    for query_id, input_data in cases.items():
        assert len(input_data.patents) == 41
        assert input_data.query.selected_comparator_source_id in input_data.query.permitted_inputs
        assert all(source.rights is not None for source in input_data.sources + [patent.source for patent in input_data.patents])
        disclosure = [item for item in input_data.evidence if item.evidence_kind == "patent_disclosure"]
        assert len(disclosure) == 1
        assert all("evaluator" not in source.source.uri.lower() for source in input_data.sources)
        dossier, _, _ = run_dossier(input_data, run_id=f"adapter-{query_id}", code_commit="test")
        assert dossier.candidates
        linked = promote_disclosed_links(dossier, input_data)
        assert linked.candidates
        assert any(item.association_status == "retrieved_candidate" for item in linked.candidates)
        assert any(item.association_status == "disclosed_link" for item in linked.candidates)
        assert all(item.source_id in {source.source.source_id for source in linked.sources} for item in linked.candidates)


def test_rights_boundary_blocks_restricted_product_surfaces_and_preserves_local_view():
    cohort = ROOT / "results/healthtech/ht-public-cohort-20261028-r1"
    input_data = next(iter(build_abbott_case_inputs(cohort).values()))
    dossier, _, _ = run_dossier(input_data, run_id="rights-boundary", code_commit="test")

    with pytest.raises(RightsBoundaryError, match="product_display blocked"):
        export_markdown(dossier, purpose="product_display")
    restricted_source = next(source for source in dossier.sources if source.source.source_type == "patent_document")
    with pytest.raises(RightsBoundaryError, match="redistribution blocked"):
        history_module.source_view(dossier, restricted_source.source.source_id, purpose="redistribution")
    local_view = history_module.source_view(dossier, restricted_source.source.source_id)
    assert local_view["rights"]["product_display"] == "BLOCKED_LOCAL"
    assert "Rights basis" in export_markdown(dossier)


def test_boston_marking_parser_is_score_independent_and_row_bounded():
    text = (
        "WATCHMAN FLX LAAC Device\n"
        "9883936\n10463377\n10751158\n11241237\n11413047\n11432809\n"
        "M635WU50200\n"
        "WATCHMAN FLX Pro LAAC Device\n"
        "9883936\n10463377\n10751158\n11241237\n11413047\n11432809\n11484320\n"
        "M635WU60200\n"
        "Zero Tip Airway Retrieval Basket\n6159220\n"
    )
    rows = _validate_product_rows(text)
    assert rows["watchman-flx"]["raw_patent_numbers"] == PRODUCTS[0]["patent_numbers"]
    assert rows["watchman-flx-pro"]["raw_patent_numbers"] == PRODUCTS[1]["patent_numbers"]
    assert "Zero Tip" not in str(rows["watchman-flx-pro"]["disclosure_text"])

    with pytest.raises(ValueError, match="unexpected Boston patent row"):
        _validate_product_rows(text.replace("11484320", "9999999"))


def test_public_cohort_registry_binds_typed_rights_policy_ids():
    rows = [
        _source_registry_row({
            "source_id": "openfda-pma-p100009-base",
            "source_type": "regulatory_record",
        }),
        _source_registry_row({
            "source_id": "abbott-product-patent-disclosures",
            "source_type": "independent_disclosure",
        }),
        _source_registry_row({
            "source_id": "google-patents-us1234567b2",
            "source_type": "patent_document",
        }),
    ]

    assert [row["rights_policy_id"] for row in rows] == [
        "openfda-pma-records",
        "abbott-product-patent-disclosures",
        "google-patents-pages",
    ]
    assert _rights_policy_id("openfda-pma-p230007-base", "regulatory_record") == "openfda-pma-records"
    with pytest.raises(ValueError, match="no typed rights policy"):
        _source_registry_row({"source_id": "unknown-source", "source_type": "other"})


def test_abbott_development_protocol_freezes_unjudged_distractors_and_groups():
    cohort = ROOT / "results/healthtech/ht-public-cohort-20261028-r1"
    protocol = build_abbott_development_protocol(cohort)
    assert protocol["status"] == "DEVELOPMENT_ONLY_FREEZE_NO_HOLDOUT"
    assert protocol["counts"] == {
        "eligible_devices": 3,
        "universe_patents": 41,
        "disclosed_pairs": 61,
        "unjudged_distractor_pairs": 62,
    }
    assert protocol["split"]["final_holdout"] == []
    assert protocol["groups"]["family_mapping"]["status"] == "UNKNOWN_NOT_ASSUMED"
    assert all(protocol["distractors_by_query"][query_id] for query_id in protocol["eligible_query_ids"])


def test_development_cohorts_have_per_link_disclosure_provenance():
    for relative, expected_pairs in (
        ("results/healthtech/ht-public-cohort-20261028-r1", 61),
        ("results/healthtech/ht-boston-watchman-20261028-r4", 13),
    ):
        report = verify_cohort_provenance(ROOT / relative)
        assert report["status"] in {"PASS", "PASS_WITH_LEGACY_RIGHTS"}
        assert report["counts"]["disclosed_pairs"] == expected_pairs
        assert report["counts"]["covered_pairs"] == expected_pairs
        assert report["counts"]["final_holdout_queries"] == 0

    boston = verify_cohort_provenance(ROOT / "results/healthtech/ht-boston-watchman-20261028-r4")
    assert boston["rights_binding"] == "TYPED_POLICY_ID"
    abbott = verify_cohort_provenance(ROOT / "results/healthtech/ht-public-cohort-20261028-r1")
    assert abbott["rights_binding"] == "LEGACY_TEXT_ONLY"


def test_provenance_verifier_rejects_an_uncovered_reference_pair(tmp_path):
    source = ROOT / "results/healthtech/ht-boston-watchman-20261028-r4"
    cohort = tmp_path / "cohort"
    cohort.mkdir()
    for relative in ("manifest.json", "runtime.json", "source_registry.json", "split_manifest.json", "distractors.json"):
        destination = cohort / relative
        destination.write_text((source / relative).read_text(encoding="utf-8"), encoding="utf-8")
    references_path = source / "evaluator/references.json"
    references = json.loads(references_path.read_text(encoding="utf-8"))
    references["disclosure_evidence"][0]["patent_id_canonical"] = references["disclosure_evidence"][0]["patent_id_canonical"][1:]
    evaluator_dir = cohort / "evaluator"
    evaluator_dir.mkdir()
    (evaluator_dir / "references.json").write_text(json.dumps(references), encoding="utf-8")
    with pytest.raises(CohortProvenanceError, match="without disclosure evidence"):
        verify_cohort_provenance(cohort)
