import pytest
from patent_to_pilot.research.sg_sampling import corpus_sample
from patent_to_pilot.research.mtm_runtime import InputBoundaryError


def test_sample_is_fixed_stratified_unique_and_order_invariant():
    rows = [{'id': f'F{i:03}', 'source_chars': i // 3} for i in range(403)]
    a = corpus_sample(rows)
    assert a == corpus_sample(reversed(rows))
    assert len(a['sample']) == len({r['id'] for r in a['sample']}) == 100
    assert [sum(r['stratum'] == s for r in a['sample']) for s in range(4)] == [25] * 4
    assert sum(a['stratum_sizes']) == 403


def test_small_population_and_empty_source_remain_visible():
    rows = [{'id': str(i), 'source_chars': 0} for i in range(7)]
    assert {r['id'] for r in corpus_sample(rows)['sample']} == {r['id'] for r in rows}


@pytest.mark.parametrize('rows', [[], [{'id': 'a', 'source_chars': True}],
    [{'id': 'a', 'source_chars': -1}], [{'id': 'a', 'source_chars': 1, 'label': 1}],
    [{'id': 'a', 'source_chars': 0}] * 2])
def test_bad_or_label_augmented_population_rejected(rows):
    with pytest.raises(InputBoundaryError):
        corpus_sample(rows)
