"""P4-T02: execution modes, exact models, missing capabilities and credential presence (no network).

Three execution modes are named for the owner:

* ``local_only``            - search, compare and inspect run on this computer with no model and no network;
* ``self_hosted_endpoint``  - a model served by a server the owner runs (Ollama or an OpenAI-compatible server on this
                              computer, or on another machine such as a GPU box);
* ``api_provider``          - a commercial API (OpenRouter, Typhoon, Anthropic), reached with a key.

Everything here is computed from the stored profiles, their last recorded connection check and the presence of the
named environment variables. No socket is opened: reachability is the last recorded check, never re-probed here.

Credentials: only the NAME of an environment variable is stored or shown. Presence is reported as a boolean. The value is
never returned, logged or written. The one-time setup path is a Windows *user* environment variable that the owner sets
in their own PowerShell window (the value is typed into a hidden prompt, so it never reaches this server, the browser,
the shell history or a file); the Workbench reads it at request time after a restart.
"""
from __future__ import annotations

import os
import re
from urllib.parse import urlsplit

from patent_to_pilot.budget import ledger as budget_ledger
from patent_to_pilot.workbench.providers import ProviderProfile, TEMPLATES

MODES = ("local_only", "self_hosted_endpoint", "api_provider")
MODE_TEXT = {"local_only": "Local only", "self_hosted_endpoint": "Self-hosted endpoint", "api_provider": "API provider"}
API_PROVIDERS = {"openrouter": "OpenRouter", "typhoon": "Typhoon (OpenTyphoon)", "anthropic": "Anthropic"}
# Variable names the project uses. Names only; listing a name never implies it is set.
KNOWN_CREDENTIALS = {
    "OPENROUTER_API_KEY": "OpenRouter API key (API provider: OpenRouter chat templates)",
    "TYPHOON_API_KEY": "Typhoon API key (API provider: OpenTyphoon; research callers)",
    "ANTHROPIC_API_KEY": "Anthropic API key (API provider: Claude chat templates)",
}
_ENV = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,127}$")
ROLE_TEXT = {"chat": "Chat model", "embedding": "Embedding model", "rerank": "Reranker"}
ROLE_USE = {
    "embedding": "Dense half of hybrid retrieval (optional). Lexical search works without it.",
    "chat": "Optional. No Search, Compare or Inspect step uses chat output yet; only its connection check calls it.",
    "rerank": "Optional. No Search, Compare or Inspect step uses a reranker yet; only its connection check calls it.",
}
LOCAL_WORKS = "local search, compare and inspect still work"


# ----------------------------------------------------------------------------------------------- credentials
def windows_user_env_present(name: str) -> bool | None:
    """Whether a Windows *user* environment variable of this name holds a non-empty value (None off Windows or when
    the registry cannot be read). Used only to say "set, restart the Workbench"; the value is never kept."""
    if os.name != "nt" or not _ENV.match(name):
        return None
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
            value, _kind = winreg.QueryValueEx(key, name)
    except FileNotFoundError:
        return False
    except OSError:
        return None
    present = bool(value)
    del value
    return present


def setup_steps(name: str) -> dict:
    """Owner-run, one-time steps for a Windows user environment variable. The commands contain the NAME only."""
    if not _ENV.match(name):
        raise ValueError("not an environment variable name")
    return {
        "where": "Windows user environment variable (applies to programs started after it is set)",
        "set_powershell": (f'$k = Read-Host "Paste {name} (input is hidden)" -AsSecureString; '
                           f'[Environment]::SetEnvironmentVariable("{name}", '
                           f'[Net.NetworkCredential]::new("", $k).Password, "User"); Remove-Variable k'),
        "remove_powershell": f'[Environment]::SetEnvironmentVariable("{name}", $null, "User")',
        "after": "Close the Workbench window, then start it again with Start-PTP.cmd from Explorer or a new window. "
                 "The server reads environment variables only when it starts.",
        "never": "Do not paste the key into the Workbench, a profile, a project file, a chat or a .env file in the "
                 "repository. The Workbench stores the variable name only.",
    }


def credential_status(name: str, used_by: list[str] | None = None, purpose: str = "") -> dict:
    in_process = bool(os.environ.get(name))
    user_env = windows_user_env_present(name)
    if in_process:
        state = "set"
    elif user_env:
        state = "set_restart_needed"
    else:
        state = "not_set"
    return {"name": name, "purpose": purpose, "present_in_server": in_process, "windows_user_env": user_env,
            "state": state, "used_by": sorted(used_by or []), "setup": setup_steps(name)}


