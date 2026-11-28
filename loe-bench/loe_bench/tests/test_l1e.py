"""Hand-checkable C2 fixtures for evidence parity and the development gate."""
from dataclasses import replace
from datetime import date
from hashlib import sha256
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from scripts import l1dev_protocol
from loe_bench import devx, l1e_prompt, llm_arm
from loe_bench.dataset import Entity, features_at
from loe_bench.t2_features import AsOfBuilder
from loe_bench.tests import test_e7_challenge as e7, test_t2

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
with patch.object(sys, "path", [str(SCRIPTS), *sys.path]):
    from l1e_protocol import jsonl, native_risks, read_outputs


class EvidenceTests(TestCase):
    def evidence_fixture(self, challenge):
        cutoff = test_t2.T
        product = dict(test_t2.product("001"), approval_date_text="2003-01-01",
                       form_route="TABLET;ORAL", strength="10 MG")
        partial = dict(product, product_no="002", strength="UNKNOWN")
        patent = test_t2.patent("001", "A", date(2015, 1, 1), date(2012, 1, 1))
        future_submission = test_t2.patent("001", "B", date(2019, 1, 1), date(2014, 6, 1))
        exclusivities = [test_t2.exclusivity("001", "NCE", date(2015, 1, 1)),
                         test_t2.exclusivity("001", "I-1", date(2013, 1, 1))]
        archive = test_t2.history([product, partial], [patent, future_submission], exclusivities)
        entity = Entity("DRUG", nda_first=date(2003, 1, 1), nda_dates=[date(2003, 1, 1), date(2015, 1, 1)])
        row = {"asof": AsOfBuilder(archive, challenge=challenge).build(
            "DRUG", cutoff, 12, features_at(entity, cutoff)),
            "breadth": devx.presentation_breadth([product, partial], test_t2.ED), "y": 1}
        return row

    def actual_challenge(self, name, when):
        fixture = e7.ChallengeTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.edition("2013-12-25", "20131226000000", name=name, when=when)
        return fixture.history().lookup(e7.KEY, test_t2.T)

    def check_crosswalk(self, challenge, dates, present, missing):
        class History:
            def lookup(self, key, cutoff):
                return challenge

        source = self.evidence_fixture(History())
        forecast = {"entity": "Example", "t0": "2014-01-01", "horizon_months": 12,
                    "as_of_evidence": l1e_prompt.from_m3(source)}
        system, user = l1e_prompt.build_prompt(forecast)
        self.assertEqual(system, llm_arm.SYSTEM)
        serialized = json.loads(user.split("Evidence available as of t0 (JSON):\n")[1].splitlines()[0])
        m3, = devx.model_inputs([source], [0.75], "M3", ("K07",))
        self.assertEqual({k: v for k, v in m3["x"].items() if k not in l1e_prompt.EXCLUDED},
                         {k: serialized[k] for k in l1e_prompt.CROSSWALK})
        self.assertFalse(set(serialized) & (set(l1e_prompt.EXCLUDED) | {"y", "action"}))
        self.assertEqual(serialized["n_nda_prior"], 1)
        self.assertEqual(serialized["listed_patent_count"], 1)
        self.assertEqual(serialized["other_exclusivity_remaining_years"], 0)
        self.assertEqual(serialized["other_exclusivity_remaining_years_missing"], 0)
        self.assertEqual(serialized["latest_patent_expiry"], "2015-01-01")
        self.assertEqual(serialized["latest_exclusivity_expiry"], "2015-01-01")
        self.assertEqual((serialized["strength_count"], serialized["strength_missing"]), (1, 1))
        self.assertEqual((serialized["form_route_count"], serialized["form_route_missing"]), (1, 0))
        self.assertEqual(serialized["challenge_witnesses"], dates)
        self.assertEqual((serialized["challenge_present"], serialized["challenge_missing"]), (present, missing))
        return forecast

    def test_dated_challenge_matches_m3_and_future_witness_is_rejected(self):
        forecast = self.check_crosswalk(self.actual_challenge("Example", "12/1/2013"),
                                        [{"date": "2013-12-01", "source": "FDA_PIV"}], 1, 0)
        forecast["as_of_evidence"]["challenge_witnesses"][0]["date"] = "2014-01-02"
        with self.assertRaisesRegex(ValueError, "as-of"):
            l1e_prompt.build_prompt(forecast)

    def test_undated_challenge_differs_from_fresh_verified_nonobservation(self):
        self.check_crosswalk(self.actual_challenge("Example", "pre-MMA"), [], 0, 1)
        self.check_crosswalk(self.actual_challenge("Second", "12/1/2013"), [], 0, 0)

    def test_frozen_patent_relinkage_source_is_admitted(self):
        dated = self.actual_challenge("Example", "12/1/2013")
        linked = replace(dated, witnesses=(replace(dated.witnesses[0], source="RAI_OB_PATENT"),))
        self.check_crosswalk(linked, [{"date": "2013-12-01", "source": "RAI_OB_PATENT"}], 1, 0)


