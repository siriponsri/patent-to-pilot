// Patent-to-Pilot Workbench (PTP-2026-11-21/G01–G02). All results come from the local server; nothing is computed
// or pre-written here. Data are rendered with textContent (no HTML injection).
"use strict";

const S = { projectId: null, project: null, comparison: null, caps: null, liveRunId: null, view: "workbench",
  lastFocus: null, retrieval: null, providers: null };
const isSample = () => S.project && S.project.data_origin === "synthetic_fixture";

const $ = (id) => document.getElementById(id);
function el(tag, attrs = {}, ...kids) {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v == null || v === false) continue;
    if (k === "class") n.className = v;
    else if (k === "text") n.textContent = v;
    else if (k.startsWith("on")) n.addEventListener(k.slice(2), v);
    else n.setAttribute(k, v);
  }
  for (const c of kids.flat()) if (c != null) n.append(c.nodeType ? c : document.createTextNode(String(c)));
  return n;
}
function status(msg, isError = false) { const s = $("status"); s.textContent = msg; s.classList.toggle("error", isError); }

async function api(method, path, body) {
  const opt = { method, headers: {} };
  if (body !== undefined) { opt.headers["Content-Type"] = "application/json"; opt.body = JSON.stringify(body); }
  const res = await fetch(path, opt);
  const data = await res.json().catch(() => ({ error: "bad_response", message: `HTTP ${res.status}` }));
  if (!res.ok) { const e = new Error(data.message || data.error); e.code = data.error; throw e; }
  return data;
}

function show(view) {
  S.view = view;
  for (const b of document.querySelectorAll(".tab")) {
    if (b.dataset.view === view) b.setAttribute("aria-current", "page"); else b.removeAttribute("aria-current");
  }
  for (const v of ["workbench", "evidence", "runs", "changes", "providers"]) $("view-" + v).hidden = !S.projectId || v !== view;
  $("welcome").hidden = !!S.projectId;
  if (view === "evidence") renderSources();
  if (view === "runs") renderRuns();
  if (view === "changes") renderChanges();
  if (view === "providers") renderProviders();
}

function labels() {
  const L = $("labels"); L.replaceChildren();
  if (!S.projectId) return;
  L.append(el("span", { class: "label", text: isSample() ? "Sample data" : "Your files" }));
  const last = S.comparison && S.comparison.last_run;
  if (last) {
    if (S.liveRunId === last.run_id) L.append(el("span", { class: "label live", text: "Live local run" }));
    else L.append(el("span", { class: "label recorded", text: `Recorded run · ${last.run_id}` }));
  }
  const R = S.retrieval;
  if (R && R.retrieval_mode === "hybrid") {
    const fresh = R.active_freshness === "fresh";
    L.append(el("span", { class: "label", text: `Hybrid mode · ${R.embedding_profile_id}${fresh ? "" : " · index out of date (rebuilt on next run)"}` }));
  } else L.append(el("span", { class: "label", text: "Lexical mode" }));
}

async function loadProjectList() {
  const { projects } = await api("GET", "/api/projects");
  const sel = $("project-select");
  sel.replaceChildren(...projects.map((p) => el("option", { value: p.project_id, text: `${p.title}${p.data_origin === "synthetic_fixture" ? " (sample)" : ""}` })),
    el("option", { value: "__new", text: "Create or open another project…" }));
  sel.hidden = !projects.length;
  if (S.projectId) sel.value = S.projectId;
  return projects;
}

async function loadProject() {
  S.project = await api("GET", `/api/projects/${S.projectId}`);
  S.comparison = await api("GET", `/api/projects/${S.projectId}/comparison`);
  S.retrieval = await api("GET", `/api/projects/${S.projectId}/retrieval`);
  $("project-title").textContent = $("project-select").hidden ? S.project.title : "";
  renderWorkbench(); labels();
}

function reqLabel(rid) { return S.project.mission.requirements.find((r) => r.requirement_id === rid).label; }

