import numpy as np

import power_sim as sim
from loe_bench.review_metrics import ReviewQueue
from loe_bench.tracka_statistics import panel as registered_panel


def test_calendars_and_full_panel_burden():
    a, b, c, d, e, f = map(sim.burden, sim.DESIGNS[:6])
    all_burden = (a, b, c, d, e, f)
    assert [x["total_freezes_and_prediction_runs_each"] for x in all_burden] == [1, 43, 12, 7, 43, 24]
    assert [x["final_maturity"] for x in all_burden] == [
        "2028-11-27", "2039-10-01", "2039-10-01", "2039-10-01", "2040-10-01", "2039-10-01",
    ]
    assert abs(b["completion"]["0.99"]["0.0"] - .99**43) < 1e-12
    assert a["already_frozen"]


def test_horizons_share_one_event_and_absorb_after_approval():
    t4c, _ = sim.source()
    fits = sim.unpack_fits(t4c)
    a = sim.DESIGNS[0]
    panel, n = sim.make_panel(a, sim.CENTRAL, fits, np.random.default_rng(2026))
    assert n == 651
    first = panel[12][0]
    second = panel[24][0]
    assert np.array_equal(first.drugs, second.drugs)
    assert first.event.sum() < second.event.sum()
    assert not np.any(first.event & ~second.event)

    b = sim.DESIGNS[1]
    panel, _ = sim.make_panel(b, sim.CENTRAL, fits, np.random.default_rng(2026))
    rows = panel[24]
    mature = set(rows[0].drugs[rows[0].event])
    assert mature
    assert mature.isdisjoint(rows[8].drugs)
    assert mature.intersection(rows[1].drugs[rows[1].event])


def test_exact_counts_rebuild_queue_and_split_ties():
    row_ids = np.array([0, 1, 2, 4, 5, 6])
    score = np.array([.9, .8, .8, .5, .3, .1])
    event = np.array([False, True, False, True, False, False])
    s = sim.Stratum(row_ids, event, score, np.zeros((6, 2)), None)
    counts = np.array([[1, 1, 1, 1, 1, 1, 1], [0, 1, 3, 0, 1, 1, 1], [0, 0, 0, 5, 2, 0, 0],
                       [0, 1, 1, 1, 4, 0, 0]], dtype=np.int16)
    totals = counts[:, row_ids].sum(axis=1, dtype=np.int32)
    queue = ReviewQueue(score, np.zeros(len(score), dtype=int))
    expected = [np.dot(queue.allocation(row[row_ids])[0], event * row[row_ids]) for row in counts]
    assert np.allclose(expected, [0., .25, 0., .5], rtol=0, atol=1e-15)
    for method in (sim.exact_capture, sim.bootstrap_capture):
        assert np.allclose(method(score, s, counts, totals // 5), expected, rtol=0, atol=1e-15)


def test_registered_seed_and_exact_bootstrap_agree():
    n = 55
    rng = np.random.default_rng(321)
    y = np.arange(n) < 12
    b1 = rng.integers(5, size=n) / 5
    m = rng.normal(size=(n, 2)) + y[:, None]
    keys = [f"{i:03d}" for i in range(n)]
    native = {a: [(score, .3, True) for score in s] for a, s in zip(("B1", "M1", "M3"), (b1, *m.T), strict=True)}
    _, saved = registered_panel(keys, native, y, np.ones(n))
    s = sim.Stratum(np.arange(n), y, b1, m, None)
    methods = sim.panel_metrics([s], n, (0., 0.), sim.PAIRS, draws=2000, seed=20261127)
    expected = [np.quantile(saved[f"M3-{a}:recall"], .025, method="linear") for a in ("B1", "M1")]
    np.testing.assert_allclose(methods["full"], expected, atol=1e-12, rtol=0)


def test_overlapping_origins_share_drug_weights_and_rebuild_each_capacity():
    rng = np.random.default_rng(18)
    ids = [np.arange(28), np.arange(4, 31)]
    strata = [sim.Stratum(keys, (keys % 3) != 1, (keys % 6) / 6,
                         rng.integers(12, size=(len(keys), 2)) / 12, None) for keys in ids]
    keys = np.concatenate(ids)
    labels = np.concatenate([s.event for s in strata])
    cutoffs = np.repeat(np.arange(2), [len(s.drugs) for s in strata])
    scores = np.concatenate([s.scores((0., 0.)) for s in strata])
    queues = [ReviewQueue(arm, cutoffs) for arm in scores.T]
    recalls = []
    for counts in sim.bootstrap_counts(31, 400, 20270401):
        row_weights = counts[keys]
        positives = labels * row_weights
        recalls.append([queue.allocation(row_weights)[0] @ positives / positives.sum() for queue in queues])
    recalls = np.asarray(recalls)
    expected = np.quantile(recalls[:, [2]] - recalls[:, :2], .025, axis=0, method="linear")
    observed = sim.panel_metrics(strata, 31, (0., 0.), sim.PAIRS, draws=400)["full"]
    np.testing.assert_allclose(observed, expected, atol=1e-12, rtol=0)


def test_no_bootstrap_events_is_unevaluable():
    y = np.zeros(10, dtype=bool)
    s = sim.Stratum(np.arange(10), y, np.arange(10), np.ones((10, 2)), None)
    result = sim.panel_metrics([s], 10, (0., 0.), sim.PAIRS, draws=2000)
    assert result["invalid_draws"] == 2000
    assert np.isnan(result["full"]).all()


def test_sequence_rates_treat_undefined_as_non_rejection():
    bounds = np.array([[.1, .1, .1], [-.1, .2, .1], [0., .1, .1], [.1, np.nan, .1]])
    result = sim.outcome_rates(bounds)
    assert result["H2"]["marginal"]["count"] == 3
    assert result["H2"]["sequence"]["count"] == 1
    assert result["H2"]["conditional"]["denominator"] == 2
    assert result["H2"]["unevaluable"]["count"] == 1
    assert result["H2"]["sequence"]["mcse"] > 0


def test_calibration_uses_exact_rank_breakpoints():
    score = np.array([9., 8., 6., 5., 3., 11., 4., 1., 0., -.5])
    event = np.array([False] * 5 + [True, True, False, False, False])
    edges = np.sort(sim.breakpoints(score, event))
    for shift in (-3.1, -1., 2., 6., 10.):
        shifted = score + event * shift
        expected = np.searchsorted(edges, shift)
        assert expected == sim.allocation(shifted, np.sort(shifted), len(event) // 5) @ event


def test_t4c_reference_is_only_a_committed_tabulation():
    raw, digest = sim.source()
    assert len(digest) == 64
    rates = sim.reference_rates(raw)
    assert [rates[n]["H1"]["count"] for n in (50, 75, 150)] == [1838, 2498, 4029]
    assert [rates[n]["H2"]["count"] for n in (50, 75, 150)] == [102, 197, 680]
