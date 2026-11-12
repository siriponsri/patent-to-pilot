import pytest
from patent_to_pilot.research.mtm_runtime import InputBoundaryError
from patent_to_pilot.research import paper1_rewrite_arms as arms
from patent_to_pilot.research import paper1_analysis as pa

SRC = 'An infusion device comprising a reservoir and a controller that stops delivery when line pressure exceeds 40 kPa.'


def fa_output(req, **over):
    out = {'version': arms.FA_VERSION, 'query_id': 'q1', 'source_sha256': arms.sha(SRC),
           'function': 'Delivers fluid and stops at over-pressure.', 'mechanism': 'A controller halts the actuator.',
           'problem': 'Prevents harm from excessive pressure.', 'conditions': 'Stops above 40 kPa.'}
    out.update(over); return out


def test_fa_and_gr_requests_are_matched_and_bound():
    fa, gr = arms.prepare('FA', SRC, 'q1'), arms.prepare('GR', SRC, 'q1')
    assert fa['schema']['properties']['query_id'] == {'const': 'q1'}
    assert sum(fa['schema']['properties'][f]['maxLength'] for f in arms.FA_FIELDS) == gr['schema']['properties']['abstract']['maxLength'] == 2000
    assert list(fa['schema']['properties'])[3:] == list(arms.FA_FIELDS)
    assert arms.EXAMPLE_SOURCE in fa['messages'][0]['content'] and arms.EXAMPLE_SOURCE in gr['messages'][0]['content']
    assert 'domain' not in gr['messages'][0]['content']
    with pytest.raises(InputBoundaryError):
        arms.prepare('XX', SRC, 'q1')


def test_fa_text_and_rejections():
    req = arms.prepare('FA', SRC, 'q1')
    assert arms.validate_and_text(fa_output(req), req).split('\n')[3] == 'Stops above 40 kPa.'
    for bad in (fa_output(req, query_id='q2'), fa_output(req, problem=''), fa_output(req, function='   '),
                fa_output(req, mechanism='x' * 501), dict(fa_output(req), extra='y')):
        with pytest.raises(InputBoundaryError):
            arms.validate_and_text(bad, req)
    req['messages'][1]['content'] += ' '
    with pytest.raises(RuntimeError):
        arms.validate_and_text(fa_output(req), req)


def test_gr_text():
    req = arms.prepare('GR', SRC, 'q1')
    out = {'version': arms.GR_VERSION, 'query_id': 'q1', 'source_sha256': arms.sha(SRC), 'abstract': ' A pump. '}
    assert arms.validate_and_text(out, req) == 'A pump.'


def test_lexical_descriptives():
    d = arms.lexical_descriptives(SRC, 'Stops delivery above 40 kPa using a controller.')
    assert d['numbers_retained_share'] == 1.0 and 0 < d['content_words_absent_share'] < 1
    assert arms.lexical_descriptives('no numbers here', 'x')['numbers_retained_share'] is None


def test_rrf_fusion_and_ties():
    assert pa.rrf_fuse(['a', 'b', 'c'], ['c', 'b', 'd']) == ['c', 'b', 'a', 'd']
    fused = pa.rrf_fuse(['a', 'b'], ['b', 'a'])
    assert fused == ['a', 'b']                      # exact tie -> better B0 rank first
    fused = pa.rrf_fuse(['a'], ['x', 'y'])
    assert fused == ['a', 'x', 'y']                 # a and x tie at rank 1 -> B0 member first
    assert len(pa.rrf_fuse([str(i) for i in range(200)], [str(i) for i in range(200, 400)])) == 200
    with pytest.raises(InputBoundaryError):
        pa.rrf_fuse(['a', 'a'], ['b'])


def test_components_and_bootstrap():
    groups = pa.components({'q1': ['t1'], 'q2': ['t1', 't2'], 'q3': ['t3'], 'q4': ['t2']})
    assert groups == [['q1', 'q2', 'q4'], ['q3']]
    deltas = {'q1': 0.1, 'q2': 0.1, 'q3': 0.0, 'q4': 0.1}
    ci = pa.cluster_bootstrap_ci(deltas, groups, resamples=2000)
    assert ci['components'] == 2 and ci['largest_component_share'] == 0.75 and ci['ci_low'] <= ci['mean'] <= ci['ci_high']
    assert pa.cluster_bootstrap_ci(deltas, groups, resamples=2000) == ci   # seeded, reproducible
    with pytest.raises(InputBoundaryError):
        pa.cluster_bootstrap_ci({'q1': 0.1}, groups)
    assert pa.sign_flip_p({'q%d' % i: 0.0 for i in range(10)}, resamples=200) == 1.0


def test_interpretation_and_gatekeeping():
    ci = lambda lo, hi: {'ci_low': lo, 'ci_high': hi}
    assert pa.interpret(ci(0.001, 0.02)) == 'SUPERIOR'
    assert pa.interpret(ci(-0.005, 0.006)) == 'PRACTICALLY_EQUIVALENT'
    assert pa.interpret(ci(-0.005, 0.02)) == 'INCONCLUSIVE'
    assert pa.interpret(ci(-0.02, -0.001)) == 'INFERIOR'
    assert pa.noninferior(ci(-0.019, 0.01)) and not pa.noninferior(ci(-0.021, 0.01))
    r = pa.gatekeep({'H1': ci(0.01, 0.03), 'H2': ci(-0.01, 0.02), 'H3': ci(0.01, 0.02)})
    assert r == {'H1': 'SUPERIOR', 'H2': 'INCONCLUSIVE', 'H3': 'NOT_TESTED_GATE_CLOSED'}
    assert pa.exposure_strata({'a': True, 'b': False, 'c': True, 'd': False}, {'a': True, 'b': True, 'c': False, 'd': False}) == \
        {'both': 1, 'arm_only': 1, 'reference_only': 1, 'neither': 1}