function renderWorkbench() {
  const P = S.project, C = S.comparison;
  $("sum-project").textContent = `${P.title} (${P.scenario_id})`;
  const cur = P.sources.filter((s) => s.status === "current").map((s) => `${s.source_id} · ${s.version_id}`);
  $("sum-sources").textContent = `${cur.length} current: ${cur.join(", ")}`;
  const last = C.last_run;
  $("sum-run").textContent = last ? `${last.kind} · ${last.status} · ${new Date(last.finished_at || Date.now()).toLocaleString()}` : "Not run yet";
  $("mission").textContent = P.mission.mission;
  $("requirements").replaceChildren(...P.mission.requirements.map((r) => el("li", { text: `${r.requirement_id} — ${r.label}` })));
  const ch = P.changes.find((c) => c.event_id === "CHANGE-S2-V2");
  const applied = ch && ch.status === "applied";
  $("apply-change").hidden = !isSample();
  $("apply-change").disabled = !last || applied;
  $("apply-change").textContent = applied ? "Sample source revision applied" : "Apply sample source revision";
  $("trace-link").hidden = !last;
  const wrap = $("matrix-wrap");
  if (!C.cells.length) { wrap.replaceChildren(el("p", { class: "muted", text: "No result yet. Select Run comparison to run the local engine." })); return; }
  const reqs = P.mission.requirements;
  const table = el("table", { class: "matrix" },
    el("caption", { class: "muted", text: "Candidates × requirements. Select a citation to open the exact source passage." }),
    el("thead", {}, el("tr", {}, el("th", { scope: "col", text: "Candidate" }), ...reqs.map((r) => el("th", { scope: "col", text: `${r.requirement_id} · ${r.label}` })))),
    el("tbody", {}, ...P.mission.candidates.map((c) => el("tr", {},
      el("th", { scope: "row", text: c.label }),
      ...reqs.map((r) => cellTd(C.cells.find((x) => x.candidate_id === c.candidate_id && x.requirement_id === r.requirement_id), r))))));
  wrap.replaceChildren(table);
}

const ICON = { meets: "✓", does_not_meet: "✕", unknown: "?", needs_review: "!" };
function cellTd(cell, req) {
  const td = el("td", { class: "cell", "data-req": `${req.requirement_id} · ${req.label}` });
  if (!cell) { td.append(el("span", { class: "muted", text: "Not assessed" })); return td; }
  td.append(el("span", { class: `badge ${cell.display_outcome}` }, el("span", { "aria-hidden": "true", text: ICON[cell.display_outcome] }), cell.label));
  td.append(el("p", { text: cell.explanation }));
  if (cell.citation) {
    const c = cell.citation;
    td.append(el("button", { class: "cite", "aria-label": `Open citation ${c.source_id} version ${c.version_id} passage ${c.passage_id}`,
      onclick: (ev) => openCitation(c.source_id, c.version_id, c.passage_id, ev.currentTarget) },
      `${c.source_id} · ${c.version_id}`));
  }
  if (cell.supersedes_id) td.append(el("p", { class: "muted", text: "Updated after a source revision; the previous assessment is kept in history." }));
  return td;
}

async function openCitation(sid, vid, pid, trigger) {
  S.lastFocus = trigger || document.activeElement;
  const body = $("drawer-body"); body.replaceChildren(el("p", { text: "Loading exact passage…" }));
  $("drawer").hidden = false; $("drawer-close").focus();
  try {
    const c = await api("GET", `/api/projects/${S.projectId}/sources/${sid}/versions/${vid}/passages/${pid}`);
    $("drawer-title").textContent = `${c.source_id} · ${c.version_id} · ${c.passage_id}`;
    const badge = c.status === "current" ? el("span", { class: "pill current", text: "Current" }) : el("span", { class: "pill historical", text: `Superseded (current: ${c.current_version})` });
    body.replaceChildren(
      el("p", {}, el("b", { text: c.title }), " ", badge, " ", el("span", { class: "pill", text: c.data_origin === "synthetic_fixture" ? "Sample data" : "Your file" })),
      el("p", { class: "muted", text: "Exact text of this stored version, served by the local application. The highlighted passage is the cited span." }),
      el("pre", { class: "source", lang: "und" }, c.text_before, el("mark", { text: c.quote }), c.text_after),
      el("h3", { text: "Used by" }),
      el("ul", {}, ...c.used_by.map((u) => el("li", { text: `${u.candidate_id} / ${u.requirement_id}: ${u.outcome} (${u.state})` }))),
      el("p", {}, "Other versions: ", ...c.all_versions.map((v) => el("button", { class: "cite", onclick: () => openSource(sid, v) }, `${sid} · ${v}`))),
      el("details", {}, el("summary", { text: "Technical details" }),
        el("p", { class: "mono", text: `sha256 ${c.sha256}` }),
        el("p", { class: "mono", text: `offsets ${c.start_char}–${c.end_char} (${c.offset_convention})` })));
  } catch (e) { body.replaceChildren(el("p", { class: "status error", text: `Could not open this citation: ${e.message} (${e.code}).` })); }
}

