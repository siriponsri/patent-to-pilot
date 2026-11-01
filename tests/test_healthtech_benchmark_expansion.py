from scripts.healthtech.run_helmers_diagnostic import auc, average_precision
from scripts.healthtech.run_panorama_lexical_baseline import bm25, parse_options, rank_row
from scripts.healthtech.acquire_manifest_datasets import digest_file, rights_record


def test_manifest_git_blob_sha1_matches_git_semantics(tmp_path):
    payload = tmp_path / "fixture.csv"
    payload.write_bytes(b"a,b\n1,2\n")
    assert digest_file(payload, "git_blob_sha1") == "cfa20f81071245f292f0b52b37beb7adf9259a26"


def test_noncommercial_license_is_not_cleared_for_commercial_release():
    rights = rights_record({"license": "cc-by-nc-4.0"})
    assert rights["source_rights_status"] == "NON_COMMERCIAL_LICENSE_REPORTED"
    assert rights["permitted_scope"] == "local_research_only_until_rights_review"
    assert rights["commercial_release"] == "NOT_CLEARED"


def test_panorama_par4pc_ranker_prefers_matching_option():
    row = {
        "context": {"title": "wrist support", "abstract": "a wrist support device", "claims": ["limits wrist movement"]},
        "options": {
            "A": {"title": "wrist support", "abstract": "a wrist support device", "claims": ["limits wrist movement"]},
            "B": {"title": "cat toy", "abstract": "a toy for cats", "claims": ["has a bell"]},
        },
    }
    ranked, failure = rank_row("PAR4PC", row)
    assert failure is None
    assert ranked[0] == "A"


def test_panorama_option_parser_handles_pi4pc_json():
    row = {"context": "claim context", "options": '{"10": "matching paragraph", "11": "other paragraph"}'}
    context, options = parse_options("PI4PC", row)
    assert context == "claim context"
    assert options["10"] == "matching paragraph"


def test_bm25_empty_document_is_zero():
    assert bm25(["claim"], [], {}, 2, 1.0) == 0.0


def test_helmers_metrics_are_bounded_and_deterministic():
    labels = [1, 0, 1]
    scores = [0.9, 0.8, 0.7]
    assert average_precision(labels, scores) == (1.0 + 2.0 / 3.0) / 2.0
    assert auc(labels, scores) == 0.5
