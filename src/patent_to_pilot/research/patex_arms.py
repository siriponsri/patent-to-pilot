"""Paper 2 (P2-OA) prototype: PatEx-style actions and budget-matched arms.

Runtime only. This module never sees reference labels (K): it does not import the
evaluator (``funnel_eval``), and a ``Query`` carries only an id and its text.
Backends and the solver LLM are injected; nothing here loads a model, opens a
corpus or touches a GPU.

Actions: ``SEARCH(query, method, top_n)``, ``VISIT(id, fields)``,
``SELECT(id, passage_locations)``, ``STOP``. Every action has a *declared* cost,
is admitted against one hard per-query budget before it runs, and logs its
observation (returned ids, versions, excerpt bytes, tokens, declared seconds).
A refused action is recorded, never retried, and ends the episode.

Funnel order is enforced at runtime: VISIT needs an id returned by a SEARCH,
SELECT needs a visited id and a visited field. So Select ⊆ Visit ⊆ Search.

Arms (all share the same environment, tools and budget object):

* ``E0``      fixed retrieval: one SEARCH, then a declared fixed visit/select policy.
* ``E0-deep`` one deep SEARCH (pool 500-1,000) + a fixed reranker hook.
* ``E1``      fixed multi-query schedule of pre-declared query templates, RRF-fused.
* ``E3``      claim-element deficit-aware search (CEDS): split the claim into
              elements; each move targets the least-covered element (element
              query, function reformulation, CPC hop, citation hop). Coverage needs
              a visited, source-located passage with a mechanically matched quote.
* ``E2``      ReAct agent: an injected LLM chooses actions under a strict JSON
              schema. An invalid action stops the agent; it falls back to an
              injected fixed arm (E0), and the fallback cost is reported separately.

Trajectories are deterministic: no timestamps, no measured time; query text,
LLM output, excerpts and quotes are stored as hashes only.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping, Protocol, Sequence

from patent_to_pilot.research.acquisition_harness import BudgetRefused, canonical_sha256, rrf_fuse

SCHEMA_VERSION = "ptp-paper2-patex-arms-v0"

METHODS = ("dense", "bm25", "hybrid")
BACKEND_METHODS = ("dense", "bm25")
FIELDS = ("title", "abstract", "claims", "description")
ACTIONS = ("SEARCH", "VISIT", "SELECT", "STOP")
RELATIONS = ("cpc", "citation")
STAGES = ("search", "visit", "select")

STOP_SCHEDULE_COMPLETE = "SCHEDULE_COMPLETE"
STOP_AGENT_STOP = "AGENT_STOP"
STOP_BUDGET_REFUSED = "BUDGET_REFUSED"
STOP_INVALID_ACTION = "INVALID_ACTION"
STOP_MAX_STEPS = "MAX_STEPS"
STOP_EMPTY_SEARCH = "EMPTY_SEARCH"
STOP_ALL_COVERED = "ALL_COVERED"
STOP_MOVES_EXHAUSTED = "MOVES_EXHAUSTED"

RANKING_OWN = "OWN"
RANKING_FALLBACK = "FALLBACK"


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Costs and budget
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ActionCost:
    actions: int = 0
    llm_calls: int = 0
    tokens: int = 0
    returned_ids: int = 0
    visits: int = 0
    selects: int = 0
    observation_bytes: int = 0
    rerank_docs: int = 0
    cpu_seconds: float = 0.0
    gpu_seconds: float = 0.0
    wall_seconds: float = 0.0
    usd: float = 0.0

    def __post_init__(self) -> None:
        for name, value in asdict(self).items():
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise TypeError(f"cost field {name} must be numeric")
            if value != value or value < 0 or value == float("inf"):
                raise ValueError(f"cost field {name} must be finite and >= 0")

    def __add__(self, other: "ActionCost") -> "ActionCost":
        return ActionCost(**{k: getattr(self, k) + getattr(other, k) for k in asdict(self)})

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


ZERO = ActionCost()


@dataclass(frozen=True)
class ArmBudget:
    """One hard per-query budget shared by every arm. ``None`` = uncapped."""

    max_actions: int
    max_llm_calls: int
    max_tokens: int
    max_wall_seconds: float
    max_returned_ids: int | None = None
    max_visits: int | None = None
    max_selects: int | None = None
    max_observation_bytes: int | None = None
    max_rerank_docs: int | None = None
    max_usd: float | None = None

    def __post_init__(self) -> None:
        for name in ("max_actions", "max_llm_calls", "max_tokens"):
            v = getattr(self, name)
            if isinstance(v, bool) or not isinstance(v, int) or v < 0:
                raise ValueError(f"{name} must be a non-negative int")
        if not (self.max_wall_seconds >= 0):
            raise ValueError("max_wall_seconds must be >= 0")

    def limits(self) -> dict[str, float | int]:
        caps = {
            "actions": self.max_actions, "llm_calls": self.max_llm_calls, "tokens": self.max_tokens,
            "wall_seconds": self.max_wall_seconds, "returned_ids": self.max_returned_ids,
            "visits": self.max_visits, "selects": self.max_selects,
            "observation_bytes": self.max_observation_bytes, "rerank_docs": self.max_rerank_docs,
            "usd": self.max_usd,
        }
        return {k: v for k, v in caps.items() if v is not None}

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class Ledger:
    def __init__(self, budget: ArmBudget):
        self.budget = budget
        self.spent = ZERO
        self.refusals: list[dict[str, Any]] = []

    def admit(self, what: str, cost: ActionCost) -> None:
        after = self.spent + cost
        exceeded = [k for k, cap in self.budget.limits().items() if getattr(after, k) > cap]
        if exceeded:
            self.refusals.append({"what": what, "declared_cost": cost.to_dict(), "exceeded": exceeded})
            raise BudgetRefused(exceeded)
        self.spent = after


# ---------------------------------------------------------------------------
# Environment (injected document store + declared costs)
# ---------------------------------------------------------------------------


class DocumentStore(Protocol):
    """Injected, deterministic store. ``search`` serves BACKEND_METHODS only."""

    def search(self, method: str, query: str, top_n: int) -> Sequence[str]: ...

    def version(self, doc_id: str) -> str | None: ...

    def field_text(self, doc_id: str, field_name: str) -> str | None: ...

    # Optional, used only by EXPAND (CPC / citation hops):
    # def neighbours(self, doc_id: str, relation: str, top_n: int) -> Sequence[str]: ...


CostFn = Callable[[Mapping[str, Any]], ActionCost]


def default_patex_cost_model(*, max_visit_bytes: int) -> dict[str, CostFn]:
    """Illustrative declared costs. A real study must freeze measured values."""

    search_seconds = {"dense": 0.1, "bm25": 0.05, "hybrid": 0.15}

    def search(a: Mapping[str, Any]) -> ActionCost:
        s = search_seconds[a["method"]]
        gpu = 0.05 if a["method"] in ("dense", "hybrid") else 0.0
        return ActionCost(actions=1, returned_ids=a["top_n"], gpu_seconds=gpu, cpu_seconds=0.02, wall_seconds=s)

    return {
        "SEARCH": search,
        "VISIT": lambda a: ActionCost(actions=1, visits=1, observation_bytes=max_visit_bytes * len(a["fields"]),
                                      cpu_seconds=0.01, wall_seconds=0.01),
        "SELECT": lambda a: ActionCost(actions=1, selects=1, cpu_seconds=0.001, wall_seconds=0.001),
        "RERANK": lambda a: ActionCost(actions=1, rerank_docs=a["n"], gpu_seconds=0.002 * a["n"],
                                       wall_seconds=0.002 * a["n"]),
        "EXPAND": lambda a: ActionCost(actions=1, returned_ids=a["top_n"], cpu_seconds=0.01, wall_seconds=0.02),
    }


def whitespace_token_counter(text: str) -> int:
    """Stand-in counter. Not a real tokenizer."""

    return len(text.split())


def _truncate_utf8(text: str, max_bytes: int) -> str:
    data = text.encode("utf-8")
    if len(data) <= max_bytes:
        return text
    return data[:max_bytes].decode("utf-8", errors="ignore")


def _dedupe(ids: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for i in ids:
        if not isinstance(i, str) or not i:
            raise ValueError("document ids must be non-empty strings")
        if i not in seen:
            seen.add(i)
            out.append(i)
    return out


class PatexEnv:
    def __init__(self, store: DocumentStore, cost_model: Mapping[str, CostFn], *, max_top_n: int = 1000,
                 max_visit_bytes: int = 4000, token_counter: Callable[[str], int] = whitespace_token_counter,
                 methods: Sequence[str] = METHODS):
        missing = [a for a in ("SEARCH", "VISIT", "SELECT", "RERANK") if a not in cost_model]
        if missing:
            raise ValueError(f"cost model lacks actions: {missing}")
        bad = [m for m in methods if m not in METHODS]
        if bad or not methods:
            raise ValueError(f"unknown methods: {bad}")
        self.store, self.cost_model = store, cost_model
        self.max_top_n, self.max_visit_bytes = max_top_n, max_visit_bytes
        self.token_counter, self.methods = token_counter, tuple(methods)

    def declared_cost(self, action: str, args: Mapping[str, Any]) -> ActionCost:
        cost = self.cost_model[action](args)
        if cost.actions < 1:
            raise ValueError(f"declared cost of {action} must count one action")
        return cost

    def run_search(self, method: str, query: str, top_n: int) -> list[str]:
        if method == "hybrid":
            lists = [_dedupe(self.store.search(m, query, top_n)) for m in BACKEND_METHODS]
            ids = rrf_fuse(lists, pool_size=top_n) if any(lists) else []
        else:
            ids = _dedupe(self.store.search(method, query, top_n))
        return ids[:top_n]


# ---------------------------------------------------------------------------
# Solver (injected LLM)
# ---------------------------------------------------------------------------

LLMCallable = Callable[[list[dict[str, str]], int], str]


@dataclass(frozen=True)
class SolverSpec:
    llm: LLMCallable
    token_counter: Callable[[str], int]
    max_output_tokens: int
    seconds_per_call: float = 0.0
    usd_per_1k_tokens: float = 0.0

    def declared_cost(self, messages: list[dict[str, str]]) -> ActionCost:
        tokens = sum(self.token_counter(m["content"]) for m in messages) + self.max_output_tokens
        return ActionCost(llm_calls=1, tokens=tokens, gpu_seconds=self.seconds_per_call,
                          wall_seconds=self.seconds_per_call, usd=tokens * self.usd_per_1k_tokens / 1000.0)


# ---------------------------------------------------------------------------
# Trajectory and episode state
# ---------------------------------------------------------------------------


class Trajectory:
    def __init__(self, query_id: str, arm: str):
        self.query_id, self.arm = query_id, arm
        self.records: list[dict[str, Any]] = []

    def log(self, event: str, **fields: Any) -> None:
        rec = {"schema": SCHEMA_VERSION, "query_id": self.query_id, "arm": self.arm,
               "seq": len(self.records), "event": event}
        rec.update(fields)
        self.records.append(rec)

    def lines(self) -> list[str]:
        return [json.dumps(r, sort_keys=True, ensure_ascii=False) for r in self.records]

    def write(self, path: Path) -> str:
        data = ("\n".join(self.lines()) + "\n").encode("utf-8")
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "xb") as handle:  # never overwrite
            handle.write(data)
        return hashlib.sha256(data).hexdigest()


class InvalidAction(Exception):
    pass


@dataclass(frozen=True)
class Query:
    """Runtime query: id and text only. Reference labels never travel with it."""

    query_id: str
    text: str


class _Episode:
    def __init__(self, env: PatexEnv, budget: ArmBudget, query: Query, arm: str, max_locations: int = 5):
        self.env, self.query = env, query
        self.ledger = Ledger(budget)
        self.traj = Trajectory(query.query_id, arm)
        self.max_locations = max_locations
        self.lists: list[tuple[str, ...]] = []
        self.searched: dict[str, str] = {}
        self.visited: dict[str, str] = {}
        self.visited_fields: dict[str, set[str]] = {}
        self.visible_bytes: dict[tuple[str, str], int] = {}
        self.selections: list[dict[str, Any]] = []
        self.excerpts: dict[str, dict[str, str]] = {}

    # -- accounting
    def _admit(self, action: str, args_log: Mapping[str, Any], cost: ActionCost) -> bool:
        try:
            self.ledger.admit(action, cost)
        except BudgetRefused as exc:
            self.traj.log("refused", action=action, args=dict(args_log), declared_cost=cost.to_dict(),
                          exceeded=list(exc.exceeded), cumulative_cost=self.ledger.spent.to_dict())
            return False
        return True

    def call_llm(self, solver: SolverSpec, purpose: str, messages: list[dict[str, str]]) -> str | None:
        cost = solver.declared_cost(messages)
        if not self._admit("LLM:" + purpose, {"prompt_sha256": canonical_sha256(messages)}, cost):
            return None
        raw = solver.llm(messages, solver.max_output_tokens)
        raw = raw if isinstance(raw, str) else ""
        self.traj.log("llm", purpose=purpose, declared_cost=cost.to_dict(),
                      prompt_sha256=canonical_sha256(messages), output_sha256=_sha(raw),
                      output_tokens_counted=solver.token_counter(raw),
                      cumulative_cost=self.ledger.spent.to_dict())
        return raw

    # -- actions
    def search(self, query_text: str, method: str, top_n: int) -> list[str] | None:
        if method not in self.env.methods:
            raise InvalidAction("BAD_METHOD")
        if isinstance(top_n, bool) or not isinstance(top_n, int) or not (1 <= top_n <= self.env.max_top_n):
            raise InvalidAction("BAD_TOP_N")
        args = {"query": query_text, "method": method, "top_n": top_n}
        log_args = {"query_sha256": _sha(query_text), "method": method, "top_n": top_n}
        cost = self.env.declared_cost("SEARCH", args)
        if not self._admit("SEARCH", log_args, cost):
            return None
        ids = self.env.run_search(method, query_text, top_n)
        versions = []
        for i in ids:
            v = self.env.store.version(i)
            if v is None:
                raise ValueError(f"backend returned unknown document {i}")
            versions.append(v)
            self.searched.setdefault(i, v)
        self.lists.append(tuple(ids))
        self.traj.log("observation", action="SEARCH", args=log_args, declared_cost=cost.to_dict(),
                      declared_seconds=cost.wall_seconds, returned_ids=list(ids), versions=versions,
                      returned_count=len(ids), cumulative_cost=self.ledger.spent.to_dict())
        return ids

    def visit(self, doc_id: str, fields: Sequence[str]) -> dict[str, Any] | None:
        if doc_id not in self.searched:
            raise InvalidAction("UNSEARCHED_ID")
        if (not isinstance(fields, (list, tuple)) or not fields or len(set(fields)) != len(fields)
                or any(f not in FIELDS for f in fields)):
            raise InvalidAction("BAD_FIELDS")
        args = {"id": doc_id, "fields": list(fields)}
        cost = self.env.declared_cost("VISIT", args)
        if not self._admit("VISIT", args, cost):
            return None
        version = self.env.store.version(doc_id)
        excerpts: dict[str, str] = {}
        per_field: dict[str, Any] = {}
        for f in fields:
            full = self.env.store.field_text(doc_id, f)
            if full is None:
                per_field[f] = {"missing": True, "bytes": 0, "full_bytes": 0, "sha256": None, "tokens": 0}
                continue
            ex = _truncate_utf8(full, self.env.max_visit_bytes)
            nb = len(ex.encode("utf-8"))
            excerpts[f] = ex
            self.excerpts.setdefault(doc_id, {})[f] = ex
            per_field[f] = {"missing": False, "bytes": nb, "full_bytes": len(full.encode("utf-8")),
                            "sha256": _sha(ex), "tokens": self.env.token_counter(ex)}
            self.visible_bytes[(doc_id, f)] = max(self.visible_bytes.get((doc_id, f), 0), nb)
            self.visited_fields.setdefault(doc_id, set()).add(f)
        self.visited.setdefault(doc_id, version or "")
        self.visited_fields.setdefault(doc_id, set())
        self.traj.log("observation", action="VISIT", args=args, declared_cost=cost.to_dict(),
                      declared_seconds=cost.wall_seconds, id=doc_id, version=version, fields=per_field,
                      excerpt_bytes=sum(v["bytes"] for v in per_field.values()),
                      observation_tokens=sum(v["tokens"] for v in per_field.values()),
                      cumulative_cost=self.ledger.spent.to_dict())
        return {"id": doc_id, "version": version, "fields": excerpts}

    def _check_locations(self, doc_id: str, locs: Any) -> list[dict[str, Any]]:
        if not isinstance(locs, list) or not (1 <= len(locs) <= self.max_locations):
            raise InvalidAction("BAD_LOCATIONS")
        out = []
        for loc in locs:
            if not isinstance(loc, dict) or not ({"field", "start", "end"} <= set(loc) <= {"field", "start", "end", "quote"}):
                raise InvalidAction("BAD_LOCATIONS")
            f, s, e = loc["field"], loc["start"], loc["end"]
            if f not in self.visited_fields.get(doc_id, set()):
                raise InvalidAction("BAD_LOCATIONS")
            if any(isinstance(x, bool) or not isinstance(x, int) for x in (s, e)) or not (0 <= s < e):
                raise InvalidAction("BAD_LOCATIONS")
            if "quote" in loc and not isinstance(loc["quote"], str):
                raise InvalidAction("BAD_LOCATIONS")
            out.append(dict(loc))
        return out

    def select(self, doc_id: str, locations: Any) -> dict[str, Any] | None:
        if doc_id not in self.visited:
            raise InvalidAction("UNVISITED_ID")
        if any(s["doc_id"] == doc_id for s in self.selections):
            raise InvalidAction("ALREADY_SELECTED")
        locs = self._check_locations(doc_id, locations)
        log_locs = [{"field": l["field"], "start": l["start"], "end": l["end"],
                     "quote_sha256": _sha(l["quote"]) if "quote" in l else None} for l in locs]
        args = {"id": doc_id, "passage_locations": log_locs}
        cost = self.env.declared_cost("SELECT", args)
        if not self._admit("SELECT", args, cost):
            return None
        sel = {"doc_id": doc_id, "version": self.visited[doc_id], "locations": locs}
        self.selections.append(sel)
        self.traj.log("observation", action="SELECT", args=args, declared_cost=cost.to_dict(),
                      declared_seconds=cost.wall_seconds, id=doc_id, version=sel["version"],
                      cumulative_cost=self.ledger.spent.to_dict())
        return sel

    def expand(self, doc_id: str, relation: str, top_n: int) -> list[str] | None:
        """CPC or citation hop from a visited document. Returned ids count as Search."""

        if doc_id not in self.visited:
            raise InvalidAction("UNVISITED_ID")
        if relation not in RELATIONS:
            raise InvalidAction("BAD_RELATION")
        if isinstance(top_n, bool) or not isinstance(top_n, int) or not (1 <= top_n <= self.env.max_top_n):
            raise InvalidAction("BAD_TOP_N")
        if "EXPAND" not in self.env.cost_model or not hasattr(self.env.store, "neighbours"):
            raise ValueError("EXPAND needs a declared cost and store.neighbours")
        args = {"id": doc_id, "relation": relation, "top_n": top_n}
        cost = self.env.declared_cost("EXPAND", args)
        if not self._admit("EXPAND", args, cost):
            return None
        ids = _dedupe(self.env.store.neighbours(doc_id, relation, top_n))[:top_n]
        versions = []
        for i in ids:
            v = self.env.store.version(i)
            if v is None:
                raise ValueError(f"backend returned unknown document {i}")
            versions.append(v)
            self.searched.setdefault(i, v)
        if ids:
            self.lists.append(tuple(ids))
        self.traj.log("observation", action="EXPAND", args=args, declared_cost=cost.to_dict(),
                      declared_seconds=cost.wall_seconds, returned_ids=list(ids), versions=versions,
                      returned_count=len(ids), cumulative_cost=self.ledger.spent.to_dict())
        return ids

    def rerank(self, reranker: Callable[[str, Sequence[str]], Sequence[str]], ids: Sequence[str]) -> list[str] | None:
        args = {"n": len(ids)}
        cost = self.env.declared_cost("RERANK", args)
        if not self._admit("RERANK", {"n": len(ids), "input_sha256": canonical_sha256(list(ids))}, cost):
            return None
        out = list(reranker(self.query.text, list(ids)))
        if sorted(out) != sorted(ids):
            raise ValueError("reranker must return a permutation of its input")
        self.traj.log("observation", action="RERANK", declared_cost=cost.to_dict(),
                      declared_seconds=cost.wall_seconds, input_sha256=canonical_sha256(list(ids)),
                      output_ids=out, cumulative_cost=self.ledger.spent.to_dict())
        return out

    # -- result
    def final_ranking(self, pool_size: int) -> list[str]:
        selected = [s["doc_id"] for s in self.selections]
        rest: list[str] = []
        if self.lists:
            rest = rrf_fuse(self.lists, pool_size=max(1, len(self.searched)))
        ordered = selected + [d for d in rest if d not in set(selected)]
        return ordered[:pool_size]


@dataclass
class ArmResult:
    query_id: str
    arm: str
    ranking: list[str]
    ranking_source: str
    stop_reason: str
    stages_run: tuple[str, ...]
    searched: tuple[str, ...]
    visited: tuple[str, ...]
    selections: tuple[dict[str, Any], ...]
    cost: ActionCost
    fallback_cost: ActionCost
    refusals: list[dict[str, Any]]
    trajectory: Trajectory = field(repr=False)
    extras: dict[str, Any] = field(default_factory=dict)

    def funnel_record(self) -> dict[str, Any]:
        """Plain data for the evaluator (contains quotes; keep private)."""

        return {"query_id": self.query_id, "arm": self.arm, "stages_run": list(self.stages_run),
                "searched": list(self.searched), "visited": list(self.visited),
                "selections": [json.loads(json.dumps(s)) for s in self.selections],
                "ranking": list(self.ranking), "ranking_source": self.ranking_source}

    def summary(self) -> dict[str, Any]:
        return {"query_id": self.query_id, "arm": self.arm, "ranking_size": len(self.ranking),
                "ranking_sha256": canonical_sha256(self.ranking), "ranking_source": self.ranking_source,
                "stop_reason": self.stop_reason, "stages_run": list(self.stages_run),
                "searched": len(self.searched), "visited": len(self.visited), "selected": len(self.selections),
                "cost": self.cost.to_dict(), "fallback_cost": self.fallback_cost.to_dict(),
                "refusals": len(self.refusals), "trajectory_sha256": canonical_sha256(self.trajectory.records),
                **({"extras": self.extras} if self.extras else {})}


def _finish(ep: _Episode, arm: str, stop: str, stages: Sequence[str], pool_size: int) -> ArmResult:
    ranking = ep.final_ranking(pool_size)
    ep.traj.log("stop", stop_reason=stop, ranking_source=RANKING_OWN, ranking_sha256=canonical_sha256(ranking),
                ranking_size=len(ranking), searched=len(ep.searched), visited=len(ep.visited),
                selected=len(ep.selections), cumulative_cost=ep.ledger.spent.to_dict())
    return ArmResult(ep.query.query_id, arm, ranking, RANKING_OWN, stop, tuple(stages), tuple(ep.searched),
                     tuple(ep.visited), tuple(ep.selections), ep.ledger.spent, ZERO, list(ep.ledger.refusals),
                     ep.traj)


# ---------------------------------------------------------------------------
# Fixed arms
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FixedFunnelPolicy:
    """Declared visit/select policy for fixed arms (0 = stage not run)."""

    visit_top: int = 0
    select_top: int = 0
    visit_fields: tuple[str, ...] = ("abstract",)
    select_field: str = "abstract"

    def __post_init__(self) -> None:
        if not (0 <= self.select_top <= self.visit_top):
            raise ValueError("need 0 <= select_top <= visit_top")
        if not self.visit_fields or any(f not in FIELDS for f in self.visit_fields):
            raise ValueError("bad visit_fields")
        if self.select_top and self.select_field not in self.visit_fields:
            raise ValueError("select_field must be a visited field")

    def stages(self) -> tuple[str, ...]:
        return ("search",) + (("visit",) if self.visit_top else ()) + (("select",) if self.select_top else ())

    def actions(self) -> int:
        return self.visit_top + self.select_top


def _run_fixed_funnel(ep: _Episode, ranking: Sequence[str], policy: FixedFunnelPolicy) -> bool:
    for doc in list(ranking)[: policy.visit_top]:
        if ep.visit(doc, list(policy.visit_fields)) is None:
            return False
    for doc in list(ranking)[: policy.select_top]:
        nb = ep.visible_bytes.get((doc, policy.select_field), 0)
        if nb == 0:
            ep.traj.log("skipped", action="SELECT", id=doc, reason="FIELD_EMPTY")
            continue
        if ep.select(doc, [{"field": policy.select_field, "start": 0, "end": nb}]) is None:
            return False
    return True


class _ArmBase:
    arm_id = ""

    def __init__(self, env: PatexEnv, budget: ArmBudget, *, pool_size: int):
        if pool_size < 1:
            raise ValueError("pool_size must be >= 1")
        self.env, self.budget, self.pool_size = env, budget, pool_size

    def _check_planned(self, actions: int, llm_calls: int = 0) -> None:
        if actions > self.budget.max_actions or llm_calls > self.budget.max_llm_calls:
            raise ValueError(f"{self.arm_id} schedule exceeds the shared budget")

    def _start(self, query: Query, **cfg: Any) -> _Episode:
        ep = _Episode(self.env, self.budget, query, self.arm_id)
        ep.traj.log("start", budget=self.budget.to_dict(), pool_size=self.pool_size,
                    config_sha256=canonical_sha256(cfg))
        return ep


class FixedRetrievalArm(_ArmBase):
    """E0: one SEARCH with a declared method and top_n, then a fixed funnel policy."""

    arm_id = "E0"

    def __init__(self, env: PatexEnv, budget: ArmBudget, *, method: str, top_n: int, pool_size: int,
                 policy: FixedFunnelPolicy = FixedFunnelPolicy()):
        super().__init__(env, budget, pool_size=pool_size)
        if method not in env.methods or not (1 <= top_n <= env.max_top_n):
            raise ValueError("bad E0 method/top_n")
        self.method, self.top_n, self.policy = method, top_n, policy
        self._check_planned(1 + policy.actions())

    def run(self, query: Query) -> ArmResult:
        ep = self._start(query, method=self.method, top_n=self.top_n, policy=asdict(self.policy))
        ids = ep.search(query.text, self.method, self.top_n)
        stop = STOP_SCHEDULE_COMPLETE
        if ids is None or not _run_fixed_funnel(ep, ids, self.policy):
            stop = STOP_BUDGET_REFUSED
        return _finish(ep, self.arm_id, stop, self.policy.stages(), self.pool_size)


Reranker = Callable[[str, Sequence[str]], Sequence[str]]


class DeepRetrievalArm(_ArmBase):
    """E0-deep: a deep SEARCH, a fixed reranker hook on the top ``rerank_top``, then the funnel."""

    arm_id = "E0-deep"

    def __init__(self, env: PatexEnv, budget: ArmBudget, *, method: str, top_n: int, reranker: Reranker,
                 rerank_top: int, pool_size: int, policy: FixedFunnelPolicy = FixedFunnelPolicy()):
        super().__init__(env, budget, pool_size=pool_size)
        if method not in env.methods or not (1 <= top_n <= env.max_top_n) or not (1 <= rerank_top <= top_n):
            raise ValueError("bad E0-deep configuration")
        self.method, self.top_n, self.reranker, self.rerank_top, self.policy = method, top_n, reranker, rerank_top, policy
        self._check_planned(2 + policy.actions())

    def run(self, query: Query) -> ArmResult:
        ep = self._start(query, method=self.method, top_n=self.top_n, rerank_top=self.rerank_top,
                         policy=asdict(self.policy))
        stop = STOP_SCHEDULE_COMPLETE
        ids = ep.search(query.text, self.method, self.top_n)
        if ids is None:
            return _finish(ep, self.arm_id, STOP_BUDGET_REFUSED, self.policy.stages(), self.pool_size)
        head = ep.rerank(self.reranker, ids[: self.rerank_top]) if ids else []
        if head is None:
            return _finish(ep, self.arm_id, STOP_BUDGET_REFUSED, self.policy.stages(), self.pool_size)
        ordered = head + ids[self.rerank_top:]
        ep.lists = [tuple(ordered)]  # the reranked order replaces the raw search order
        if not _run_fixed_funnel(ep, ordered, self.policy):
            stop = STOP_BUDGET_REFUSED
        return _finish(ep, self.arm_id, stop, self.policy.stages(), self.pool_size)


@dataclass(frozen=True)
class QueryTemplate:
    """Pre-declared query template for E1. ``source``: 'original' or 'llm'."""

    name: str
    method: str
    top_n: int
    source: str = "original"
    instruction: str = ""

    def __post_init__(self) -> None:
        if self.source not in ("original", "llm"):
            raise ValueError("source must be 'original' or 'llm'")
        if self.source == "llm" and not self.instruction:
            raise ValueError("llm template needs an instruction")


class MultiQueryArm(_ArmBase):
    """E1: fixed multi-query schedule, RRF-fused, then the fixed funnel policy."""

    arm_id = "E1"

    def __init__(self, env: PatexEnv, budget: ArmBudget, templates: Sequence[QueryTemplate], *, pool_size: int,
                 solver: SolverSpec | None = None, policy: FixedFunnelPolicy = FixedFunnelPolicy()):
        super().__init__(env, budget, pool_size=pool_size)
        if not templates or len({t.name for t in templates}) != len(templates):
            raise ValueError("E1 needs uniquely named templates")
        for t in templates:
            if t.method not in env.methods or not (1 <= t.top_n <= env.max_top_n):
                raise ValueError(f"bad template {t.name}")
        n_llm = sum(t.source == "llm" for t in templates)
        if n_llm and solver is None:
            raise ValueError("llm templates need a SolverSpec")
        self.templates, self.solver, self.policy = tuple(templates), solver, policy
        self._check_planned(len(templates) + policy.actions(), n_llm)

    def run(self, query: Query) -> ArmResult:
        ep = self._start(query, templates=[asdict(t) for t in self.templates], policy=asdict(self.policy))
        stop = STOP_SCHEDULE_COMPLETE
        for t in self.templates:
            text = query.text
            if t.source == "llm":
                msgs = [{"role": "system", "content": t.instruction}, {"role": "user", "content": query.text}]
                out = ep.call_llm(self.solver, "template:" + t.name, msgs)
                if out is None:
                    stop = STOP_BUDGET_REFUSED
                    break
                if out.strip():
                    text = out.strip()
                else:
                    ep.traj.log("template_empty_used_original", template=t.name)
            if ep.search(text, t.method, t.top_n) is None:
                stop = STOP_BUDGET_REFUSED
                break
        if stop == STOP_SCHEDULE_COMPLETE:
            fused = ep.final_ranking(max(1, len(ep.searched))) if ep.searched else []
            if not _run_fixed_funnel(ep, fused, self.policy):
                stop = STOP_BUDGET_REFUSED
        return _finish(ep, self.arm_id, stop, self.policy.stages(), self.pool_size)


# ---------------------------------------------------------------------------
# E2: ReAct agent
# ---------------------------------------------------------------------------


_REQUIRED = {
    "SEARCH": {"query", "method", "top_n"},
    "VISIT": {"id", "fields"},
    "SELECT": {"id", "passage_locations"},
    "STOP": set(),
}


def patex_action_schema(*, methods: Sequence[str], max_top_n: int, max_query_chars: int,
                        max_locations: int) -> dict[str, Any]:
    """Schema shown to the solver. ``parse_patex_action`` is the authority."""

    loc = {"type": "object", "additionalProperties": False, "required": ["field", "start", "end"],
           "properties": {"field": {"enum": list(FIELDS)}, "start": {"type": "integer", "minimum": 0},
                          "end": {"type": "integer", "minimum": 1}, "quote": {"type": "string"}}}
    return {
        "type": "object", "additionalProperties": False, "required": ["action", "args"],
        "properties": {
            "action": {"enum": list(ACTIONS)},
            "args": {"type": "object", "additionalProperties": False, "properties": {
                "query": {"type": "string", "minLength": 1, "maxLength": max_query_chars},
                "method": {"enum": list(methods)},
                "top_n": {"type": "integer", "minimum": 1, "maximum": max_top_n},
                "id": {"type": "string"},
                "fields": {"type": "array", "items": {"enum": list(FIELDS)}, "minItems": 1},
                "passage_locations": {"type": "array", "items": loc, "minItems": 1, "maxItems": max_locations},
            }},
        },
    }


def parse_patex_action(raw: str, *, methods: Sequence[str], max_top_n: int,
                       max_query_chars: int) -> tuple[str, dict[str, Any]]:
    """Strict static parse; no repair. State checks happen in the episode."""

    try:
        obj = json.loads(raw, parse_constant=lambda c: (_ for _ in ()).throw(ValueError(c)))
    except (ValueError, TypeError) as exc:
        raise InvalidAction("NOT_JSON") from exc
    if not isinstance(obj, dict) or set(obj) != {"action", "args"}:
        raise InvalidAction("BAD_ENVELOPE")
    action, args = obj["action"], obj["args"]
    if action not in ACTIONS:
        raise InvalidAction("UNKNOWN_ACTION")
    if not isinstance(args, dict) or set(args) != _REQUIRED[action]:
        raise InvalidAction("BAD_ARGS")
    if "query" in args:
        q = args["query"]
        if not isinstance(q, str) or not q.strip() or len(q) > max_query_chars:
            raise InvalidAction("BAD_QUERY")
    if "method" in args and args["method"] not in methods:
        raise InvalidAction("BAD_METHOD")
    if "top_n" in args:
        n = args["top_n"]
        if isinstance(n, bool) or not isinstance(n, int) or not (1 <= n <= max_top_n):
            raise InvalidAction("BAD_TOP_N")
    if "id" in args and (not isinstance(args["id"], str) or not args["id"]):
        raise InvalidAction("BAD_ID")
    return action, dict(args)


FallbackProvider = Callable[[Query], ArmResult]


class ReActArm(_ArmBase):
    """E2: static ReAct agent over SEARCH/VISIT/SELECT/STOP; no cross-task memory."""

    arm_id = "E2"

    def __init__(self, env: PatexEnv, budget: ArmBudget, solver: SolverSpec, *, pool_size: int,
                 fallback: FallbackProvider, max_top_n: int = 200, max_query_chars: int = 2000,
                 max_locations: int = 5, obs_ids: int = 20):
        super().__init__(env, budget, pool_size=pool_size)
        self.solver, self.fallback = solver, fallback
        self.max_top_n = min(max_top_n, env.max_top_n)
        self.max_query_chars, self.max_locations, self.obs_ids = max_query_chars, max_locations, obs_ids

    def _messages(self, query: Query, ep: _Episode, last_obs: Any) -> list[dict[str, str]]:
        schema = patex_action_schema(methods=self.env.methods, max_top_n=self.max_top_n,
                                     max_query_chars=self.max_query_chars, max_locations=self.max_locations)
        system = ("You search for prior art. Choose ONE action: SEARCH, VISIT a searched id, SELECT passages "
                  "of a visited id (byte offsets into the visited field), or STOP. Reply with JSON only, "
                  "matching this schema: " + json.dumps(schema, sort_keys=True))
        state = {"spent": ep.ledger.spent.to_dict(), "budget": self.budget.to_dict(),
                 "pool_top": ep.final_ranking(self.obs_ids) if ep.lists else [],
                 "visited": list(ep.visited), "selected": [s["doc_id"] for s in ep.selections],
                 "last_observation": last_obs}
        user = "QUERY:\n" + query.text + "\nSTATE:\n" + json.dumps(state, sort_keys=True, ensure_ascii=False)
        return [{"role": "system", "content": system}, {"role": "user", "content": user}]

    def run(self, query: Query) -> ArmResult:
        ep = self._start(query, max_top_n=self.max_top_n, max_locations=self.max_locations, obs_ids=self.obs_ids)
        ep.max_locations = self.max_locations
        last_obs: Any = None
        stop = STOP_MAX_STEPS
        for _ in range(self.budget.max_actions + self.budget.max_llm_calls + 1):
            raw = ep.call_llm(self.solver, "decide", self._messages(query, ep, last_obs))
            if raw is None:
                stop = STOP_BUDGET_REFUSED
                break
            try:
                action, args = parse_patex_action(raw, methods=self.env.methods, max_top_n=self.max_top_n,
                                                  max_query_chars=self.max_query_chars)
                if action == "STOP":
                    ep.traj.log("agent_stop")
                    stop = STOP_AGENT_STOP
                    break
                if action == "SEARCH":
                    out = ep.search(args["query"], args["method"], args["top_n"])
                    if out is not None:
                        last_obs = {"action": "SEARCH", "ids": out[: self.obs_ids],
                                    "versions": [ep.searched[i] for i in out[: self.obs_ids]]}
                elif action == "VISIT":
                    out = ep.visit(args["id"], args["fields"])
                    if out is not None:
                        last_obs = {"action": "VISIT", **out}
                else:
                    out = ep.select(args["id"], args["passage_locations"])
                    if out is not None:
                        last_obs = {"action": "SELECT", "id": args["id"], "ok": True}
            except InvalidAction as exc:
                ep.traj.log("invalid_action", reason=str(exc), output_sha256=_sha(raw))
                stop = STOP_INVALID_ACTION
                break
            if out is None:
                stop = STOP_BUDGET_REFUSED
                break
        if stop != STOP_INVALID_ACTION and ep.searched:
            return _finish(ep, self.arm_id, stop, STAGES, self.pool_size)
        if stop != STOP_INVALID_ACTION:
            ep.traj.log("empty_search", prior_stop_reason=stop)
            stop = STOP_EMPTY_SEARCH
        fb = self.fallback(query)
        ep.traj.log("fallback", fallback_arm=fb.arm, fallback_trajectory_sha256=canonical_sha256(fb.trajectory.records),
                    fallback_cost=fb.cost.to_dict(), own_searched=len(ep.searched), own_visited=len(ep.visited),
                    own_selected=len(ep.selections))
        ep.traj.log("stop", stop_reason=stop, ranking_source=RANKING_FALLBACK,
                    ranking_sha256=canonical_sha256(fb.ranking), ranking_size=len(fb.ranking),
                    cumulative_cost=ep.ledger.spent.to_dict())
        return ArmResult(query.query_id, self.arm_id, list(fb.ranking), RANKING_FALLBACK, stop, fb.stages_run,
                         fb.searched, fb.visited, fb.selections, ep.ledger.spent, fb.cost,
                         list(ep.ledger.refusals), ep.traj)


# ---------------------------------------------------------------------------
# E3: claim-element deficit-aware search (CEDS)
# ---------------------------------------------------------------------------

RUNTIME_NORMALISATION_ID = "nfc-collapse-whitespace-strip-v1"  # same rule as the evaluator
_WS = re.compile(r"\s+")


def runtime_normalise(text: str) -> str:
    return _WS.sub(" ", unicodedata.normalize("NFC", text)).strip()


@dataclass(frozen=True)
class ClaimElement:
    element_id: str
    text: str


ElementSplitter = Callable[[str], Sequence[ClaimElement]]
PassageExtractor = Callable[[ClaimElement, str, Mapping[str, str]], Sequence[Mapping[str, Any]]]
Reformulator = Callable[[ClaimElement], str]

CEDS_MOVES = ("element_query", "function_reformulation", "cpc_hop", "citation_hop")
_REFUSED = object()
_SKIPPED = object()


def verify_passage(excerpts: Mapping[str, str], proposal: Any) -> tuple[bool, str | None]:
    """Mechanical check of a proposed passage against the *visited* excerpt only."""

    if not isinstance(proposal, Mapping) or set(proposal) != {"field", "start", "end", "quote"}:
        return False, "BAD_SHAPE"
    f, s0, e0, quote = proposal["field"], proposal["start"], proposal["end"], proposal["quote"]
    if any(isinstance(x, bool) or not isinstance(x, int) for x in (s0, e0)) or not isinstance(quote, str):
        return False, "BAD_SHAPE"
    if not runtime_normalise(quote):
        return False, "EMPTY_QUOTE"
    if f not in excerpts:
        return False, "FIELD_NOT_VISITED"
    data = excerpts[f].encode("utf-8")
    if not (0 <= s0 < e0 <= len(data)):
        return False, "OUT_OF_VISIBLE"
    try:
        span = data[s0:e0].decode("utf-8")
    except UnicodeDecodeError:
        return False, "OFF_BOUNDARY"
    if runtime_normalise(span) != runtime_normalise(quote):
        return False, "QUOTE_MISMATCH"
    return True, None


class DeficitAwareArm(_ArmBase):
    """E3 (CEDS). Split the claim into elements; each move targets the least-covered element.

    An element is covered only by a passage of a VISITed document whose byte locator
    lies in the visible excerpt and whose quote matches the span after
    ``runtime_normalise``. The extractor may only *propose* passages. Moves per
    element, in declared order: element query, function reformulation of that element,
    CPC hop, citation hop (hops start from the earliest visited document not yet used
    as a seed for that relation). Stops when every element is covered, every move is
    spent, or the budget refuses. Reference labels are never an input.
    """

    arm_id = "E3"

    def __init__(self, env: PatexEnv, budget: ArmBudget, *, splitter: ElementSplitter,
                 extractor: PassageExtractor, reformulator: Reformulator, pool_size: int,
                 method: str = "dense", top_n: int = 20, hop_top_n: int = 10, visit_per_move: int = 1,
                 visit_fields: Sequence[str] = ("abstract", "claims"), moves: Sequence[str] = CEDS_MOVES,
                 max_proposals: int = 3, max_elements: int = 20, split_cost: ActionCost = ZERO,
                 extract_cost: ActionCost = ZERO, reformulate_cost: ActionCost = ZERO):
        super().__init__(env, budget, pool_size=pool_size)
        if method not in env.methods or not (1 <= top_n <= env.max_top_n) or not (1 <= hop_top_n <= env.max_top_n):
            raise ValueError("bad E3 method/top_n")
        if not moves or len(set(moves)) != len(moves) or any(m not in CEDS_MOVES for m in moves):
            raise ValueError("bad E3 moves")
        if not visit_fields or any(f not in FIELDS for f in visit_fields) or visit_per_move < 1:
            raise ValueError("bad E3 visit settings")
        self.splitter, self.extractor, self.reformulator = splitter, extractor, reformulator
        self.method, self.top_n, self.hop_top_n = method, top_n, hop_top_n
        self.visit_per_move, self.visit_fields, self.moves = visit_per_move, tuple(visit_fields), tuple(moves)
        self.max_proposals, self.max_elements = max_proposals, max_elements
        self.split_cost, self.extract_cost, self.reformulate_cost = split_cost, extract_cost, reformulate_cost

    def _config(self) -> dict[str, Any]:
        return {"method": self.method, "top_n": self.top_n, "hop_top_n": self.hop_top_n,
                "visit_per_move": self.visit_per_move, "visit_fields": list(self.visit_fields),
                "moves": list(self.moves), "max_proposals": self.max_proposals,
                "split_cost": self.split_cost.to_dict(), "extract_cost": self.extract_cost.to_dict(),
                "reformulate_cost": self.reformulate_cost.to_dict(), "normalisation": RUNTIME_NORMALISATION_ID}

    def _move(self, ep: _Episode, target: ClaimElement, move: str, seeds_used: set[tuple[str, str]]) -> Any:
        if move == "element_query":
            out = ep.search(target.text, self.method, self.top_n)
            return _REFUSED if out is None else out
        if move == "function_reformulation":
            if not ep._admit("REFORMULATE", {"element_id": target.element_id}, self.reformulate_cost):
                return _REFUSED
            text = (self.reformulator(target) or "").strip()
            ep.traj.log("reformulation", element_id=target.element_id, text_sha256=_sha(text),
                        cumulative_cost=ep.ledger.spent.to_dict())
            if not text:
                return _SKIPPED
            out = ep.search(text, self.method, self.top_n)
            return _REFUSED if out is None else out
        relation = "cpc" if move == "cpc_hop" else "citation"
        seed = next((d for d in ep.visited if (relation, d) not in seeds_used), None)
        if seed is None:
            return _SKIPPED
        seeds_used.add((relation, seed))
        out = ep.expand(seed, relation, self.hop_top_n)
        return _REFUSED if out is None else out

    def _extract(self, ep: _Episode, elements: Sequence[ClaimElement], coverage: dict[str, list[dict[str, Any]]],
                 doc: str, rejected: dict[str, int]) -> bool:
        """Check uncovered elements against one visited doc; SELECT it if it covers any. False = refused."""

        excerpts = dict(ep.excerpts.get(doc, {}))
        accepted: list[dict[str, Any]] = []
        for el in elements:
            if coverage[el.element_id]:
                continue
            if not ep._admit("EXTRACT", {"element_id": el.element_id, "id": doc}, self.extract_cost):
                return False
            proposals = list(self.extractor(el, doc, excerpts))
            ep.traj.log("extract", element_id=el.element_id, id=doc, proposals=len(proposals),
                        considered=min(len(proposals), self.max_proposals),
                        cumulative_cost=ep.ledger.spent.to_dict())
            for prop in proposals[: self.max_proposals]:
                ok, reason = verify_passage(excerpts, prop)
                quote = prop.get("quote") if isinstance(prop, Mapping) else None
                ep.traj.log("coverage_check", element_id=el.element_id, id=doc, accepted=ok, reason=reason,
                            quote_sha256=_sha(quote) if isinstance(quote, str) else None)
                if not ok:
                    rejected[reason] = rejected.get(reason, 0) + 1
                    continue
                loc = {k: prop[k] for k in ("field", "start", "end", "quote")}
                coverage[el.element_id].append({"doc_id": doc, "field": loc["field"], "start": loc["start"],
                                                "end": loc["end"]})
                if loc not in accepted:
                    accepted.append(loc)
                break
        if accepted and ep.select(doc, accepted[: ep.max_locations]) is None:
            return False
        return True

    def run(self, query: Query) -> ArmResult:
        ep = self._start(query, **self._config())
        coverage: dict[str, list[dict[str, Any]]] = {}
        rejected: dict[str, int] = {}
        moves_log: list[list[str]] = []
        elements: list[ClaimElement] = []
        stop = STOP_BUDGET_REFUSED
        if ep._admit("SPLIT", {"query_sha256": _sha(query.text)}, self.split_cost):
            elements = list(self.splitter(query.text))
            ids = [e.element_id for e in elements]
            if (not elements or len(elements) > self.max_elements or len(set(ids)) != len(ids)
                    or any(not isinstance(e, ClaimElement) or not e.element_id or not e.text.strip()
                           for e in elements)):
                raise ValueError("splitter must return 1..max_elements unique non-empty ClaimElements")
            ep.traj.log("elements", element_ids=ids, text_sha256=[_sha(e.text) for e in elements],
                        cumulative_cost=ep.ledger.spent.to_dict())
            coverage = {e.element_id: [] for e in elements}
            stop = self._loop(ep, elements, coverage, rejected, moves_log)
        extras = {
            "elements": len(elements),
            "covered": sum(bool(v) for v in coverage.values()),
            "coverage": {k: [c["doc_id"] for c in v] for k, v in coverage.items()},
            "rejected": dict(sorted(rejected.items())),
            "moves": moves_log,
        }
        ep.traj.log("coverage_summary", **extras)
        res = _finish(ep, self.arm_id, stop, STAGES, self.pool_size)
        res.extras = extras
        return res

    def _loop(self, ep: _Episode, elements: Sequence[ClaimElement], coverage: dict[str, list[dict[str, Any]]],
              rejected: dict[str, int], moves_log: list[list[str]]) -> str:
        order = {e.element_id: i for i, e in enumerate(elements)}
        tried = {e.element_id: 0 for e in elements}
        seeds_used: set[tuple[str, str]] = set()
        while True:
            uncovered = [e for e in elements if not coverage[e.element_id]]
            if not uncovered:
                return STOP_ALL_COVERED
            # least covered first (uncovered = 0 passages); tie: fewest moves tried, then claim order
            target = min(uncovered, key=lambda e: (len(coverage[e.element_id]), tried[e.element_id],
                                                   order[e.element_id]))
            if tried[target.element_id] >= len(self.moves):
                return STOP_MOVES_EXHAUSTED
            move = self.moves[tried[target.element_id]]
            tried[target.element_id] += 1
            moves_log.append([target.element_id, move])
            ep.traj.log("target", element_id=target.element_id, move=move)
            out = self._move(ep, target, move, seeds_used)
            if out is _REFUSED:
                return STOP_BUDGET_REFUSED
            if out is _SKIPPED:
                ep.traj.log("move_skipped", element_id=target.element_id, move=move)
                continue
            for doc in [i for i in out if i not in ep.visited][: self.visit_per_move]:
                if ep.visit(doc, list(self.visit_fields)) is None:
                    return STOP_BUDGET_REFUSED
                if not self._extract(ep, elements, coverage, doc, rejected):
                    return STOP_BUDGET_REFUSED


# ---------------------------------------------------------------------------
# Budget-matched runner
# ---------------------------------------------------------------------------


def run_arms(queries: Sequence[Query], arms: Sequence[_ArmBase], *, out_dir: Path | None = None) -> dict[str, Any]:
    """Run every arm on every query. All arms must share one env, one budget object and one pool size."""

    if not arms:
        raise ValueError("no arms")
    if len({id(a.budget) for a in arms}) != 1:
        raise ValueError("arms must share one budget object")
    if len({id(a.env) for a in arms}) != 1:
        raise ValueError("arms must share one environment (same tools)")
    if len({a.pool_size for a in arms}) != 1:
        raise ValueError("arms must share one pool size")
    if len({a.arm_id for a in arms}) != len(arms):
        raise ValueError("duplicate arm ids")
    rows, records = [], []
    for q in queries:
        for arm in arms:
            res = arm.run(q)
            if out_dir is not None:
                res.trajectory.write(Path(out_dir) / res.arm / f"{_safe_name(q.query_id)}.jsonl")
            rows.append(res.summary())
            records.append(res.funnel_record())
    totals: dict[str, Any] = {}
    for arm in arms:
        sel = [r for r in rows if r["arm"] == arm.arm_id]
        agg = ZERO
        stops: dict[str, int] = {}
        for r in sel:
            agg = agg + ActionCost(**r["cost"])
            stops[r["stop_reason"]] = stops.get(r["stop_reason"], 0) + 1
        totals[arm.arm_id] = {"queries": len(sel), "cost": agg.to_dict(), "stop_reasons": dict(sorted(stops.items())),
                              "fallbacks": sum(r["ranking_source"] == RANKING_FALLBACK for r in sel)}
    budget = arms[0].budget
    return {"schema": SCHEMA_VERSION, "budget": budget.to_dict(), "pool_size": arms[0].pool_size,
            "per_query": rows, "funnel_records": records, "totals": totals}


def _safe_name(query_id: str) -> str:
    if not query_id or any(c in query_id for c in "/\\:") or query_id in (".", ".."):
        return _sha(query_id)
    return query_id
