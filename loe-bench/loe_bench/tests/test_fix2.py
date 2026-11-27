"""Active-moiety and product-scope fixtures for the T7 error classes."""
import unittest
from datetime import date
from unittest.mock import patch

from loe_bench import dataset
from loe_bench.moiety import Registry
from loe_bench.ob_history import Edition
from loe_bench.t2_features import _EditionIndex
from loe_bench.tests.test_fix1 import RawFixture, application, original, product, write_jsonl


def substance(unii, *names, moiety=None, relation="ACTIVE MOIETY"):
    return {
        "approvalID": unii,
        "names": [{"name": name} for name in names],
        "relationships": [{"type": relation, "relatedSubstance": {"approvalID": moiety}}] if moiety else [],
    }


def fixtures():
    return Registry([
        substance("0000000001", "ALPHA"),
        substance("0000000002", "ALPHA HYDROCHLORIDE", "ALPHA HCL", moiety="0000000001"),
        substance("0000000003", "ALPHA VALERATE", moiety="0000000001"),
        substance("0000000004", "ALPHA HYCLATE", moiety="0000000001"),
        substance("0000000005", "ALPHAZ"),
        substance("0000000006", "BETA"),
        substance("0000000007", "WATER"),
        substance("0000000008", "SODIUM PHOSPHATE DIBASIC HEPTAHYDRATE", moiety="0000000010"),
        substance("0000000009", "POTASSIUM PHOSPHATE DIBASIC", moiety="0000000010"),
        substance("0000000010", "PHOSPHATE ION"),
        substance("0000000011", "DEXTROSE", "DEXTROSE MONOHYDRATE"),
        substance("0000000012", "BETA ALCOHOL", moiety="0000000006", relation="METABOLITE"),
        substance("0000000013", "SHARED"),
        substance("0000000014", "SHARED"),
    ])


class TestRegistry(unittest.TestCase):
    def setUp(self):
        self.registry = fixtures()

    def test_registry_alias_salts_ester_and_hydrate(self):
        for name in ("ALPHA", "ALPHA HYDROCHLORIDE", "ALPHA HCL", "ALPHA VALERATE", "ALPHA HYCLATE"):
            with self.subTest(name=name):
                resolved = self.registry.composition([name])
                self.assertEqual(resolved.key, "U:0000000001")
                self.assertFalse(resolved.low_confidence)

    def test_preserves_distinct_names_electrolytes_and_non_moiety_relations(self):
        comp = self.registry.composition
        self.assertNotEqual(comp(["ALPHA"]).key, comp(["ALPHAZ"]).key)
        self.assertNotEqual(comp(["BETA"]).key, comp(["BETA ALCOHOL"]).key)
        self.assertEqual(comp(["SODIUM PHOSPHATE DIBASIC HEPTAHYDRATE"]).key,
                         comp(["SODIUM PHOSPHATE DIBASIC"]).key)
        self.assertNotEqual(comp(["SODIUM PHOSPHATE DIBASIC"]).key,
                            comp(["POTASSIUM PHOSPHATE DIBASIC"]).key)

    def test_combination_set_order_repetition_and_compound_field(self):
        comp = self.registry.composition
        expected = "U:0000000001|U:0000000006"
        self.assertEqual(comp(["BETA", "ALPHA HYCLATE", "ALPHA"]).key, expected)
        self.assertEqual(comp(["ALPHA: BETA", "BETA"]).key, expected)
        self.assertNotEqual(comp(["ALPHA"]).key, expected)

    def test_fallback_is_low_confidence_and_annotation_can_disambiguate(self):
        comp = self.registry.composition
        self.assertEqual(comp(["UNKNOWN DIMALEATE"]).key, "UNKNOWN")
        self.assertTrue(comp(["UNKNOWN DIMALEATE"]).low_confidence)
        self.assertTrue(comp(["SHARED"]).low_confidence)
        self.assertEqual(comp(["SHARED"], ["0000000014"]).key, "U:0000000014")
        self.assertEqual(comp(["STERILE WATER FOR INJECTION"], ["0000000007"]).key,
                         comp(["WATER"]).key)

    def test_label_scope_conflict_and_corroborated_extra(self):
        native = product("ALPHA HYDROCHLORIDE", brand_name="ALPHA 0.2% AND DEXTROSE 5%")
        annotation = {"substance_name": ["ALPHA HCL", "DEXTROSE MONOHYDRATE"],
                      "unii": ["0000000011", "0000000002"], "spl_id": ["a"]}
        self.assertEqual(self.registry.product(native, annotation).key, "U:0000000001|U:0000000011")
        annotation["spl_id"] = ["a", "b"]
        self.assertEqual(self.registry.product(native, annotation).key, "U:0000000001")
        annotation["spl_id"] = ["a"]
        annotation["substance_name"] = ["ALPHA", "BETA"]
        self.assertEqual(self.registry.product(native, annotation).key, "U:0000000001")