async function openSource(sid, vid) {
  const body = $("drawer-body"); $("drawer").hidden = false;
  try {
    const v = await api("GET", `/api/projects/${S.projectId}/sources/${sid}/versions/${vid}`);
    $("drawer-title").textContent = `${v.source_id} · ${v.version_id}`;
    body.replaceChildren(
      el("p", {}, el("b", { text: v.title }), " ", el("span", { class: `pill ${v.status}`, text: v.status === "current" ? "Current" : "Historical" })),
      el("p", {}, "Passages: ", ...v.passages.map((p) => el("button", { class: "cite", onclick: (ev) => openCitation(sid, vid, p.passage_id, ev.currentTarget) }, p.passage_id))),
      el("pre", { class: "source", text: v.text }),
      el("details", {}, el("summary", { text: "Technical details" }), el("p", { class: "mono", text: `sha256 ${v.sha256} · imported by ${v.import_event}` })));
    $("drawer-close").focus();
  } catch (e) { body.replaceChildren(el("p", { class: "status error", text: `Could not open this source: ${e.message} (${e.code}).` })); }
}

function closeDrawer() { $("drawer").hidden = true; if (S.lastFocus && document.contains(S.lastFocus)) S.lastFocus.focus(); }

async function renderSources() {
  await loadProject();
  const form = $("add-doc-form");
  form.hidden = isSample();
  if (!isSample()) {
    const sel = $("doc-candidate"), keep = sel.value;
    sel.replaceChildren(...S.project.mission.candidates.map((c) => el("option", { value: c.candidate_id, text: c.label })));
    if (keep) sel.value = keep;
  }
  const box = $("sources"); box.replaceChildren();
  if (!S.project.sources.length) box.append(el("p", { class: "muted", text: "No documents yet. Add a text or Markdown file above." }));
  const by = {};
  for (const s of S.project.sources) (by[s.source_id] ||= []).push(s);
  for (const [sid, vs] of Object.entries(by)) {
    box.append(el("div", { class: "card" }, el("h3", { text: `${sid} — ${vs[vs.length - 1].title}` }),
      ...vs.map((v) => el("p", {}, el("button", { class: "cite", onclick: () => openSource(sid, v.version_id) }, `${sid} · ${v.version_id}`), " ",
        el("span", { class: `pill ${v.status}`, text: v.status === "current" ? "Current" : "Historical" }), " ",
        el("span", { class: "muted", text: `${v.candidate_id} · imported ${new Date(v.imported_at).toLocaleString()} (${v.import_event})` })))));
  }
  for (const c of S.project.changes.filter((c) => c.status !== "applied"))
    box.append(el("div", { class: "card" }, el("h3", { text: `${c.source_id} · ${c.version_id}` }), el("span", { class: "pill incoming", text: "Incoming — not imported" }),
      el("p", { class: "muted", text: "This revision is not searchable and did not support any result. Apply it from the Workbench." })));
  box.append(el("p", { class: "muted", text: `Searchable index: ${S.project.searchable_index.passages} passages from ${S.project.searchable_index.source_versions.join(", ") || "no sources"}.` }));
}

function toBase64(buf) {
  const bytes = new Uint8Array(buf); let bin = "";
  for (let i = 0; i < bytes.length; i += 0x8000) bin += String.fromCharCode.apply(null, bytes.subarray(i, i + 0x8000));
  return btoa(bin);
}

