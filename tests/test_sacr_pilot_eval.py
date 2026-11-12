import pytest
from patent_to_pilot.research.sacr_pilot_eval import evaluate_arms
from patent_to_pilot.research.mtm_runtime import InputBoundaryError


def fixture():
    corpus = [{'relevant_id': f, 'title_en': '', 'abstract_en': '', 'claims_text': ''} for f in ('F1', 'F2', 'F3')]
    queries = [{'query_id': q, 'title_en': '', 'abstract_en': ''} for q in ('Q1', 'Q2', 'Q3')]
    relations = [{'query_id': 'Q1', 'relevant_id': 'F1', 'relevance_score': 1, 'domain_rel': 'OUT'},
                 {'query_id': 'Q2', 'relevant_id': 'F2', 'relevance_score': 1, 'domain_rel': 'IN'},
                 {'query_id': 'Q3', 'relevant_id': 'F3', 'relevance_score': 1, 'domain_rel': 'OUT'}]
    return corpus, queries, relations


def test_pilot_restriction_and_paired_counts():
    corpus, queries, relations = fixture()
    arms = {'B0': {'Q1': ['F2', 'F1'], 'Q2': ['F2']}, 'SACR': {'Q1': ['F1', 'F2'], 'Q2': ['F3']}}
    public, private = evaluate_arms(corpus, queries, relations, ['Q1', 'Q2'], arms)
    assert public['OUT']['eligible_queries'] == 1 and public['IN']['eligible_queries'] == 1   # Q3 excluded
    assert public['OUT']['paired']['NDCG@10']['sacr_better'] == 1
    assert public['IN']['paired']['Recall@10']['b0_better'] == 1
    assert 'Q1' in private['OUT']['SACR']
    with pytest.raises(InputBoundaryError):
        evaluate_arms(corpus, queries, relations, ['Q1', 'Q2'], {'B0': arms['B0'], 'SACR': {'Q1': ['F1']}})
