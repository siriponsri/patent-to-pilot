from dataclasses import replace
from datetime import date
import unittest

from loe_bench.ob_linkage import HistoricalMoietyLinker
from loe_bench.psg import Capture, PSGHistory, link_key, parse_listing
from loe_bench.tests.test_fix2b import audit_registry


def archived_row(name="Nicotine Polacrilex", recommendation="02/2012"):
    html = f"""
    <table summary="Newly Added Recommendations">
      <tr><th>Revisions</th><th></th></tr>
      <tr><th>Active Ingredient</th><th>Type</th><th>Route</th>
          <th>Dosage Form</th><th>RLD Application Number</th><th>Date Recommended</th></tr>
      <tr><td><a href="/downloads/UCM001.pdf">{name} (PDF - 12KB)</a></td>
          <td>Draft</td><td>Oral</td><td>Gum</td><td>12345</td><td>{recommendation}</td></tr>
    </table>
    """
    row, = parse_listing(html, "fixture", "http://www.fda.gov/", archived=True)
    return row


class TestPSGAsOf(unittest.TestCase):
    def test_month_precision_future_posting_and_revision(self):
        row = archived_row()
        self.assertEqual(row.kind, "revision")
        self.assertEqual(row.recommended_by, date(2012, 2, 29))
        self.assertEqual(row.applications, ("012345",))
        history = PSGHistory([Capture(date(2012, 2, 20), (("NICOTINE", row),))])
        self.assertIsNone(history.psg_asof("NICOTINE", date(2012, 2, 28))["has_psg"])
        features = history.psg_asof("NICOTINE", date(2012, 2, 29))
        self.assertEqual(features, dict(has_psg=True, years_since_first_psg=None, n_psgs=1,
                                        revised_within_1y=True))
        self.assertIsNone(history.psg_asof("NICOTINE", date(2013, 2, 1))["revised_within_1y"])
        contradictory = PSGHistory([Capture(date(2012, 1, 31), (("NICOTINE", row),))])
        self.assertIsNone(contradictory.psg_asof("NICOTINE", date(2013, 1, 1))["has_psg"])

    def test_wayback_late_capture_is_excluded_and_complete_membership_filters(self):
        row = replace(archived_row(), kind="new")
        partial = Capture(date(2012, 3, 1), (("NICOTINE", row),))
        complete = Capture(date(2012, 5, 1), (), complete=True)
        later = Capture(date(2012, 7, 1), (("NICOTINE", row),), complete=True)
        history = PSGHistory([later, partial, complete])
        self.assertIsNone(history.psg_asof("NICOTINE", date(2012, 2, 29))["has_psg"])
        self.assertTrue(history.psg_asof("NICOTINE", date(2012, 3, 1))["has_psg"])
        self.assertIsNone(history.psg_asof("NICOTINE", date(2012, 5, 1))["n_psgs"])
        self.assertEqual(history.psg_asof("NICOTINE", date(2012, 7, 1))["n_psgs"], 1)
        values = history.model_values("UNKNOWN", date(2012, 7, 1))
        self.assertEqual(values["has_psg_missing"], 1.0)
        self.assertEqual(values["has_psg"], 0.0)

    def test_fix2c_resolves_whole_composition_and_aliases(self):
        linker = HistoricalMoietyLinker.__new__(HistoricalMoietyLinker)
        linker.registry = audit_registry()
        legacy_key = linker.registry.composition(["Nicotine Polacrilex"]).key
        linker.aliases = {legacy_key: "NICOTINE"}
        linker.entities = {"NICOTINE": object()}
        self.assertEqual(link_key(archived_row(), linker), "NICOTINE")
        self.assertIsNone(link_key(archived_row("Nicotine Polacrilex; Unrecognized Agent"), linker))
