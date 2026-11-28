"""Check which C9 rows can be affected by missing ANDA attribution."""

from datetime import date
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from c9_dev_projection import linkage_scope, sensitivity


class DevelopmentLinkageTest(unittest.TestCase):
    def test_attributable_ambiguity_and_unlinked_pool_are_separate(self):
        excluded = [
            dict(approval="1993-01-02", dated_groups=[], undated_groups=[], orange_book_leads=[]),
            dict(approval="1995-01-01", dated_groups=["A"], undated_groups=["A", "B"],
                 orange_book_leads=[]),
            dict(approval="1997-01-01", dated_groups=[], undated_groups=[],
                 orange_book_leads=[{"key": "C"}]),
        ]
        scope, unlinked = linkage_scope(excluded)
        self.assertEqual(scope, {"B": [date(1995, 1, 1)], "C": [date(1997, 1, 1)]})
        self.assertEqual(unlinked, [date(1993, 1, 2)])

    def test_sensitivity_counts_rows_once_and_distinguishes_prior_from_window(self):
        rows = [
            dict(t=date(1995, 1, 1), t_end=date(1997, 1, 1), y=0),
            dict(t=date(1996, 1, 1), t_end=date(1998, 1, 1), y=1),
            dict(t=date(2000, 1, 1), t_end=date(2002, 1, 1), y=0),
        ]
        self.assertEqual(
            sensitivity(rows, [date(1995, 1, 1), date(1997, 1, 1), date(1997, 2, 1)]),
            dict(prior_eligibility=3, within_window=2, union=3, negative_labels=1),
        )
