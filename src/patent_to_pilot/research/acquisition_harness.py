"""Paper 2 prototype: budgeted acquisition harness (fixed union vs agent).

Prototype only. Backends, the LLM and the token counter are injected; this module
never loads a model, opens a corpus or touches a GPU. Every cost is a *declared*
cost: it is fixed before the call, checked against the per-query budget, and
charged in full when the call is admitted. A call whose declared cost would cross
any cap is refused before execution, recorded, and never retried.

Two controllers share one interface (``run(query) -> RunResult``):

* ``FixedUnionController``: a declared tool sequence, RRF (k=60) fused to a
  fixed pool size.
* ``AgentController``: an injected LLM picks the next tool from a constrained JSON
  action schema. An invalid action is recorded and the controller stops; it then
  falls back to the fixed-union ranking so every query keeps a ranking.

Trajectories are deterministic JSON records (no timestamps, no measured time).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping, Protocol, Sequence

RRF_K = 60
SCHEMA_VERSION = "ptp-paper2-acquisition-harness-v0"

TOOL_NAMES = ("dense_search", "bm25_search", "cpc_filter", "citation_expand", "read")
SEARCH_TOOLS = ("dense_search", "bm25_search")

# Stop reasons (closed vocabulary).
STOP_SEQUENCE_COMPLETE = "SEQUENCE_COMPLETE"
STOP_AGENT_STOP = "AGENT_STOP"
STOP_BUDGET_REFUSED = "BUDGET_REFUSED"
STOP_INVALID_ACTION = "INVALID_ACTION"
STOP_MAX_STEPS = "MAX_STEPS"
STOP_EMPTY_POOL = "EMPTY_POOL"

RANKING_OWN = "OWN"
RANKING_FALLBACK = "FIXED_UNION_FALLBACK"


# ---------------------------------------------------------------------------
# Costs and budgets
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Cost:
    tool_calls: int = 0
    llm_calls: int = 0
    tokens: int = 0
    encoder_passages: int = 0
    cpu_seconds: float = 0.0
    gpu_seconds: float = 0.0
    wall_seconds: float = 0.0

    def __post_init__(self) -> None:
        for name, value in asdict(self).items():
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise TypeError(f"cost field {name} must be numeric")
            if value != value or value < 0 or value == float("inf"):
                raise ValueError(f"cost field {name} must be finite and >= 0")

    def __add__(self, other: "Cost") -> "Cost":
        return Cost(**{k: getattr(self, k) + getattr(other, k) for k in asdict(self)})

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


ZERO_COST = Cost()


@dataclass(frozen=True)
class Budget:
    """Hard per-query caps. ``None`` means uncapped for that field."""

    max_tool_calls: int
    max_llm_calls: int
    max_tokens: int
    max_wall_seconds: float
    max_encoder_passages: int | None = None

    def __post_init__(self) -> None:
        for name in ("max_tool_calls", "max_llm_calls", "max_tokens"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative int")
        if not (self.max_wall_seconds >= 0):
            raise ValueError("max_wall_seconds must be >= 0")

    def limits(self) -> dict[str, float | int]:
        out: dict[str, float | int] = {
            "tool_calls": self.max_tool_calls,
            "llm_calls": self.max_llm_calls,
            "tokens": self.max_tokens,
            "wall_seconds": self.max_wall_seconds,
        }
        if self.max_encoder_passages is not None:
            out["encoder_passages"] = self.max_encoder_passages
        return out

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class BudgetRefused(Exception):
    def __init__(self, exceeded: Sequence[str]):
        super().__init__("budget would be exceeded: " + ",".join(exceeded))
        self.exceeded = tuple(exceeded)


class BudgetLedger:
    """Admits a declared cost only if every cap still holds afterwards."""

    def __init__(self, budget: Budget):
        self.budget = budget
        self.spent = ZERO_COST
        self.refusals: list[dict[str, Any]] = []

    def would_exceed(self, cost: Cost) -> list[str]:
        after = self.spent + cost
        return [name for name, cap in self.budget.limits().items() if getattr(after, name) > cap]

    def admit(self, what: str, cost: Cost) -> None:
        exceeded = self.would_exceed(cost)
        if exceeded:
            self.refusals.append({"what": what, "declared_cost": cost.to_dict(), "exceeded": exceeded})
            raise BudgetRefused(exceeded)
        self.spent = self.spent + cost


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


class SearchBackend(Protocol):
    """Injected retrieval backend. All return values must be deterministic."""

    def dense(self, query: str, k: int) -> Sequence[str]: ...

    def bm25(self, query: str, k: int) -> Sequence[str]: ...

    def cpc_codes(self, family_id: str) -> Sequence[str]: ...

    def citations(self, family_id: str, k: int) -> Sequence[str]: ...

    def text(self, family_id: str) -> str: ...


CostModel = Mapping[str, Callable[[Mapping[str, Any]], Cost]]


def default_cost_model(token_counter: Callable[[str], int]) -> dict[str, Callable[[Mapping[str, Any]], Cost]]:
    """Illustrative declared costs; a real study must freeze its own model."""

    return {
        "dense_search": lambda a: Cost(tool_calls=1, encoder_passages=1, gpu_seconds=0.05, wall_seconds=0.1),
        "bm25_search": lambda a: Cost(tool_calls=1, cpu_seconds=0.05, wall_seconds=0.05),
        "cpc_filter": lambda a: Cost(tool_calls=1, cpu_seconds=0.01, wall_seconds=0.01),
        "citation_expand": lambda a: Cost(tool_calls=1, cpu_seconds=0.01, wall_seconds=0.01),
        "read": lambda a: Cost(tool_calls=1, cpu_seconds=0.01, wall_seconds=0.01),
    }


def whitespace_token_counter(text: str) -> int:
    """Default stand-in counter. Not a real tokenizer."""

    return len(text.split())


@dataclass(frozen=True)
class ToolResult:
    ids: tuple[str, ...]
    text: str | None = None  # only ``read`` returns text


class ToolBox:
    """Executes tools against an injected backend after budget admission."""

    def __init__(self, backend: SearchBackend, cost_model: CostModel, *, max_k: int = 1000):
        missing = [t for t in TOOL_NAMES if t not in cost_model]
        if missing:
            raise ValueError(f"cost model lacks tools: {missing}")
        self.backend = backend
        self.cost_model = cost_model
        self.max_k = max_k

    def declared_cost(self, tool: str, args: Mapping[str, Any]) -> Cost:
        cost = self.cost_model[tool](args)
        if cost.tool_calls < 1:
            raise ValueError(f"declared cost of {tool} must count at least one tool call")
        return cost

    def execute(self, tool: str, args: Mapping[str, Any]) -> ToolResult:
        b = self.backend
        if tool == "dense_search":
            ids = b.dense(args["query"], args["k"])
        elif tool == "bm25_search":
            ids = b.bm25(args["query"], args["k"])
        elif tool == "cpc_filter":
            codes = set(args["codes"])
            ids = [f for f in args["candidates"] if codes.intersection(b.cpc_codes(f))]
        elif tool == "citation_expand":
            ids = b.citations(args["family_id"], args["k"])
        elif tool == "read":
            return ToolResult(ids=(args["family_id"],), text=b.text(args["family_id"]))
        else:  # pragma: no cover - guarded by callers
            raise ValueError(f"unknown tool {tool}")
        out = _dedupe(ids)
        if tool in SEARCH_TOOLS or tool == "citation_expand":
            out = out[: args["k"]]
        return ToolResult(ids=tuple(out))


# ---------------------------------------------------------------------------
# Pool, fusion and hashing
# ---------------------------------------------------------------------------


def _dedupe(ids: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for fid in ids:
        if not isinstance(fid, str) or not fid:
            raise ValueError("family ids must be non-empty strings")
        if fid not in seen:
            seen.add(fid)
            out.append(fid)
    return out


def rrf_fuse(rankings: Sequence[Sequence[str]], *, k: int = RRF_K, pool_size: int) -> list[str]:
    """Reciprocal rank fusion; ties broken by best rank, then family id."""

    if pool_size < 1:
        raise ValueError("pool_size must be >= 1")
    score: dict[str, float] = {}
    best: dict[str, int] = {}
    for ranking in rankings:
        for rank, fid in enumerate(_dedupe(ranking), start=1):
            score[fid] = score.get(fid, 0.0) + 1.0 / (k + rank)
            best[fid] = min(best.get(fid, rank), rank)
    ordered = sorted(score, key=lambda f: (-score[f], best[f], f))
    return ordered[:pool_size]


def canonical_sha256(value: Any) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


class Pool:
    def __init__(self, pool_size: int):
        if pool_size < 1:
            raise ValueError("pool_size must be >= 1")
        self.pool_size = pool_size
        self.lists: list[tuple[str, ...]] = []

    def add(self, ids: Sequence[str]) -> None:
        if ids:
            self.lists.append(tuple(ids))

    def ranking(self) -> list[str]:
        if not self.lists:
            return []
        return rrf_fuse(self.lists, pool_size=self.pool_size)

    def sha256(self) -> str:
        return canonical_sha256(self.ranking())


# ---------------------------------------------------------------------------
# Trajectory log
# ---------------------------------------------------------------------------


class Trajectory:
    """Deterministic per-query event list; written once as JSONL."""

    def __init__(self, query_id: str, controller: str):
        self.query_id = query_id
        self.controller = controller
        self.records: list[dict[str, Any]] = []

    def log(self, event: str, **fields: Any) -> None:
        record = {
            "schema": SCHEMA_VERSION,
            "query_id": self.query_id,
            "controller": self.controller,
            "seq": len(self.records),
            "event": event,
        }
        record.update(fields)
        self.records.append(record)

    def lines(self) -> list[str]:
        return [json.dumps(r, sort_keys=True, ensure_ascii=False) for r in self.records]

    def write(self, path: Path) -> str:
        """Exclusive create; refuses to overwrite. Returns the file sha256."""

        data = ("\n".join(self.lines()) + "\n").encode("utf-8")
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "xb") as handle:
            handle.write(data)
        return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------------------
# Controllers
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Query:
    query_id: str
    text: str


@dataclass
class RunResult:
    query_id: str
    controller: str
    ranking: list[str]
    ranking_source: str
    stop_reason: str
    cost: Cost
    fallback_cost: Cost
    refusals: list[dict[str, Any]]
    trajectory: Trajectory = field(repr=False)

    @property
    def total_cost(self) -> Cost:
        return self.cost + self.fallback_cost

    def summary(self) -> dict[str, Any]:
        return {
            "query_id": self.query_id,
            "controller": self.controller,
            "ranking_size": len(self.ranking),
            "ranking_sha256": canonical_sha256(self.ranking),
            "ranking_source": self.ranking_source,
            "stop_reason": self.stop_reason,
            "cost": self.cost.to_dict(),
            "fallback_cost": self.fallback_cost.to_dict(),
            "refusals": len(self.refusals),
            "trajectory_sha256": canonical_sha256(self.trajectory.records),
        }


def _call_tool(toolbox: ToolBox, ledger: BudgetLedger, pool: Pool, traj: Trajectory,
               tool: str, args: Mapping[str, Any]) -> ToolResult | None:
    """Admit, execute, record. Returns None if refused (caller must stop)."""

    cost = toolbox.declared_cost(tool, args)
    logged_args = _loggable_args(tool, args)
    try:
        ledger.admit(tool, cost)
    except BudgetRefused as exc:
        traj.log("refused", tool=tool, args=logged_args, declared_cost=cost.to_dict(),
                 exceeded=list(exc.exceeded), cumulative_cost=ledger.spent.to_dict())
        return None
    result = toolbox.execute(tool, args)
    if tool != "read":
        pool.add(result.ids)
    traj.log("tool", tool=tool, args=logged_args, declared_cost=cost.to_dict(),
             result_ids=list(result.ids), result_sha256=canonical_sha256(list(result.ids)),
             text_sha256=None if result.text is None else hashlib.sha256(result.text.encode("utf-8")).hexdigest(),
             pool_sha256=pool.sha256(), cumulative_cost=ledger.spent.to_dict())
    return result


def _loggable_args(tool: str, args: Mapping[str, Any]) -> dict[str, Any]:
    """Query text is logged by hash only so trajectories never carry it."""

    out = dict(args)
    if "query" in out:
        out["query_sha256"] = hashlib.sha256(str(out.pop("query")).encode("utf-8")).hexdigest()
    if "candidates" in out:
        out["candidates_sha256"] = canonical_sha256(list(out.pop("candidates")))
    return out


LLMCallable = Callable[[list[dict[str, str]], int], str]


@dataclass(frozen=True)
class LLMSpec:
    llm: LLMCallable
    token_counter: Callable[[str], int]
    max_output_tokens: int
    seconds_per_call: float = 0.0

    def declared_cost(self, messages: list[dict[str, str]]) -> Cost:
        prompt_tokens = sum(self.token_counter(m["content"]) for m in messages)
        return Cost(llm_calls=1, tokens=prompt_tokens + self.max_output_tokens,
                    gpu_seconds=self.seconds_per_call, wall_seconds=self.seconds_per_call)


def _call_llm(spec: LLMSpec, ledger: BudgetLedger, traj: Trajectory, purpose: str,
              messages: list[dict[str, str]]) -> str | None:
    cost = spec.declared_cost(messages)
    try:
        ledger.admit("llm:" + purpose, cost)
    except BudgetRefused as exc:
        traj.log("refused", tool="llm", purpose=purpose, declared_cost=cost.to_dict(),
                 exceeded=list(exc.exceeded), cumulative_cost=ledger.spent.to_dict())
        return None
    raw = spec.llm(messages, spec.max_output_tokens)
    if not isinstance(raw, str):
        raw = ""
    traj.log("llm", purpose=purpose, declared_cost=cost.to_dict(),
             prompt_sha256=canonical_sha256(messages),
             output_sha256=hashlib.sha256(raw.encode("utf-8")).hexdigest(),
             output_tokens_counted=spec.token_counter(raw),
             cumulative_cost=ledger.spent.to_dict())
    return raw


class Controller(Protocol):
    name: str

    def run(self, query: Query) -> RunResult: ...


@dataclass(frozen=True)
class Step:
    """One fixed-union step.

    ``tool`` is a TOOL_NAME or ``"llm_view"``. Search steps take ``query_ref``
    (``"original"`` or ``"view:<name>"``) and ``k``; ``llm_view`` takes ``name``
    and ``instruction``; ``citation_expand``/``read`` take ``from_rank`` (1-based
    rank in the current pool); ``cpc_filter`` takes ``codes`` and filters the
    current pool.
    """

    tool: str
    k: int = 0
    query_ref: str = "original"
    name: str = ""
    instruction: str = ""
    from_rank: int = 1
    codes: tuple[str, ...] = ()


class FixedUnionController:
    name = "fixed_union"

    def __init__(self, toolbox: ToolBox, budget: Budget, steps: Sequence[Step], *, pool_size: int,
                 llm: LLMSpec | None = None):
        if not steps:
            raise ValueError("fixed union needs at least one step")
        for s in steps:
            if s.tool not in TOOL_NAMES and s.tool != "llm_view":
                raise ValueError(f"unknown step tool {s.tool}")
            if s.tool == "llm_view" and llm is None:
                raise ValueError("llm_view step needs an LLMSpec")
        self.toolbox, self.budget, self.steps = toolbox, budget, tuple(steps)
        self.pool_size, self.llm = pool_size, llm

    def run(self, query: Query) -> RunResult:
        ledger, pool = BudgetLedger(self.budget), Pool(self.pool_size)
        traj = Trajectory(query.query_id, self.name)
        traj.log("start", budget=self.budget.to_dict(), pool_size=self.pool_size,
                 steps_sha256=canonical_sha256([asdict(s) for s in self.steps]))
        views: dict[str, str] = {"original": query.text}
        stop = STOP_SEQUENCE_COMPLETE
        for step in self.steps:
            if step.tool == "llm_view":
                messages = [{"role": "system", "content": step.instruction},
                            {"role": "user", "content": query.text}]
                out = _call_llm(self.llm, ledger, traj, "view:" + step.name, messages)
                if out is None:
                    stop = STOP_BUDGET_REFUSED
                    break
                views["view:" + step.name] = out.strip() or query.text
                continue
            args = self._args(step, views, pool)
            if args is None:
                traj.log("skipped", tool=step.tool, reason="EMPTY_POOL_OR_RANK")
                continue
            if _call_tool(self.toolbox, ledger, pool, traj, step.tool, args) is None:
                stop = STOP_BUDGET_REFUSED
                break
        ranking = pool.ranking()
        traj.log("stop", stop_reason=stop, ranking_sha256=canonical_sha256(ranking),
                 ranking_size=len(ranking), cumulative_cost=ledger.spent.to_dict())
        return RunResult(query.query_id, self.name, ranking, RANKING_OWN, stop, ledger.spent, ZERO_COST,
                         list(ledger.refusals), traj)

    @staticmethod
    def _args(step: Step, views: Mapping[str, str], pool: Pool) -> dict[str, Any] | None:
        if step.tool in SEARCH_TOOLS:
            if step.query_ref not in views:
                raise ValueError(f"unknown query_ref {step.query_ref}")
            return {"query": views[step.query_ref], "k": step.k}
        current = pool.ranking()
        if step.tool == "cpc_filter":
            return {"candidates": current, "codes": list(step.codes)} if current else None
        if not (1 <= step.from_rank <= len(current)):
            return None
        fid = current[step.from_rank - 1]
        return {"family_id": fid, "k": step.k} if step.tool == "citation_expand" else {"family_id": fid}


# ---- Agent ---------------------------------------------------------------


class InvalidAction(Exception):
    pass


AGENT_ACTIONS = TOOL_NAMES + ("stop",)


def action_schema(max_k: int, max_query_chars: int) -> dict[str, Any]:
    """JSON schema shown to the LLM (validation below is the authority)."""

    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["action", "args"],
        "properties": {
            "action": {"enum": list(AGENT_ACTIONS)},
            "args": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "query": {"type": "string", "minLength": 1, "maxLength": max_query_chars},
                    "k": {"type": "integer", "minimum": 1, "maximum": max_k},
                    "codes": {"type": "array", "items": {"type": "string"}, "minItems": 1},
                    "family_id": {"type": "string"},
                },
            },
        },
    }


_REQUIRED_ARGS = {
    "dense_search": {"query", "k"},
    "bm25_search": {"query", "k"},
    "cpc_filter": {"codes"},
    "citation_expand": {"family_id", "k"},
    "read": {"family_id"},
    "stop": set(),
}


def parse_action(raw: str, *, pool_ids: Sequence[str], max_k: int, max_query_chars: int) -> tuple[str, dict[str, Any]]:
    """Strict parse; no repair. Raises InvalidAction with a short reason."""

    try:
        obj = json.loads(raw, parse_constant=lambda c: (_ for _ in ()).throw(ValueError(c)))
    except (ValueError, TypeError) as exc:
        raise InvalidAction("NOT_JSON") from exc
    if not isinstance(obj, dict) or set(obj) != {"action", "args"}:
        raise InvalidAction("BAD_ENVELOPE")
    action, args = obj["action"], obj["args"]
    if action not in AGENT_ACTIONS:
        raise InvalidAction("UNKNOWN_ACTION")
    if not isinstance(args, dict) or set(args) != _REQUIRED_ARGS[action]:
        raise InvalidAction("BAD_ARGS")
    if "query" in args:
        q = args["query"]
        if not isinstance(q, str) or not q.strip() or len(q) > max_query_chars:
            raise InvalidAction("BAD_QUERY")
    if "k" in args:
        k = args["k"]
        if isinstance(k, bool) or not isinstance(k, int) or not (1 <= k <= max_k):
            raise InvalidAction("BAD_K")
    if "codes" in args:
        codes = args["codes"]
        if not isinstance(codes, list) or not codes or not all(isinstance(c, str) and c for c in codes):
            raise InvalidAction("BAD_CODES")
    if "family_id" in args and args["family_id"] not in set(pool_ids):
        raise InvalidAction("FAMILY_NOT_IN_POOL")
    return action, dict(args)


FallbackProvider = Callable[[Query], RunResult]


class AgentController:
    name = "agent"

    def __init__(self, toolbox: ToolBox, budget: Budget, llm: LLMSpec, *, pool_size: int,
                 fallback: FallbackProvider, max_k: int = 200, max_query_chars: int = 2000,
                 view_ids: int = 20, read_chars: int = 2000):
        self.toolbox, self.budget, self.llm = toolbox, budget, llm
        self.pool_size, self.fallback = pool_size, fallback
        self.max_k, self.max_query_chars = max_k, max_query_chars
        self.view_ids, self.read_chars = view_ids, read_chars

    def _messages(self, query: Query, pool: Pool, last_read: str | None, ledger: BudgetLedger) -> list[dict[str, str]]:
        state = {
            "pool_top": pool.ranking()[: self.view_ids],
            "spent": ledger.spent.to_dict(),
            "budget": self.budget.to_dict(),
            "last_read": None if last_read is None else last_read[: self.read_chars],
        }
        system = ("Choose one retrieval action. Reply with JSON only, matching this schema: "
                  + json.dumps(action_schema(self.max_k, self.max_query_chars), sort_keys=True))
        user = "QUERY:\n" + query.text + "\nSTATE:\n" + json.dumps(state, sort_keys=True)
        return [{"role": "system", "content": system}, {"role": "user", "content": user}]

    def run(self, query: Query) -> RunResult:
        ledger, pool = BudgetLedger(self.budget), Pool(self.pool_size)
        traj = Trajectory(query.query_id, self.name)
        traj.log("start", budget=self.budget.to_dict(), pool_size=self.pool_size)
        last_read: str | None = None
        stop = STOP_MAX_STEPS
        max_steps = self.budget.max_llm_calls + self.budget.max_tool_calls + 1
        for _ in range(max_steps):
            raw = _call_llm(self.llm, ledger, traj, "decide", self._messages(query, pool, last_read, ledger))
            if raw is None:
                stop = STOP_BUDGET_REFUSED
                break
            try:
                action, args = parse_action(raw, pool_ids=pool.ranking(), max_k=self.max_k,
                                            max_query_chars=self.max_query_chars)
            except InvalidAction as exc:
                traj.log("invalid_action", reason=str(exc),
                         output_sha256=hashlib.sha256(raw.encode("utf-8")).hexdigest())
                stop = STOP_INVALID_ACTION
                break
            if action == "stop":
                traj.log("agent_stop")
                stop = STOP_AGENT_STOP
                break
            if action == "cpc_filter":
                args = {"candidates": pool.ranking(), "codes": args["codes"]}
            result = _call_tool(self.toolbox, ledger, pool, traj, action, args)
            if result is None:
                stop = STOP_BUDGET_REFUSED
                break
            if result.text is not None:
                last_read = result.text
        ranking = pool.ranking()
        source, fallback_cost = RANKING_OWN, ZERO_COST
        if stop == STOP_INVALID_ACTION or not ranking:
            if stop != STOP_INVALID_ACTION:
                traj.log("empty_pool", prior_stop_reason=stop)
                stop = STOP_EMPTY_POOL
            fb = self.fallback(query)
            ranking, source, fallback_cost = list(fb.ranking), RANKING_FALLBACK, fb.cost
            traj.log("fallback", fallback_controller=fb.controller,
                     fallback_trajectory_sha256=canonical_sha256(fb.trajectory.records),
                     fallback_cost=fb.cost.to_dict())
        traj.log("stop", stop_reason=stop, ranking_source=source, ranking_sha256=canonical_sha256(ranking),
                 ranking_size=len(ranking), cumulative_cost=ledger.spent.to_dict())
        return RunResult(query.query_id, self.name, ranking, source, stop, ledger.spent, fallback_cost,
                         list(ledger.refusals), traj)


# ---------------------------------------------------------------------------
# Matched-budget comparison
# ---------------------------------------------------------------------------


def compare_matched_budget(queries: Sequence[Query], *, toolbox: ToolBox, budget: Budget,
                           steps: Sequence[Step], llm: LLMSpec, pool_size: int,
                           out_dir: Path | None = None, **agent_kw: Any) -> dict[str, Any]:
    """Run both controllers on every query under the same budget.

    The fixed union is run once per query and reused as the agent's fallback, so
    a fallback ranking is the identical fixed-union ranking. The agent's own
    spend and the (shared) fallback spend are reported separately.
    """

    fixed = FixedUnionController(toolbox, budget, steps, pool_size=pool_size, llm=llm)
    rows: list[dict[str, Any]] = []
    rankings: dict[str, dict[str, list[str]]] = {}
    for query in queries:
        fu = fixed.run(query)
        agent = AgentController(toolbox, budget, llm, pool_size=pool_size, fallback=lambda q, fu=fu: fu, **agent_kw)
        ag = agent.run(query)
        for res in (fu, ag):
            if out_dir is not None:
                res.trajectory.write(Path(out_dir) / res.controller / f"{_safe_name(query.query_id)}.jsonl")
            rows.append(res.summary())
        rankings[query.query_id] = {"fixed_union": fu.ranking, "agent": ag.ranking}
    totals: dict[str, dict[str, Any]] = {}
    for name in ("fixed_union", "agent"):
        sel = [r for r in rows if r["controller"] == name]
        agg = ZERO_COST
        for r in sel:
            agg = agg + Cost(**r["cost"])
        stops: dict[str, int] = {}
        for r in sel:
            stops[r["stop_reason"]] = stops.get(r["stop_reason"], 0) + 1
        totals[name] = {"queries": len(sel), "cost": agg.to_dict(), "stop_reasons": dict(sorted(stops.items())),
                        "fallbacks": sum(r["ranking_source"] == RANKING_FALLBACK for r in sel)}
    return {"schema": SCHEMA_VERSION, "budget": budget.to_dict(), "pool_size": pool_size,
            "per_query": rows, "totals": totals, "rankings": rankings}


def _safe_name(query_id: str) -> str:
    if not query_id or any(c in query_id for c in "/\\:") or query_id in (".", ".."):
        return hashlib.sha256(query_id.encode("utf-8")).hexdigest()
    return query_id