async function addDocument(ev) {
  ev.preventDefault();
  const f = $("doc-file").files[0];
  if (!f) { status("Choose a file first.", true); return; }
  const btn = ev.submitter || ev.target.querySelector("button"); btn.disabled = true;
  status(`Adding ${f.name}…`);
  try {
    const r = await api("POST", `/api/projects/${S.projectId}/documents`, { filename: f.name, content_base64: toBase64(await f.arrayBuffer()),
      candidate_id: $("doc-candidate").value, source_id: $("doc-source-id").value.trim() || null });
    if (r.status === "unchanged") status(`${r.source_id} · ${r.version_id} already has exactly this content; nothing changed.`);
    else {
      if (r.run_id) S.liveRunId = r.run_id;
      const res = r.result || {};
      const rechecked = (res.reacquired || []).length + (res.revalidated_by_search || []).length;
      status(`${r.source_id} · ${r.version_id} added (${r.event_type === "source_revision" ? "new version" : "new source"}, ${r.passages} passages).` +
        (r.run_id ? ` ${rechecked} result(s) re-checked by run ${r.run_id}.` : " Run the comparison to use it."));
    }
    $("doc-file").value = ""; $("doc-source-id").value = "";
    await renderSources();
  } catch (e) { status(`Could not add the document: ${e.message} (${e.code}).`, true); }
  finally { btn.disabled = false; }
}

async function renderRuns() {
  await loadProject();
  const box = $("runs"); box.replaceChildren();
  if (!S.project.runs.length) { box.append(el("p", { class: "muted", text: "No runs yet." })); return; }
  box.append(el("table", { class: "matrix" }, el("thead", {}, el("tr", {}, ...["Run", "Kind", "State", "Stop reason", "Started", "Via"].map((h) => el("th", { scope: "col", text: h })))),
    el("tbody", {}, ...S.project.runs.slice().reverse().map((r) => el("tr", {},
      el("td", {}, el("button", { class: "cite", onclick: () => openRun(r.run_id) }, r.run_id)),
      el("td", { text: r.kind }), el("td", { text: `${r.status} (${r.execution_mode === "live_local" ? "Live local run" : r.execution_mode})` }),
      el("td", { text: r.stop_reason || "" }), el("td", { text: new Date(r.started_at).toLocaleString() }), el("td", { text: r.invoked_via }))))));
}

const ACTION_LABEL = { plan_obligation: "Plan obligation", search_current_sources: "Search current sources", read_passage: "Read passage",
  check_criterion: "Check criterion", commit_assessment: "Commit assessment", reuse_valid_result: "Reuse valid result", error: "Error",
  retrieval_setup: "Retrieval setup" };
async function openRun(runId) {
  const r = await api("GET", `/api/runs/${runId}`);
  const recorded = S.liveRunId !== runId;
  $("run-detail").replaceChildren(el("div", { class: "card" },
    el("h3", { text: `${r.run_id} · ${r.kind}` }),
    el("p", {}, el("span", { class: `label ${recorded ? "recorded" : "live"}`, text: recorded ? "Recorded run" : "Live local run" }),
      ` execution_mode=${r.execution_mode} · data_origin=${r.data_origin} · strategy=${r.strategy} · invoked via ${r.invoked_via} · ${r.status} (${r.stop_reason})`),
    el("p", { text: `Limits: ${r.limits.max_acquisition_actions} acquisition actions, ${r.limits.max_source_reads} source reads, ${r.limits.max_wall_seconds} s. ` +
      `Used: ${r.counters.acquisition_actions} acquisition action(s), ${r.counters.source_reads} source read(s). ` +
      (r.counters.retrieval_effective ? `Retrieval: ${r.counters.retrieval_effective}${r.counters.query_embeddings != null ? `, ${r.counters.query_embeddings} query embedding(s)` : ""}. ` : "Retrieval: lexical. ") +
      `Paid model calls: ${r.counters.paid_model_calls || 0}.` + (r.counters.retrieval_note ? ` Note: ${r.counters.retrieval_note}` : "") }),
    el("p", { class: "muted mono", text: `core ${r.core_identity} · config ${r.config_sha256.slice(0, 16)}…` }),
    el("ol", { class: "trace" }, ...r.actions.map((a) => el("li", {},
      el("b", { text: ACTION_LABEL[a.action_type] || a.action_type }), a.candidate_id ? ` — ${a.candidate_id}/${a.requirement_id}` : "", a.status !== "ok" ? ` (${a.status})` : "",
      el("details", {}, el("summary", { text: "details" }), el("pre", { class: "source mono", text: JSON.stringify(a.detail, null, 2) })))))));
  if (S.view !== "runs") show("runs");
  $("run-detail").scrollIntoView({ block: "start" });
}

