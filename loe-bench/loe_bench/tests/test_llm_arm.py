import unittest

from loe_bench.llm_arm import build_prompt, parse_response, run_rows

ROW = {"entity": "ABEMACICLIB", "t0": "2026-11-27", "horizon_months": 12, "rule_baseline": 0,
       "p_model": 0.05, "verdict": "CONTESTED", "action": "PREDICT_NO_ENTRY", "next_evidence": "L_challenge"}
GOOD = '{"p_entry": 0.2, "action": "PREDICT_NO_ENTRY", "missing_evidence": ["patent status"]}'


class T(unittest.TestCase):
    def test_prompt_label_free(self):
        s, u = build_prompt(ROW)
        for bad in ("p_model", "CONTESTED", "PREDICT_NO_ENTRY\n", "L_challenge", "0.05"):
            self.assertNotIn(bad, u)
        self.assertIn("ABEMACICLIB", u)
        self.assertIn("rule_baseline: 0", u)

    def test_label_field_rejected(self):
        with self.assertRaises(ValueError):
            build_prompt(dict(ROW, entry_date="2027-01-01"))

    def test_parse(self):
        self.assertTrue(parse_response(GOOD)["valid"])
        self.assertTrue(parse_response("```json\n" + GOOD + "\n```")["valid"])
        self.assertTrue(parse_response("Sure: " + GOOD)["valid"])
        for bad in ("nonsense", "", None, '{"p_entry": 1.5, "action": "PREDICT_ENTRY", "missing_evidence": []}',
                    '{"p_entry": 0.5, "action": "MAYBE", "missing_evidence": []}',
                    '{"p_entry": true, "action": "PREDICT_ENTRY", "missing_evidence": []}'):
            r = parse_response(bad)
            self.assertFalse(r["valid"])
            self.assertEqual(r["action"], "ABSTAIN_REFER_TO_EVALUATOR")

    def test_run_rows_mock(self):
        res = run_rows([ROW, ROW], lambda s, u: GOOD)
        self.assertEqual(len(res), 2)
        self.assertEqual(res[0]["entity"], "ABEMACICLIB")


if __name__ == "__main__":
    unittest.main()
