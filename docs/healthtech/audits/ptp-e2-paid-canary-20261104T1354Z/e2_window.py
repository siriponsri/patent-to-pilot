"""One-window E2 admission + bounded canary. Aborts before any reservation on a failed gate.

Args: <mcp_as_of_utc> <mcp_total_credits> <mcp_total_usage> <run_stamp>
No key material is printed; the existing collector/runner read the key file themselves.
"""
import hashlib, json, os, subprocess, sys, urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(r"C:/Users/User/Desktop/myProject/patent-to-pilot")
L = Path(os.environ["LOCALAPPDATA"]) / "PatentToPilot" / "healthtech"
LEDGER = L / "accounting" / "project-api.sqlite3"
PACK = L / "private-artifacts" / "ptp-e2-rights-cleared-fda-pack-r2-20261103" / "evidence-pack.json"
RECEIPT = L / "private-artifacts" / "ptp-e2-rights-cleared-fda-pack-r2-20261103" / "preparation-receipt.json"
ENV = REPO / ".env"
EXPECT = dict(
    head="e948cd5", ledger="d0041edaf8be80cf01f77be3333bc4c5568254e5e7e2b1151d45960ef6b8c1d2",
    key_scope="sha256:7cbe4013fd1c43bb8096135bc6e4ed9a0befb7607ebe820bcfcb2c33544d7b97",
    creator="666994c4b8526e18e00aa3e477c20b63b5bf55164489f310cf371795f88e367c",
    workspace="50a0e4a8f9b2c38c52824ca3aa5a7c105c65c588821a9ed4e86b3eaa1b10b0d2",
    pack="e146ab85db3792c3028e9becb0d71ea645a0cd0cfe426a9233622496e7aef489",
    auth="PTP-HT-OR-E2-20261103-USD100")
mcp_at, credits, usage, stamp = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
RUN_ID = f"ptp-e2-paid-canary-{stamp}"
OUT = L / "private-artifacts" / RUN_ID
OUT.mkdir(parents=False, exist_ok=False)
gates = {}
log = lambda k, v: (gates.__setitem__(k, v), print(f"{k}: {v}", flush=True))
now = lambda: datetime.now(timezone.utc)
iso = lambda d: d.isoformat()
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
canon = lambda v: json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
PY = [sys.executable]
ENVV = dict(os.environ, PYTHONPATH=str(REPO / "src"))
ENVV.pop("OPENROUTER_API_KEY", None)


def stop(code):
    log("ABORT_BEFORE_RESERVATION", code)
    (OUT / "gates.json").write_text(json.dumps(gates, indent=2) + "\n", encoding="utf-8")
    sys.exit(3)


def age(ts):
    return (now() - datetime.fromisoformat(ts.replace("Z", "+00:00"))).total_seconds()


log("window_open_mcp_as_of_utc", mcp_at)
# 1. checkout / ledger quiescence
head = subprocess.run(["git", "-C", str(REPO), "rev-parse", "--short=7", "HEAD"], capture_output=True, text=True).stdout.strip()
dirty = subprocess.run(["git", "-C", str(REPO), "status", "--porcelain"], capture_output=True, text=True).stdout.strip()
log("head", head); log("worktree_clean", dirty == "")
if head != EXPECT["head"] or dirty:
    stop("CHECKOUT_CHANGED")
ledger_before = sha(LEDGER); log("ledger_sha256_before", ledger_before)
side = [p.name for p in LEDGER.parent.iterdir() if p.name.startswith(LEDGER.name + "-")]
log("ledger_sidecars", side)
if ledger_before != EXPECT["ledger"] or side:
    stop("LEDGER_CHANGED_OR_OPEN_WRITER")
# 2. fresh public route pricing
t = now()
raw = urllib.request.urlopen("https://openrouter.ai/api/v1/models/qwen/qwen3-32b/endpoints", timeout=20).read()
(OUT / "public-endpoint-raw.json").write_bytes(raw)
eps = json.loads(raw)["data"]["endpoints"]
sel = [e for e in eps if e.get("tag") == "deepinfra/fp8" and e.get("provider_name") == "DeepInfra"]
if len(sel) != 1:
    stop("ROUTE_MISSING")
