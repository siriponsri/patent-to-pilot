"""Small fixtures for the C9P input, optimization and launch contracts."""

import contextlib
import importlib.util
import io
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from c9.dry_run import fixture, synthetic_rows
from c9.inputs import (load_projection, prediction_record, schedule, select_training,
                       specification, tokenize_rows, track_rows)
from c9.runpod import allowances, stage_bundle, verify_transfer
from loe_bench.c9 import grpo_reward


class TestC9Inputs(unittest.TestCase):
    def test_hash_order_cycles_and_excludes_incomplete_windows(self):
        rows = list(synthetic_rows(10))
        rows[0]["covered_through"] = "2015-12-31"
        rows[1]["resolved_linkage"] = False
        roster = select_training(rows)
        self.assertEqual(roster, select_training(reversed(rows)))
        self.assertEqual(len(roster), 256)
        ordered = [r["drug_key"] for r in roster]
        self.assertEqual(ordered[:8], [
            "synthetic-002", "synthetic-006", "synthetic-007", "synthetic-003",
            "synthetic-008", "synthetic-004", "synthetic-005", "synthetic-009",
        ])
        self.assertEqual(ordered, ordered[:8] * 32)
        self.assertEqual({r["label"] for r in roster}, {0, 1})
        for row in rows:
            row["first_final_anda"] = None
        with self.assertRaisesRegex(ValueError, "both classes"):
            select_training(rows)

    def test_future_input_is_rejected(self):
        rows = list(synthetic_rows())
        rows[0]["first_final_anda"] = "2016-01-02"
        with self.assertRaisesRegex(ValueError, "clipped"):
            select_training(rows)
        rows[0]["forecast"]["t0"] = "2017-01-01"
        with self.assertRaisesRegex(ValueError, "cutoff outside"):
            select_training(rows)

    def test_projection_hash_and_track_a_field_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "track-a.json"
            sha = fixture(path, training=False)
            raw = load_projection(path, sha, training=False)
            self.assertEqual(len(track_rows(raw)), 16)
            with self.assertRaisesRegex(ValueError, "mismatch"):
                load_projection(path, "1" * 64, training=False)
            raw[0]["label"] = 1
            with self.assertRaisesRegex(ValueError, "unexpected projection"):
                track_rows(raw)

    def test_prediction_and_rewards_for_invalid_and_valid_abstention(self):
        row = {"drug_key": "fixture", "t0": "2026-11-27"}
        valid = '{"p_entry":0.25,"action":"ABSTAIN_REFER_TO_EVALUATOR","missing_evidence":["x"]}'
        self.assertEqual(grpo_reward(valid, 1), -0.5625)
        self.assertEqual(prediction_record(row, valid)["rank_score"], 0.25)
        for text in ("", "{}", valid.replace("0.25", "true")):
            parsed = prediction_record(row, text)
            self.assertFalse(parsed["valid"])
            self.assertEqual(parsed["brier_probability"], 0.5)
            self.assertEqual(parsed["rank_score"], -1.0)
            self.assertEqual(grpo_reward(text, 1), -1.25)
        with self.assertRaisesRegex(ValueError, "missing captured"):
            prediction_record(row, None)

    def test_prompt_oversize_fails_with_no_truncation(self):
        row = {"drug_key": "fixture", "messages": ["s", "u"]}
        class Tokenizer:
            def apply_chat_template(self, *_args, **kwargs):
                assert kwargs["add_generation_prompt"] and "truncation" not in kwargs
                return [1] * 2049
        with self.assertRaisesRegex(ValueError, "pair failed"):
            tokenize_rows([row], Tokenizer(), specification()["prompt"]["max_prompt_tokens"])

    def test_frozen_schedule(self):
        spec = specification()
        self.assertEqual(schedule(spec), (32, 8, 2))
        self.assertEqual(schedule(spec, dry=True), (2, 8, 1))


