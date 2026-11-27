import os
import unittest
from datetime import date

from loe_bench.ob_history import (OBHistory, load_edition, parse_exclusivity, parse_ob_date,
                                  parse_patents, parse_products)

FIX = os.path.join(os.path.dirname(__file__), "fixtures")
P12 = os.path.join(FIX, "ob_ed_2012.zip")
P20 = os.path.join(FIX, "ob_ed_2020.zip")


def _hist():
    return OBHistory([(date(2012, 1, 17), lambda: load_edition(P12, date(2012, 1, 17))),
                      (date(2020, 10, 9), lambda: load_edition(P20, date(2020, 10, 9)))])


class TestParsing(unittest.TestCase):
    def test_dates(self):
        self.assertEqual(parse_ob_date("Apr 28, 2020"), date(2020, 4, 28))
        self.assertIsNone(parse_ob_date("Approved Prior to Jan 1, 1982"))
        self.assertIsNone(parse_ob_date(""))

    def test_products_with_header_and_ingredient_key(self):
        e = load_edition(P20, date(2020, 10, 9))
        self.assertEqual(len(e.products), 3)
        self.assertEqual(e.products[0]["ingredient_key"], "DRUGA")  # salt word dropped
        self.assertEqual(e.products[2]["ingredient_key"], "DRUGC|DRUGD")
        self.assertIsNone(e.products[1]["approval_date"])

    def test_products_headerless_2009_style(self):
        e = load_edition(P12, date(2012, 1, 17))
        self.assertEqual([p["appl_no"] for p in e.products], ["012345", "023456"])
        self.assertEqual(e.products[0]["approval_date"], date(2010, 1, 5))

    def test_patent_with_and_without_submission_column(self):
        new = load_edition(P20, date(2020, 10, 9)).patents
        old = load_edition(P12, date(2012, 1, 17)).patents
        self.assertTrue(all(p["has_submission_col"] for p in new))
        self.assertEqual(new[0]["submission_date"], date(2012, 2, 2))
        self.assertIsNone(new[2]["submission_date"])  # blank in file
        self.assertFalse(any(p["has_submission_col"] for p in old))
        self.assertTrue(old[0]["drug_substance"] and old[0]["drug_product"])
        self.assertTrue(new[1]["delist"])
        self.assertEqual(new[0]["use_code"], "U-1")

    def test_exclusivity(self):
        new = load_edition(P20, date(2020, 10, 9)).exclusivity
        old = load_edition(P12, date(2012, 1, 17)).exclusivity
        self.assertEqual((new[0]["code"], new[0]["expiry"]), ("NP", date(2022, 1, 5)))
        self.assertEqual((old[0]["code"], old[0]["expiry"]), ("NCE", date(2015, 1, 5)))

    def test_inline_text_parsers(self):
        self.assertEqual(len(parse_products("Ingredient~Appl_No~Product_No\nX~1~001\n")), 1)
        self.assertEqual(parse_patents("Appl_No~Patent_No\n5~9\n")[0]["patent_no"], "9")
        self.assertEqual(parse_exclusivity("Appl_No~Exclusivity_Code\n5~NCE\n")[0]["code"], "NCE")


class TestAsOf(unittest.TestCase):
    def test_leakage_future_edition_never_used(self):
        h = _hist()
        # cutoff before the 2020 edition: its patent 3333333 and NP exclusivity must not appear
        f = h.features_asof("012345", date(2019, 12, 31))
        self.assertEqual(f["edition_date"], "2012-01-17")
        self.assertEqual({p["patent_no"] for p in f["patents"]}, {"1111111", "2222222"})
        self.assertEqual(f["exclusivity_codes"], ["NCE"])
        self.assertNotIn(date(2020, 10, 9), h._cache)  # later edition never even loaded
        # the day the later edition is dated it becomes eligible; the day before it is not
        self.assertEqual(h.features_asof("012345", date(2020, 10, 8))["edition_date"], "2012-01-17")
        g = h.features_asof("012345", date(2020, 10, 9))
        self.assertEqual(g["edition_date"], "2020-10-09")
        self.assertIn("3333333", {p["patent_no"] for p in g["patents"]})

    def test_features_values(self):
        g = _hist().features_asof("12345", date(2021, 1, 1))
        self.assertEqual(g["status"], "OK")
        self.assertEqual(g["n_patents"], 2)
        self.assertEqual(g["n_unexpired_patents"], 1)  # 2022222 expired 2020-06-01 < cutoff
        self.assertEqual(g["max_patent_expiry"], "2031-06-01")
        self.assertEqual(g["max_exclusivity_expiry"], "2022-01-05")
        self.assertEqual(g["earliest_patent_submission"], "2012-02-02")
        self.assertTrue(g["submission_date_available"])
        old = _hist().features_asof("012345", date(2013, 1, 1))
        self.assertFalse(old["submission_date_available"])
        self.assertIsNone(old["earliest_patent_submission"])

    def test_ingredient_key_lookup(self):
        g = _hist().features_asof("DRUGD|DRUGC", date(2021, 1, 1))
        self.assertEqual(g["n_patents"], 1)
        self.assertEqual(g["exclusivity_codes"], ["ODE-1"])
        self.assertEqual(_hist().features_asof("DRUGA HYDROCHLORIDE", date(2013, 1, 1))["status"], "OK")

    def test_missing_edition_is_unknown_not_false(self):
        f = _hist().features_asof("012345", date(2011, 12, 31))
        self.assertEqual(f["status"], "UNKNOWN")
        self.assertIsNone(f["listed"])
        self.assertIsNone(f["n_patents"])
        self.assertIsNone(f["exclusivity_codes"])
        self.assertIsNone(f["edition_date"])
        self.assertEqual(OBHistory([]).features_asof("1", date(2020, 1, 1))["status"], "UNKNOWN")

    def test_not_listed_is_distinct_from_unknown(self):
        f = _hist().features_asof("999999", date(2021, 1, 1))
        self.assertEqual(f["status"], "NOT_LISTED")
        self.assertIs(f["listed"], False)
        self.assertEqual(f["n_patents"], 0)

    def test_real_manifest_if_data_present(self):
        mp = os.path.join(os.path.dirname(__file__), "..", "..", "data", "OB_EDITIONS.json")
        from loe_bench.ob_history import DEFAULT_DIR
        if not (os.path.exists(mp) and os.path.isdir(DEFAULT_DIR)):
            self.skipTest("private OB editions not available")
        h = OBHistory.from_manifest(mp)
        self.assertGreaterEqual(len({d.year for d in h.edition_dates()}), 2)
        self.assertEqual(h.features_asof("202155", date(2009, 1, 1))["status"], "UNKNOWN")  # before first edition
        e = h.features_asof("202155", date(2021, 6, 1))  # ELIQUIS 2.5MG tablet
        self.assertEqual(e["status"], "OK")
        self.assertEqual(e["edition_date"], "2021-02-12")
        self.assertGreater(e["n_patents"], 0)
        # approval (Dec 2012) postdates the 2009-12 edition: listed=False there, not UNKNOWN
        self.assertEqual(h.features_asof("202155", date(2011, 1, 1))["status"], "NOT_LISTED")

if __name__ == "__main__":
    unittest.main()
