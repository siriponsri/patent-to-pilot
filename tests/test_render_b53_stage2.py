import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts' / 'writing'))
import render_b53_stage2 as rb  # noqa: E402


def _result():
    prim, mean = {}, {}
    for F in rb.ARMS:
        for a in ('patent_aware', 'claim_focused'):
            prim[f'{F}|{a}-generic'] = {'delta_C': -0.0123, 'ci95': [-0.02, 0.004], 'p': 0.01, 'holm_p': 0.0004,
                                        'wins': 40, 'losses': 60, 'ties': 53}
        for s, _ in rb.SYSTEMS:
            mean[f'{F}|{s}'] = 0.1
    return {'C': 153, 'n_out': 905, 'pi100': {F: 0.371 for F in rb.ARMS}, 'B53_3_primary_on_C': prim, 'mean_ndcg100': mean}


def test_render_contains_every_arm_and_formats():
    md = rb.render(_result())
    assert '(C) = 153' in md and 'OUT ทั้งหมด 905' in md
    for F in rb.ARMS:
        assert rb.NAMES[F] in md
    assert '−0.012 [−0.020, +0.004] (40/60)' in md
    assert '< 0.001' in md
    assert md.count('| F0 patembed-base |') == 2
