import hashlib
import json

import pytest

from patent_to_pilot.evaluation.dapfam_staging import jsonl_bytes, stage_native_dev
from patent_to_pilot.research.mtm_runtime import InputBoundaryError


def fixture():
    corpus = [{"relevant_id": "f1", "title_en": "Corpus", "abstract_en": "A", "claims_text": "C"}]
    queries = [{"query_id": q, "title_en": t, "abstract_en": "abstract", "claims_text": "MUST_NOT_EXPORT"}
               for q, t in (("q1", "dev title"), ("hidden-id", "HIDDEN_TEXT"))]
    relations = [{"query_id": q, "relevant_id": "f1", "relevance_score": 1, "domain_rel": "OUT"}
                 for q in ("q1", "hidden-id")]
    assignment = {"q1": "dev", "hidden-id": "test"}
    kwargs = {"source_hashes": {"synthetic": "a" * 64}, "expected_dev": 1, "expected_protected": 1,
              "expected_corpus": 1, "expected_corpus_sha256": hashlib.sha256(jsonl_bytes([
                  {"id": "f1", "title": "Corpus", "abstract": "A", "claims": "C"}])).hexdigest()}
    return corpus, queries, relations, assignment, kwargs


def test_projection_preserves_native_ta_and_full_corpus_without_protected_exports(tmp_path):
    c, q, r, split, kw = fixture()
    dest = tmp_path / "stage"
    result = stage_native_dev(c, q, r, split, dest, **kw)
    assert result["protected_exports"] == 0
    assert json.loads((dest / "runtime-dev/queries-ta.jsonl").read_text())["text"] == "dev title\nabstract"
    for path in dest.rglob("*"):
        if path.is_file():
            text = path.read_text()
            assert "hidden-id" not in text and "HIDDEN_TEXT" not in text and "MUST_NOT_EXPORT" not in text
    for path in (dest / "runtime-dev").iterdir():
        assert "relevance_score" not in path.read_text() and "eligible_queries" not in path.read_text()
    evaluation = json.loads((dest / "dev-evaluation/manifest.json").read_text())
    assert evaluation["eligible_queries"] == {"ALL": 1, "IN": 0, "OUT": 1}
    with pytest.raises(InputBoundaryError, match="preserve"):
        stage_native_dev(c, q, r, split, dest, **kw)


@pytest.mark.parametrize("bad", ["split", "query", "corpus", "relation", "empty"])
def test_invalid_inputs_never_create_completion(tmp_path, bad):
    c, q, r, split, kw = fixture()
    if bad == "split":
        split["hidden-id"] = "dev"
    elif bad == "query":
        q.pop()
    elif bad == "corpus":
        c[0]["claims_text"] = "changed"
    elif bad == "relation":
        r.append(r[0])
    else:
        q[0]["title_en"] = q[0]["abstract_en"] = ""
    with pytest.raises(InputBoundaryError):
        stage_native_dev(c, q, r, split, tmp_path / "stage", **kw)
    assert not (tmp_path / "stage/owner-complete.json").exists()
