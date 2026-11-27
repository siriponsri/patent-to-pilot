"""Regression cases from the eleven FIX2 design splits and identifier guards."""
import unittest
from datetime import date
from unittest.mock import patch

from loe_bench import dataset
from loe_bench.moiety import Registry
from loe_bench.moiety_linkage import link_compositions
from loe_bench.tests.test_fix1 import RawFixture, application, original, product, write_jsonl
from loe_bench.tests.test_fix2 import substance


# The first two IDs per ambiguous name reproduce the decision at the GSRS
# approvalID locators. The named FDA anchors are in FIX2_fresh_audit.csv.
AMBIGUOUS = (
    ("ESTRADIOL", "4TI98Z838E", "VW299DJ6U7", None),
    ("CARVEDILOL", "0K47UL67F2", "GW13D96IND", None),
    ("AMLODIPINE BESYLATE", "864V2Q084H", "885H5YC40L", "1J444QC288"),
    ("MODAFINIL", "R3UK8X3U3D", "152JRG3T0U", None),
    ("ETODOLAC", "2M36281008", "1046G5D6YD", None),
    ("DULOXETINE HYDROCHLORIDE", "9044SC542W", "7AKC5EXT4Q", "O5TNM5N07U"),
    ("ABACAVIR SULFATE", "J220T4J9Q2", "1PPL256S5A", "WR2TIP26VS"),
    ("PROPRANOLOL HYDROCHLORIDE", "F8A3652H1V", "YP6GDU0L78", "9Y8NXQ24VQ"),
    ("CHLORPHENIRAMINE MALEATE", "V1Q0O9OJ9Z", "5T8587JTSU", "3U6IO1965U"),
    ("IBUPROFEN", "WK2XYI10QM", "99W8H60N62", None),
    ("NICOTINE", "6M3C89ZY6R", "42XNU684Z1", None),
)
OTHER = (
    ("NORETHINDRONE ACETATE", "9S44LIC7OJ", "T18F433X4S"),
    ("BENAZEPRIL HYDROCHLORIDE", "N1SN99T69T", "JRM708L703"),
    ("LAMIVUDINE", "2T8Q726O95", None),
    ("PSEUDOEPHEDRINE HYDROCHLORIDE", "6V9V2RYJ8N", "7CUC9DDI9F"),
)
CASES = (
    ("ESTRADIOL", "NORETHINDRONE ACETATE"),
    ("NICOTINE POLACRILEX",),
    ("CARVEDILOL",),
    ("AMLODIPINE BESYLATE",),
    ("AMLODIPINE BESYLATE", "BENAZEPRIL HYDROCHLORIDE"),
    ("MODAFINIL",),
    ("ETODOLAC",),
    ("DULOXETINE HYDROCHLORIDE",),
    ("ABACAVIR SULFATE", "LAMIVUDINE"),
    ("PROPRANOLOL HYDROCHLORIDE",),
    ("CHLORPHENIRAMINE MALEATE", "IBUPROFEN", "PSEUDOEPHEDRINE HYDROCHLORIDE"),
)


def audit_registry():
    records = [substance(code, name, moiety=target)
               for name, code, _, target in AMBIGUOUS]
    records.extend(substance(other, name) for name, _, other, _ in AMBIGUOUS)
    records.extend(substance(code, name, moiety=target) for name, code, target in OTHER)
    return Registry(records)


