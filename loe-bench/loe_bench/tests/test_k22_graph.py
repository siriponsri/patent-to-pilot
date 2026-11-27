import unittest
from datetime import date

from loe_bench import evidence_graph as graph
from loe_bench.challenge import ChallengeEvidence, Witness
from loe_bench.kleene import T3
from loe_bench.ob_history import EditionSource, parse_patents
from loe_bench.regulatory_graph import _patent_scope
from loe_bench.t2_features import AsOfBuilder

from .test_t2 import T, exclusivity, history, patent, product


APPROVED = date(2010, 1, 1)
APPL = "000001"


def witness(when, source="FDA_PIV", corroboration=None):
    return Witness(source, "fixture", when, "2014-01-01", "a" * 64, "row 1", "", corroboration)


def snapshot(*, exclusions=(), patents=(), witnesses=(), approval=APPROVED):
    return {"regulatory": {"patents": patents, "exclusivities": exclusions, "original_approvals": {
        APPL: product("001", approved=approval) if approval else None}}, "challenge_witnesses": witnesses}


def assignment(evidence, cutoff=T, horizon=0, observation=T3.UNKNOWN):
    return graph.build_assignment(evidence, cutoff, horizon, observation, graph_version="v2")


class RegulatoryGraphTests(unittest.TestCase):
    def test_nce_one_filing_boundaries_and_no_universal_approval_floor(self):
        for code in ("NCE", "NCE*"):
            with self.subTest(code=code):
                nce = [exclusivity("001", code, date(2015, 1, 1))]
                bare = snapshot(exclusions=nce)
                self.assertEqual(assignment(bare, date(2013, 12, 31))["L_excl"], T3.FALSE)
                self.assertEqual(assignment(bare)["L_excl"], T3.UNKNOWN)
                premature = snapshot(exclusions=nce, witnesses=[witness(date(2013, 12, 31))])
                self.assertEqual(assignment(premature)["L_excl"], T3.UNKNOWN)
                qualified = snapshot(exclusions=nce, witnesses=[witness(T)])
                self.assertEqual(assignment(qualified)["L_excl"], T3.TRUE)
                self.assertEqual(assignment(qualified)["L_challenge"], T3.UNKNOWN)
                self.assertEqual(graph.verdict_label(assignment(qualified)), "OPEN")
                self.assertEqual(assignment(bare, horizon=12)["L_excl"], T3.TRUE)

    def test_scoped_protections_contribute_contested_through_published_date(self):
        for code in ("ODE", "ODE*", "I-123", "D-1", "NDF"):
            with self.subTest(code=code):
                scoped = snapshot(exclusions=[exclusivity("001", code, date(2015, 1, 1))])
                self.assertEqual(graph.verdict_label(assignment(scoped)), "CONTESTED")
                self.assertEqual(graph.verdict_label(assignment(scoped, horizon=12)), "OPEN")

    def test_waivers_and_later_applicant_codes_do_not_extend_bar(self):
        future = [exclusivity("001", code, date(2020, 1, 1)) for code in ("W", "PC", "CGT")]
        self.assertEqual(assignment(snapshot(exclusions=future))["L_excl"], T3.TRUE)
        future.append(exclusivity("001", "NCE", date(2015, 1, 1)))
        self.assertEqual(assignment(snapshot(exclusions=future), date(2013, 1, 1))["L_excl"], T3.FALSE)

    def test_gain_and_ped_use_published_attachment_and_adjusted_nce_one(self):
        codes = [("NCE", date(2015, 1, 1)), ("GAIN", date(2020, 1, 1)), ("PED", date(2020, 7, 1))]
        attached = [exclusivity("001", code, expiry) for code, expiry in codes]
        self.assertEqual(assignment(snapshot(exclusions=attached), date(2019, 6, 30))["L_excl"], T3.FALSE)
        timely = snapshot(exclusions=attached, witnesses=[witness(date(2019, 7, 1))])
        self.assertEqual(assignment(timely, date(2019, 7, 1))["L_excl"], T3.TRUE)
        self.assertEqual(assignment(snapshot(exclusions=attached), date(2020, 7, 1))["L_excl"], T3.TRUE)
        scoped = [exclusivity("001", "ODE", date(2017, 1, 1)), exclusivity("001", "GAIN", date(2022, 1, 1))]
        for rows in (scoped, scoped[1:]):
            self.assertEqual(assignment(snapshot(exclusions=rows), date(2020, 1, 1))["L_excl"], T3.UNKNOWN)
        other_product = [attached[0], dict(attached[1], product_no="002")]
        self.assertEqual(assignment(snapshot(exclusions=other_product), date(2018, 1, 1))["L_excl"], T3.UNKNOWN)

    def test_patent_scope_carveout_delisting_and_ped_suffix(self):
        expiry = date(2020, 1, 1)
        use_only = dict(patent("001", "1234", expiry), use_code="U-22", drug_substance=False, drug_product=False)
        self.assertEqual(_patent_scope(use_only), "METHOD_OF_USE")
        self.assertEqual(_patent_scope(dict(use_only, has_scope_flags=False)), "UNKNOWN")
        self.assertEqual(graph.verdict_label(assignment(snapshot(patents=[use_only]))), "CONTESTED")
        for flag in ("drug_substance", "drug_product"):
            with self.subTest(flag=flag):
                broad = dict(use_only, **{flag: True})
                self.assertEqual(assignment(snapshot(patents=[broad]))["L_pat"], T3.FALSE)
                self.assertEqual(graph.verdict_label(assignment(snapshot(patents=[broad]), observation=T3.FALSE)), "BLOCKED")
                pediatric = patent("001", "1234*PED", date(2020, 7, 1))
                self.assertEqual(assignment(snapshot(patents=[broad, pediatric]), expiry)["L_pat"], T3.FALSE)
                self.assertEqual(assignment(snapshot(patents=[broad, pediatric]), date(2020, 7, 1))["L_pat"], T3.TRUE)
                excluded = snapshot(patents=[dict(broad, delist=True), pediatric])
                self.assertEqual(assignment(excluded)["L_pat"], T3.TRUE)

    def test_legacy_patent_row_without_scope_columns_is_unknown(self):
        fields = "Appl_No~Product_No~Patent_No~Patent_Expire_Date_Text~Patent_Use_Code\n"
        old, = parse_patents(fields + "1~001~1234~Jan 01, 2025~U-123\n")
        self.assertFalse(old["has_scope_flags"])
        self.assertEqual(_patent_scope(old), "UNKNOWN")
        self.assertEqual(assignment(snapshot(patents=[old]))["L_pat"], T3.UNKNOWN)

    def test_conditional_stay_uses_earliest_corroborated_court_date(self):
        later = witness(date(2013, 10, 1), "RAI_COURT", {"document": "fixture"})
        earlier = witness(date(2013, 6, 1), "RAI_OB_PATENT", {"case_type": "ANDA_CORROBORATED"})
        broad = dict(patent("001", "1234", date(2020, 1, 1)), drug_substance=True)
        both = snapshot(patents=[broad], witnesses=[later, earlier, witness(date(2013, 3, 1))])
        self.assertEqual(assignment(both, horizon=22)["L_challenge"], T3.FALSE)
        self.assertEqual(graph.verdict_label(assignment(both, horizon=23)), "OPEN")
        unspecific = witness(earlier.date, "RAI_OB_PATENT", {"case_type": "UNSPECIFIED"})
        self.assertEqual(assignment(snapshot(patents=[broad], witnesses=[unspecific]), horizon=24)["L_challenge"], T3.UNKNOWN)
        self.assertEqual(assignment(snapshot(witnesses=[witness(earlier.date)]), horizon=24)["L_challenge"], T3.UNKNOWN)

    def test_stay_during_nce_one_can_extend_to_seven_and_half_years(self):
        nce = exclusivity("001", "NCE", date(2015, 1, 1))
        court = witness(T, "RAI_COURT", {"document": "fixture"})
        evidence = snapshot(exclusions=[nce], witnesses=[witness(T), court])
        self.assertEqual(assignment(evidence, horizon=30)["L_challenge"], T3.FALSE)
        self.assertEqual(assignment(evidence, horizon=42)["L_challenge"], T3.TRUE)

    def test_missing_data_and_empty_fresh_inventory_have_distinct_meanings(self):
        self.assertEqual(set(assignment({}).values()), {T3.UNKNOWN})
        self.assertEqual(graph.verdict_label(assignment(snapshot())), "OPEN")
        nce = exclusivity("001", "NCE", date(2015, 1, 1))
        self.assertEqual(assignment(snapshot(exclusions=[nce], approval=None))["L_excl"], T3.UNKNOWN)
        unknown = dict(patent("001", "1234", None), drug_substance=True)
        self.assertEqual(assignment(snapshot(patents=[unknown]))["L_pat"], T3.UNKNOWN)

    def test_builder_keeps_raw_features_and_ignores_future_evidence(self):
        products = [product("001", approved=APPROVED)]
        patents = [dict(patent("001", "1234", date(2020, 1, 1)), drug_product=True)]
        exclusions = [exclusivity("001", "ODE", date(2017, 1, 1))]
        base = history(products, patents, exclusions)
        tomorrow = date(2014, 1, 2)

        def unavailable():
            self.fail("future Orange Book edition loaded")

        extended = history(products + [product("002", approved=tomorrow)],
                           patents + [patent("001", "4567", date(2028, 1, 1), tomorrow)],
                           exclusions + [exclusivity("002", "NCE", date(2024, 1, 1))],
                           [EditionSource(tomorrow, unavailable, availability=({"date": T.isoformat()},))])

        class Challenge:
            def lookup(self, key, cutoff):
                return ChallengeEvidence(T3.UNKNOWN, ())

        v1 = AsOfBuilder(base, challenge=Challenge()).build("DRUG", T, 12, {})
        v2 = AsOfBuilder(base, challenge=Challenge(), graph_version="v2").build("DRUG", T, 12, {})
        self.assertEqual(v1.x, v2.x)
        self.assertEqual(v1.verdict, "BLOCKED")
        self.assertEqual(v2.verdict, "CONTESTED")
        self.assertEqual(v2, AsOfBuilder(extended, challenge=Challenge(), graph_version="v2").build("DRUG", T, 12, {}))
        self.assertEqual(assignment(v2.snapshot, horizon=12), assignment(dict(v2.snapshot, challenge_witnesses=[
            witness(tomorrow, "RAI_COURT", {"document": "fixture"}), witness(tomorrow)]), horizon=12))
        self.assertEqual(graph.decide(v2.snapshot, T, 12, 0.5, graph_version="v2")["verdict"], "CONTESTED")
