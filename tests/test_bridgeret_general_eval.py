import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts' / 'healthtech'))
import bridgeret_general_eval as ge  # noqa: E402


def test_ndcg10_graded_and_recall():
    rel = {'a': 2, 'b': 1}
    assert ge.ndcg10(['a', 'b'], rel) == pytest.approx(1.0)
    swapped = (1 + 2 / math.log2(3)) / (2 + 1 / math.log2(3))
    assert ge.ndcg10(['b', 'a'], rel) == pytest.approx(swapped)
    assert ge.ndcg10(['x'] * 10 + ['a'], rel) == 0.0
    assert ge.recall100(['x', 'a'], rel) == 0.5


def test_score_task_requires_every_query(tmp_path):
    rel = {'q1': {'a': 1}, 'q2': {'b': 1}}
    with pytest.raises(SystemExit):
        ge.score_task({'q1': ['a']}, rel)
    r = ge.score_task({'q1': ['a'], 'q2': ['x', 'b']}, rel)
    assert r['n'] == 2 and r['R@100'] == 1.0


def test_read_qrels_drops_zero_scores(tmp_path):
    p = tmp_path / 'q.tsv'
    p.write_text('query-id\tcorpus-id\tscore\nq1\ta\t1\nq1\tb\t0\nq2\tc\t0\n', encoding='utf-8')
    assert ge.read_qrels(p) == {'q1': {'a': 1}}