e = sel[0]
p_in, p_out = float(e["pricing"]["prompt"]) * 1e6, float(e["pricing"]["completion"]) * 1e6
log("route", {"provider": "DeepInfra", "tag": "deepinfra/fp8", "prompt_usd_per_million": round(p_in, 6),
              "completion_usd_per_million": round(p_out, 6), "context_length": e.get("context_length"), "status": e.get("status")})
if round(p_in, 6) != 0.08 or round(p_out, 6) != 0.28 or e.get("context_length") != 40960:
    stop("ROUTE_PRICE_OR_CONTEXT_CHANGED")
obs = {"format": "ptp-public-openrouter-endpoint-observation-v1", "http_status": 200, "observed_utc": iso(t),
       "raw_sha256": hashlib.sha256(raw).hexdigest(), "url": "https://openrouter.ai/api/v1/models/qwen/qwen3-32b/endpoints",
       "selected_route": {"completion_usd_per_million": 0.28, "context_length": 40960, "model": "qwen/qwen3-32b",
                          "prompt_usd_per_million": 0.08, "provider_name": "DeepInfra",
                          "supported_parameters": e.get("supported_parameters"), "tag": "deepinfra/fp8"}}
(OUT / "public-endpoint-observation.json").write_text(json.dumps(obs, indent=1, sort_keys=True) + "\n", encoding="utf-8")
snap = {"completion_usd_per_million": 0.28, "context_length": 40960, "max_input_tokens": 6144, "max_price_completion": 0.28,
        "max_price_prompt": 0.08, "model": "qwen/qwen3-32b", "non_thinking_parameters": {"reasoning": {"enabled": False}},
        "prompt_usd_per_million": 0.08, "snapshot_utc": iso(t), "timeout_seconds": 45.0,
        "unsupported_billable_components": [], "upstream_provider": "DeepInfra"}
snap["snapshot_sha256"] = hashlib.sha256(canon(snap).encode()).hexdigest()
(OUT / "model-snapshot.json").write_text(json.dumps(snap, indent=1, sort_keys=True) + "\n", encoding="utf-8")
log("pricing_snapshot_sha256", snap["snapshot_sha256"])
# 3. dispatch-key metadata (non-billable GET /api/v1/key via existing collector)
r = subprocess.run(PY + [str(REPO / "scripts/healthtech/collect_openrouter_metadata.py"), "--key-file", str(ENV),
                         "--output", str(OUT / "key-observation.json")], capture_output=True, text=True, env=ENVV, cwd=REPO)
log("collector_exit", r.returncode); log("collector_status", r.stdout.strip()[-60:])
if r.returncode != 0:
    stop("KEY_OBSERVATION_FAILED")
ko = json.loads((OUT / "key-observation.json").read_text(encoding="utf-8"))
km = ko.get("key_metadata", {})
checks = {"key_scope": ko.get("key_scope") == EXPECT["key_scope"],
          "creator_user_id_sha256": km.get("creator_user_id_sha256") == EXPECT["creator"],
          "workspace_id_sha256": km.get("workspace_id_sha256") == EXPECT["workspace"],
          "not_management_key": km.get("is_management_key") is False,
          "key_limit_state": km.get("key_limit_state"), "key_usage_usd": km.get("usage")}
log("key_binding", checks)
if not (checks["key_scope"] and checks["creator_user_id_sha256"] and checks["workspace_id_sha256"] and checks["not_management_key"]):
    stop("KEY_SCOPE_MISMATCH")
# 4. MCP account observation bound to the dispatch key, then the existing join
from decimal import Decimal
acct = {"format": "ptp-openrouter-credit-snapshot-v2", "provider": "openrouter", "source": "approved_integration",
        "as_of_utc": mcp_at, "remaining_credits_usd": str(Decimal(credits) - Decimal(usage)), "currency": "USD",
        "authorization_id": EXPECT["auth"], "key_scope": EXPECT["key_scope"],
        "account_scope": "owner-asserted-account:" + EXPECT["key_scope"].split(":")[1]}