class TestRunPod(unittest.TestCase):
    def test_time_and_cost_include_already_billed_seconds(self):
        approved = {
            "gpu": "NVIDIA A10", "gpu_count": 1, "owner_approval_ref": "example",
            "cprime_pass_ref": "example", "live_quote_ref": "example", "pod_id": "fixture",
            "data_center": "US", "gpu_usd_per_hour": 1.40, "non_gpu_total_usd": 1.0,
            "ephemeral_storage_gib": 20, "billing_started_utc": "2026-12-01T00:00:00Z",
            "core_freeze_utc": "2026-12-03T00:00:00Z", "setup_seconds": 100, "arm_seconds": 8800,
            "pull_seconds": 100, "teardown_seconds": 100,
        }
        start = datetime.fromisoformat(approved["billing_started_utc"]).timestamp()
        self.assertEqual(allowances(approved, specification(), start + 95), [100, 8800, 100, 100])
        with self.assertRaisesRegex(ValueError, "reservation exceeds"):
            allowances(approved, specification(), start + 101)

    def test_allowlisted_bundle_and_retrieval_inventory(self):
        from argparse import Namespace
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            training, track = root / "train.json", root / "track.json"
            args = Namespace(projection=training, projection_sha256=fixture(training, training=True),
                             track_a_roster=track, track_a_sha256=fixture(track, training=False))
            bundle = root / "bundle"
            stage_bundle(bundle, args)
            self.assertFalse((bundle / "data/raw").exists())
            self.assertTrue((bundle / "inputs.sha256").is_file())
            results = root / "results"
            results.mkdir()
            (results / "report.json").write_bytes(track.read_bytes())
            (results / "files.sha256").write_bytes(f"{args.track_a_sha256}  report.json\n".encode())
            self.assertEqual(verify_transfer(results), {"report.json": args.track_a_sha256})
            (results / "report.json").write_text("corrupt", encoding="ascii")
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                verify_transfer(results)


@unittest.skipUnless(all(importlib.util.find_spec(name) for name in ("torch", "peft", "transformers")),
                     "C9 training dependencies are optional")
class TestC9Optimization(unittest.TestCase):
    def test_population_advantage_and_clipping(self):
        import torch
        from c9.train import grpo_loss, standardized_advantages
        reward = torch.tensor([[0.0, 0.0, -1.0, -1.0], [-1.25] * 4])
        adv = standardized_advantages(reward)
        expected = 0.5 / 0.5001
        self.assertTrue(torch.allclose(adv, torch.tensor([[expected, expected, -expected, -expected], [0.] * 4])))
        current = torch.tensor([1.5, 0.5]).log()
        zeros = torch.zeros_like(current)
        decoder = specification()["training"]["grpo"]
        loss = grpo_loss(current, zeros, current, torch.tensor([1., -1.]), decoder)
        self.assertAlmostEqual(loss.item(), -(1.2 - 0.8) / 2)
        loss = grpo_loss(current, zeros, zeros, torch.tensor(0.), decoder)
        kl = (1 / 1.5 - 1 + current[0] + 1 / 0.5 - 1 + current[1]) / 2
        self.assertAlmostEqual(loss.item(), 0.04 * kl.item())

    def test_production_fits_64_updates_with_one_rollout_per_batch(self):
        import torch
        from c9.train import fit

        class Model(torch.nn.Module):
            device = "cpu"

            def __init__(self):
                super().__init__()
                self.weight = torch.nn.Parameter(torch.tensor(0.0))

        class Tokenizer:
            eos_token_id = 2

            def encode(self, *_args, **_kwargs):
                return [1]

        spec = specification()
        for arm in ("sft", "grpo"):
            model = Model()
            def logp(model, *_):
                return model.weight.view(1)
            def batch_rollout(model, *_):
                pairs = [([1], [2])] * 32
                fixed = [model.weight.detach().clone().view(1)] * 32
                return pairs, fixed, fixed, torch.ones(32), 0
            with patch("c9.train.completion_logp", side_effect=logp), \
                 patch("c9.train.rollout", side_effect=batch_rollout) as rollout_mock, \
                 contextlib.redirect_stdout(io.StringIO()):
                result = fit(model, Tokenizer(), [[1]] * 256, [0, 1] * 128, arm, spec, dry=False)
            self.assertEqual(result["updates"], 64)
            self.assertEqual(rollout_mock.call_count, 32 if arm == "grpo" else 0)
            self.assertNotEqual(model.weight.item(), 0.0)
