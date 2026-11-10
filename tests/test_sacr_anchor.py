import json

import pytest

from patent_to_pilot.research.mtm_runtime import InputBoundaryError
from patent_to_pilot.research.sacr_components import digest
from test_sacr_controller import setup, adapter
from test_sacr_retrieval_controller import index_inputs, make_index


def factory(data, *, mask, change=None):
    bundle = {'format': 'sacr-original-anchor-v1', 'split': 'dev', 'baseline_receipt_sha256': 'a' * 64,
              **{key + '_sha256': data['identities'][key]
                 for key in ('query_manifest', 'index_manifest', 'encoder_manifest')},
              'depth': data['limits']['depth'],
              'rows': [{**source, 'mask_sha256': digest(mask.tolist()), 'ranking': ['joint', 'split']}
                       for source in data['sources']]}
    if change:
        change(bundle)
    return json.dumps(bundle).encode()


def prepared(tmp_path, change=None):
    p, raw = index_inputs()
    index = make_index(p, raw)
    controller = setup(tmp_path, index_manifest=raw,
                       anchor_factory=lambda data: factory(data, mask=p['eligible'], change=change))
    return controller, index, p


@pytest.mark.parametrize('kind,state', [('empty', 'PROFILE_EMPTY'), ('failed', 'PROFILE_FAILED'),
                                       ('exception', 'PROFILE_FAILED')])
def test_fallback_uses_predeclared_anchor_without_retrieval(tmp_path, kind, state):
    controller, index, p = prepared(tmp_path)
    def work(q, source):
        if kind == 'exception':
            raise RuntimeError('authored failure')
        profile, costs = adapter(q, source)
        profile['blocks'] = []
        if kind == 'failed':
            profile.update(extraction_status='failed', failure_reasons=['authored failure'])
        return profile, costs
    if kind == 'exception':
        with pytest.raises(RuntimeError):
            controller.profile('q', work)
    else:
        controller.profile('q', work)
    for stage in ('generic', 'selective', 'embedding', 'acquisition', 'selection'):
        controller.journal.skip(stage, reason='whole profile fallback')
    report = controller.finalize_mixed(index, {'q': p['eligible']})
    assert report['cohort']['state_counts'][state] == 1
    assert report['cohort']['fallback_queries'] == 1
    outcomes = json.loads((controller.journal.destination / 'outcomes.json').read_text())
    assert all(r == ['joint', 'split'] for r in outcomes[0]['rankings'].values())
    assert not report['protected_evaluation_authorized']


@pytest.mark.parametrize('field,value', [('split', 'test'), ('depth', 199),
                                       ('encoder_manifest_sha256', 'f' * 64),
                                       ('baseline_receipt_sha256', '')])
def test_wrong_anchor_protocol_rejected_before_directory(tmp_path, field, value):
    with pytest.raises(InputBoundaryError):
        prepared(tmp_path, lambda b: b.update({field: value}))
    assert not (tmp_path / 'run').exists()


def test_changed_anchor_bytes_refuse_before_profile_dispatch(tmp_path):
    controller, _, _ = prepared(tmp_path)
    path = controller.journal.destination / 'anchor-bundle.json'
    path.write_bytes(path.read_bytes() + b' ')
    with pytest.raises(InputBoundaryError, match='predeclared digest'):
        controller.profile('q', lambda *_: pytest.fail('adapter called'))


def test_foreign_anchor_family_refused_at_fallback(tmp_path):
    controller, index, p = prepared(tmp_path, lambda b: b['rows'][0].update(ranking=['outside']))
    def empty(q, source):
        profile, costs = adapter(q, source)
        profile['blocks'] = []
        return profile, costs
    controller.profile('q', empty)
    for stage in ('generic', 'selective', 'embedding', 'acquisition', 'selection'):
        controller.journal.skip(stage, reason='empty profile')
    with pytest.raises(InputBoundaryError, match='eligible exposure'):
        controller.finalize_mixed(index, {'q': p['eligible']})
    assert not (controller.journal.destination / 'outcomes.json').exists()