def credentials(profiles: list[ProviderProfile]) -> list[dict]:
    """Every credential NAME the project knows of, from known names, saved profiles and templates."""
    used: dict[str, set[str]] = {n: set() for n in KNOWN_CREDENTIALS}
    for p in profiles:
        if p.credential_ref:
            used.setdefault(p.credential_ref, set()).add(f"profile {p.profile_id}")
    for t in TEMPLATES:
        ref = t.get("credential_ref")
        if ref:
            used.setdefault(ref, set()).add(f"template {t['profile_id']}")
    return [credential_status(n, sorted(u), KNOWN_CREDENTIALS.get(n, "Named by a provider profile"))
            for n, u in sorted(used.items())]


# ----------------------------------------------------------------------------------------------- profiles
def endpoint_mode(profile: ProviderProfile) -> dict:
    host = (urlsplit(profile.endpoint).hostname or "").lower()
    port = urlsplit(profile.endpoint).port
    provider = budget_ledger.provider_for_endpoint(profile.endpoint)
    if profile.adapter == "anthropic_native" or provider in API_PROVIDERS:
        name = API_PROVIDERS.get(provider, "Anthropic")
        return {"mode": "api_provider", "provider": name, "host": host, "where": f"{name} API ({host})"}
    if profile.local:
        return {"mode": "self_hosted_endpoint", "provider": profile.adapter, "host": host,
                "where": f"server on this computer ({host}{':' + str(port) if port else ''})"}
    return {"mode": "self_hosted_endpoint", "provider": profile.adapter, "host": host,
            "where": f"server on another machine ({host}); treated as a paid remote route by the request policy"}


def profile_state(profile: ProviderProfile, described: dict) -> dict:
    """Exact model, mode and the reasons (if any) this profile cannot be used now. No network access."""
    blockers: list[str] = []
    if profile.credential_ref and not described.get("credential_present"):
        blockers.append(f"{profile.credential_ref} not set for the Workbench server")
    if not profile.local and not profile.allow_remote:
        blockers.append("non-local endpoint not allowed (allow_remote is off)")
    if profile.paid:
        if profile.spend_cap_usd <= 0 or profile.max_requests <= 0:
            blockers.append("paid route without a spending envelope (spend cap and request cap must be > 0)")
        elif described.get("requests_counted", 0) >= profile.max_requests:
            blockers.append(f"request cap reached ({described.get('requests_counted')}/{profile.max_requests})")
    status = described.get("status", "unchecked")
    if status != "ready":
        blockers.append({"unchecked": "connection not checked yet", "changed_since_check":
                         "profile changed since its last check", "unavailable": "endpoint or model unavailable at the "
                         "last check", "blocked": "blocked at the last check", "failed": "last check failed"}
                        .get(status, f"status {status}"))
    last = described.get("last_check") or {}
    facts = last.get("facts") or {}
    return {"profile_id": profile.profile_id, "role": profile.role, "adapter": profile.adapter,
            "model_id": profile.model_id, "served_model_name": facts.get("served_model_name"),
            "model_digest": facts.get("model_digest"), "label": profile.label, **endpoint_mode(profile),
            "paid_route": profile.paid, "credential_ref": profile.credential_ref,
            "credential_present": bool(described.get("credential_present")), "status": status,
            "last_checked_at": last.get("checked_at"), "usable": not blockers, "blockers": blockers}


