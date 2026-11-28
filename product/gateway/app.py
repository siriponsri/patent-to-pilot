"""Same-origin MWD demo and versioned AI task API."""

import os
import sqlite3
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Callable

from fastapi import Depends, FastAPI, Header, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError

from .budget import Admission, AdmissionRefused, exclusive_owner
from .contract import (
    Abstained, Accepted, Citation, DossierSelection, Draft, Identifier, Provenance, Reason, Rejected,
    TaskRequest, TaskResponse, Unavailable,
)
from .evidence import (
    DISCLAIMER, PROMPT_VERSION, DossierNotFound, EvidenceStore, Validator, prompt, validate_claim_ids,
)
from .providers import FixtureProvider, Provider, UncertainDispatch

DEMO = Path(__file__).resolve().parents[1] / "demo"
ADMISSION_ERRORS = {
    "duplicate_request": (409, "This idempotency key already has a recorded attempt."),
    "request_in_progress": (409, "An attempt is already outstanding for this identity."),
    "daily_limit": (429, "The Bangkok daily request allowance has been used."),
    "attempt_limit": (429, "The D43 attempt allowance has been used."),
    "budget_limit": (429, "The D43 operational budget cannot cover this attempt."),
    "envelope_expired": (503, "The D43 envelope has expired."),
    "unknown_billing": (503, "Billing must be reconciled before further dispatch."),
    "route_or_price_changed": (503, "The route or tariff differs from the approved configuration."),
    "ledger_unavailable": (503, "The gateway could not establish the remaining allowance."),
}


def identity(request: Request, proxy_user: Annotated[str | None, Header(alias="X-MWD-User")] = None) -> str | None:
    """B4 can replace this dependency through FastAPI's dependency override."""
    if request.app.state.auth_mode == "dev":
        return "local-fixture"
    if (
        request.app.state.auth_mode == "proxy"
        and request.client and request.client.host in request.app.state.trusted_peers
        and proxy_user and len(proxy_user) <= 256 and proxy_user.isascii() and proxy_user.isprintable()
    ):
        return proxy_user.strip() or None
    return None


