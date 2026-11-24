"""P2-T02 amendment A2 (D19 complete-content follow-up for Qwen3 and PatEmbed): hand-checkable fixtures for the content
build overrides (window, segment separator, default unchanged), the encoder's special-token wrap and batch packing, the
c0check comparison, the gates, the frozen per-model decision rule, and the output-neutral claims filter.
Synthetic data only; no model, GPU or real data."""
from __future__ import annotations

import csv
import importlib
import io
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts" / "research"))

import p2t02_d19_decide as dd  # noqa: E402
import p2t02_d19_encode as de  # noqa: E402
import p2t02_d19_gate as dg  # noqa: E402
import p2t02_d19_inputs as di  # noqa: E402


class FakeTok:
    """Word-level fake: one id per whitespace token; '\\n' -> [99]; optional wrap ids (like CLS/SEP or EOS)."""

    def __init__(self, prefix=(), suffix=()):
        self.prefix, self.suffix = list(prefix), list(suffix)
        self.vocab = {}

    def _ids(self, text):
        out = []
        for part in text.split(" "):
            if part == "\n":
                out.append(99)
            elif part:
                out.append(self.vocab.setdefault(part, 100 + len(self.vocab)))
        return out

    def __call__(self, text, add_special_tokens=True, **kw):
        if isinstance(text, list):
            return {"input_ids": [self(t, add_special_tokens)["input_ids"] for t in text]}
        ids = self._ids(text)
        return {"input_ids": (self.prefix + ids + self.suffix) if add_special_tokens else ids}


def _build_module(monkeypatch, **env):
    for k in ("P2T02_TOKDIR", "P2T02_WIN", "P2T02_SEG_SEP"):
        monkeypatch.delenv(k, raising=False)
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    import p2t02_build_content as bc
    return importlib.reload(bc)


def _run_process(bc, tmp_path, rows, sep_ids):
    bc.TOK = FakeTok()
    bc.SEP_IDS = sep_ids
    bc.SHARDS = tmp_path
    part = [("U:1", "P1", "t1 t2", "a1 a2 a3", "c1 x")]
    claims = {"P1": rows}
    cid, st = bc.process((0, 0, part, claims))
    ln = np.load(tmp_path / "c1-0000.len.npy")
    ids = np.fromfile(tmp_path / "c1-0000.u32", dtype=np.uint32)
    return ln, ids, st


def test_build_defaults_unchanged(monkeypatch):
    bc = _build_module(monkeypatch)
    assert bc.WIN == 510 and bc.SEG_SEP == "" and bc.OVERRIDES == {}
    assert bc.TOKDIR == "/data/ptp-paper2/models/arctic-embed-m-v2.0"


def test_build_window_and_separator_override(monkeypatch, tmp_path):
    bc = _build_module(monkeypatch, P2T02_WIN="70", P2T02_SEG_SEP="\n")
    assert bc.WIN == 70 and bc.OVERRIDES == {"P2T02_WIN": "70", "P2T02_SEG_SEP": "\n"}
    assert bc.sep_ids(FakeTok(), "\n") == [99] and bc.sep_ids(FakeTok(), "") == []
    # seg0 = title + newline + abstract = 4 fake tokens (the fake splits on spaces only); 3 claims of 1 sep + 30 = 31 tokens -> 97 tokens -> windows 70 + 27
    rows = [(i, i, "", " ".join(f"w{i}_{j}" for j in range(30))) for i in (1, 2, 3)]
    ln, ids, st = _run_process(bc, tmp_path, rows, [99])
    assert ln.tolist() == [70, 27]
    assert int((ids == 99).sum()) == 3                       # one separator before each claim, none before seg0
    assert st["tok_full"] == [97]
    bc2 = _build_module(monkeypatch, P2T02_WIN="70")
    (tmp_path / "b").mkdir()
    ln2, ids2, _ = _run_process(bc2, tmp_path / "b", rows, [])
    assert ln2.tolist() == [70, 24] and int((ids2 == 99).sum()) == 0     # frozen behaviour: no separator
    _build_module(monkeypatch)                                           # leave the module at its defaults


