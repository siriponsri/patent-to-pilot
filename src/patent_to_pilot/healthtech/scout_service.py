"""Solution Scout service, replay mode (M1).

Replay serves recorded searches and recorded LLM rationales from a server-owned bundle, so the demo
runs with no GPU. It answers only briefs that were recorded; anything else fails closed. Quote
checks are recomputed against the bundle's source text on every request, never trusted from the
recording. Sessions persist as JSON under the service root. No provider or paid call is made.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import threading
from typing import Any
from uuid import uuid4

from patent_to_pilot.healthtech.contracts import canonical_patent_id
from patent_to_pilot.healthtech.scout import (
    LaneSplit,
    ScoutBrief,
    ScoutCandidate,
    ScoutReceipt,
    ScoutSession,
    TransferRationale,
    check_quote,
    normalize_ipc3,
    partition_by_field,
    two_lane_shortlist,
)

REPLAY_FORMAT = "ptp-scout-replay-v1"
SESSION_ID = re.compile(r"^[a-f0-9]{32}$")
IDEMPOTENCY_KEY = re.compile(r"^[A-Za-z0-9._:-]{1,160}$")


class ScoutError(ValueError):
    def __init__(self, status: int, code: str, message: str, *, details: Any = None):
        super().__init__(message)
        self.status, self.code, self.message, self.details = status, code, message, details


def _hash(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode("utf-8")).hexdigest()


def _atomic_write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, staging_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".staging", dir=path.parent)
    staging = Path(staging_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, allow_nan=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        staging.replace(path)
    finally:
        try:
            staging.unlink()
        except FileNotFoundError:
            pass


class ReplayBundle:
    """A recorded corpus slice, searches and rationales. ``families`` is hashed into the corpus id."""

    def __init__(self, raw: dict[str, Any], sha256: str):
        if raw.get("format") != REPLAY_FORMAT:
            raise ValueError(f"replay bundle format must be {REPLAY_FORMAT}")
        if raw.get("data_class") not in {"synthetic", "public"}:
            raise ValueError("replay bundles hold synthetic or public data only")
        self.sha256 = sha256
        self.data_class = raw["data_class"]
        self.encoder = raw["encoder"]
        self.encoder_revision = raw["encoder_revision"]
        self.families: dict[str, dict[str, Any]] = raw["families"]
        self.corpus_sha256 = _hash(self.families)
        if raw.get("corpus_bundle_sha256") != self.corpus_sha256:
            raise ValueError("replay corpus hash does not match its families")
        for family_id, family in self.families.items():
            normalize_ipc3(family.get("ipc3", []))
            if not family.get("source_text"):
                raise ValueError(f"family {family_id} has no source text")
        self.searches: dict[tuple[str, tuple[str, ...]], dict[str, Any]] = {}
        for search in raw["searches"]:
            key = (search["brief_text"], normalize_ipc3(search["own_ipc3"]))
            if key in self.searches:
                raise ValueError("duplicate recorded search")
            unknown = [r["family_id"] for r in search["ranking"] if r["family_id"] not in self.families]
            if unknown:
                raise ValueError(f"recorded ranking cites unknown families: {unknown[:3]}")
            self.searches[key] = search
        self.rationales: dict[tuple[str, str], dict[str, Any]] = {}
        for rationale in raw.get("rationales", []):
            self.rationales[(rationale["search_id"], rationale["family_id"])] = rationale

    @classmethod
    def load(cls, path: str | Path) -> "ReplayBundle":
        raw_bytes = Path(path).read_bytes()
        return cls(json.loads(raw_bytes.decode("utf-8")), hashlib.sha256(raw_bytes).hexdigest())

    def describe(self) -> dict[str, Any]:
        return {"id": "scout-replay", "mode": "replay", "data_class": self.data_class,
                "bundle_sha256": self.sha256, "corpus_bundle_sha256": self.corpus_sha256,
                "encoder": self.encoder, "encoder_revision": self.encoder_revision,
                "families": len(self.families), "recorded_searches": len(self.searches),
                "recorded_rationales": len(self.rationales), "paid_dispatch": "closed"}


class ScoutService:
    def __init__(self, root: str | Path, bundle: ReplayBundle | None):
        self.root = Path(root) / "scout"
        self.bundle = bundle
        self._lock = threading.RLock()

    def _require_bundle(self) -> ReplayBundle:
        if self.bundle is None:
            raise ScoutError(409, "scout_unavailable", "no scout replay bundle is configured on this server")
        return self.bundle

    def _dir(self, session_id: str) -> Path:
        if not SESSION_ID.fullmatch(session_id):
            raise ScoutError(400, "invalid_session_id", "session_id is invalid")
        return self.root / "sessions" / session_id

    def _read(self, path: Path, missing: str) -> dict[str, Any]:
        if not path.exists():
            raise ScoutError(404, missing, "not found")
        return json.loads(path.read_text(encoding="utf-8"))

    def describe(self) -> dict[str, Any]:
        return self._require_bundle().describe()

    def create(self, body: Any, idempotency_key: str | None) -> tuple[dict[str, Any], bool]:
        bundle = self._require_bundle()
        if not isinstance(body, dict) or set(body) - {"brief", "split"} or "brief" not in body:
            raise ScoutError(400, "invalid_request", "body must contain brief and optional split")
        if not isinstance(idempotency_key, str) or not IDEMPOTENCY_KEY.fullmatch(idempotency_key):
            raise ScoutError(400, "invalid_idempotency_key", "a bounded Idempotency-Key header is required")
        try:
            brief = ScoutBrief.model_validate(body["brief"])
            split = LaneSplit.model_validate(body.get("split") or {"n_own": 10, "n_other": 10})
        except Exception as exc:
            raise ScoutError(422, "invalid_input", "brief or split failed contract validation", details=str(exc)) from exc
        if brief.data_class != bundle.data_class:
            raise ScoutError(422, "data_class_mismatch", f"this server holds {bundle.data_class} data only")
        request = {"brief": brief.model_dump(mode="json"), "split": split.model_dump(mode="json")}
        request_hash = _hash(request)
        with self._lock:
            index_path = self.root / "idempotency.json"
            index = json.loads(index_path.read_text(encoding="utf-8")) if index_path.exists() else {}
            if idempotency_key in index:
                prior = index[idempotency_key]
                if prior["request_sha256"] != request_hash:
                    raise ScoutError(409, "idempotency_conflict", "this key was used for a different request")
                return self.session(prior["session_id"]), True
            search = bundle.searches.get((brief.text, tuple(brief.own_ipc3)))
            if search is None:
                raise ScoutError(409, "not_recorded",
                                 "replay mode answers recorded briefs only; live mode is required for new briefs")
            ranked = [r["family_id"] for r in search["ranking"]]
            scores = {r["family_id"]: float(r["score"]) for r in search["ranking"]}
            family_ipc3 = {f: bundle.families[f].get("ipc3", []) for f in ranked}
            own, other = partition_by_field(ranked, family_ipc3, brief.own_ipc3)
            candidates = []
            for lane, rank, family_id in two_lane_shortlist(own, other, split.n_own, split.n_other):
                family = bundle.families[family_id]
                raw_id = family.get("representative_raw")
                candidates.append(ScoutCandidate(
                    family_id=family_id, lane=lane, rank_in_lane=rank, score=scores[family_id],
                    ipc3=list(normalize_ipc3(family.get("ipc3", []))), representative_raw=raw_id,
                    representative_canonical=None if raw_id is None else canonical_patent_id(raw_id),
                    jurisdiction=family.get("jurisdiction"), publication_date=family.get("publication_date")))
            receipt = ScoutReceipt(
                mode="replay", corpus_bundle_sha256=bundle.corpus_sha256, encoder=bundle.encoder,
                encoder_revision=bundle.encoder_revision, input_sha256=request_hash,
                output_sha256=_hash([c.model_dump(mode="json") for c in candidates]),
                encode_ms=float(search.get("encode_ms", 0)), search_ms=float(search.get("search_ms", 0)))
            session_id = uuid4().hex
            session = ScoutSession(session_id=session_id, brief=brief, split=split, candidates=candidates,
                                   receipt=receipt)
            record = {"session": session.model_dump(mode="json"), "search_id": search["search_id"],
                      "bundle_sha256": bundle.sha256}
            _atomic_write_json(self._dir(session_id) / "session.json", record)
            index[idempotency_key] = {"session_id": session_id, "request_sha256": request_hash}
            _atomic_write_json(index_path, index)
            return record["session"], False

    def _record(self, session_id: str) -> dict[str, Any]:
        return self._read(self._dir(session_id) / "session.json", "session_not_found")

    def session(self, session_id: str) -> dict[str, Any]:
        return self._record(session_id)["session"]

    def _family_in_session(self, record: dict[str, Any], family_id: str) -> None:
        if family_id not in {c["family_id"] for c in record["session"]["candidates"]}:
            raise ScoutError(404, "family_not_in_session", "family is not in this session's shortlist")

    def family(self, session_id: str, family_id: str) -> dict[str, Any]:
        record = self._record(session_id)
        self._family_in_session(record, family_id)
        family = self._require_bundle().families[family_id]
        text = family["source_text"]
        return {"family_id": family_id, "source_text": text,
                "source_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                "data_class": self._require_bundle().data_class,
                **{k: family.get(k) for k in ("ipc3", "representative_raw", "jurisdiction", "publication_date")}}

    def rationale(self, session_id: str, family_id: str) -> dict[str, Any]:
        bundle = self._require_bundle()
        with self._lock:
            record = self._record(session_id)
            self._family_in_session(record, family_id)
            path = self._dir(session_id) / "rationales" / f"{hashlib.sha256(family_id.encode()).hexdigest()}.json"
            if path.exists():
                return json.loads(path.read_text(encoding="utf-8"))
            recorded = bundle.rationales.get((record["search_id"], family_id))
            if recorded is None:
                raise ScoutError(409, "not_recorded", "no recorded rationale for this family; live mode is required")
            text = bundle.families[family_id]["source_text"]
            quotes = [check_quote(q, text) for q in recorded["quotes"]]
            rationale = TransferRationale(
                session_id=session_id, family_id=family_id,
                source_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
                model=recorded["model"], model_revision=recorded["model_revision"],
                prompt_version=recorded["prompt_version"], what_it_does=recorded["what_it_does"],
                transferable_mechanism=recorded["transferable_mechanism"], quotes=quotes,
                quote_status="all_matched" if all(q.status == "matched" for q in quotes) else "some_unmatched")
            result = {"rationale": rationale.model_dump(mode="json"),
                      "usage": {"llm_calls": 1, "prompt_tokens": int(recorded.get("prompt_tokens", 0)),
                                "output_tokens": int(recorded.get("output_tokens", 0)),
                                "latency_seconds": float(recorded.get("latency_seconds", 0)), "replayed": True}}
            _atomic_write_json(path, result)
            return result

    def decide(self, session_id: str, family_id: str, body: Any) -> dict[str, Any]:
        if not isinstance(body, dict) or set(body) - {"decision", "note"} or \
                body.get("decision") not in {"accepted", "rejected", "pending"}:
            raise ScoutError(400, "invalid_decision", "decision must be accepted, rejected or pending")
        with self._lock:
            path = self._dir(session_id) / "rationales" / f"{hashlib.sha256(family_id.encode()).hexdigest()}.json"
            if not path.exists():
                raise ScoutError(409, "rationale_not_ready", "request the rationale before deciding on it")
            result = json.loads(path.read_text(encoding="utf-8"))
            updated = TransferRationale.model_validate(result["rationale"]).model_copy(
                update={"decision": body["decision"], "note": body.get("note")})
            result["rationale"] = TransferRationale.model_validate(updated.model_dump()).model_dump(mode="json")
            _atomic_write_json(path, result)
            return result

    def receipt(self, session_id: str) -> dict[str, Any]:
        record = self._record(session_id)
        rationale_dir = self._dir(session_id) / "rationales"
        usages = [json.loads(p.read_text(encoding="utf-8"))["usage"] for p in sorted(rationale_dir.glob("*.json"))] \
            if rationale_dir.exists() else []
        return {"search": record["session"]["receipt"], "bundle_sha256": record["bundle_sha256"],
                "rationales": {"count": len(usages), "llm_calls": sum(u["llm_calls"] for u in usages),
                               "prompt_tokens": sum(u["prompt_tokens"] for u in usages),
                               "output_tokens": sum(u["output_tokens"] for u in usages),
                               "latency_seconds": round(sum(u["latency_seconds"] for u in usages), 3)},
                "paid_calls": 0}
