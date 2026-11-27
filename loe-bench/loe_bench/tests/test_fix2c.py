"""FIX2c historical alias, source date and product identity regression tests."""
from datetime import date
from unittest.mock import patch

from loe_bench import dataset, ob_linkage
from loe_bench.ob_history import Edition, EditionSource
from loe_bench.t2_features import AsOfBuilder
from loe_bench.tests.test_fix1 import RawFixture, application, original, product
from loe_bench.tests.test_fix2b import audit_registry
from loe_bench.tests.test_t2 import ED, T, history, patent


def historical_product(application_no, ingredient, *, number="001", kind="N", approved=None):
    return dict(appl_no=application_no, product_no=number, appl_type=kind, ingredient=ingredient,
                ingredient_key=ingredient, approval_date=approved)


class HistoricalLinkageTests(RawFixture):
    def setUp(self):
        super().setUp()
        approval = original("20000101")
        annotation = {"substance_name": ["NICOTINE"], "unii": ["6M3C89ZY6R"]}
        self.ndas = [
            dict(application([approval], product("NICOTINE POLACRILEX", product_number="001")),
                 application_number="NDA000001", openfda=annotation),
            dict(application([approval], product("NICOTINE", product_number="001")),
                 application_number="NDA000002", openfda=annotation),
        ]
        self.andas = [dict(application([], product("NICOTINE")), application_number="ANDA000004")]
        self.registry = audit_registry()
        with patch.object(dataset, "registry_for", return_value=self.registry):
            self.entities = self.build(self.ndas, self.andas)
        with patch.object(ob_linkage, "registry_for", return_value=self.registry):
            self.linker = ob_linkage.HistoricalMoietyLinker(self.raw, self.entities)
        self.entity, = self.entities.values()

    def test_merged_legacy_keys_receive_patents_from_both_aliases(self):
        self.assertEqual(set(dataset.build_entities(self.raw, key_mode="legacy")),
                         {"NICOTINE", "NICOTINE POLACRILEX"})
        self.assertEqual(set(self.entity.key_aliases), {"NICOTINE", "NICOTINE POLACRILEX"})
        products = [historical_product("000001", "NICOTINE POLACRILEX"),
                    historical_product("000002", "NICOTINE")]
        expiries = [date(2014, 2, 1), date(2015, 1, 1)]
        patents = [patent("001", "A", expiries[0]),
                   dict(patent("001", "B", expiries[1]), appl_no="000002")]

        def refuse_load():
            self.fail("an unavailable edition was loaded")

        later = [EditionSource(date(2013, 12, 31), refuse_load,
                               availability=({"date": "2014-01-02"},)),
                 EditionSource(date(2014, 1, 2), refuse_load,
                               availability=({"date": T.isoformat()},))]
        archive = history(products, patents, [], later)
        builder = AsOfBuilder(archive, linker=self.linker)
        row = builder.build(self.entity.key, T, 24, {})
        self.assertEqual(row.edition_status, "FRESH")
        self.assertEqual(row.snapshot["patent_exp"], expiries)
        self.assertEqual(row.x["listed_patent_count"], 2)
        for alias in self.entity.key_aliases:
            self.assertEqual(builder.build(alias, T, 24, {}), row)
            legacy = AsOfBuilder(archive, key_mode="legacy").build(alias, T, 24, {})
            self.assertEqual(legacy.x["listed_patent_count"], 1)

    def test_exact_product_recovery_and_untyped_denominators(self):
        products = [historical_product("000001", "", kind=""),
                    historical_product("000002", "", number="002"),
                    historical_product("000003", "NICOTINE", kind=""),
                    historical_product("000004", "NICOTINE", kind=""),
                    historical_product("000005", "NICOTINE", approved=date(2013, 12, 1))]
        builder = AsOfBuilder(history(products, [patent("001", "A", date(2015, 1, 1))], []),
                              linker=self.linker)
        stats = builder.edition_linkage(Edition(ED, products, [], []))
        self.assertEqual(stats["total_nda"], 3)
        self.assertEqual(stats["matched"], 1)
        self.assertEqual(stats["application_product"], 1)
        self.assertEqual(stats["non_nda"], 1)
        self.assertEqual(stats["unknown_application_type"], 1)
        self.assertEqual(stats["link_rate"], 1 / 3)
        self.assertEqual(stats["unmatched_examples"]["no_entity_match"]["products_data_row"], 2)
        self.assertEqual(stats["unmatched_examples"]["approval_after_edition"]["products_data_row"], 5)
        self.assertEqual(builder.build(self.entity.key, T, 24, {}).x["listed_patent_count"], 1)
