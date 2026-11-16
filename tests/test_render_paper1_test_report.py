"""Tests for docs/healthtech/research/paper1-report/render_paper1_test_report.py.

Uses the real S5 dev summary (public aggregates, committed receipt) and a SYNTHETIC test summary with fake values.
No test data, no model, no network.
"""
import copy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RENDERER = ROOT / 'docs/healthtech/research/paper1-report/render_paper1_test_report.py'
RECEIPTS = ROOT / 'docs/healthtech/audits/ptp-automatic-preparation-20261112/takeover-20261112'
DEV = RECEIPTS / 'paper1-s5-eval/terminal-observation.json'
SYNTHETIC = ROOT / 'tests/fixtures/paper1_report/synthetic-test-summary.json'

spec = importlib.util.spec_from_file_location('render_paper1_test_report', RENDERER)
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)


def synthetic():
    return r.load_summary(SYNTHETIC)


def test_fixture_is_marked_fake_and_matches_builder():
    s = synthetic()
    assert s['_synthetic'].startswith('FAKE VALUES')
    builder = importlib.util.spec_from_file_location('b', SYNTHETIC.with_name('build_synthetic_test_summary.py'))
    b = importlib.util.module_from_spec(builder)
    builder.loader.exec_module(b)
    assert json.loads(json.dumps(b.build())) == s


def test_dev_mode_renders_without_verdicts():
    dev = r.load_summary(DEV)
    assert r.split_of(dev) == 'dev'
    text, problems = r.render(dev, None, RECEIPTS)
    assert problems is None
    assert 'Not applicable: this is a dev summary' in text
    for label in ('`SUPERIOR`', '`INCONCLUSIVE`', '`PRACTICALLY_EQUIVALENT`', '`INFERIOR`'):
        assert label not in text
    # known dev values (PAPER1-S5-SUMMARY.json)
    assert '| B0 | 0.0237 | 0.0973 | 0.1477 |' in text
    assert '| H1 | F-FA − B0 | 349 | -0.0006 | [-0.0116, +0.0225] | 16/31/302 |' in text
    assert '| FA | 4/4 | 11579 |' in text and '| SACR | 8/8 | 45080 |' in text


def test_test_mode_gatekeeping_labels_exactly_as_returned():
    text, problems = r.render(synthetic(), r.load_summary(DEV), None)
    assert problems == []
    assert '**SYNTHETIC INPUT' in text
    assert '| H1 | F-FA − B0 | +0.0300 | [+0.0100, +0.0500] | `SUPERIOR` |' in text
    assert '`INCONCLUSIVE`' in text and '`NOT_TESTED_GATE_CLOSED`' in text
    assert 'all verdicts MATCH' in text
    assert '| IN | F-FA − B0 | -0.0100 | [-0.0150, -0.0050] | -0.02 | non-inferior | MATCH |' in text
    assert 'non-inferiority NOT shown' in text
    assert 'dev Recall@200' in text  # side by side
    assert 'H3 `INCONCLUSIVE`' in text  # closed step shown as descriptive only


def test_efficiency_pending_for_missing_receipts(tmp_path):
    text, _ = r.render(synthetic(), None, tmp_path)
    assert r.PENDING + ' (0/5 batches settled)' in text
    assert r.PENDING + ' (0/10 batches settled)' in text


def test_test_mode_reads_settled_s8_batches():
    arms, _, used = r.collect_efficiency(RECEIPTS, 'test')
    assert arms['FA']['batches'] == 5 and arms['SACR']['batches'] == 10
    assert all(Path(p).exists() for p in used)


def test_mismatch_is_reported():
    s = synthetic()
    s['results']['confirmatory']['gatekeeping']['H2'] = 'SUPERIOR'  # tampered
    text, problems = r.render(s, None, None)
    assert problems and 'H2 verdict SUPERIOR' in problems[0]
    assert 'MISMATCH' in text


@pytest.mark.parametrize('cis,expected', [
    ({'H1': (-0.02, 0.03)}, {'H1': 'INCONCLUSIVE', 'H2': 'NOT_TESTED_GATE_CLOSED', 'H3': 'NOT_TESTED_GATE_CLOSED'}),
    ({'H1': (-0.005, 0.008)}, {'H1': 'PRACTICALLY_EQUIVALENT', 'H2': 'NOT_TESTED_GATE_CLOSED',
                               'H3': 'NOT_TESTED_GATE_CLOSED'}),
    ({'H1': (-0.03, -0.01)}, {'H1': 'INFERIOR', 'H2': 'NOT_TESTED_GATE_CLOSED', 'H3': 'NOT_TESTED_GATE_CLOSED'}),
    ({'H1': (0.01, 0.02), 'H2': (0.001, 0.02), 'H3': (0.002, 0.03)},
     {'H1': 'SUPERIOR', 'H2': 'SUPERIOR', 'H3': 'SUPERIOR'}),
])
def test_rule_copy_matches_frozen_module(cis, expected):
    from patent_to_pilot.research import paper1_analysis as frozen
    base = {'H1': (0.01, 0.05), 'H2': (-0.005, 0.025), 'H3': (-0.001, 0.041)}
    base.update(cis)
    c = {k: {'ci_low': lo, 'ci_high': hi} for k, (lo, hi) in base.items()}
    assert r.gatekeep(c) == frozen.gatekeep(c) == expected
    assert (r.EQUIVALENCE_MARGIN, r.NONINFERIORITY_MARGIN) == (frozen.EQUIVALENCE_MARGIN, frozen.NONINFERIORITY_MARGIN)


def test_cli_writes_file_and_exit_codes(tmp_path):
    out = tmp_path / 'report.md'
    assert r.main([str(SYNTHETIC), '--dev', str(DEV), '--receipts', str(RECEIPTS), '--out', str(out)]) == 0
    assert out.read_text(encoding='utf-8').startswith('# Paper 1 results tables (test)')
    bad = copy.deepcopy(synthetic())
    bad['results']['confirmatory']['harm_check_F-FA_vs_B0']['ALL']['noninferior'] = True
    p = tmp_path / 'bad.json'
    p.write_text(json.dumps(bad), encoding='utf-8')
    assert r.main([str(p)]) == 2
