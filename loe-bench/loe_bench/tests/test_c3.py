import json
from datetime import date
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

from loe_bench import c3


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from c3_dev_run import approval_metadata, project_development_anda, project_identity


DAY = date(2013, 1, 1)
END = c3.DEVELOPMENT_END
PROOF = c3.Evidence("fixture FDA action", "synthetic v1", "a" * 64, "fixture record")


def application(i):
    return f"ANDA{i:06d}"


class ApplicantEndpointTest(unittest.TestCase):
    def label(self, approvals, history=(), aliases=()):
        return c3.build_labels([("group", DAY)], approvals, c3.ApplicantIndex(history, aliases),
                               observed_through=END)["group", DAY]

    def test_dedup_aliases_and_original_applicant_at_transfer(self):
        final = date(2014, 1, 1)
        later = date(2015, 1, 1)
        approvals = [c3.Approval("group", application(i), final, PROOF) for i in range(1, 5)]
        approvals.append(approvals[0])  # another strength of the same application
        approvals.append(c3.Approval("group", application(1), later, PROOF))
        history = [
            c3.ApplicantHistory(application(i), name, final, final, PROOF)
            for i, name in enumerate(("Alpha", "Alpha Legacy", "Beta", "Gamma"), 1)
        ]
        history.append(c3.ApplicantHistory(application(1), "Delta", later, END, PROOF))
        alias = c3.NameAlias("Alpha Legacy", "Alpha", final, final, PROOF)
        two = self.label(approvals[:3], history, [alias])
        self.assertEqual((two.lower, two.upper, two.event), (2, 2, False))
        three = self.label(approvals, history, [alias])
        self.assertEqual(three.confirmed_applicants, ("alpha", "beta", "gamma"))
        self.assertEqual((three.lower, three.upper, three.event), (3, 3, True))

    def test_missing_or_conflicting_history_can_flip_the_threshold(self):
        approvals = [c3.Approval("group", application(i), END, PROOF) for i in range(1, 4)]
        history = [
            c3.ApplicantHistory(application(i), name, END, END, PROOF)
            for i, name in ((1, "Alpha"), (2, "Beta"), (3, "Conflicting A"), (3, "Conflicting B"))
        ]
        label = self.label(approvals, history)
        self.assertEqual(label.unresolved_applications, (application(3),))
        self.assertEqual((label.lower, label.upper, label.event), (2, 3, None))

    def test_excludes_nonfinal_and_authorized_generics_and_includes_window_end(self):
        approvals = [
            c3.Approval("group", application(1), DAY, PROOF, action="ORIG/TA"),
            c3.Approval("group", application(2), DAY, PROOF, authorized_generic=True),
            c3.Approval("group", application(3), DAY, PROOF, action="SUPPL/AP"),
            c3.Approval("group", "NDA000004", DAY, PROOF),
            c3.Approval("group", application(1), END, PROOF),
        ]
        label = self.label(approvals)
        self.assertEqual(label.applications, (application(1),))
        self.assertEqual((label.lower, label.upper, label.event), (1, 1, False))

    def test_open_left_boundary_and_guard_before_consuming_approvals(self):
        with self.assertRaisesRegex(ValueError, "pre-cutoff"):
            self.label([c3.Approval("group", application(1), DAY, PROOF)])

        def unread():
            self.fail("approval source consumed before validating windows")
            yield

        for cutoff in (date(2014, 1, 1), date(2016, 1, 1), date(2024, 1, 1)):
            with self.assertRaises(ValueError):
                c3.build_labels([("group", cutoff)], unread(), c3.ApplicantIndex(),
                                observed_through=date(2028, 1, 1))
        with patch("loe_bench.c3.require_cutoffs", side_effect=PermissionError):
            with self.assertRaises(PermissionError):
                c3.build_labels([("group", date(2017, 1, 1))], unread(), c3.ApplicantIndex(),
                                observed_through=date(2028, 1, 1))


