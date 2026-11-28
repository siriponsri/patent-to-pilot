import json
import unittest
from datetime import date
from pathlib import Path

from loe_bench import c9
from loe_bench.llm_arm import parse_response


TRACK_A_END = date(2028, 11, 27)
ELIGIBLE_CUTOFF = date(2014, 1, 1)


def answer(probability, action="ABSTAIN_REFER_TO_EVALUATOR"):
    return json.dumps({"p_entry": probability, "action": action, "missing_evidence": []})


class C9Test(unittest.TestCase):
    def test_calendar_and_label_maturity(self):
        end = date(2016, 1, 1)
        event = date(2015, 1, 1)
        self.assertIsNone(c9.resolve_training_label(ELIGIBLE_CUTOFF, event, None))
        self.assertIsNone(c9.resolve_training_label(ELIGIBLE_CUTOFF, event, event))
        self.assertIsNone(c9.resolve_training_label(ELIGIBLE_CUTOFF, None, event))
        self.assertEqual(c9.resolve_training_label(ELIGIBLE_CUTOFF, end, end), 1)
        self.assertEqual(c9.resolve_training_label(ELIGIBLE_CUTOFF, date(2016, 1, 2), end), 0)
        self.assertEqual(c9.resolve_training_label(ELIGIBLE_CUTOFF, None, end), 0)
        with self.assertRaisesRegex(ValueError, "prior final ANDA"):
            c9.resolve_training_label(ELIGIBLE_CUTOFF, ELIGIBLE_CUTOFF, end)
        for cutoff in (date(2015, 1, 1), date(2017, 1, 1)):
            with self.assertRaisesRegex(ValueError, "development calendar"):
                c9.resolve_training_label(cutoff, None, c9.S0)

    def test_training_order_is_fixed_and_capped(self):
        small = [(f"synthetic-{i}", ELIGIBLE_CUTOFF) for i in range(8)]
        order = c9.training_order(small)
        self.assertEqual(order, c9.training_order(reversed(small)))
        self.assertEqual(set(order[:8]), set(small))
        self.assertEqual(order[:8], order[8:16])
        self.assertEqual(len(order), 256)
        large = [(f"synthetic-{i}", ELIGIBLE_CUTOFF) for i in range(300)]
        self.assertEqual(len(set(c9.training_order(large))), 256)
        for invalid in (small[:7], small + [small[0]]):
            with self.assertRaisesRegex(ValueError, "unique training rows"):
                c9.training_order(invalid)

    def test_reward_and_supervision(self):
        for y, action in enumerate(("PREDICT_NO_ENTRY", "PREDICT_ENTRY")):
            target = parse_response(c9.sft_target(y))
            self.assertTrue(target["valid"])
            self.assertEqual((target["p_entry"], target["action"]), (y, action))
            self.assertEqual(c9.grpo_reward(answer(y), y), 0)
            self.assertEqual(c9.grpo_reward(answer(1 - y), y), -1)
            self.assertLess(c9.grpo_reward(answer(True), y), -1)
        self.assertAlmostEqual(c9.grpo_reward(answer(0.8), 1), -0.04)
        self.assertEqual(c9.grpo_reward('```json\n{}\n```', 0), -1.25)
        for label in (None, True, 2):
            with self.assertRaises(ValueError):
                c9.sft_target(label)
            with self.assertRaises(ValueError):
                c9.grpo_reward(answer(0.5), label)

    def test_hand_checked_pair_with_tie_and_malformed_output(self):
        labels = {drug: int(drug == "A") for drug in "ABCDE"}
        grpo = dict(zip("ABCDE", [answer(0.8), answer(0.8), answer(0), answer(0), "invalid"]))
        sft = dict(zip("ABCDE", ["invalid", answer(0.1), answer(0.2), answer(0.3), answer(0.4)]))
        result = c9.score_pair(labels, grpo, sft, labels, covered_through=TRACK_A_END)
        self.assertEqual((result["drugs"], result["events"], result["slots"]), (5, 1, 1))
        self.assertEqual(result["malformed"], {"grpo": 1, "sft": 1})
        self.assertAlmostEqual(result["brier"]["grpo"], 0.186)
        self.assertAlmostEqual(result["brier"]["sft"], 0.11)
        self.assertAlmostEqual(result["brier"]["difference"], 0.076)
        self.assertEqual(result["recall20"]["difference"], 0.5)
        self.assertEqual(result["brier"]["undefined_draws"], 0)
        self.assertGreater(result["recall20"]["undefined_draws"], 0)
        self.assertEqual(result, c9.score_pair(reversed(labels), grpo, sft, labels,
                                                covered_through=TRACK_A_END))

    def test_require_full_paired_mature_roster(self):
        with self.assertRaisesRegex(ValueError, "incomplete"):
            c9.score_pair(["A"], {}, {}, {}, covered_through=date(2028, 11, 26))
        with self.assertRaisesRegex(ValueError, "per frozen drug"):
            c9.score_pair(["A"], {"A": answer(0.7)}, {}, {"A": 1}, covered_through=TRACK_A_END)
        with self.assertRaisesRegex(ValueError, "captured model text"):
            c9.score_pair(["A"], {"A": answer(0.7)}, {"A": None}, {"A": 1}, covered_through=TRACK_A_END)
        with self.assertRaisesRegex(ValueError, "resolved binary"):
            pair = {"A": answer(0.5)}
            c9.score_pair(["A"], pair, pair, {"A": None}, covered_through=TRACK_A_END)

    def test_no_events_does_not_erase_paired_brier_interval(self):
        pair = {drug: answer(0.5) for drug in "ABCDE"}
        result = c9.score_pair(pair, pair, pair, dict.fromkeys(pair, 0), covered_through=TRACK_A_END)
        self.assertEqual(result["brier"]["ci95"], [0, 0])
        self.assertIsNone(result["recall20"]["difference"])
        self.assertIsNone(result["recall20"]["ci95"])
        self.assertEqual(result["recall20"]["undefined_draws"], 2000)

    def test_spec_matches_executable_constants(self):
        spec_path = Path(__file__).resolve().parents[2] / "data" / "C9_SPEC.json"
        spec = json.loads(spec_path.read_bytes())
        cohort, training, scoring = spec["cohort"], spec["training"], spec["evaluation"]
        self.assertEqual(spec["s0"]["cutoff"], c9.S0.isoformat())
        self.assertEqual(cohort["horizon_months"], c9.HORIZON_MONTHS)
        self.assertEqual(cohort["train_first_cutoff"], min(c9.TRAIN_CUTOFFS).isoformat())
        self.assertEqual(cohort["train_last_cutoff"], max(c9.TRAIN_CUTOFFS).isoformat())
        self.assertEqual(cohort["protected_retrospective_cutoffs_start"], c9.PROTECTED_START.isoformat())
        self.assertEqual(cohort["track_a_maturity"], TRACK_A_END.isoformat())
        self.assertEqual(cohort["train_row_slots"], c9.TRAIN_SLOTS)
        self.assertEqual(training["prompts_per_batch"], c9.PROMPTS_PER_BATCH)
        self.assertEqual(training["prompt_batches"], c9.PROMPT_BATCHES)
        self.assertEqual(training["seed"], c9.SEED)
        self.assertEqual(training["grpo"]["malformed_reward"], c9.MALFORMED_REWARD)
        self.assertEqual(scoring["malformed_probability"], c9.MALFORMED_PROBABILITY)
        self.assertEqual(scoring["malformed_rank_score"], c9.MALFORMED_RANK)
        self.assertEqual(scoring["bootstrap"]["draws"], c9.BOOTSTRAP_DRAWS)
        self.assertEqual(scoring["bootstrap"]["seed"], c9.SEED)
