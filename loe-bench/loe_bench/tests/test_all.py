import json
import os
import tempfile
import unittest
from datetime import date

from loe_bench.baselines import AgeHazardTable, BaseRate, Logistic, exclusivity_rule_score
from loe_bench.common import add_months, ingredient_key, norm_ingredient, parse_yyyymmdd
from loe_bench.dataset import build_entities, build_samples, snapshot_features, time_split
from loe_bench.evidence_graph import build_assignment, decide, verdict_label
from loe_bench.kleene import T3
from loe_bench.metrics import aurc, auroc, brier, cluster_bootstrap_ci, ece, selective_error
from loe_bench.purplebook import biosimilar_entries, first_biosimilar_by_reference, parse_purplebook


def _w(d, name, recs):
    with open(os.path.join(d, name), "w") as f:
        for r in recs:
            f.write(json.dumps(r) + "\n")


def synth_raw(d):
    def nda(app, ing, d0, cls="TYPE 1"):
        return {"application_number": "NDA" + app, "sponsor_name": "S",
                "submissions": [{"submission_type": "ORIG", "submission_status": "AP", "submission_status_date": d0,
                                 "submission_class_code": cls}],
                "products": [{"active_ingredients": [{"name": ing}], "route": "ORAL"}]}

    def anda(app, ing, d0):
        return {"application_number": "ANDA" + app,
                "submissions": [{"submission_type": "ORIG", "submission_status": "AP", "submission_status_date": d0}],
                "products": [{"active_ingredients": [{"name": ing}], "route": "ORAL"}]}
    _w(d, "df_nda.jsonl", [nda("1", "ALPHAZOLE HYDROCHLORIDE", "20050101"), nda("2", "BETAMAB", "20100101"),
                           nda("3", "GAMMAPRIL", "20150101"), nda("4", "OLDMED", "19700101", cls="TYPE 7")])
    _w(d, "df_anda.jsonl", [anda("9", "ALPHAZOLE", "20100601"), anda("10", "BETAMAB", "20300101")])
    _w(d, "ob_nda.jsonl", [{"products": [{"active_ingredients": [{"name": "GAMMAPRIL"}], "marketing_status": "HUMAN PRESCRIPTION DRUG"}],
                            "patents": [{"expiration_date": "20310101"}], "exclusivity": [{"exclusivity_code": "NCE", "exclusivity_expiration_date": "20200101"}]}])


class TestCommon(unittest.TestCase):
    def test_dates(self):
        self.assertEqual(parse_yyyymmdd("20230428"), date(2023, 4, 28))
        self.assertIsNone(parse_yyyymmdd("2023"))
        self.assertIsNone(parse_yyyymmdd("20231340"))
        self.assertEqual(add_months(date(2024, 1, 31), 1), date(2024, 2, 29))

    def test_key(self):
        self.assertEqual(norm_ingredient("Apixaban"), "APIXABAN")
        self.assertEqual(norm_ingredient("ALPHAZOLE HYDROCHLORIDE"), "ALPHAZOLE")
        self.assertEqual(ingredient_key([{"active_ingredients": [{"name": "B"}, {"name": "A SODIUM"}]}]), "A|B")