def test_special_wrap_and_window():
    bert = FakeTok(prefix=[1], suffix=[2])
    spec = de.wrap_spec(bert, "encode document for mixed retrieval: ")
    assert spec["prefix_ids"] == [1] and spec["suffix_ids"] == [2]
    assert len(spec["prompt_ids"]) == 5 and spec["window"] == 512 - 1 - 5 - 1
    qwen = FakeTok(prefix=[], suffix=[7])                    # EOS appended, no document prompt
    spec = de.wrap_spec(qwen, "")
    assert spec["head_ids"] == [] and spec["tail_ids"] == [7] and spec["window"] == 511


@pytest.mark.parametrize("window", [511, 512])
def test_build_accepts_qwen_window(monkeypatch, window):
    assert _build_module(monkeypatch, P2T02_WIN=str(window)).WIN == window
    _build_module(monkeypatch)


def test_gate_cosine_normalizes_fp16_vectors():
    a = np.array([[0.707, 0.707], [0.6, 0.8]], dtype=np.float16)
    assert float((a[0].astype(np.float32) ** 2).sum()) < 0.9999
    np.testing.assert_allclose(de.row_cosines(a, a), [1, 1])
    np.testing.assert_allclose(de.row_cosines(a, -a), [-1, -1])


def test_pack_batch_left_and_right():
    ids, am = de.pack_batch([np.array([5, 6], np.uint32), np.array([8], np.uint32)], [1], [2], 0, left=False)
    assert ids.tolist() == [[1, 5, 6, 2], [1, 8, 2, 0]] and am.tolist() == [[1, 1, 1, 1], [1, 1, 1, 0]]
    ids, am = de.pack_batch([np.array([5, 6], np.uint32), np.array([8], np.uint32)], [], [7], 0, left=True)
    assert ids.tolist() == [[5, 6, 7], [0, 8, 7]] and am.tolist() == [[1, 1, 1], [0, 1, 1]]
    with pytest.raises(AssertionError):
        de.pack_batch([np.zeros(511, np.uint32)], [1], [2], 0, left=False)


def test_score_check_thresholds():
    rec = np.linspace(0.2, 0.8, 1000)
    assert de.score_check(rec + 0.0004, rec)["passed"]
    bad = rec.copy()
    bad[:20] += 0.05                                       # 2% beyond 0.005 -> fails the 99% share
    assert not de.score_check(bad, rec)["passed"]
    assert not de.score_check(rec + 0.003, rec)["passed"]  # median shift beyond 0.001


def _eval(tmp_path, name, vals):
    pq = {f"q{i}": {"ALL_R@200": v, "IN_R@200": v, "OUT_R@200": v} for i, v in enumerate(vals)}
    d = {"block": "P1-DEV", "n_queries_run": 25626, "per_query": pq,
         "metrics": {"ALL_R@200": {"mean": float(np.mean(vals)), "n": len(vals)}}}
    (tmp_path / name).write_text(json.dumps(d))
    return d


def test_decide_rule_frozen():
    good = {k: {"ci95": [0.001, 0.02]} for k in ("ALL_R@200", "IN_R@200", "OUT_R@200")}
    assert dd.decide_rule("qwen3", good)["baseline"] == "qwen3-c1"
    near = {**good, "OUT_R@200": {"ci95": [-0.004, 0.02]}}
    assert dd.decide_rule("qwen3", near)["qualifies"]
    worse = {**good, "IN_R@200": {"ci95": [-0.006, 0.02]}}
    assert dd.decide_rule("patembed", worse)["baseline"] == "patembed-c0"
    zero = {**good, "ALL_R@200": {"ci95": [0.0, 0.02]}}
    assert not dd.decide_rule("patembed", zero)["qualifies"]


