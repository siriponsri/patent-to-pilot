"""Regression fixtures for the E7 availability, identity and graph contracts."""
import json
from datetime import date
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import TestCase

from loe_bench import evidence_graph as graph, t2
from loe_bench.challenge import ChallengeHistory, ChallengeIdentity, CourtRow
from loe_bench.kleene import T3
from loe_bench.ob_history import Edition, OBHistory
from loe_bench.piv_history import EntityMatcher, PIVHistory
from loe_bench.t2_features import AsOfBuilder, CHALLENGE_FEATURES
from loe_bench.tests.test_piv_history import xlsx

CUTOFF = date(2011, 1, 1)
KEY = "U:EXAMPLE"


class ChallengeTests(TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.raw = Path(directory.name)
        self.editions = []
        aliases = {"EXAMPLE": KEY, "EXAMPLE HYDROCHLORIDE": KEY, "SECOND": "U:SECOND"}
        registry = SimpleNamespace(composition=lambda names: SimpleNamespace(
            key=aliases.get(" ".join(names).upper(), "")))
        entities = {key: SimpleNamespace(nda_first=date(2000, 1, 1)) for key in aliases.values()}
        linker = SimpleNamespace(registry=registry, entities=entities, canonical=lambda key: key)
        self.identity = ChallengeIdentity(linker, [("Example Brand", KEY, date(2005, 1, 1)),
                                                   ("Second Brand", "U:SECOND", date(2012, 1, 1))])
        self.proof = {"court": "D.Del.", "docket": "1:10-cv-12345", "filed": "2010-12-20",
                      "brand": "Example Brand"}

    def edition(self, version, timestamp, **kwargs):
        payload = xlsx(**kwargs)
        digest = sha256(payload).hexdigest()
        file = digest + ".xlsx"
        (self.raw / file).write_bytes(payload)
        self.editions.append(dict(version_date=version, wayback_timestamp=timestamp, file=file,
                                  format="xlsx", rows=1, sha256=digest, parse_status="PASS",
                                  source_url="https://www.fda.gov/example.xlsx"))

    def history(self, court=(), proof=()):
        manifest = self.raw / "editions.json"
        manifest.write_text(json.dumps({"editions": self.editions}), encoding="utf-8")
        piv = PIVHistory(manifest, self.raw, EntityMatcher([]))
        return ChallengeHistory(piv, self.identity, court,
                                {"version": "fixture", "sha256": "hash", "url": "example"}, proof)

    def test_late_capture_and_future_edition_cannot_reveal_backdated_submission(self):
        self.edition("2010-12-20", "20101221000000", name="Second")
        self.edition("2010-12-30", "20110102000000", name="Example")
        self.edition("2011-01-02", "20110103000000", name="Example")
        history = self.history()
        self.assertEqual(history.lookup(KEY, CUTOFF).state, T3.FALSE)
        self.assertEqual(history.lookup(KEY, date(2011, 1, 2)).state, T3.TRUE)

    def test_future_submission_and_future_court_filing_are_not_witnesses(self):
        self.edition("2010-12-25", "20101226000000", name="Example", when="1/2/2011")
        case = CourtRow("D.Del.", "1:10-cv-12345", date(2011, 1, 2), "Example Brand", "Example", "line 2")
        proof = dict(self.proof, filed=case.filed.isoformat())
        result = self.history([case], [proof]).lookup(KEY, CUTOFF)
        self.assertEqual(result.state, T3.FALSE)
        self.assertEqual(result.witnesses, ())

    def test_stale_unproven_or_corrupt_list_cannot_establish_false(self):
        self.edition("2010-06-30", "20100701000000", name="Second")
        self.edition("2010-12-29", None, name="Second")
        self.assertEqual(self.history().lookup(KEY, CUTOFF).state, T3.UNKNOWN)
        self.edition("2010-12-30", "20101231000000", name="Second")
        (self.raw / self.editions[-1]["file"]).write_bytes(b"tampered")
        self.assertEqual(self.history().lookup(KEY, CUTOFF).state, T3.UNKNOWN)

    def test_court_requires_corrob_and_preserves_both_sources(self):
        case = CourtRow("D.Del.", "1:10-cv-12345", date(2010, 12, 20), "Example Brand", "Example", "line 2")
        self.assertEqual(self.history([case]).lookup(KEY, CUTOFF).state, T3.UNKNOWN)
        self.assertEqual(self.history([case], [self.proof]).lookup(KEY, CUTOFF).state, T3.TRUE)
        self.edition("2010-12-25", "20101226000000", name="Example hydrochloride NEW!")
        result = self.history([case], [self.proof]).lookup(KEY, CUTOFF)
        self.assertEqual(result.state, T3.TRUE)
        self.assertEqual([w.source for w in result.witnesses], ["FDA_PIV", "RAI_COURT"])
        self.assertEqual(result.witnesses[1].document_id, "D.Del. 1:10-cv-12345")
        self.assertEqual(result.witnesses[1].date, case.filed)
        self.assertEqual(result.witnesses[1].locator, "line 2")

    def test_dated_brand_and_disagreement(self):
        self.assertIsNone(self.identity.court_key("Second Brand", "", CUTOFF))
        self.assertIsNone(self.identity.court_key("Example Brand", "Second", CUTOFF))
        self.assertEqual(self.identity.court_key("Example Brand", "", CUTOFF), KEY)

    def test_shared_inputs_and_graph_decision_use_same_leaf(self):
        self.edition("2010-12-25", "20101226000000", name="Example")
        builder = AsOfBuilder(OBHistory([]), challenge=self.history())
        result = builder.build(KEY, CUTOFF, 12, {})
        m1, = t2._inputs([{"asof": result}], [0.5])
        m3, = t2._inputs([{"asof": result}], [0.5], with_verdict=True)
        self.assertEqual([m1["x"][f] for f in CHALLENGE_FEATURES], [1.0, 0.0])
        self.assertEqual([m3["x"][f] for f in CHALLENGE_FEATURES], [1.0, 0.0])
        snapshot = {"patent_exp": [date(2013, 1, 1)], "excl_exp": [CUTOFF]}
        decision = graph.decide(snapshot, CUTOFF, 12, 0.9, challenge_evidence=result.challenge.state)
        self.assertEqual(decision["trace"]["L_challenge"], "TRUE")
        self.assertEqual(decision["verdict"], "OPEN")
