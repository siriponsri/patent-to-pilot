import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
G6 = ROOT / "docs/healthtech/research/G6_MANUSCRIPT_METHODS_SKELETON_20261029.md"
SCIFACT_VERIFICATION = ROOT / "docs/healthtech/audits/luna-long-run-20261029-ht-t2-lexical-dev-20261029/verification.json"


def test_g6_keeps_scifact_separate_and_matches_component_receipt():
    text = G6.read_text(encoding="utf-8")
    verification = json.loads(SCIFACT_VERIFICATION.read_text(encoding="utf-8"))
    metrics = verification["score"]["metrics"]

    assert "Separate HT-T2 SciFact component" in text
    assert "not device-patent gold" in text
    assert "Official hidden/test labels are absent" in text
    assert "0.203787" in text
    assert f"{metrics['sentence_label']['f1']:.6f}" in text
    assert "must not be pooled with HT-T1 patent-association recall" in text
    assert verification["protocol"]["denominator_claims"] == 300
    assert verification["prediction_run"]["prediction_rows"] == 300
    assert verification["score"]["missing_prediction_claim_ids"] == []