class FrozenQueueTest(unittest.TestCase):
    def test_label_assignments_keep_full_roster_and_boundary_ties(self):
        keys = [(str(i), DAY) for i in range(5)]
        labels = dict(zip(keys, [True, None, None, False, False]))
        scores = {"M3": dict(zip(keys, [0.8, 0.8, 0.2, 0.1, 0.1])),
                  "B1": dict(zip(keys, [0.1, 0.1, 0.8, 0.1, 0.1]))}
        result = c3.score(labels, scores, observed_through=END, history_irrecoverable=False)
        self.assertEqual(result["slots_by_cutoff"], {DAY.isoformat(): 1})
        self.assertEqual(result["event_drugs"], 1)
        self.assertEqual(result["unknown_drugs"], 2)
        self.assertEqual(result["arms"]["M3"]["recall"], 0.5)
        self.assertEqual(result["arms"]["B1"]["recall"], 0.0)
        self.assertEqual(result["arms"]["M3"]["bounds"]["range_given_nonzero_events"], [0.25, 0.5])
        comparison = result["M3_minus_B1"]
        self.assertEqual(comparison["bounds"]["range_given_nonzero_events"], [-0.25, 0.5])
        self.assertEqual(comparison["bounds"]["all_unknown_positive"], 0.0)
        self.assertEqual(comparison["draws_run"], 2_000)
        self.assertGreater(comparison["undefined_draws"], 0)
        self.assertIsNone(comparison["ci95"])
        bounds = c3.score(labels, scores, observed_through=END, history_irrecoverable=True)
        self.assertEqual(bounds["status"], "DESCRIPTIVE_BOUNDS_ONLY")
        self.assertIsNone(bounds["arms"]["M3"]["recall"])
        self.assertEqual(bounds["M3_minus_B1"]["bounds"], comparison["bounds"])

    def test_paired_defined_interval_and_zero_known_event_rule(self):
        keys = [(str(i), t) for t in (date(2012, 1, 1), DAY) for i in range(5)]
        labels = dict.fromkeys(keys, True)
        scores = {"M3": dict.fromkeys(keys, 0.1), "B1": dict.fromkeys(keys, 0.2)}
        result = c3.score(labels, scores, observed_through=END, history_irrecoverable=False)
        self.assertEqual(result["event_rows"], 10)
        self.assertEqual(result["event_drugs"], 5)
        self.assertEqual(result["arms"]["M3"]["recall"], 0.2)
        self.assertEqual(result["M3_minus_B1"]["ci95"], [0.0, 0.0])
        result = c3.score(dict.fromkeys(keys), scores, observed_through=END, history_irrecoverable=False)
        self.assertEqual(result["status"], "UNDEFINED_NO_KNOWN_EVENTS")
        self.assertIsNone(result["arms"]["M3"]["recall"])
        self.assertIsNone(result["arms"]["M3"]["bounds"]["all_unknown_negative"])
        self.assertEqual(result["arms"]["M3"]["bounds"]["all_unknown_positive"], 0.2)

    def test_rejects_incomplete_frozen_queue(self):
        with self.assertRaisesRegex(ValueError, "match exactly"):
            c3.score({("a", DAY): True}, {"M3": {}, "B1": {}}, observed_through=END,
                     history_irrecoverable=False)


class DevelopmentProjectionTest(unittest.TestCase):
    def test_mixed_application_is_projected_before_decoding_outcomes(self):
        admitted = {"submission_type": "ORIG", "submission_status": "AP",
                    "submission_status_date": "20160101", "application_docs": [
                        {"application_docs_date": "20160101", "application_docs_url": "admitted"},
                        {"application_docs_date": "20170101", "application_docs_url": "future-doc"}]}
        later = {"submission_type": "ORIG", "submission_status": "AP",
                 "submission_status_date": "20170101", "application_docs": "future-action"}
        application_row = {"application_number": application(1), "sponsor_name": "Snapshot",
                           "submissions": [admitted, later], "products": [
                               {"product_number": "001"}, {"product_number": "002",
                                                           "approval_date": "20170101"}]}
        payload = json.dumps(application_row).encode()
        original_loads = json.loads

        def guarded_loads(raw):
            self.assertNotIn(b"20170101", raw)
            self.assertNotIn(b"future-", raw)
            return original_loads(raw)

        with patch("json.loads", side_effect=guarded_loads):
            approval = project_development_anda(payload)
            self.assertEqual(len(approval["products"]), 1)
            self.assertEqual(approval_metadata(payload, END), {
                "snapshot_sponsor": "Snapshot", "same_day_documents": ["admitted"],
            })
            application_row["submissions"] = [later]
            future_only = json.dumps(application_row).encode()
            self.assertIsNone(project_development_anda(future_only))
            self.assertEqual(project_identity(future_only)["products"], [{"product_number": "001"}])