(OUT / "account-observation.json").write_text(json.dumps(acct, indent=1, sort_keys=True) + "\n", encoding="utf-8")
r = subprocess.run(PY + ["-m", "patent_to_pilot.providers.credit_from_metadata", "--key-observation", str(OUT / "key-observation.json"),
                         "--account-observation", str(OUT / "account-observation.json"), "--output", str(OUT / "credit-snapshot.json")],
                   capture_output=True, text=True, env=ENVV, cwd=REPO)
log("credit_join", (r.returncode, (r.stdout or r.stderr).strip()[-80:]))
if r.returncode != 0:
    stop("CREDIT_JOIN_FAILED")
cs = json.loads((OUT / "credit-snapshot.json").read_text(encoding="utf-8"))
log("credit_snapshot", {k: cs.get(k) for k in ("as_of_utc", "remaining_credits_usd", "key_limit_unlimited", "snapshot_sha256")})
# 5. rights / payload identity via existing dry-run
r = subprocess.run(PY + [str(REPO / "scripts/healthtech/run_openrouter_generation_evidence_pack.py"), "--pack", str(PACK),
                         "--model-snapshot", str(OUT / "model-snapshot.json"), "--output", str(OUT / "dry-run.json"),
                         "--run-id", RUN_ID + "-dry", "--mode", "dry-run"], capture_output=True, text=True, env=ENVV, cwd=REPO)
if r.returncode != 0:
    stop("DRY_RUN_FAILED")
dry = json.loads((OUT / "dry-run.json").read_text(encoding="utf-8")); rec = json.loads(RECEIPT.read_text(encoding="utf-8"))
same = dry["pack_sha256"] == EXPECT["pack"] and all(
    c["message_sha256"] == rec["message_sha256"][c["case_id"]] and c["payload_sha256"] == rec["payload_sha256"][c["case_id"]]
    and all(b["decision"] == "ALLOWED_WITH_ATTRIBUTION" for b in c["source_bindings"]) for c in dry["manifest"]["cases"])
log("rights_payload_identity", same)
if not same:
    stop("RIGHTS_OR_PAYLOAD_CHANGED")
# 6. freshness margin
ages = {"credit_as_of_age_s": round(age(cs["as_of_utc"]), 1), "pricing_age_s": round(age(snap["snapshot_utc"]), 1)}
log("ages_before_dispatch", ages)
if max(ages.values()) > 120 or min(ages.values()) < 0:
    stop("WINDOW_MARGIN_INSUFFICIENT")
if sha(LEDGER) != EXPECT["ledger"]:
    stop("LEDGER_CHANGED_DURING_WINDOW")
(OUT / "gates.json").write_text(json.dumps(gates, indent=2) + "\n", encoding="utf-8")
# 7. live canary through the existing runner and canonical ledger (retries=0 enforced by policy)
log("dispatch_start_utc", iso(now()))
r = subprocess.run(PY + [str(REPO / "scripts/healthtech/run_openrouter_generation_evidence_pack.py"), "--pack", str(PACK),
                         "--model-snapshot", str(OUT / "model-snapshot.json"), "--output", str(OUT / "receipt.json"),
                         "--run-id", RUN_ID, "--mode", "live", "--credit-snapshot", str(OUT / "credit-snapshot.json"),
                         "--env-file", str(ENV)], capture_output=True, text=True, env=ENVV, cwd=REPO)
log("dispatch_end_utc", iso(now()))
log("runner_exit", r.returncode)
log("runner_stdout", r.stdout.strip()[-400:])
log("runner_stderr", r.stderr.strip()[-200:])
log("ledger_sha256_after", sha(LEDGER))
(OUT / "gates.json").write_text(json.dumps(gates, indent=2) + "\n", encoding="utf-8")
print("OUT_DIR", OUT.name)