async function renderChanges() {
  await loadProject();
  const box = $("changes"); box.replaceChildren();
  if (!S.project.changes.length) box.append(el("p", { class: "muted", text: "No changes yet." }));
  for (const c of S.project.changes.slice().reverse()) {
    const kind = CHANGE_LABEL[c.event_type] || c.event_type;
    const what = c.event_type === "source_addition" ? `${c.source_id} · ${c.version_id} added`
      : c.event_type === "retrieval_mode_change" ? `${c.supersedes_version_id} → ${c.version_id}`
      : c.event_type === "index_generation_switch" ? `${c.supersedes_version_id || "none"} → ${c.source_id}`
      : `${c.source_id} ${c.supersedes_version_id} → ${c.version_id}`;
    const card = el("div", { class: "card" }, el("h3", { text: `${kind}: ${what}` }),
      el("p", { class: "muted", text: `${c.event_id} · status: ${c.status}` }));
    if (c.result && c.result.run_id) {
      const res = c.result;
      card.append(el("p", {}, "Processed by run ", el("button", { class: "cite", onclick: () => openRun(res.run_id) }, res.run_id), ` (${res.execution_strategy}).`));
      if (res.retrieval) card.append(el("p", { class: "muted", text: `Retrieval during this update: ${res.retrieval.effective}` + (res.retrieval.refreshed_from ? ` (index rebuilt from ${res.retrieval.refreshed_from})` : "") + (res.retrieval.reason ? ` — ${res.retrieval.reason}` : "") }));
      card.append(el("h4", { text: `Changed results (${res.affected.length})` }));
      if (!res.affected.length) card.append(el("p", { class: "muted", text: "No result changed." }));
      for (const a of res.affected) {
        card.append(el("div", { class: "grid2" },
          a.before ? changeSide("Before", a.before) : el("div", { class: "card muted", text: "No earlier result" }), changeSide("After", a.after)));
      }
      card.append(el("h4", { text: "Unchanged" }),
        el("ul", {}, ...res.revalidated_by_search.map((k) => el("li", { text: `${k}: search re-executed; same evidence, assessment kept.` })),
          ...res.outside_changed_scope.map((k) => el("li", { text: `${k}: not affected by this change; not re-run.` }))));
    } else if (c.result && c.result.note) card.append(el("p", { class: "muted", text: c.result.note }));
    else card.append(el("p", { class: "muted", text: "Not applied yet." }));
    box.append(card);
  }
  box.append(el("p", { class: "muted", text: "Planned (not in this goal): withdrawal and effective-date events." }));
}
const CHANGE_LABEL = { source_revision: "Source revision", source_addition: "New source", retrieval_mode_change: "Retrieval mode",
  index_generation_switch: "Index generation" };
function changeSide(title, cell) {
  const c = cell.citation;
  return el("div", { class: "card" }, el("b", { text: `${title}: ${cell.candidate_id}/${cell.requirement_id}` }), " ",
    el("span", { class: `badge ${cell.outcome}`, text: `${ICON[cell.outcome]} ${cell.outcome.replaceAll("_", " ")}` }),
    el("p", { text: cell.explanation }),
    c ? el("button", { class: "cite", onclick: (ev) => openCitation(c.source_id, c.version_id, c.passage_id, ev.currentTarget) }, `${c.source_id} · ${c.version_id}`) : null);
}