def test_gate_relay_content_final(tmp_path):
    br = tmp_path / "br"
    for p in ("logs", "evals-a3r1", "runs/z-qwen3", "runs/z-arctic"):
        (br / p).mkdir(parents=True)
    (br / "logs/gate-qwen3.json").write_text(json.dumps({"gate_passed": True}))
    _eval(br / "evals-a3r1", "z-qwen3.json", [0.1, 0.2])
    for p in ("runs/z-qwen3/units.json", "runs/z-arctic/units.json"):
        (br / p).write_text(json.dumps(["U:1", "U:2"]))
    assert dg.relay("qwen3", br)["passed"]
    (br / "runs/z-qwen3/units.json").write_text(json.dumps(["U:2", "U:1"]))
    assert not dg.relay("qwen3", br)["passed"]

    outs = {k: "h" + k for k in dg.DATA_OUTPUTS} | {"stats.json": "x"}
    man = {"outputs_sha256": outs, "inputs": {"texts-v1/corpus.jsonl": "c", "tokenizer_json_sha256": "t",
                                               "claims_files": 54}}
    (tmp_path / "a.json").write_text(json.dumps(man))
    (tmp_path / "b.json").write_text(json.dumps(dict(man, outputs_sha256=dict(outs, **{"stats.json": "y"}))))
    assert dg.content(tmp_path / "a.json", tmp_path / "b.json")["passed"]      # stats.json (timings) not compared
    bad = dict(man, outputs_sha256=dict(outs, **{"c1.ids.u32": "z"}))
    (tmp_path / "c.json").write_text(json.dumps(bad))
    assert not dg.content(tmp_path / "a.json", tmp_path / "c.json")["passed"]
    ov = dict(man, inputs=dict(man["inputs"], env_overrides={"P2T02_WIN": "511"}))
    (tmp_path / "d.json").write_text(json.dumps(ov))
    assert not dg.content(tmp_path / "a.json", tmp_path / "d.json")["passed"]  # the reproduction must use no override

    g = tmp_path / "g"
    g.mkdir()
    for n in ("relay", "content-arctic", "validate", "c0check", "preflight"):
        (g / f"{n}.json").write_text(json.dumps({"passed": True, "model": "qwen3"}))
    for n, model in (("model", "qwen3"), ("arctic", "arctic")):
        (g / f"weights-{n}.json").write_text(json.dumps({"status": "PASS", "model": model}))
    window = {"model": "qwen3", "model_dir": "tok", "window": 511, "max_positions": 512,
              "segment_separator": "\n", "segment_separator_ids": [7]}
    (g / "window.json").write_text(json.dumps(window))
    stats = {"window_content_tokens": 511, "window_model_positions": 512, "segment_separator_ids": [7],
             "env_overrides": {"P2T02_WIN": "511", "P2T02_TOKDIR": "tok", "P2T02_SEG_SEP": "\n"}}
    (g / "stats.json").write_text(json.dumps(stats))
    parts = [g / f for f in ("relay.json", "content-arctic.json", "validate.json", "c0check.json", "window.json",
                             "stats.json", "preflight.json", "weights-model.json", "weights-arctic.json")]
    assert dg.final("qwen3", parts)["gate_passed"]
    assert not dg.final("patembed", parts)["gate_passed"]
    assert dg.final("qwen3", parts[:-1])["missing"] == ["weights-arctic"]
    (g / "stats.json").write_text(json.dumps(dict(stats, segment_separator_ids=[8])))
    assert not dg.final("qwen3", parts)["gate_passed"]


def _zip(path, member, rows):
    buf = io.StringIO()
    w = csv.writer(buf, delimiter="\t", lineterminator="\n")
    for r in rows:
        w.writerow(r)
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(member, buf.getvalue())


def test_claims_filter_is_output_neutral(tmp_path, monkeypatch):
    bc = _build_module(monkeypatch)
    head = ["patent_id", "claim_sequence", "claim_text", "dependent", "claim_number", "exemplary"]
    rows = [head,
            ["0000123", "0", 'A widget "with" quotes,\ttab', "", "1", "1"],
            ["999", "0", "Other document claim", "", "1", "1"],
            ["0000123", "1", "2. (canceled)", "", "2", "0"],
            ["D0045", "0", "Line one\nline two", "", "1", "1"],
            ["0000123", "2", "The widget of claim 1.", "claim 1", "3", "0"]]
    src, dst = tmp_path / "g_claims_1999.tsv.zip", tmp_path / "out" / "g_claims_1999.tsv.zip"
    dst.parent.mkdir()
    _zip(src, "g_claims_1999.tsv", rows)
    need = {"P123", "PD45"}
    r = di.filter_zip(src, dst, need, bc.pat_key)
    assert r["rows_in"] == 5 and r["rows_kept"] == 4
    bc.init_scan(need)
    a, b = bc.scan(str(src)), bc.scan(str(dst))
    assert a[1] == b[1] and a[2] == b[2] == 1
    assert [x[3] for x in b[1]["P123"]] == ['A widget "with" quotes, tab', "The widget of claim 1."]
