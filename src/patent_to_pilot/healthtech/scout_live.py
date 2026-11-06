"""Solution Scout live dense search on CPU.

Loads a public corpus (``corpus.jsonl`` from ``build_scout_hupd_subset.py``), its precomputed
PatEmbed-large passage vectors (one row per ``dense_passages`` window, float16 or float32), and
encodes each brief on the CPU with the same mean pooling and query prompt as the V100 runner.
Family score = max over its passages (MaxP). Nothing leaves the machine and no paid call is made.
"""
from __future__ import annotations

from datetime import date
import hashlib
import json
from pathlib import Path
import time
from typing import Any

from patent_to_pilot.evaluation.dapfam_acquisition import DENSE_QUERY_PREFIX, dense_passages

PATEMBED_LARGE = {"repo": "datalyes/patembed-large", "revision": "2d5c0f92a3e5dc3d5415c08e612c57543c0e03ad",
                  "model_safetensors_sha256": "234ea36a876fe5d5c416c1cbaad6f7221e17861fadd6481f0b96588fdc1ca482",
                  "licence": "CC BY-NC-SA 4.0 (non-commercial)"}


def source_text(row: dict[str, Any]) -> str:
    """The candidate text shown in the UI, given to the LLM and used for quote checks."""
    return "\n\n".join(part for part in (row.get("title"), row.get("abstract"), row.get("claims")) if part)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


class CpuQueryEncoder:
    """PatEmbed-large query encoder on CPU: mean pooling over the attention mask, L2-normalised."""

    def __init__(self, model_dir: str | Path, *, verify: bool = True):
        import torch
        from transformers import AutoModel, AutoTokenizer

        model_dir = Path(model_dir)
        if verify and _sha256_file(model_dir / "model.safetensors") != PATEMBED_LARGE["model_safetensors_sha256"]:
            raise ValueError("PatEmbed-large weight hash mismatch")
        config = json.loads((model_dir / "sentence_bert_config.json").read_text(encoding="utf-8"))
        self.max_length = int(config["max_seq_length"])
        self.torch = torch
        self.tokenizer = AutoTokenizer.from_pretrained(model_dir)
        self.model = AutoModel.from_pretrained(model_dir, torch_dtype=torch.float32).eval()

    def encode(self, text: str):
        torch = self.torch
        with torch.inference_mode():
            batch = self.tokenizer([text], padding=True, truncation=True, max_length=self.max_length,
                                   return_tensors="pt")
            hidden = self.model(**batch).last_hidden_state
            mask = batch["attention_mask"].unsqueeze(-1).to(hidden.dtype)
            pooled = (hidden * mask).sum(1) / mask.sum(1).clamp(min=1e-9)
            return torch.nn.functional.normalize(pooled, p=2, dim=1)[0].numpy()


class LiveIndex:
    def __init__(self, rows: list[dict[str, Any]], vectors, encoder, *, corpus_sha256: str, vectors_sha256: str,
                 manifest: dict[str, Any] | None = None):
        import numpy as np

        self.np = np
        self.rows = rows
        self.by_id = {row["id"]: i for i, row in enumerate(rows)}
        counts = [len(dense_passages(r.get("title"), r.get("abstract"), r.get("claims"))) for r in rows]
        if any(c == 0 for c in counts):
            raise ValueError("every corpus row needs at least one passage")
        if sum(counts) != vectors.shape[0]:
            raise ValueError(f"vector rows {vectors.shape[0]} do not match corpus passages {sum(counts)}")
        self.offsets = np.concatenate([[0], np.cumsum(counts)[:-1]]).astype(np.int64)
        self.vectors = np.ascontiguousarray(vectors, dtype=np.float32)  # float16 on disk, float32 for fast dot products
        self.family_ids = np.array([r["id"] for r in rows])
        self.encoder = encoder
        self.corpus_sha256 = corpus_sha256
        self.vectors_sha256 = vectors_sha256
        self.manifest = manifest or {}

    @classmethod
    def load(cls, data_dir: str | Path, model_dir: str | Path, *, encoder=None) -> "LiveIndex":
        import numpy as np

        data_dir = Path(data_dir)
        corpus = data_dir / "corpus.jsonl"
        vectors_path = next(p for p in (data_dir / "passage-vectors-f16.npy", data_dir / "passage-vectors-f32.npy")
                            if p.exists())
        rows = [json.loads(line) for line in corpus.read_text(encoding="utf-8").splitlines() if line.strip()]
        manifest_path = data_dir / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
        corpus_sha = _sha256_file(corpus)
        if manifest.get("corpus_sha256") and manifest["corpus_sha256"] != corpus_sha:
            raise ValueError("corpus hash does not match its manifest")
        return cls(rows, np.load(vectors_path), encoder or CpuQueryEncoder(model_dir), corpus_sha256=corpus_sha,
                   vectors_sha256=_sha256_file(vectors_path), manifest=manifest)

    def family(self, family_id: str) -> dict[str, Any]:
        row = self.rows[self.by_id[family_id]]
        published = row.get("date_published")
        return {"ipc3": row.get("ipc3", []), "representative_raw": row["id"], "jurisdiction": row["id"][:2],
                "publication_date": None if not published else date(int(published[:4]), int(published[4:6]),
                                                                    int(published[6:8])).isoformat(),
                "title": row.get("title"), "source_text": source_text(row)}

    def has(self, family_id: str) -> bool:
        return family_id in self.by_id

    def search(self, brief_text: str) -> tuple[list[tuple[str, float]], float, float]:
        """All families ranked by MaxP cosine, best first; returns (ranking, encode_ms, search_ms)."""
        np = self.np
        started = time.perf_counter()
        query = self.encoder.encode(DENSE_QUERY_PREFIX + " ".join(brief_text.split())).astype(np.float32)
        encoded = time.perf_counter()
        family_scores = np.maximum.reduceat(self.vectors @ query, self.offsets)
        order = np.lexsort((self.family_ids, -family_scores))
        ranking = [(self.rows[i]["id"], float(family_scores[i])) for i in order]
        finished = time.perf_counter()
        return ranking, (encoded - started) * 1000, (finished - encoded) * 1000

    def describe(self) -> dict[str, Any]:
        return {"id": "scout-live", "mode": "live", "data_class": "public", "families": len(self.rows),
                "passages": int(self.vectors.shape[0]), "corpus_sha256": self.corpus_sha256,
                "vectors_sha256": self.vectors_sha256, "encoder": PATEMBED_LARGE,
                "source": self.manifest.get("source"), "corpus_licence": self.manifest.get("licence"),
                "paid_dispatch": "closed"}