const STATE_TEXT = { active: "Active", ready: "Ready", not_configured: "Not configured", configured_not_ready: "Configured, not ready",
  blocked_without_envelope: "Blocked (no spending envelope)", envelope_recorded: "Envelope recorded", unavailable: "Unavailable",
  installed_not_enabled: "Installed, not enabled", unchecked: "Not checked", blocked: "Blocked", failed: "Check failed",
  changed_since_check: "Changed since last check" };
const st = (s) => STATE_TEXT[s] || s;

async function renderProviders() {
  const [c, P] = await Promise.all([api("GET", "/api/capabilities"), api("GET", "/api/providers")]);
  S.caps = c; S.providers = P;
  S.retrieval = await api("GET", `/api/projects/${S.projectId}/retrieval`);
  const role = (n, p, extra) => el("div", { class: "card" }, el("h3", { text: `${n} — ${st(p.state)}` }),
    el("p", { class: "muted", text: extra || (p.profiles && p.profiles.length ? p.profiles.join(", ") : "No profile.") }));
  $("providers").replaceChildren(el("div", { class: "grid3" },
    role("Lexical search", c.lexical, c.lexical.description), role("Chat model", c.chat), role("Embedding model", c.embedding),
    role("Reranker", c.rerank), role("Paid API", c.api_model, c.api_model.description),
    role("PDF ingestion", c.ingestion.pdf, c.ingestion.pdf.description)),
    el("p", { class: "muted", text: `Model downloads allowed: ${c.model_downloads_allowed ? "yes" : "no"} · parser ${c.parser_profile} · store ${c.store_path}` }));
  renderRetrieval(); renderProfiles();
  const tpl = $("pf-template");
  if (!tpl.options.length) {
    tpl.replaceChildren(el("option", { value: "", text: "Blank profile" }), ...P.templates.map((t, i) => el("option", { value: String(i), text: t.label })));
    tpl.addEventListener("change", () => fillProfileForm(tpl.value === "" ? {} : S.providers.templates[Number(tpl.value)]));
  }
}

function renderRetrieval() {
  const R = S.retrieval, box = $("retrieval");
  const ready = S.providers.profiles.filter((p) => p.role === "embedding" && p.status === "ready");
  const active = R.generations.find((g) => g.generation_id === R.active_generation_id);
  const pick = el("select", { id: "idx-profile", "aria-label": "Embedding profile" }, ...ready.map((p) => el("option", { value: p.profile_id, text: p.profile_id })));
  box.replaceChildren(el("div", { class: "card" },
    el("p", {}, el("b", { text: `Mode: ${R.retrieval_mode === "hybrid" ? "Hybrid (lexical + dense)" : "Lexical"}` })),
    el("p", { class: "muted", text: active ? `Active index ${active.generation_id}: ${active.n_vectors} passages, ${active.dimension} dimensions, profile ${active.profile_id} · ${R.active_freshness === "fresh" ? "matches the current sources" : "out of date: rebuilt automatically before the next hybrid search"}` : "No dense index yet." }),
    ready.length ? el("p", {}, pick, " ", el("button", { onclick: buildIndex }, active ? "Rebuild index" : "Build index")) :
      el("p", { class: "muted", text: "To build a dense index, add an embedding profile below and run its check." }),
    el("p", {}, el("button", { disabled: R.retrieval_mode === "lexical" ? "" : null, onclick: () => setMode("lexical") }, "Use lexical"), " ",
      el("button", { disabled: R.retrieval_mode === "hybrid" || !active ? "" : null, onclick: () => setMode("hybrid") }, "Use hybrid")),
    R.generations.length > 1 ? el("details", {}, el("summary", { text: `All index generations (${R.generations.length})` }),
      el("ul", {}, ...R.generations.map((g) => el("li", { class: "mono", text: `${g.generation_id} · ${g.status} · ${g.n_vectors} vectors · ${g.embedded_vectors} embedded, ${g.reused_vectors} reused` })))) : null));
}

