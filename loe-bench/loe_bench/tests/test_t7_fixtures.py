"""Small, hand-checkable cases for the T7 flags and replay."""
from datetime import date
import unittest

from loe_bench.common import ingredient_key
from loe_bench.dataset import Entity
from scripts import t7_audit as audit


def application(number, *products, substances=(), uniis=(), approved=date(2000, 1, 1)):
    key = ingredient_key([
        {"active_ingredients": [{"name": name} for name in names]}
        for names in products
    ])
    source = audit.FILES[number.startswith("ANDA")]
    return audit.Application(
        source, number, approved, key,
        tuple((str(i), names, "ORAL", "TABLET") for i, names in enumerate(products, 1)),
        substances, uniis, (),
    )


def flags(app, *others):
    grouped = {}
    for item in (app, *others):
        grouped.setdefault(item.key, []).append(item)
    return audit.flag_key(app.key, grouped[app.key], audit.reverse_indexes(grouped))


class T7Fixtures(unittest.TestCase):
    def test_standalone_electrolytes_erased_and_distinct_formulas_merge(self):
        first = application("NDA001", ("PEG", "SODIUM CHLORIDE"))
        second = application("NDA002", ("PEG", "POTASSIUM CHLORIDE"))
        self.assertEqual(first.key, second.key)
        self.assertEqual(flags(first, second), (["POSSIBLE_FALSE_MERGE", "COMBINATION"], []))

    def test_application_union_hides_single_and_combination_products(self):
        app = application("NDA001", ("TRICHLORMETHIAZIDE",),
                          ("RESERPINE", "TRICHLORMETHIAZIDE"))
        self.assertEqual(flags(app), (["POSSIBLE_FALSE_MERGE", "COMBINATION"], []))

    def test_annotation_can_surface_a_missing_drug_component(self):
        alone = application("NDA001", ("LIDOCAINE HYDROCHLORIDE",),
                            substances=("LIDOCAINE HYDROCHLORIDE",))
        mixed = application("NDA002", ("LIDOCAINE HYDROCHLORIDE",),
                            substances=("LIDOCAINE HYDROCHLORIDE", "DEXTROSE"))
        self.assertEqual(flags(alone, mixed), (["POSSIBLE_FALSE_MERGE"], []))

    def test_split_indexes_include_alias_anda_keys_and_ignore_case(self):
        base = application("NDA001", ("DRUG",), substances=("Drug",), uniis=("SAME",))
        salt = application("ANDA002", ("DRUG DIMALEATE",), uniis=("SAME",))
        alias = application("ANDA003", ("DRUG ALIAS",), substances=("drug",))
        self.assertEqual(flags(base, salt, alias),
                         (["POSSIBLE_FALSE_SPLIT"], ["DRUG ALIAS", "DRUG DIMALEATE"]))

    def test_rendered_combination_can_split_with_redundant_raw_string(self):
        pair = application("NDA001", ("HYDROCHLOROTHIAZIDE", "IRBESARTAN"), uniis=("A", "B"))
        duplicate = application("ANDA002", ("IRBESARTAN: HYDROCHLOROTHIAZIDE",),
                                ("HYDROCHLOROTHIAZIDE", "IRBESARTAN"), uniis=("A", "B"))
        self.assertIn("POSSIBLE_FALSE_SPLIT", flags(pair, duplicate)[0])
        mapping = {("", "IRBESARTAN: HYDROCHLOROTHIAZIDE"): pair.key}
        self.assertEqual(audit.amended_key(duplicate, mapping), pair.key)

    def test_salt_and_hydrate_names_do_not_flag_merge(self):
        a = application("NDA001", ("DRUG",), substances=("DRUG",), uniis=("BASE",))
        b = application("NDA002", ("DRUG HYDROCHLORIDE",),
                        substances=("DRUG HYDROCHLORIDE MONOHYDRATE",), uniis=("SALT",))
        self.assertEqual(flags(a, b), ([], []))

    def test_development_cutoff_and_seeded_sampling(self):
        grouped = {}
        entities = {}
        for i in range(110):
            approved = date(2014, 1, 2) if i == 109 else audit.CUTOFF
            app = application(f"NDA{i:03d}", (f"DRUG {i}",), approved=approved)
            grouped[app.key] = [app]
            entities[app.key] = Entity(app.key, nda_first=approved)
        sample, sizes, _ = audit.sample_keys(entities, grouped)
        reverse = dict(reversed(list(entities.items())))
        self.assertEqual(sample, audit.sample_keys(reverse, grouped)[0])
        self.assertEqual(len(sample), 100)
        self.assertEqual(set(sample.values()), {"RANDOM"})
        self.assertEqual(sizes["RANDOM"], 109)
        self.assertNotIn("DRUG 109", sample)

    def test_replay_counts_dates_per_sampled_key(self):
        early = date(1999, 1, 1)
        later = date(2000, 1, 1)
        nda = application("NDA001", ("DRUG",), approved=later)
        anda = application("ANDA002", ("DRUG DIMALEATE",), approved=early)
        rows = [{"key": "DRUG", "verdict": "FALSE_SPLIT", "date_targets": ["DRUG"]}]
        edits = [{"raw_ingredient": "DRUG DIMALEATE", "corrected_key": "DRUG",
                  "reason": "Verified salt", "locator": "ANDA002 active_ingredients"}]
        result = audit.date_impacts(rows, {"DRUG": Entity("DRUG", nda_first=later)},
                                    {nda.key: [nda], anda.key: [anda]}, edits)
        self.assertEqual((result["first_nda_changed"], result["first_anda_changed"],
                          result["either_changed"]), (0, 1, 1))

    def test_scoped_ingredient_override_preserves_unrelated_single_product(self):
        alone = application("NDA001", ("LIDOCAINE HYDROCHLORIDE",))
        mixed = application("NDA002", ("LIDOCAINE HYDROCHLORIDE",))
        mapping = {("NDA002", "LIDOCAINE HYDROCHLORIDE"): "DEXTROSE|LIDOCAINE"}
        self.assertEqual(audit.amended_key(alone, mapping), "LIDOCAINE")
        self.assertEqual(audit.amended_key(mixed, mapping), "DEXTROSE|LIDOCAINE")


if __name__ == "__main__":
    unittest.main()
