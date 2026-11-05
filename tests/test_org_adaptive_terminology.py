"""The organization-adaptive study is a new manuscript: earlier unpublished labels must not leak into it."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
STUDY_FILES = [
    "docs/healthtech/research/ORG_ADAPTIVE_CROSS_DOMAIN_PROTOCOL_DRAFT_20261105_EN.md",
    "docs/healthtech/research/ORG_ADAPTIVE_POC_PLAN_20261105_EN.md",
    "docs/healthtech/research/ORG_ADAPTIVE_MANUSCRIPT_PLAN_20261105_EN.md",
    "src/patent_to_pilot/evaluation/dapfam_acquisition.py",
    "scripts/healthtech/build_dapfam_acquisition_stage0.py",
    "scripts/healthtech/run_dapfam_dense_pool.py",
    "scripts/healthtech/check_dense_pooling_equivalence.py",
    "scripts/healthtech/evaluate_dapfam_pool.py",
    "scripts/healthtech/run_qwen_query_actions.py",
]
STUDY_DIRS = ["docs/healthtech/audits/ptp-org-adaptive-stage0-20261105"]
BANNED = re.compile(
    r"paper\s*86|\barm-?0\d\b|final-?872|selection-?125|train-?(250|179)|nine-cell|journal_08|\bmyis\b"
    r"|\ba[67]\b|construction recipe|representation transfer",
    re.IGNORECASE,
)
BANNED_PROFILE_NAMES = re.compile(r"\b(BALANCED|DEEP|FAST)\b")


def _files():
    paths = [ROOT / name for name in STUDY_FILES]
    for directory in STUDY_DIRS:
        paths.extend(p for p in (ROOT / directory).rglob("*") if p.is_file())
    return paths


def _offending(text: str) -> str | None:
    match = BANNED.search(text) or BANNED_PROFILE_NAMES.search(text)
    return match.group(0) if match else None


def test_patterns_catch_labels_but_not_ordinary_words():
    for label in ("Paper 86", "ARM-03", "arm03", "A6", "Final-872", "Train250", "FAST profile", "journal_08"):
        assert _offending(label), label
    for ordinary in ("fast path", "deep pools", "data6", "dense passage retriever", "A61 class"):
        assert _offending(ordinary) is None, ordinary


def test_study_files_avoid_earlier_unpublished_labels():
    offenders = []
    for path in _files():
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            label = _offending(line)
            if label:
                offenders.append(f"{path.relative_to(ROOT)}:{number}: {label}")
    assert offenders == []
