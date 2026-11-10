import copy

import numpy as np
import pytest

from patent_to_pilot.research.sacr_factorial import compare_factorial
from test_sacr_factorial import fixture


def test_selection_reuses_acquisition_without_search_or_double_charge(monkeypatch):
    args = fixture()
    original = compare_factorial(**args)
    def forbidden(**kwargs):
        pytest.fail('selection must not repeat acquisition')
    monkeypatch.setattr('patent_to_pilot.research.sacr_factorial.acquire_union', forbidden)
    selected = compare_factorial(**args, acquired=original['acquisition'])
    assert selected['arms'] == original['arms']
    assert selected['candidate_passages'] == original['candidate_passages']
    assert selected['accounting']['actual_acquisition_dot_products'] == 0
    assert selected['accounting']['actual_component_passage_dot_products'] == 6
    assert selected['accounting']['acquisition_reused']


@pytest.mark.parametrize('case', ['foreign', 'duplicate', 'union', 'scores', 'views', 'depth',
                                  'mask', 'nonunit', 'dtype', 'view_vector'])
def test_reused_acquisition_cannot_bypass_exposure_and_vector_checks(case):
    args = fixture()
    acquired = copy.deepcopy(compare_factorial(**args)['acquisition'])
    if case == 'foreign':
        acquired['G']['family_ids'][0] = 'outside'
    elif case == 'duplicate':
        acquired['G']['family_ids'] = ['split', 'split']
    elif case == 'union':
        acquired['G']['rankings']['generic'] = []
        acquired['G']['rankings']['anchor'] = []
    elif case == 'scores':
        acquired['G']['anchor_scores'][0] = float('nan')
    elif case == 'views':
        acquired['G']['rankings']['extra'] = []
    elif case == 'depth':
        args['depth'] = 201
    elif case == 'mask':
        args['eligible'][:] = False
    elif case == 'nonunit':
        args['passage_vectors'] *= 2
    elif case == 'dtype':
        args['passage_vectors'] = args['passage_vectors'].astype(np.float64)
    else:
        args['generic_views'][1][1] *= 2
    with pytest.raises(ValueError):
        compare_factorial(**args, acquired=acquired)
