"""Fixtures for E8 availability, composition safeguards and edition agreement."""

import struct
import unittest
from collections import defaultdict
from datetime import date
from unittest.mock import Mock

from loe_bench.moiety import Registry
from loe_bench.nber_ob import _expiry, nber_sources, read_dta118
from loe_bench.ob_history import Edition, EditionSource, OBHistory
from loe_bench.ob_linkage import HistoricalMoietyLinker
from loe_bench.ob_overlap import compare_editions
from loe_bench.t2_features import AsOfBuilder


def _tiny_dta():
    sections = [
        b"<stata_dta><header><release>118</release><byteorder>LSF</byteorder>"
        b"<K>\x03\0</K><N>\x02\0\0\0\0\0\0\0</N></header>",
        b"<map>" + bytes(112) + b"</map>",
        b"<variable_types>" + struct.pack("<3H", 65529, 65527, 6) + b"</variable_types>",
        b"<varnames>" + b"".join(k.ljust(129, b"\0") for k in (b"edition", b"expiry", b"nda"))
        + b"</varnames>",
        b"<sortlist></sortlist>", b"<formats></formats>", b"<value_label_names></value_label_names>",
        b"<variable_labels></variable_labels>", b"<characteristics></characteristics>",
        b"<data>" + struct.pack("<hf6shf6s", 1987, 1, b"000123", 2010, 2**127, b"000120") + b"</data>",
        b"<strls></strls>", b"<value_labels></value_labels>", b"</stata_dta>",
    ]
    offsets = [0]
    for section in sections:
        offsets.append(offsets[-1] + len(section))
    sections[1] = b"<map>" + struct.pack("<14Q", *offsets) + b"</map>"
    return b"".join(sections)


def _source(day, available, kind, *, protection_only=False):
    loader = Mock(return_value=Edition(day, [], [], [], protection_only=protection_only))
    return EditionSource(day, loader, {"kind": kind}, ({"date": available.isoformat()},))


class TestE8(unittest.TestCase):
    def test_stata_dates_and_numeric_missing(self):
        first, second = read_dta118(_tiny_dta())
        self.assertEqual((first["edition"], first["nda"], _expiry(first["expiry"])),
                         (1987, "000123", date(1960, 1, 2)))
        self.assertIsNone(_expiry(second["expiry"]))
        with self.assertRaises(ValueError):
            list(read_dta118(_tiny_dta()[:-2]))

    def test_annual_availability_basis(self):
        assumed, exact = nber_sources({
            "archive": {"file": "unused.zip"},
            "editions": [{"year": 2009}, {"year": 2010, "publication_date": "2010-02-09"}],
        })
        self.assertEqual(assumed.edition_date, date(2009, 12, 31))
        self.assertEqual(assumed.availability[0]["date"], "2010-01-01")
        self.assertEqual(exact.availability[0]["date"], "2010-02-09")
        history = OBHistory([assumed, exact])
        self.assertEqual(history.features_asof("1", date(2009, 12, 31))["status"], "UNKNOWN")
        self.assertIs(history.available_source_asof(date(2010, 2, 8))[0], assumed)
        self.assertIs(history.available_source_asof(date(2010, 2, 9))[0], exact)

    def test_freshest_admitted_source_and_zip_tie(self):
        annual = _source(date(2010, 12, 31), date(2011, 1, 1), "nber_annual", protection_only=True)
        earlier = _source(date(2010, 12, 30), date(2010, 12, 30), "fda_zip")
        tied = _source(date(2010, 12, 31), date(2011, 1, 2), "fda_zip")
        history = OBHistory([tied, earlier, annual])
        self.assertEqual(history.features_asof("12345", date(2010, 12, 31))["source"]["kind"], "fda_zip")
        annual.loader.assert_not_called()
        tied.loader.assert_not_called()
        result = history.features_asof("12345", date(2011, 1, 1))
        self.assertEqual(result["source"]["kind"], "nber_annual")
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertIsNone(result["n_patents"])
        self.assertEqual(history.features_asof("12345", date(2011, 1, 2))["source"]["kind"], "fda_zip")
        self.assertEqual(AsOfBuilder(history).build("X", date(2011, 1, 2), 12, {}).edition_source["kind"],
                         "fda_zip")

    def test_partial_ingredient_needs_exact_composition_anchor(self):
        linker = object.__new__(HistoricalMoietyLinker)
        linker.registry = Registry()
        linker.aliases = {}
        linker.entities = {"ALPHA": object(), "ALPHA|BETA": object()}
        linker.nda_products = defaultdict(set, {("012345", "001"): {("ALPHA|BETA", frozenset())}})
        row = dict(appl_no="012345", product_no="001", ingredient="ALPHA", partial_ingredient=True)
        self.assertEqual(linker.match(row), ("ALPHA|BETA", "application_product_partial_ingredient"))
        self.assertEqual(linker.match(dict(row, product_no="002")), (None, "no_exact_product_anchor"))
        row.update(appl_type="N", ingredient_key="ALPHA", approval_date=None)
        expiry = date(2012, 1, 1)
        patent = dict(appl_no="012345", product_no="001", appl_type="N", patent_no="1", expiry=expiry,
                      submission_date=None, has_submission_col=False, use_code="",
                      drug_substance=None, drug_product=None, delist=None)
        cutoff = date(2000, 1, 1)
        edition = Edition(cutoff, [row], [patent, dict(patent, appl_type="A", patent_no="2")], [],
                          protection_only=True)
        source = EditionSource(cutoff, lambda: edition, {"kind": "nber_annual"},
                               ({"date": cutoff.isoformat()},))
        history = OBHistory([source])
        self.assertEqual(history.features_asof("ALPHA|BETA", cutoff, linker=linker)["n_patents"], 1)
        self.assertEqual(AsOfBuilder(history, linker=linker).build(
            "ALPHA|BETA", cutoff, 12, {}).x["listed_patent_count"], 1)

    def test_overlap_collapses_products_and_requires_exact_expiry(self):
        day1, day2 = date(2024, 1, 1), date(2025, 1, 1)
        p1 = dict(appl_type="N", appl_no="000001", patent_no="01", expiry=day1)
        p2 = dict(p1, patent_no="02")
        x = dict(appl_type="N", appl_no="000001", code="NCE", expiry=day1)
        a = Edition(day1, [], [p1, dict(p1, product_no="002"), p2], [x])
        b = Edition(day2, [], [dict(p1, patent_no="01*PED"), dict(p2, expiry=day2),
                               dict(p1, appl_type="A", patent_no="03")],
                    [x, dict(x, appl_type="")])
        result = compare_editions(a, b, lambda row: row["appl_type"])
        self.assertEqual(result["patents"]["jaccard"], 1 / 3)
        self.assertEqual(result["patents"]["raw_zip_identifier_jaccard"], 0)
        self.assertEqual(result["patents"]["shared_identity_different_expiry_sets"], 1)
        self.assertEqual(result["patents"]["archival_excluded"], {"non_nda": 1})
        self.assertEqual(result["exclusivity"]["jaccard"], 1)
        self.assertEqual(result["exclusivity"]["archival_excluded"], {"unclassified": 1})