function renderProfiles() {
  const box = $("profiles"), ps = S.providers.profiles;
  if (!ps.length) { box.replaceChildren(el("p", { class: "muted", text: "No profiles yet. Lexical mode needs none." })); return; }
  box.replaceChildren(el("table", { class: "matrix" },
    el("thead", {}, el("tr", {}, ...["Profile", "Role", "Model", "Where", "Status", ""].map((h) => el("th", { scope: "col", text: h })))),
    el("tbody", {}, ...ps.map((p) => el("tr", {},
      el("td", { text: p.profile_id }), el("td", { text: p.role }), el("td", { text: `${p.model_id} (${p.adapter})` }),
      el("td", { text: `${p.locality}${p.paid_route ? " · paid route" : ""}${p.credential_ref ? ` · key ${p.credential_ref}: ${p.credential_present ? "set" : "not set"}` : ""}` }),
      el("td", {}, el("span", { class: `pill ${p.status === "ready" ? "current" : "historical"}`, text: st(p.status) }),
        p.last_check ? el("details", {}, el("summary", { text: "check details" }),
          el("ul", {}, ...p.last_check.items.map((i) => el("li", { text: `${i.check}: ${i.state}${i.detail ? ` — ${i.detail}` : ""}` })))) : null),
      el("td", {}, el("button", { onclick: () => checkProfile(p.profile_id) }, "Check"), " ",
        el("button", { onclick: () => fillProfileForm(p) }, "Edit"), " ",
        el("button", { onclick: () => deleteProfile(p.profile_id) }, "Delete")))))));
}

function fillProfileForm(p) {
  $("pf-id").value = p.profile_id || ""; $("pf-role").value = p.role || "chat"; $("pf-adapter").value = p.adapter || "ollama";
  $("pf-model").value = p.model_id || ""; $("pf-endpoint").value = p.endpoint || ""; $("pf-cred").value = p.credential_ref || "";
  $("pf-qprefix").value = p.query_prefix || ""; $("pf-remote").checked = !!p.allow_remote;
  $("pf-cap").value = p.spend_cap_usd || 0; $("pf-max").value = p.max_requests || 0;
  $("pf-id").focus();
}

async function saveProfile(ev) {
  ev.preventDefault();
  const body = { profile_id: $("pf-id").value.trim(), role: $("pf-role").value, adapter: $("pf-adapter").value,
    model_id: $("pf-model").value.trim(), credential_ref: $("pf-cred").value.trim() || null, allow_remote: $("pf-remote").checked,
    spend_cap_usd: Number($("pf-cap").value || 0), max_requests: Number($("pf-max").value || 0) };
  if ($("pf-endpoint").value.trim()) body.endpoint = $("pf-endpoint").value.trim();
  if (body.role === "embedding" && $("pf-qprefix").value) body.query_prefix = $("pf-qprefix").value;
  try { await api("POST", "/api/providers", body); status(`Profile ${body.profile_id} saved. Select Check to test it.`); await renderProviders(); }
  catch (e) { status(`Profile not saved: ${e.message}`, true); }
}

async function checkProfile(id) {
  status(`Checking ${id}…`);
  try { const d = await api("POST", `/api/providers/${id}/check`, {}); status(`${id}: ${st(d.status)}.`, d.status !== "ready"); }
  catch (e) { status(`Check failed: ${e.message}`, true); }
  await renderProviders();
}

async function deleteProfile(id) {
  try { await api("POST", `/api/providers/${id}/delete`, {}); status(`Profile ${id} deleted.`); }
  catch (e) { status(`Not deleted: ${e.message}`, true); }
  await renderProviders();
}

async function buildIndex() {
  const pid = $("idx-profile").value; status(`Building a dense index with ${pid}…`);
  try {
    const r = await api("POST", `/api/projects/${S.projectId}/index`, { profile_id: pid });
    const g = r.generation; if (r.run_id) S.liveRunId = r.run_id;
    status(`Index ${g.generation_id} active: ${g.n_vectors} passages (${g.embedded_vectors} embedded, ${g.reused_vectors} reused).`);
  } catch (e) { status(`Index not built: ${e.message}`, true); }
  await renderProviders(); labels();
}

