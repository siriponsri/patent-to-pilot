import pytest
from patent_to_pilot.research.mtm_runtime import InputBoundaryError
from patent_to_pilot.research.paper1_a2 import tail_fuse, a2_systems, select_k, a2_dev_design


def test_tail_fuse_keeps_head_and_fills_from_arm():
    b0 = ['a', 'b', 'c', 'd', 'e']
    assert tail_fuse(b0, ['c', 'x', 'y'], 2, depth=5) == ['a', 'b', 'c', 'x', 'y']
    assert tail_fuse(b0, ['x'], 2, depth=5) == ['a', 'b', 'x', 'c', 'd']   # arm runs out -> B0 continues
    assert tail_fuse(b0, ['x', 'y'], 5, depth=5) == b0
    assert tail_fuse(b0, ['x', 'y'], 0, depth=3) == ['x', 'y', 'a']
    with pytest.raises(InputBoundaryError):
        tail_fuse(b0, ['x', 'x'], 2)


def test_select_k_rule():
    def m(in_deltas, outs):
        r = {'IN': {'B0': {'Recall@200': 0.5}}, 'OUT': {'B0': {'Recall@200': 0.1}}}
        for k, d, o in zip((50, 100, 150), in_deltas, outs):
            r['IN']['T-FA(%d)' % k] = {'Recall@200': 0.5 + d}; r['OUT']['T-FA(%d)' % k] = {'Recall@200': o}
        return r
    assert select_k(m((-0.02, -0.005, -0.001), (0.20, 0.16, 0.16)))['k_star'] == 150   # 50 inadmissible; tie -> larger k
    assert select_k(m((-0.009, -0.005, -0.001), (0.20, 0.16, 0.15)))['k_star'] == 50
    assert select_k(m((-0.02, -0.03, -0.011), (0.2, 0.2, 0.2)))['status'] == 'NO_ADMISSIBLE_TAIL_FUSION_ON_DEV'


def test_dev_design_end_to_end():
    corpus = [{'relevant_id': 'F%03d' % i, 'title_en': '', 'abstract_en': '', 'claims_text': ''} for i in range(400)]
    queries = [{'query_id': 'Q%d' % i, 'title_en': '', 'abstract_en': ''} for i in range(4)]
    rel = [{'query_id': 'Q%d' % i, 'relevant_id': 'F%03d' % (300 + i), 'relevance_score': 1, 'domain_rel': 'OUT'} for i in range(4)]
    rel += [{'query_id': 'Q%d' % i, 'relevant_id': 'F%03d' % (10 + i), 'relevance_score': 1, 'domain_rel': 'IN'} for i in range(4)]
    ref = {'Q%d' % i: ['F%03d' % j for j in range(200)] for i in range(4)}
    fa = {'Q%d' % i: ['F%03d' % (300 + i)] + ['F%03d' % j for j in range(200, 299)] for i in range(4)}
    systems = a2_systems(ref, {'FA': fa, 'GR': ref, 'SACR': ref, 'shuffle': ref})
    public, _ = a2_dev_design(corpus, queries, rel, systems)
    assert public['OUT']['metrics']['T-FA(150)']['Recall@200'] == 1 and public['IN']['metrics']['T-FA(150)']['Recall@200'] == 1
    assert public['selection']['k_star'] == 150