class TestFix2bEntities(RawFixture):
    def test_eleven_design_splits_link_original_nda_and_anda(self):
        registry = audit_registry()
        codes = {row[0]: row[1] for row in AMBIGUOUS + OTHER}
        for names in CASES:
            with self.subTest(names=names):
                resin = names == ("NICOTINE POLACRILEX",)
                label = ("NICOTINE",) if resin else names
                item = product(names[0])
                item["active_ingredients"] = [{"name": name} for name in names]
                nda = application([original("20000101")], item)
                anda = application([original("20020101")], product("NICOTINE") if resin else item)
                annotated = [codes[name] for name in label]
                if resin:
                    nda["openfda"] = {"substance_name": list(label), "unii": annotated}
                anda["openfda"] = {"substance_name": list(label), "unii": annotated}
                with patch.object(dataset, "registry_for", return_value=registry):
                    entities = self.build([nda], [anda])
                    fix2 = dataset.build_entities(self.raw, key_mode="fix2")
                self.assertEqual(len(entities), 1)
                entity, = entities.values()
                self.assertEqual(entity.key, "|".join(sorted(registry.from_ids(annotated))))
                self.assertEqual(entity.anda_first, date(2002, 1, 1))
                self.assertIsNone(next(iter(fix2.values())).anda_first)

    def test_snapshot_uses_canonical_key_for_unannotated_product(self):
        item = product("CARVEDILOL")
        nda = application([original("20000101")], item)
        nda["openfda"] = {"substance_name": ["CARVEDILOL"], "unii": ["0K47UL67F2"]}
        write_jsonl(self.raw, "ob_nda.jsonl", [
            {"approval_date": "20000101", "products": [item],
             "patents": [{"expiration_date": "20100101"}]},
        ])
        with patch.object(dataset, "registry_for", return_value=audit_registry()):
            entities = self.build([nda], [])
            snapshots = dataset.snapshot_features(self.raw, date(2000, 1, 1), entities)
        self.assertEqual(snapshots["U:0K47UL67F2"]["patent_exp"], [date(2010, 1, 1)])


class TestLinkage(unittest.TestCase):
    def test_synonyms_salt_and_similar_names(self):
        registry = Registry([
            substance("0000000001", "ALPHA"),
            substance("0000000002", "ALPHA HYDROCHLORIDE", "ALPHA HCL", moiety="0000000001"),
            substance("0000000003", "ALPHAZ", "ALPHA-Z"),
            substance("0000000004", "BETA"),
        ])
        base, salt, distinct, combo = [registry.composition(names) for names in (
            ["ALPHA"], ["Alpha HCl"], ["ALPHA-Z"], ["ALPHA", "BETA"])]
        links = link_compositions([base, salt, distinct, combo])
        self.assertEqual(links.key(base.key), links.key(salt.key))
        self.assertNotEqual(links.key(base.key), links.key(distinct.key))
        self.assertNotEqual(links.key(base.key), links.key(combo.key))

    def test_modafinil_and_armodafinil_keep_distinct_gsrs_moieties(self):
        registry = Registry([
            substance("R3UK8X3U3D", "MODAFINIL"),
            substance("V63XWA605I", "ARMODAFINIL"),
        ])
        modafinil = registry.composition(["MODAFINIL"])
        armodafinil = registry.composition(["ARMODAFINIL"])
        links = link_compositions([modafinil, armodafinil])
        self.assertEqual(links.key(modafinil.key), "U:R3UK8X3U3D")
        self.assertEqual(links.key(armodafinil.key), "U:V63XWA605I")

    def test_rejects_conflicting_complete_sets_through_unresolved_bridge(self):
        registry = Registry([
            substance("0000000001", "SHARED", "OTHER"),
            substance("0000000002", "SHARED", "OTHER"),
            substance("0000000003", "BETA"),
        ])
        one, two = "0000000001", "0000000002"
        rows = [registry.composition([name, "BETA"], hints) for name, hints in (
            ("SHARED", [one]), ("SHARED", []), ("OTHER", [one]), ("OTHER", [two]))]
        links = link_compositions(rows)
        self.assertEqual(links.canonical, {})
        conflict, = links.conflicts
        self.assertEqual(conflict["keys"], sorted({row.key for row in rows}))
        self.assertEqual(links, link_compositions(reversed(rows)))

    def test_partial_key_cannot_replace_an_identifier(self):
        registry = Registry([
            substance("0000000001", "SHARED"),
            substance("0000000002", "SHARED"),
            substance("0000000003", "BETA"),
            substance("0000000004", "BETA"),
        ])
        partial = registry.composition(["SHARED", "BETA"], ["0000000001"])
        complete = registry.composition(["SHARED", "BETA"], ["0000000002", "0000000003"])
        links = link_compositions([partial, complete])
        self.assertEqual(links.canonical, {})
        self.assertEqual(len(links.conflicts), 1)