async function setMode(mode) {
  status(`Switching to ${mode} retrieval…`);
  try {
    const r = await api("POST", `/api/projects/${S.projectId}/retrieval`, { mode });
    if (r.run_id) S.liveRunId = r.run_id;
    status(`Retrieval is now ${mode}.` + (r.run_id ? ` Results re-checked by run ${r.run_id}.` : ""));
  } catch (e) { status(`Mode not changed: ${e.message}`, true); }
  await loadProject(); await renderProviders();
}

async function run() {
  const b = $("run"); b.disabled = true; b.textContent = "Running…"; status("Running the comparison with the local engine…");
  try {
    const r = await api("POST", `/api/projects/${S.projectId}/runs`, {});
    S.liveRunId = r.run_id;
    await loadProject();
    status(`Run ${r.run_id} ${r.status}: ${r.counters.acquisition_actions} searches, ${r.counters.source_reads} passage reads.`);
  } catch (e) { status(`Run failed: ${e.message}. Previous results stay available.`, true); }
  finally { b.disabled = false; b.textContent = "Run comparison"; }
}

async function applyChange() {
  const b = $("apply-change"); b.disabled = true; status("Reviewing affected evidence…");
  try {
    const r = await api("POST", `/api/projects/${S.projectId}/changes`, { event_id: "CHANGE-S2-V2" });
    S.liveRunId = r.run_id;
    await loadProject();
    status(r.already_applied ? "This revision was already applied; showing the recorded result." :
      `Revision applied by run ${r.run_id}: ${r.result.affected.length} affected, ${r.result.unchanged.length} unchanged.`);
    show("changes");
  } catch (e) { status(`Revision failed: ${e.message}. The prior committed result is still shown.`, true); b.disabled = false; }
}

async function openSample() {
  status("Opening the sample project…");
  try {
    const r = await api("POST", "/api/demo/bootstrap", {});
    S.projectId = r.project_id;
    await loadProjectList();
    await loadProject();
    status(r.reopened ? "Sample project reopened from the local store." : "Sample project created. Four sources imported; nothing has been run yet.");
    show("workbench");
  } catch (e) { status(`Could not open the sample: ${e.message}`, true); }
}

async function createProject(ev) {
  ev.preventDefault();
  const title = $("new-project-title").value.trim();
  try {
    const r = await api("POST", "/api/projects", { title });
    S.projectId = r.project_id; $("new-project-title").value = "";
    await loadProjectList(); await loadProject();
    status(`Project "${r.title}" created. Add your documents on the Evidence page.`);
    show("evidence");
  } catch (e) { status(`Project not created: ${e.message}`, true); }
}

async function switchProject() {
  const v = $("project-select").value;
  if (v === "__new") { S.projectId = null; S.project = null; labels(); show("workbench"); status("Open the sample or create a project."); return; }
  S.projectId = v; S.liveRunId = null;
  await loadProject();
  status(`Opened ${S.project.title} (recorded results).`);
  show(S.view);
}

async function init() {
  for (const b of document.querySelectorAll(".tab")) b.addEventListener("click", () => S.projectId ? show(b.dataset.view) : status("Open the sample or create a project first."));
  $("open-sample").addEventListener("click", openSample);
  $("new-project-form").addEventListener("submit", createProject);
  $("add-doc-form").addEventListener("submit", addDocument);
  $("profile-form").addEventListener("submit", saveProfile);
  $("project-select").addEventListener("change", switchProject);
  $("run").addEventListener("click", run);
  $("apply-change").addEventListener("click", applyChange);
  $("trace-link").addEventListener("click", (e) => { e.preventDefault(); if (S.comparison.last_run) openRun(S.comparison.last_run.run_id); });
  $("drawer-close").addEventListener("click", closeDrawer);
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && !$("drawer").hidden) closeDrawer(); });
  try {
    const projects = await loadProjectList();
    if (projects.length) { S.projectId = projects[0].project_id; $("project-select").value = S.projectId; await loadProject(); status(`Reopened ${S.project.title} (recorded results).`); }
  } catch (e) { status(`Server not reachable: ${e.message}`, true); }
  show("workbench");
}
init();