class TestDataset(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        synth_raw(self.d)
        self.ents = build_entities(self.d)

    def test_entities(self):
        self.assertEqual(self.ents["ALPHAZOLE"].anda_first, date(2010, 6, 1))
        self.assertTrue(self.ents["ALPHAZOLE"].nme)
        self.assertFalse(self.ents["OLDMED"].nme)

    def test_labels_and_censoring(self):
        end = date(2020, 1, 1)
        rows = build_samples(self.ents, [date(2008, 1, 1), date(2012, 1, 1)], 36, end)
        by = {(r["key"], r["t"].year): r for r in rows}
        self.assertEqual(by[("ALPHAZOLE", 2008)]["y"], 1)     # ANDA 2010-06 within 36m of 2008-01
        self.assertNotIn(("ALPHAZOLE", 2012), by)             # already had ANDA at cutoff
        self.assertEqual(by[("BETAMAB", 2012)]["y"], 0)       # ANDA 2030 not within window, window before data end
        self.assertNotIn(("OLDMED", 2008), by)                # only_nme=True
        # censoring: window beyond data_end with y=0 is dropped
        rows2 = build_samples(self.ents, [date(2019, 1, 1)], 36, end)
        self.assertEqual([r for r in rows2 if r["key"] == "BETAMAB"], [])

    def test_no_future_feature_leak(self):
        from loe_bench.dataset import features_at
        e = self.ents["ALPHAZOLE"]
        f1 = features_at(e, date(2006, 1, 1))
        self.assertAlmostEqual(f1["age_years"], 1.0, delta=0.01)
        self.assertEqual(f1["n_nda_prior"], 1.0)

    def test_embargo(self):
        rows = build_samples(self.ents, [date(2008, 1, 1), date(2010, 1, 1), date(2012, 1, 1)], 36, date(2030, 1, 1))
        tr, te, dropped = time_split(rows, date(2010, 1, 1), date(2011, 1, 1))
        self.assertTrue(all(r["t_end"] <= date(2011, 1, 1) for r in tr))
        self.assertTrue(dropped > 0)

    def test_snapshot(self):
        s = snapshot_features(self.d, date(2026, 1, 1), self.ents)
        self.assertIn("GAMMAPRIL", s)
        self.assertEqual(s["GAMMAPRIL"]["patent_exp"], [date(2031, 1, 1)])
        self.assertEqual(exclusivity_rule_score(s["GAMMAPRIL"], date(2026, 1, 1), 24), 0)
        self.assertEqual(exclusivity_rule_score(s["GAMMAPRIL"], date(2026, 1, 1), 72), 1)


class TestMetrics(unittest.TestCase):
    def test_known(self):
        self.assertAlmostEqual(brier([1.0, 0.0], [1, 0]), 0.0)
        self.assertAlmostEqual(brier([0.5, 0.5], [1, 0]), 0.25)
        self.assertAlmostEqual(auroc([0.1, 0.2, 0.8, 0.9], [0, 0, 1, 1]), 1.0)
        self.assertAlmostEqual(auroc([0.5, 0.5, 0.5, 0.5], [0, 1, 0, 1]), 0.5)
        self.assertAlmostEqual(ece([0.8] * 10, [1] * 8 + [0] * 2), 0.0)

    def test_selective(self):
        p = [0.05, 0.5, 0.95, 0.5]
        y = [0, 1, 1, 0]
        r = selective_error(p, y, 0.25, 0.75)
        self.assertAlmostEqual(r["coverage"], 0.5)
        self.assertAlmostEqual(r["error"], 0.0)

    def test_aurc_perfect_ranking_beats_random(self):
        y = [0, 0, 0, 1, 1, 1] * 5
        good = [0.05, 0.1, 0.1, 0.9, 0.9, 0.95] * 5
        bad = [0.9, 0.1, 0.95, 0.1, 0.9, 0.05] * 5
        self.assertLess(aurc(good, y), aurc(bad, y))

    def test_cluster_bootstrap_runs(self):
        p = [0.2, 0.8, 0.3, 0.7] * 10
        y = [0, 1, 0, 1] * 10
        g = [i // 4 for i in range(40)]
        lo, hi = cluster_bootstrap_ci(brier, p, y, g, n_boot=30)
        self.assertLessEqual(lo, hi)


class TestBaselines(unittest.TestCase):
    def _rows(self):
        rows = []
        for i in range(400):
            age = (i % 20) + 0.5
            y = int(age > 12)
            rows.append({"key": str(i), "y": y, "x": {"age_years": age, "age_sq": age * age / 10, "nme": 1.0, "orphan": 0.0,
                                                      "priority": 0.0, "oral": 1.0, "injectable": 0.0, "n_nda_prior": 1.0}})
        return rows

    def test_models_learn(self):
        rows = self._rows()
        y = [r["y"] for r in rows]
        for m in (AgeHazardTable(), Logistic(epochs=200)):
            p = m.fit(rows).predict(rows)
            self.assertGreater(auroc(p, y), 0.9, m.name)
        self.assertAlmostEqual(BaseRate().fit(rows).predict(rows)[0], sum(y) / len(y))


class TestEvidenceGraph(unittest.TestCase):
    t = date(2026, 1, 1)

    def test_three_verdicts(self):
        open_ = {"excl_exp": [date(2025, 1, 1)], "patent_exp": [date(2026, 6, 1)]}
        contested = {"excl_exp": [date(2025, 1, 1)], "patent_exp": [date(2031, 1, 1)]}
        blocked = {"excl_exp": [date(2029, 1, 1)], "patent_exp": [date(2026, 6, 1)]}
        self.assertEqual(verdict_label(build_assignment(open_, self.t, 24)), "OPEN")
        self.assertEqual(verdict_label(build_assignment(contested, self.t, 24)), "CONTESTED")
        self.assertEqual(verdict_label(build_assignment(blocked, self.t, 24)), "BLOCKED")

    def test_blocked_is_final_and_contested_abstains(self):
        blocked = {"excl_exp": [date(2029, 1, 1)], "patent_exp": []}
        self.assertEqual(decide(blocked, self.t, 24, 0.99)["action"], "PREDICT_NO_ENTRY")
        contested = {"excl_exp": [], "patent_exp": [date(2031, 1, 1)]}
        d = decide(contested, self.t, 24, 0.5)
        self.assertEqual(d["action"], "ABSTAIN_REFER_TO_EVALUATOR")
        self.assertEqual(d["next_evidence"]["leaf"], "L_challenge")
        self.assertGreater(d["next_evidence"]["voi_bits"], 0)

    def test_challenge_evidence_resolves(self):
        s = {"excl_exp": [], "patent_exp": [date(2031, 1, 1)]}
        a = build_assignment(s, self.t, 24, challenge_evidence=T3.TRUE)   # e.g. documented settlement licence date
        self.assertEqual(verdict_label(a), "OPEN")


PB = """Purple Book test,,,,,,,,,,,,,,,,,,,,,,,,
N/R/U,Applicant,BLA Number,Proprietary Name,Proper Name,BLA Type,Strength,Dosage Form,Route of Administration,Product Presentation,Marketing Status,Licensure,Approval Date,Ref. Product Proper Name,Ref. Product Proprietary Name,Supplement Number,Submission Type,License Number,Product Number,Center,Date of First Licensure,Exclusivity Expiration Date,First Interchangeable Exclusivity Exp. Date,Ref. Product Exclusivity Exp. Date,Orphan Exclusivity Exp. Date
U,Sandoz Inc.,761071,Hyrimoz,adalimumab-adaz,351(k) Biosimilar,40MG,Injection ,Subcutaneous,Pre-Filled Syringe,Rx,Licensed,"October 30, 2018",adalimumab,Humira,,Original,2003,001,CDER,,,,,
,Other,761072,"Brand, with comma",adalimumab-xxxx,351(k) Interchangeable,40MG,Injection,Subcutaneous,PFS,Rx,Licensed,"July 01, 2019",adalimumab,Humira,,Original,2004,001,CDER,,,,,
,AbbVie,125057,Humira,adalimumab,351(a),40MG,Injection,Subcutaneous,PFS,Rx,Licensed,"December 31, 2002", ,,0,Original,1,001,CDER,,,,,
"""


class TestPurpleBook(unittest.TestCase):
    def test_parse(self):
        rows = parse_purplebook(PB)
        self.assertEqual(len(rows), 3)
        b = biosimilar_entries(rows)
        self.assertEqual(len(b), 2)
        f = first_biosimilar_by_reference(b)
        self.assertEqual(f["adalimumab"]["first_approval"], date(2018, 10, 30))
        self.assertEqual(f["adalimumab"]["n_distinct_bla"], 2)


if __name__ == "__main__":
    unittest.main()