class GateTests(TestCase):
    def test_fixed_gate_full_roster_and_native_scores(self):
        valid = '{"p_entry":0.25,"action":"ABSTAIN_REFER_TO_EVALUATOR","missing_evidence":[]}'
        inputs = [dict(entity=f"Fixture {i}", t0="2012-01-01", horizon_months=12)
                  for i in range(l1dev_protocol.GATE_ROWS + 1)]
        with TemporaryDirectory() as folder:
            path = Path(folder) / "outputs.jsonl"
            for first_valid, total, status, gate_status, full in (
                (179, 200, "STOP_VALIDITY_GATE", "FAIL", False),
                (180, 200, "STOP_TIME_CAP", "PASS", False),
                (180, 201, "COMPLETE", "PASS", True),
            ):
                with self.subTest(first_valid=first_valid, returned=total):
                    rows = [dict(row, raw_text=text, **llm_arm.parse_response(text))
                            for i, row in enumerate(inputs[:total])
                            for text in [valid if i < first_valid else "invalid"]]
                    data = jsonl(rows)
                    path.write_bytes(data)
                    summary = dict(input_sha256="fixture", output_sha256=sha256(data).hexdigest(), n_rows=total,
                                   n_planned=len(inputs), first_200_valid=first_valid, valid_json=first_valid,
                                   abstains=total, status=status)
                    parsed, gate = read_outputs(path, summary, inputs, "fixture")
                    self.assertEqual((gate["status"], gate["full_roster"]), (gate_status, full))
                    self.assertEqual(native_risks(parsed), [0.25] * first_valid + [-1.0] * (total - first_valid))

    def test_four_arm_queue_keeps_fractional_capture_and_grouped_ap(self):
        with patch.object(sys, "path", [str(SCRIPTS), *sys.path]), patch.dict("os.environ"):
            from l1dev_local import score_panel

        cutoff = date(2014, 1, 1)
        rows = [{"t": cutoff, "key": str(i), "y": int(i == 0)} for i in range(5)]
        arms = ("L1e", "L1", "M3", "B1")
        scores = {"L1e": [0.25, 0.25, -1, -1, -1], "L1": [0, 1, 0, 0, 0],
                  "M3": [1, 0, 0, 0, 0], "B1": [1, 1, 1, 1, 1]}
        result = score_panel(rows, scores, [cutoff], arms=arms)
        self.assertEqual(result["queue_slots"], 1)
        self.assertEqual(result["L1e_cutoffs"][0]["boundary_tie_rows"], 2)
        self.assertEqual([result["levels"]["L1e"][name]["estimate"]
                          for name in ("recall", "precision", "average_precision")], [0.5] * 3)
        self.assertEqual(result["contrasts"]["L1e-M3"]["recall"]["estimate"], -0.5)
