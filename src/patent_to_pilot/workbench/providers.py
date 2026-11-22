"""Provider ports for PTP-2026-11-21/G02: chat, embedding and rerank, configured independently.

Adapters (stdlib HTTP only, no SDK dependency):

* ``ollama``            - local Ollama server: chat (/api/chat), embedding (/api/embed); no rerank API.
* ``openai_compatible`` - any server speaking the OpenAI wire format: /models, /chat/completions, /embeddings,
                          and the common /rerank extension (vLLM, TEI, Infinity, llama.cpp server ...).
* ``anthropic_native``  - Anthropic Messages API (/v1/messages, /v1/models): chat only. Claude models are not
                          assumed to speak the OpenAI format.

Policy (checked before any socket is opened):

* Credentials are referenced by the NAME of an environment variable. The value is read at request time, sent only
  in the request header, and never stored, logged, exported or returned by any API.
* A non-loopback endpoint needs ``allow_remote`` on the profile.
* A paid route (``anthropic_native``, or ``openai_compatible`` on a non-loopback host) needs a recorded spending
  envelope (``spend_cap_usd`` > 0 and ``max_requests`` > 0). Model requests are counted against ``max_requests``.
  Token usage is recorded when the provider reports it; money is "unknown" until priced (never assumed zero).
* Nothing here downloads a model. A profile is not "usable" until its connection check passes.
* Every billable request on a paid remote route also goes through the shared budget ledger
  (``patent_to_pilot.budget.ledger``, P0-T05) that the research callers use: the request's conservative maximum cost is
  reserved in the approved envelope for its provider (scope ``workbench``, plus the profile's own cap) before the socket
  opens, then settled with the reported cost, released on an HTTP error answer, or left unknown (which pauses paid
  dispatch until reconciled) on a timeout or unreadable answer. No approved envelope, or no known price -> blocked.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, fields
import ipaddress
import json
import math
import os
import re
import socket
import time
import urllib.error
import urllib.request
from urllib.parse import urlsplit

from patent_to_pilot.budget import ledger as budget_ledger

ROLES =("chat", "embedding", "rerank")
ADAPTERS = {
    "ollama": {"roles": ("chat", "embedding"), "paid": False, "default_endpoint": "http://127.0.0.1:11434"},
    "openai_compatible": {"roles": ("chat", "embedding", "rerank"), "paid": "if_remote",
                          "default_endpoint": "http://127.0.0.1:8000/v1"},
    "anthropic_native": {"roles": ("chat",), "paid": True, "default_endpoint": "https://api.anthropic.com"},
}
ANTHROPIC_VERSION = "2023-06-01"
PROBE_SCHEMA = {"type": "object", "properties": {"ok": {"type": "boolean"}}, "required": ["ok"],
                "additionalProperties": False}
_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
_ENV = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,127}$")


class ProviderError(Exception):
    """kind: config | blocked | missing_credential | unreachable | timeout | http_status | bad_response |
    not_supported"""

    def __init__(self, kind: str, message: str) -> None:
        super().__init__(message)
        self.kind = kind


def is_loopback_url(url: str) -> bool:
    host = (urlsplit(url).hostname or "").lower()
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


REQUEST_OPTION_KEYS = {"reasoning", "temperature", "seed", "top_p", "provider"}


@dataclass
class ProviderProfile:
    profile_id: str
    role: str
    adapter: str
    model_id: str
    endpoint: str = ""
    credential_ref: str | None = None
    allow_remote: bool = False
    spend_cap_usd: float = 0.0
    max_requests: int = 0
    timeout_s: float = 60.0
    max_batch: int = 16
    query_prefix: str = ""
    document_prefix: str = ""
    dimensions: int | None = None
    label: str = ""
    request_options: dict | None = None   # extra chat-body fields for openai_compatible, e.g. OpenRouter reasoning off

    @classmethod
    def from_dict(cls, d: dict) -> "ProviderProfile":
        known = {f.name for f in fields(cls)}
        unknown = sorted(set(d) - known)
        if unknown:
            raise ProviderError("config", f"unknown profile field(s): {', '.join(unknown)}")
        p = cls(**d)
        if not p.endpoint and p.adapter in ADAPTERS:
            p.endpoint = ADAPTERS[p.adapter]["default_endpoint"]
        p.validate()
        return p

    def validate(self) -> None:
        if not isinstance(self.profile_id, str) or not _ID.match(self.profile_id):
            raise ProviderError("config", "profile_id must be 1-64 characters: letters, digits, . _ -")
        if self.adapter not in ADAPTERS:
            raise ProviderError("config", f"adapter must be one of {sorted(ADAPTERS)}")
        if self.role not in ROLES:
            raise ProviderError("config", f"role must be one of {list(ROLES)}")
        if self.role not in ADAPTERS[self.adapter]["roles"]:
            raise ProviderError("config", f"adapter {self.adapter} does not offer the {self.role} role")
        if not isinstance(self.model_id, str) or not self.model_id.strip():
            raise ProviderError("config", "model_id is required")
        parts = urlsplit(self.endpoint)
        if parts.scheme not in ("http", "https") or not parts.hostname:
            raise ProviderError("config", "endpoint must be an http(s) URL")
        if parts.username or parts.password or parts.query or parts.fragment:
            raise ProviderError("config", "endpoint must not contain credentials, a query or a fragment")
        if self.credential_ref is not None and not _ENV.match(str(self.credential_ref)):
            raise ProviderError("config", "credential_ref must be an environment variable NAME, not a key")
        if self.adapter == "anthropic_native" and not self.credential_ref:
            raise ProviderError("config", "anthropic_native needs credential_ref (e.g. ANTHROPIC_API_KEY)")
        for name, lo in (("spend_cap_usd", 0), ("max_requests", 0), ("timeout_s", 1), ("max_batch", 1)):
            v = getattr(self, name)
            if not isinstance(v, (int, float)) or isinstance(v, bool) or v < lo:
                raise ProviderError("config", f"{name} must be a number >= {lo}")
        if self.dimensions is not None and (not isinstance(self.dimensions, int) or self.dimensions < 1):
            raise ProviderError("config", "dimensions must be a positive integer or null")
        if self.role != "embedding" and (self.query_prefix or self.document_prefix or self.dimensions):
            raise ProviderError("config", "query/document prefixes and dimensions apply to embedding profiles only")
        if self.request_options is not None:
            if self.adapter != "openai_compatible" or self.role != "chat":
                raise ProviderError("config", "request_options apply to openai_compatible chat profiles only")
            if not isinstance(self.request_options, dict) or set(self.request_options) - REQUEST_OPTION_KEYS:
                raise ProviderError("config", f"request_options keys must be among {sorted(REQUEST_OPTION_KEYS)}")
            try:
                json.dumps(self.request_options)
            except (TypeError, ValueError):
                raise ProviderError("config", "request_options must be JSON") from None

    @property
    def local(self) -> bool:
        return is_loopback_url(self.endpoint)

    @property
    def paid(self) -> bool:
        flag = ADAPTERS[self.adapter]["paid"]
        return flag is True or (flag == "if_remote" and not self.local)

    def to_dict(self) -> dict:
        return asdict(self)

    def public(self) -> dict:
        """Safe to show and export: the credential is represented by its variable name and presence only."""
        d = asdict(self)
        d["credential_present"] = bool(self.credential_ref and os.environ.get(self.credential_ref))
        d["locality"] = "local" if self.local else "remote"
        d["paid_route"] = self.paid
        return d


def request_policy(profile: ProviderProfile, billable: bool, used_requests: int) -> str | None:
    """None when allowed, else the reason the request is blocked (checked before any network access)."""
    if not profile.local and not profile.allow_remote:
        return "remote endpoint not allowed for this profile (allow_remote is false)"
    if billable and profile.paid:
        if profile.spend_cap_usd <= 0 or profile.max_requests <= 0:
            return "paid route without a recorded spending envelope (spend_cap_usd and max_requests must be > 0)"
        if used_requests >= profile.max_requests:
            return f"request cap reached ({used_requests}/{profile.max_requests})"
    return None


def l2_normalize(vec: list[float]) -> list[float]:
    n = math.sqrt(sum(x * x for x in vec))
    if not math.isfinite(n) or n == 0:
        raise ProviderError("bad_response", "embedding vector is zero or not finite")
    return [x / n for x in vec]


class ProviderClient:
    """One profile, one client. ``ledger`` receives one event per network request (allowed, failed or blocked)."""

    def __init__(self, profile: ProviderProfile, ledger=None, used_requests: int = 0, budget=None) -> None:
        profile.validate()
        self.profile = profile
        self.ledger = ledger
        self.used_requests = used_requests
        self.budget = budget          # a BudgetLedger; None = the shared ledger for paid remote routes
        self.last_models: dict[str, dict] = {}

    def _budget_gate(self, billable: bool):
        if not (billable and self.profile.paid):
            return None
        if self.budget is not None:
            return self.budget
        return None if self.profile.local else budget_ledger.shared_ledger()

    # ------------------------------------------------------------------ transport
    def _credential(self) -> str | None:
        ref = self.profile.credential_ref
        if not ref:
            return None
        value = os.environ.get(ref)
        if not value:
            raise ProviderError("missing_credential", f"environment variable {ref} is not set for the server process")
        return value

    def _record(self, operation: str, billable: bool, status: str, started: float, usage=None, detail=None):
        if self.ledger is not None:
            self.ledger({"profile_id": self.profile.profile_id, "operation": operation, "billable": billable,
                         "status": status, "usage": usage, "latency_ms": round((time.monotonic() - started) * 1000, 1),
                         "detail": detail})

    def _call(self, operation: str, method: str, path: str, body: dict | None = None, billable: bool = False):
        started = time.monotonic()
        blocked = request_policy(self.profile, billable, self.used_requests)
        if blocked:
            self._record(operation, billable, "blocked", started, detail=blocked)
            raise ProviderError("blocked", blocked)
        headers = {"Accept": "application/json", "User-Agent": "ptp-workbench/G02"}
        try:
            key = self._credential()
        except ProviderError as exc:
            self._record(operation, billable, "missing_credential", started, detail=str(exc))
            raise
        if self.profile.adapter == "anthropic_native":
            headers["anthropic-version"] = ANTHROPIC_VERSION
            headers["x-api-key"] = key or ""
        elif key:
            headers["Authorization"] = "Bearer " + key
        data = None
        if body is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        url = self.profile.endpoint.rstrip("/") + path
        gate = self._budget_gate(billable)
        reservation = None
        if gate is not None:
            provider = budget_ledger.provider_for_endpoint(self.profile.endpoint)
            max_out = body.get("max_tokens") if isinstance(body, dict) else 0
            est = budget_ledger.estimate_chat_max_usd(budget_ledger.price_for(provider, self.profile.model_id),
                                                      len(data or b""), int(max_out or 0))
            try:
                reservation = gate.reserve(provider, est, scope="workbench", model=self.profile.model_id,
                                           tag=f"workbench/{self.profile.profile_id}",
                                           tag_usd_cap=float(self.profile.spend_cap_usd),
                                           tag_max_requests=int(self.profile.max_requests),
                                           detail={"operation": operation})
            except budget_ledger.BudgetRefused as exc:
                self._record(operation, billable, "blocked", started, detail=f"budget ledger: {exc}")
                raise ProviderError("blocked", f"budget ledger refused the request ({exc.reason}): {exc}") from None
        handlers = [urllib.request.ProxyHandler({})] if self.profile.local else []
        opener = urllib.request.build_opener(*handlers)
        if billable and self.profile.paid:
            self.used_requests += 1  # counted when attempted, including failures
        try:
            with opener.open(urllib.request.Request(url, data, headers, method=method),
                             timeout=self.profile.timeout_s) as r:
                raw = r.read()
        except urllib.error.HTTPError as exc:
            if reservation is not None:
                gate.release(reservation.entry_id, outcome=f"http_{exc.code}")
            snippet = exc.read()[:240].decode("utf-8", "replace")
            self._record(operation, billable, f"http_{exc.code}", started, detail=snippet)
            raise ProviderError("http_status", f"HTTP {exc.code} from {self.profile.adapter}: {snippet}") from None
        except (socket.timeout, TimeoutError):
            if reservation is not None:   # may have been billed upstream: unknown cost pauses paid dispatch
                gate.mark_unknown(reservation.entry_id, outcome="timeout")
            self._record(operation, billable, "timeout", started)
            raise ProviderError("timeout", f"no answer within {self.profile.timeout_s:g} s") from None
        except (urllib.error.URLError, ConnectionError, OSError) as exc:
            reason = getattr(exc, "reason", exc)
            if reservation is not None:
                if isinstance(reason, (ConnectionRefusedError, socket.gaierror)):
                    gate.release(reservation.entry_id, outcome="not_sent")
                else:
                    gate.mark_unknown(reservation.entry_id, outcome=f"transport:{type(reason).__name__}")
            self._record(operation, billable, "unreachable", started, detail=str(reason))
            raise ProviderError("unreachable", f"cannot reach {url}: {reason}") from None
        try:
            out = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            if reservation is not None:
                gate.mark_unknown(reservation.entry_id, outcome="bad_response")
            self._record(operation, billable, "bad_response", started)
            raise ProviderError("bad_response", "response is not JSON") from None
        usage = self._usage(out)
        if reservation is not None:
            usage = dict(usage or {})
            cost, source = usage.get("cost_usd"), "usage.cost"
            if cost is None:          # providers without a cost field: price x reported tokens, else unknown
                price = budget_ledger.price_for(budget_ledger.provider_for_endpoint(self.profile.endpoint),
                                                self.profile.model_id)
                tin = usage.get("prompt_tokens", usage.get("input_tokens"))
                tout = usage.get("completion_tokens", usage.get("output_tokens"))
                if price and isinstance(tin, int) and isinstance(tout, int):
                    cost = (tin * float(price["input"]) + tout * float(price["output"])) / 1_000_000
                    source = "computed_from_reported_tokens"
            fin = gate.settle(reservation.entry_id, cost, outcome="ok")
            usage.update({"budget_entry_id": reservation.entry_id, "budget_envelope": reservation.envelope_id,
                          "cost_source": source if fin["status"] == "settled" else "unknown"})
        self._record(operation, billable, "ok", started, usage=usage)
        return out

    def _usage(self, out) -> dict | None:
        if not isinstance(out, dict):
            return None
        u = out.get("usage")
        if isinstance(u, dict):
            d = {k: u[k] for k in ("input_tokens", "output_tokens", "prompt_tokens", "completion_tokens",
                                   "total_tokens") if isinstance(u.get(k), int)}
            if isinstance(u.get("cost"), (int, float)) and not isinstance(u.get("cost"), bool):
                d["cost_usd"] = float(u["cost"])          # OpenRouter reports the billed amount per response
            return d or None
        if "prompt_eval_count" in out or "eval_count" in out:  # Ollama
            return {"input_tokens": out.get("prompt_eval_count"), "output_tokens": out.get("eval_count")}
        return None

    # ------------------------------------------------------------------ ports
    def list_models(self) -> dict[str, dict]:
        a = self.profile.adapter
        if a == "ollama":
            out = self._call("list_models", "GET", "/api/tags")
            models = {m["name"]: {"digest": m.get("digest")} for m in out.get("models", []) if isinstance(m, dict)}
        elif a == "openai_compatible":
            out = self._call("list_models", "GET", "/models")
            models = {m["id"]: {} for m in out.get("data", []) if isinstance(m, dict) and "id" in m}
        else:
            out = self._call("list_models", "GET", "/v1/models")
            models = {m["id"]: {} for m in out.get("data", []) if isinstance(m, dict) and "id" in m}
        if not isinstance(out, dict):
            raise ProviderError("bad_response", "model list is not an object")
        self.last_models = models
        return models

    def model_entry(self) -> dict | None:
        want = self.profile.model_id
        for name in (want, want + ":latest"):
            if name in self.last_models:
                return {"name": name, **self.last_models[name]}
        return None

    def chat(self, messages: list[dict], max_tokens: int = 256, json_schema: dict | None = None,
             system: str | None = None) -> dict:
        if self.profile.role != "chat":
            raise ProviderError("not_supported", "this profile is not a chat profile")
        a, model = self.profile.adapter, self.profile.model_id
        if a == "ollama":
            msgs = ([{"role": "system", "content": system}] if system else []) + messages
            body = {"model": model, "messages": msgs, "stream": False, "options": {"num_predict": max_tokens}}
            if json_schema:
                body["format"] = json_schema
            out = self._call("chat", "POST", "/api/chat", body, billable=True)
            text = (out.get("message") or {}).get("content")
        elif a == "openai_compatible":
            msgs = ([{"role": "system", "content": system}] if system else []) + messages
            body = {**(self.profile.request_options or {}),
                    "model": model, "messages": msgs, "max_tokens": max_tokens, "stream": False}
            if json_schema:
                body["response_format"] = {"type": "json_schema",
                                           "json_schema": {"name": "ptp_output", "schema": json_schema, "strict": True}}
            out = self._call("chat", "POST", "/chat/completions", body, billable=True)
            try:
                text = out["choices"][0]["message"]["content"]
            except (KeyError, IndexError, TypeError):
                text = None
        else:
            body = {"model": model, "max_tokens": max_tokens, "messages": messages}
            if system:
                body["system"] = system
            if json_schema:  # forced tool call: the long-standing way to get schema-shaped output
                body["tools"] = [{"name": "ptp_output", "description": "Return the answer.", "input_schema": json_schema}]
                body["tool_choice"] = {"type": "tool", "name": "ptp_output"}
            out = self._call("chat", "POST", "/v1/messages", body, billable=True)
            blocks = out.get("content") if isinstance(out, dict) else None
            text = None
            if isinstance(blocks, list):
                for b in blocks:
                    if json_schema and b.get("type") == "tool_use":
                        text = json.dumps(b.get("input"), ensure_ascii=False)
                        break
                    if not json_schema and b.get("type") == "text":
                        text = b.get("text")
                        break
        if not isinstance(text, str):
            raise ProviderError("bad_response", "no text in the chat response")
        result = {"text": text, "model": model, "usage": self._usage(out)}
        if json_schema:
            try:
                result["parsed"] = json.loads(text)
            except json.JSONDecodeError:
                raise ProviderError("bad_response", "structured output is not valid JSON") from None
        return result

    def embed(self, texts: list[str], kind: str) -> list[list[float]]:
        """kind is 'query' or 'document'; the profile's prefix for that kind is prepended (part of the
        embedding-space identity). Returned vectors are L2-normalised by PTP."""
        if self.profile.role != "embedding":
            raise ProviderError("not_supported", "this profile is not an embedding profile")
        if kind not in ("query", "document"):
            raise ValueError("kind must be 'query' or 'document'")
        prefix = self.profile.query_prefix if kind == "query" else self.profile.document_prefix
        out_vecs: list[list[float]] = []
        for i in range(0, len(texts), self.profile.max_batch):
            batch = [prefix + t for t in texts[i:i + self.profile.max_batch]]
            if self.profile.adapter == "ollama":
                out = self._call("embed", "POST", "/api/embed", {"model": self.profile.model_id, "input": batch},
                                 billable=True)
                vecs = out.get("embeddings") if isinstance(out, dict) else None
            else:
                body = {"model": self.profile.model_id, "input": batch, "encoding_format": "float"}
                if self.profile.dimensions:
                    body["dimensions"] = self.profile.dimensions
                out = self._call("embed", "POST", "/embeddings", body, billable=True)
                data = out.get("data") if isinstance(out, dict) else None
                vecs = None
                if isinstance(data, list) and all(isinstance(d, dict) for d in data):
                    vecs = [d.get("embedding") for d in sorted(data, key=lambda d: d.get("index", 0))]
            if not isinstance(vecs, list) or len(vecs) != len(batch):
                raise ProviderError("bad_response", "embedding count does not match the input count")
            for v in vecs:
                if not isinstance(v, list) or not v or not all(isinstance(x, (int, float)) for x in v):
                    raise ProviderError("bad_response", "embedding is not a list of numbers")
                out_vecs.append(l2_normalize([float(x) for x in v]))
        dims = {len(v) for v in out_vecs}
        if len(dims) > 1:
            raise ProviderError("bad_response", f"inconsistent embedding dimensions {sorted(dims)}")
        if self.profile.dimensions and dims and dims != {self.profile.dimensions}:
            raise ProviderError("bad_response", f"dimension {dims.pop()} differs from the profile's {self.profile.dimensions}")
        return out_vecs

    def rerank(self, query: str, documents: list[str]) -> list[float]:
        if self.profile.role != "rerank":
            raise ProviderError("not_supported", "this profile is not a rerank profile")
        if self.profile.adapter != "openai_compatible":
            raise ProviderError("not_supported", f"{self.profile.adapter} has no rerank endpoint")
        out = self._call("rerank", "POST", "/rerank",
                         {"model": self.profile.model_id, "query": query, "documents": documents}, billable=True)
        results = out.get("results") if isinstance(out, dict) else None
        if not isinstance(results, list):
            raise ProviderError("bad_response", "rerank response has no results list")
        scores: list[float | None] = [None] * len(documents)
        for r in results:
            idx, s = r.get("index"), r.get("relevance_score", r.get("score"))
            if isinstance(idx, int) and 0 <= idx < len(documents) and isinstance(s, (int, float)) and math.isfinite(s):
                scores[idx] = float(s)
        if any(s is None for s in scores):
            raise ProviderError("bad_response", "rerank response does not score every document")
        return scores  # type: ignore[return-value]


# ---------------------------------------------------------------------- connection check
def _item(check: str, state: str, detail: str = "", **extra) -> dict:
    return {"check": check, "state": state, "detail": detail, **extra}


def connection_check(client: ProviderClient) -> dict:
    """Distinguishes reachability, model availability and the role's own capability. Every state is observed;
    nothing is assumed. States: pass | fail | blocked | not_supported | not_checked."""
    p = client.profile
    items: list[dict] = []
    facts: dict = {}
    try:
        client.list_models()
        items.append(_item("endpoint_reachable", "pass", f"{len(client.last_models)} model(s) listed"))
    except ProviderError as exc:
        state = "blocked" if exc.kind in ("blocked", "missing_credential") else "fail"
        items.append(_item("endpoint_reachable", state, str(exc)))
        return {"overall": "blocked" if state == "blocked" else "unavailable", "items": items, "facts": facts}
    entry = client.model_entry()
    if entry is None:
        items.append(_item("model_available", "fail", f"{p.model_id} is not served by this endpoint"))
        return {"overall": "unavailable", "items": items, "facts": facts}
    items.append(_item("model_available", "pass", entry["name"]))
    facts["served_model_name"] = entry["name"]
    facts["model_digest"] = entry.get("digest")

    def run(name, fn):
        try:
            return fn()
        except ProviderError as exc:
            state = {"blocked": "blocked", "missing_credential": "blocked", "not_supported": "not_supported"}.get(
                exc.kind, "fail")
            items.append(_item(name, state, str(exc)))
            return None

    required = []
    if p.role == "chat":
        required = ["chat"]
        r = run("chat", lambda: client.chat([{"role": "user", "content": "Reply with the single word OK."}],
                                            max_tokens=16))
        if r is not None:
            items.append(_item("chat", "pass" if r["text"].strip() else "fail", f"{len(r['text'])} characters"))
            items.append(_item("usage_reporting", "pass" if r["usage"] else "fail",
                               "token usage reported" if r["usage"] else "no usage in the response"))
            s = run("structured_output", lambda: client.chat(
                [{"role": "user", "content": 'Return {"ok": true} as JSON.'}], max_tokens=32, json_schema=PROBE_SCHEMA))
            if s is not None:
                ok = isinstance(s.get("parsed"), dict) and isinstance(s["parsed"].get("ok"), bool)
                items.append(_item("structured_output", "pass" if ok else "fail",
                                   "schema-shaped JSON returned" if ok else "JSON did not match the schema"))
        items.append(_item("streaming", "not_checked", "The Workbench does not stream model output yet."))
    elif p.role == "embedding":
        required = ["embedding"]
        q = run("embedding", lambda: client.embed(["PTP query probe: supported temperature range"], "query"))
        d = run("embedding", lambda: client.embed(["PTP document probe: operates from 40 to 70 °C."], "document")) \
            if q is not None else None
        if q is not None and d is not None:
            dim_q, dim_d = len(q[0]), len(d[0])
            ok = dim_q == dim_d
            facts["dimension"] = dim_q
            cos = sum(a * b for a, b in zip(q[0], d[0])) if ok else None
            items.append(_item("embedding", "pass" if ok else "fail",
                               f"query/document vectors of dimension {dim_q}/{dim_d}", cosine=None if cos is None else round(cos, 4)))
            items.append(_item("embedding_query_document_semantics", "pass",
                               f"query prefix {p.query_prefix!r}, document prefix {p.document_prefix!r} applied by PTP"))
    else:
        required = ["rerank"]
        s = run("rerank", lambda: client.rerank("supported temperature range",
                                                ["The supported temperature range is 40 to 70 °C.",
                                                 "The housing is painted blue."]))
        if s is not None:
            items.append(_item("rerank", "pass", "scores " + ", ".join(f"{x:.4f}" for x in s),
                               ordered=s[0] > s[1]))
    items.append(_item("context_limit", "not_checked", "Bounded request sizes are used; the limit is not probed."))
    states = {i["check"]: i["state"] for i in items}
    if any(states.get(r) == "blocked" for r in required):
        overall = "blocked"
    elif all(states.get(r) == "pass" for r in required):
        overall = "ready"
    else:
        overall = "failed"
    return {"overall": overall, "items": items, "facts": facts}


TEMPLATES = [
    {"profile_id": "ollama-qwen3-8b", "role": "chat", "adapter": "ollama", "model_id": "qwen3:8b",
     "label": "Local standard (Qwen3-8B via Ollama)"},
    {"profile_id": "ollama-qwen3-4b", "role": "chat", "adapter": "ollama", "model_id": "qwen3:4b",
     "label": "Local small (Qwen3-4B via Ollama)"},
    {"profile_id": "ollama-bge-m3", "role": "embedding", "adapter": "ollama", "model_id": "bge-m3",
     "label": "Local multilingual embedding (BGE-M3 via Ollama)"},
    {"profile_id": "local-qwen3-embed-0.6b", "role": "embedding", "adapter": "openai_compatible",
     "model_id": "Qwen/Qwen3-Embedding-0.6B", "endpoint": "http://127.0.0.1:8000/v1",
     "query_prefix": "Instruct: Given a requirement, retrieve passages that state it\nQuery: ",
     "label": "Local embedding server (Qwen3-Embedding-0.6B, OpenAI-compatible)"},
    {"profile_id": "local-qwen3-rerank-0.6b", "role": "rerank", "adapter": "openai_compatible",
     "model_id": "Qwen/Qwen3-Reranker-0.6B", "endpoint": "http://127.0.0.1:8000/v1",
     "label": "Local reranker (Qwen3-Reranker-0.6B, OpenAI-compatible /rerank)"},
    {"profile_id": "api-claude-haiku", "role": "chat", "adapter": "anthropic_native", "model_id": "claude-haiku-5-5",
     "credential_ref": "ANTHROPIC_API_KEY", "allow_remote": True, "label": "API economical (Claude Haiku 5.5)"},
    {"profile_id": "api-claude-sonnet", "role": "chat", "adapter": "anthropic_native",
     "model_id": "claude-sonnet-5-5", "credential_ref": "ANTHROPIC_API_KEY", "allow_remote": True,
     "label": "API stronger (Claude Sonnet 5.5)"},
    # OpenRouter (owner decisions D7/D9, envelope E1: Workbench checks <= USD 0.20 in total, so 0.05 and 20 requests
    # each). Reasoning is switched off so thinking tokens are never billed.
    {"profile_id": "openrouter-qwen3-7-flash", "role": "chat", "adapter": "openai_compatible", "model_id": "qwen/qwen3.7-flash",
     "endpoint": "https://openrouter.ai/api/v1", "credential_ref": "OPENROUTER_API_KEY", "allow_remote": True,
     "spend_cap_usd": 0.05, "max_requests": 20, "request_options": {"reasoning": {"enabled": False}, "temperature": 0},
     "label": "OpenRouter Qwen3.7 Flash (cheapest)"},
    {"profile_id": "openrouter-deepseek-v4-flash", "role": "chat", "adapter": "openai_compatible", "model_id": "deepseek/deepseek-v4-flash-0731",
     "endpoint": "https://openrouter.ai/api/v1", "credential_ref": "OPENROUTER_API_KEY", "allow_remote": True,
     "spend_cap_usd": 0.05, "max_requests": 20, "request_options": {"reasoning": {"effort": "none"}, "temperature": 0},
     "label": "OpenRouter DeepSeek V4 Flash"},
    {"profile_id": "openrouter-qwen3-32b", "role": "chat", "adapter": "openai_compatible", "model_id": "qwen/qwen3-32b",
     "endpoint": "https://openrouter.ai/api/v1", "credential_ref": "OPENROUTER_API_KEY", "allow_remote": True,
     "spend_cap_usd": 0.05, "max_requests": 20, "request_options": {"reasoning": {"enabled": False}, "temperature": 0},
     "label": "OpenRouter Qwen3-32B (open weights)"},
    {"profile_id": "openrouter-claude-haiku-5-5", "role": "chat", "adapter": "openai_compatible", "model_id": "anthropic/claude-haiku-5.5",
     "endpoint": "https://openrouter.ai/api/v1", "credential_ref": "OPENROUTER_API_KEY", "allow_remote": True,
     "spend_cap_usd": 0.05, "max_requests": 20, "request_options": {"reasoning": {"effort": "none"}, "temperature": 0},
     "label": "OpenRouter Claude Haiku 5.5"},
]
