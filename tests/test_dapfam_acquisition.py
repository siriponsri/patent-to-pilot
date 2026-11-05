from patent_to_pilot.evaluation.dapfam_acquisition import (
    DENSE_DOCUMENT_PREFIX,
    DENSE_QUERY_PREFIX,
    dense_passages,
    dense_query_text,
    dense_query_windows,
    component_split,
    first_ipc_section,
    macro_recall,
    maxp_top_k,
    positive_relations,
    query_components,
)


def test_dense_passages_windows_and_normalization():
    claims = " ".join(f"w{i}" for i in range(700))
    passages = dense_passages("Ｔitle", "abs  text", claims)
    tokens = ("Title abs text " + claims).split(" ")
    assert len(tokens) == 703
    # windows start at 0, 320, 640
    assert len(passages) == 3
    assert passages[0] == DENSE_DOCUMENT_PREFIX + " ".join(tokens[0:384])
    assert passages[2] == DENSE_DOCUMENT_PREFIX + " ".join(tokens[640:703])
    assert dense_passages("", None, " ") == []


def test_dense_query_text_keeps_fullwidth_and_joins_fields():
    assert dense_query_text("Ｔ  a", None, "c\nd") == DENSE_QUERY_PREFIX + "Ｔ a  c d"


def test_dense_query_windows_cover_whole_query():
    claims = " ".join(f"c{i}" for i in range(400))
    windows = dense_query_windows("t", "a", claims)
    body = ["t", "a"] + [f"c{i}" for i in range(400)]
    assert len(windows) == 2
    assert windows[0] == DENSE_QUERY_PREFIX + " ".join(body[0:384])
    assert windows[1] == DENSE_QUERY_PREFIX + " ".join(body[320:402])
    assert dense_query_windows(None, "", "  ") == []


def test_maxp_top_k_uses_family_max_and_lexical_ties():
    scores = [0.5, 0.9, 0.7, 0.7]
    families = [0, 0, 1, 2]
    assert maxp_top_k(scores, families, ["f0", "fb", "fa"], k=3) == [("f0", 0.9), ("fa", 0.7), ("fb", 0.7)]
    assert maxp_top_k(scores, families, ["f0", "fb", "fa"], k=1) == [("f0", 0.9)]


def test_positive_relations_and_macro_recall_skip_unjudged():
    qrels = [
        {"query_id": "q1", "relevant_id": "a", "relevance_score": 1, "domain_rel": "OUT"},
        {"query_id": "q1", "relevant_id": "b", "relevance_score": 1, "domain_rel": "IN"},
        {"query_id": "q1", "relevant_id": "z", "relevance_score": 0, "domain_rel": "OUT"},
        {"query_id": "q2", "relevant_id": "c", "relevance_score": 1, "domain_rel": "IN"},
    ]
    pos = positive_relations(qrels)
    out = {q: v["OUT"] for q, v in pos.items()}
    assert out == {"q1": {"a"}, "q2": set()}
    value, n = macro_recall({"q1": ["x", "a"]}, out, k=1)
    assert (value, n) == (0.0, 1)
    value, n = macro_recall({"q1": ["x", "a"]}, out, k=2)
    assert (value, n) == (1.0, 1)


def test_components_and_split_keep_shared_targets_together():
    pos = {"q1": {"IN": {"t1"}, "OUT": set()}, "q2": {"IN": set(), "OUT": {"t1"}},
           "q3": {"IN": {"t9"}, "OUT": set()}}
    comps = query_components(pos, ["q1", "q2", "q3", "q4"])
    assert comps["q1"] == comps["q2"] == "q1"
    assert comps["q3"] == "q3" and comps["q4"] == "q4"
    sections = {"q1": "A", "q2": "B", "q3": "A", "q4": "H"}
    split = component_split(comps, sections, seed=7)
    assert split["q1"] == split["q2"]
    assert set(split.values()) <= {"dev", "test"} and len(split) == 4
    assert split == component_split(comps, sections, seed=7)
    big = component_split(comps, sections, seed=7, large_component_threshold=2)
    assert big["q1"] == big["q2"] == "dev"


def test_qwen_action_a_parser_filters_codes():
    import importlib.util
    from pathlib import Path

    path = Path(__file__).resolve().parents[1] / "scripts/healthtech/run_qwen_query_actions.py"
    spec = importlib.util.spec_from_file_location("run_qwen_query_actions", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    parsed, error = module.parse_action_a(
        '```json\n{"functional_query": "a  b", "target_ipc3": ["b01", "A61", "X99", "B01"]}\n```', ["A61"])
    assert error is None and parsed == {"functional_query": "a b", "target_ipc3": ["B01"], "dropped_ipc3": 3}
    parsed, _ = module.parse_action_a('{"functional_query": "q", "target_ipc3": ["C12N1/00", "F03B", "G01"]}', ["C12"])
    assert parsed["target_ipc3"] == ["F03", "G01"] and parsed["dropped_ipc3"] == 1
    assert module.parse_action_a("no json here", [])[0] is None
    assert module.parse_action_a('{"functional_query": "", "target_ipc3": []}', [])[1] == "schema"


def test_first_ipc_section():
    assert first_ipc_section(["A61", "B01"]) == "A"
    assert first_ipc_section([]) == "?"
    assert first_ipc_section(None) == "?"