def create_app(
    *, ledger_path: Path | None = None, demo: Path = DEMO, provider: Provider | None = None,
    validator: Validator = validate_claim_ids, clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    auth_mode: str | None = None, trusted_peers: frozenset[str] = frozenset(), public_origin: str | None = None,
    qualified_tasks: frozenset[str] = frozenset(),
) -> FastAPI:
    if provider is None and os.environ.get("MWD_PROVIDER", "fixture") == "fixture":
        provider = FixtureProvider()
    is_fixture = provider is not None and provider.route.provider == "fixture"
    path = (ledger_path or Path(os.environ.get(
        "MWD_LEDGER_PATH", str(Path.home() / ".mwd" / "ledger.sqlite3"),
    ))).resolve()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.evidence = EvidenceStore(demo / "data")
        with exclusive_owner(path):
            app.state.admission = Admission(path, require_existing=provider is not None and not is_fixture)
            yield

    app = FastAPI(title="Market Window Dossier Gateway", version="1.0.0", lifespan=lifespan)
    app.state.auth_mode = auth_mode or ("dev" if is_fixture else "disabled")
    app.state.trusted_peers = trusted_peers

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request: Request, error: RequestValidationError) -> JSONResponse:
        # Pydantic errors can contain submitted values. Return a fixed message.
        error_body = Rejected(reason="invalid_request", message="The task or required request fields are invalid.")
        return JSONResponse(status_code=422, content=error_body.model_dump(), headers={"Cache-Control": "no-store"})

    def problem(response: Response, status: int, reason: Reason, message: str, next_step: str | None = None):
        response.status_code = status
        model = Abstained if status == 200 else Rejected if status < 500 else Unavailable
        return model(reason=reason, message=message, next_step=next_step)

    def refused(response: Response, reason: str):
        status, message = ADMISSION_ERRORS[reason]
        return problem(response, status, reason, message)

    @app.post(
        "/api/v1/tasks", operation_id="runDossierTask", response_model=TaskResponse,
        responses={
            200: {"description": "Draft or evidence abstention", "model": Accepted | Abstained},
            401: {"model": Rejected}, 403: {"model": Rejected}, 404: {"model": Rejected},
            409: {"model": Rejected}, 422: {"model": Rejected}, 429: {"model": Rejected},
            503: {"model": Unavailable},
        },
    )
    def run_task(
        response: Response, http_request: Request, request: TaskRequest,
        idempotency_key: Annotated[Identifier, Header(alias="Idempotency-Key")],
        user: Annotated[str | None, Depends(identity)],
    ) -> TaskResponse:
        response.headers["Cache-Control"] = "no-store"
        origin = http_request.headers.get("origin")
        allowed = public_origin or f"{http_request.url.scheme}://{http_request.url.netloc}"
        if origin is not None and origin != allowed:
            return problem(response, 403, "cross_origin", "Open the dossier on the gateway origin.")
        if user is None:
            return problem(response, 401, "identity_required", "An authenticated identity is required.")
        if provider is None or (not is_fixture and (
            app.state.auth_mode != "proxy" or request.task not in qualified_tasks or validator is validate_claim_ids
        )):
            return problem(response, 503, "provider_unqualified", "No qualified provider is enabled for this task.")
        try:
            evidence = app.state.evidence.load(request)
        except DossierNotFound:
            return problem(response, 404, "dossier_not_found", "The dossier selection is absent from the release index.")
        except (OSError, ValueError, KeyError, TypeError):
            return problem(response, 503, "provider_unavailable", "The released dossier could not be loaded.")
        if request.task == "A4":
            return problem(
                response, 200, "claim_text_missing", "Approved original claim text is unavailable.",
                "Look up the publication, claim and dependencies with a patent professional.",
            )
        messages = prompt(request, evidence)
        estimate = provider.route.estimate(messages)
        if estimate is None:
            return problem(response, 200, "evidence_missing", "The selected evidence exceeds the prompt limit.")
        admission = app.state.admission
        try:
            reservation = admission.reserve(provider.route, estimate, user, idempotency_key, request.task, clock())
        except AdmissionRefused as exc:
            return refused(response, exc.reason)
        except (OSError, sqlite3.Error, ValueError):
            return refused(response, "ledger_unavailable")

        try:
            completion = provider.complete(request, evidence, messages)
        except Exception as exc:
            # The exchange may already have been billed even if a provider adapter crashed.
            outcome = exc.reason if isinstance(exc, UncertainDispatch) else "adapter_failure"
            detail = exc.detail if isinstance(exc, UncertainDispatch) else None
            reason = "route_or_price_changed" if outcome == "route_or_price_changed" else "unknown_billing"
            try:
                admission.unknown(reservation, outcome, detail)
            except (OSError, sqlite3.Error, ValueError):
                return refused(response, "ledger_unavailable")
            return refused(response, reason)

        try:
            draft = Draft.model_validate_json(completion.text or "")
            citations = validator(request, draft, evidence)
            result = "ok" if draft.items else "evidence_missing"
        except ValidationError:
            result = "invalid_output"
        except ValueError:
            result = "unsupported_evidence"
        try:
            admission.settle(reservation, completion, result)
        except AdmissionRefused as exc:
            return refused(response, exc.reason)
        except (OSError, sqlite3.Error, ValueError):
            return refused(response, "ledger_unavailable")
        if result != "ok":
            return problem(
                response, 200, result, "The gateway withheld the draft.",
                "Review the dossier sources and hand-off checklist.",
            )
        forecast = evidence.forecast if request.task == "A1" or (
            request.task == "A3" and request.question_id == "market_window"
        ) else None
        if forecast and all(c.claim_id != forecast.claim_id for c in citations):
            claim = evidence.claims[forecast.claim_id]
            citations.append(Citation(claim_id=claim.id, sources=[evidence.sources[src] for src in claim.source_ids]))
        return Accepted(
            selection=DossierSelection(**request.model_dump(include=set(DossierSelection.model_fields))),
            task=request.task, label="AI draft", disclaimer=DISCLAIMER, items=draft.items, citations=citations,
            provenance=Provenance(
                provider=provider.route.provider, model=provider.route.preset.model,
                prompt_version=PROMPT_VERSION, generated_at=clock(),
            ),
            forecast=forecast,
        )

    @app.get("/", include_in_schema=False)
    def landing():
        return RedirectResponse("/demo/")

    @app.get("/demo/", include_in_schema=False)
    def demo_index():
        return FileResponse(demo / "index.html")

    @app.get("/demo/{asset}", include_in_schema=False)
    def demo_asset(asset: str):
        if asset in {"index.html", "styles.css", "app.js", "data.bundle.js"}:
            return FileResponse(demo / asset)
        return Response(status_code=404)

    for folder in ("assets", "data", "dossiers"):
        app.mount(f"/demo/{folder}", StaticFiles(directory=demo / folder), name=f"demo-{folder}")
    return app
