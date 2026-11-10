import importlib.util
from pathlib import Path
import pytest


def evaluator():
    path = Path(__file__).resolve().parents[1] / 'scripts/healthtech/evaluate_dapfam_native_baseline.py'
    spec = importlib.util.spec_from_file_location('native_eval_fixture', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def record():
    return {'query_id': 'q', 'families': [f'F{i:03}' for i in range(200)], 'scores': [0.5] * 200}


def test_complete_tied_ranking_accepted_without_reordering():
    row = record()
    assert evaluator().checked_rankings([row], {'q'}) == {'q': row['families']}


@pytest.mark.parametrize('case', ['duplicate_query', 'missing_query', 'duplicate_family', 'tie_order', 'nan', 'short'])
def test_invalid_completed_baseline_rejected(case):
    row = record()
    records, population = [row], {'q'}
    if case == 'duplicate_query': records.append(row)
    if case == 'missing_query': population.add('missing')
    if case == 'duplicate_family': row['families'][1] = row['families'][0]
    if case == 'tie_order': row['families'].reverse()
    if case == 'nan': row['scores'][0] = float('nan')
    if case == 'short': row['scores'].pop()
    with pytest.raises(ValueError):
        evaluator().checked_rankings(records, population)