# ----------------------------------------------------------------------------------------------- summary
def execution_status(core, project_id: str | None = None) -> dict:
    registry = core.registry
    described = registry.list()
    profiles = [registry.get(d["profile_id"]) for d in described]
    states = [profile_state(p, d) for p, d in zip(profiles, described)]
    creds = credentials(profiles)

    # ---- capabilities (what works, what does not and why)
    caps: list[dict] = [
        {"capability": "local_search_compare_inspect", "title": "Search, Compare and Inspect", "state": "available",
         "mode": "local_only", "detail": "Runs on this computer with no model and no network. Always available."},
        {"capability": "structural_acquisition", "title": "Bounded relation search (Compare)", "state": "available",
         "mode": "local_only", "detail": "Local; uses the project's own documents only."},
    ]
    for role in ("embedding", "chat", "rerank"):
        mine = [s for s in states if s["role"] == role]
        ok = [s for s in mine if s["usable"]]
        if ok:
            state, detail = "available", ", ".join(f"{s['model_id']} ({MODE_TEXT[s['mode']]}, {s['profile_id']})"
                                                   for s in ok)
        elif mine:
            state = "unavailable"
            detail = "; ".join(f"{s['profile_id']} ({s['model_id']}): {', '.join(s['blockers'])}" for s in mine)
        else:
            state, detail = "not_configured", "No profile."
        caps.append({"capability": role, "title": ROLE_TEXT[role], "state": state, "optional": True,
                     "use": ROLE_USE[role], "detail": detail})
    from patent_to_pilot.workbench import ingest as I
    pdf = I.pdf_capability()
    caps.append({"capability": "pdf_ingestion", "title": "PDF ingestion", "optional": True,
                 "state": "available" if pdf["state"] == "active" else "unavailable", "detail": pdf["description"]})

    # ---- missing capabilities, in plain sentences
    missing: list[str] = []
    for c in creds:
        if c["state"] == "set":
            continue
        what = ", ".join(c["used_by"]) if c["used_by"] else "no Workbench profile yet"
        if c["state"] == "set_restart_needed":
            missing.append(f"{c['name']} is set for your Windows user but not for this running server → restart "
                           f"the Workbench to use it ({what}); {LOCAL_WORKS}.")
        else:
            missing.append(f"{c['name']} not set → API calls that need it are unavailable ({what}); "
                           f"{LOCAL_WORKS}.")
    for s in states:
        if not s["usable"]:
            missing.append(f"{ROLE_TEXT[s['role']]} {s['model_id']} ({s['profile_id']}, {MODE_TEXT[s['mode']]}) "
                           f"unavailable: {', '.join(s['blockers'])}; {LOCAL_WORKS}.")
    if not any(s["role"] == "embedding" and s["usable"] for s in states):
        missing.append(f"No ready embedding model → hybrid (dense) retrieval unavailable; lexical search is used and "
                       f"{LOCAL_WORKS}.")
    if pdf["state"] != "active":
        missing.append("PDF ingestion unavailable (pypdf not installed); text and Markdown files work.")

    out = {"task": "P4-T02", "modes": {m: MODE_TEXT[m] for m in MODES}, "network_probe": False,
           "reachability_note": "Reachability is the last recorded connection check; this view opens no connection.",
           "profiles": states, "capabilities": caps, "missing": missing, "credentials": creds,
           "secrets_policy": "Only environment-variable names are stored or shown; values are never returned, "
                             "logged or written by the Workbench."}
    out["active"] = _active(core, project_id, {s["profile_id"]: s for s in states}) if project_id else {
        "mode": "local_only", "mode_text": MODE_TEXT["local_only"], "model_id": None,
        "summary": "Local only: no model is in use. Open a project to see its retrieval mode."}
    return out


def _active(core, project_id: str, by_id: dict) -> dict:
    r = core.retrieval_status(project_id)
    base = {"project_id": project_id, "retrieval_mode": r["retrieval_mode"],
            "local_search": "available (no model, no network)"}
    last = core.comparison(project_id)["last_run"]
    if last:
        counters = core.run_view(last["run_id"])["counters"]
        base["last_run"] = {"run_id": last["run_id"], "retrieval_effective": counters.get("retrieval_effective",
                                                                                          "lexical"),
                            "retrieval_note": counters.get("retrieval_note"),
                            "paid_model_calls": counters.get("paid_model_calls", 0),
                            "remote_calls": counters.get("remote_calls", 0)}
    if r["retrieval_mode"] != "hybrid":
        return {**base, "mode": "local_only", "mode_text": MODE_TEXT["local_only"], "model_id": None,
                "profile_id": None, "effective": "lexical",
                "summary": "Local only: lexical search on this computer. No model, no network."}
    s = by_id.get(r["embedding_profile_id"])
    if s is None:
        return {**base, "mode": "local_only", "mode_text": MODE_TEXT["local_only"], "model_id": None,
                "profile_id": r["embedding_profile_id"], "effective": "lexical_fallback",
                "summary": f"Hybrid requested, but profile {r['embedding_profile_id']} no longer exists: lexical "
                           f"search only."}
    fresh = r["active_freshness"] == "fresh"
    common = {**base, "profile_id": s["profile_id"], "model_id": s["model_id"],
              "served_model_name": s["served_model_name"], "model_digest": s["model_digest"], "where": s["where"],
              "paid_route": s["paid_route"], "index_fresh": fresh, "active_generation_id": r["active_generation_id"]}
    if not s["usable"]:
        return {**common, "mode": "local_only", "mode_text": MODE_TEXT["local_only"], "requested_mode": s["mode"],
                "effective": "lexical_fallback", "blockers": s["blockers"],
                "summary": f"Hybrid requested with {s['model_id']} ({MODE_TEXT[s['mode']]}), but it is unavailable "
                           f"({', '.join(s['blockers'])}): lexical search on this computer is used."}
    return {**common, "mode": s["mode"], "mode_text": MODE_TEXT[s["mode"]], "effective": "hybrid",
            "summary": f"Hybrid: lexical search on this computer + embeddings from {s['model_id']} via {s['where']}. "
                       f"If the endpoint is unreachable during a run, the run falls back to lexical search and "
                       f"records why." + ("" if fresh else " The index is out of date and is rebuilt before the next "
                                                            "hybrid search.")}