class TestEntityModes(RawFixture):
    def test_mixed_original_products_get_distinct_keys_and_no_invented_dates(self):
        a = product("ALPHA", product_number="001")
        b = product("ALPHA: BETA", product_number="002")
        rec = application([original("20000101", submission_class_code="TYPE 1")], a, b)
        rec["application_number"] = "NDA000001"
        andas = [application([original("20010101")], product("ALPHA HYDROCHLORIDE"))]
        write_jsonl(self.raw, "ob_nda.jsonl", [
            dict(product_number=number, approval_date=when, products=[
                dict(application_type="N", application_number="000001", **p)])
            for number, when, p in [("001", "20000101", a), ("002", "20050101", b)]
        ])
        with patch.object(dataset, "registry_for", return_value=fixtures()):
            entities = self.build([rec], andas)
        single, combo = "U:0000000001", "U:0000000001|U:0000000006"
        self.assertEqual(set(entities), {single, combo})
        self.assertEqual(entities[single].nda_first, date(2000, 1, 1))
        self.assertEqual(entities[single].anda_first, date(2001, 1, 1))
        self.assertIsNone(entities[combo].nda_first)
        self.assertFalse(entities[combo].nme)
        self.assertEqual(set(dataset.build_entities(self.raw, key_mode="legacy")), {"ALPHA|ALPHA BETA"})

    def test_missing_registry_flag_and_legacy_replay(self):
        ndas = [application([original("20000101")],
                            product("SODIUM CHLORIDE"), product("POTASSIUM CHLORIDE"))]
        entities = self.build(ndas, [])
        self.assertEqual(set(entities), {"E:SODIUM CHLORIDE", "E:POTASSIUM CHLORIDE"})
        self.assertTrue(all(e.key_confidence == "LOW_CONFIDENCE" for e in entities.values()))
        self.assertEqual(dataset.build_entities(self.raw, key_mode="legacy"), {})

    def test_snapshot_and_historical_edition_share_moiety_keys(self):
        when = date(2000, 1, 1)
        item = product("ALPHA VALERATE")
        write_jsonl(self.raw, "ob_nda.jsonl", [
            {"approval_date": "20000101", "products": [item],
             "patents": [{"expiration_date": "20100101"}]},
        ])
        with patch.object(dataset, "registry_for", return_value=fixtures()):
            entities = self.build([application([original("20000101")], product("ALPHA"))], [])
            snapshot = dataset.snapshot_features(self.raw, when, entities)
        key = "U:0000000001"
        self.assertEqual(snapshot[key]["patent_exp"], [date(2010, 1, 1)])

        historical = {"ingredient": "ALPHA VALERATE", "ingredient_key": "ALPHA VALERATE",
                      "appl_type": "N", "approval_date": when, "appl_no": "1", "product_no": "1"}
        edition = Edition(when, [historical], [], [])
        self.assertEqual(_EditionIndex(edition, fixtures()).records(key), ([], []))
        self.assertEqual(_EditionIndex(edition).records("ALPHA VALERATE"), ([], []))
