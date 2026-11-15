import pytest
from patent_to_pilot.research.mtm_runtime import InputBoundaryError
from patent_to_pilot.research.paper1_dev_eval import build_systems, evaluate_dev, first_positive_bin


def _data():
    corpus = [{'relevant_id': 'F%03d' % i, 'title_en': '', 'abstract_en': '', 'claims_text': ''} for i in range(300)]
    queries = [{'query_id': 'Q%d' % i, 'title_en': '', 'abstract_en': ''} for i in range(6)]
    relations = []
    for i in range(6):
        relations.append({'query_id': 'Q%d' % i, 'relevant_id': 'F%03d' % (250 + i), 'relevance_score': 1, 'domain_rel': 'OUT'})
        relations.append({'query_id': 'Q%d' % i, 'relevant_id': 'F%03d' % (10 + i), 'relevance_score': 1, 'domain_rel': 'IN'})
    ref = {'Q%d' % i: ['F%03d' % j for j in range(200)] for i in range(6)}      # finds IN positives, not OUT
    arm = {'Q%d' % i: ['F%03d' % (250 + i)] + ['F%03d' % j for j in range(100, 299) if j != 250 + i][:199] for i in range(6)}
    return corpus, queries, relations, ref, arm


def test_fa_rescues_out_positive_and_fusion_keeps_in():
    corpus, queries, relations, ref, arm = _data()
    systems = build_systems(ref, ref, {'FA': arm, 'GR': ref, 'SACR': ref},
                            {'FA': 'MOVEMENT_PRESENT', 'GR': 'MOVEMENT_PRESENT', 'SACR': 'MOVEMENT_PRESENT'})
    public, private = evaluate_dev(corpus, queries, relations, systems)
    out = public['main']['OUT']
    assert out['metrics']['B0']['Recall@200'] == 0 and out['metrics']['F-FA']['Recall@200'] == 1
    h1 = out['paired_primary']['H1']
    assert h1['wins'] == 6 and h1['mean_delta'] == 1 and 'verdict' not in h1
    assert out['exposure_strata_vs_B0']['F-FA'] == {'both': 0, 'arm_only': 6, 'reference_only': 0, 'neither': 0}
    assert public['main']['IN']['metrics']['F-FA']['Recall@200'] == 1
    assert out['first_positive_rank_bins']['FA'] == {'1-10': 6}
    assert public['c3_audit']['excluded_queries'] == 0


def test_c1_fault_refuses_arm():
    corpus, queries, relations, ref, arm = _data()
    with pytest.raises(InputBoundaryError):
        build_systems(ref, ref, {'FA': arm, 'GR': ref, 'SACR': ref},
                      {'FA': 'ENGINEERING_FAULT_ARM_DID_NOT_REACH_RETRIEVAL', 'GR': 'MOVEMENT_PRESENT', 'SACR': 'MOVEMENT_PRESENT'})


def test_c3_excludes_self_positive_query():
    corpus, queries, relations, ref, arm = _data()
    corpus.append({'relevant_id': 'Q1', 'title_en': '', 'abstract_en': '', 'claims_text': ''})
    systems = build_systems(ref, ref, {'FA': arm, 'GR': ref, 'SACR': ref}, {a: 'MOVEMENT_PRESENT' for a in ('FA', 'GR', 'SACR')})
    public, _ = evaluate_dev(corpus, queries, relations, systems)
    assert public['c3_audit']['excluded_queries'] == 1
    assert public['c3_family_overlap_sensitivity']['OUT']['eligible_queries'] == 5


def test_first_positive_bin():
    assert first_positive_bin(['a', 'b'] + ['x%d' % i for i in range(60)] + ['g'], {'g'}) == '51-100'
    assert first_positive_bin(['a'], {'g'}) == 'none'
