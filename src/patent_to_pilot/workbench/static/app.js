// Patent-to-Pilot Workbench (PTP-2026-11-21/G01). All results come from the local server; nothing is computed
// or pre-written here. Data are rendered with textContent (no HTML injection).
"use strict";

const S = { projectId: null, project: null, comparison: null, caps: null, liveRunId: null, view: "workbench",
  lastFocus: null };

const $ = (id) => document.getElementById(id);
function el(tag, attrs = {}, ...kids) {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
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
  L.append(el("span", { class: "label", text: "Sample data" }));
  const last = S.comparison && S.comparison.last_run;
  if (last) {
    if (S.liveRunId === last.run_id) L.append(el("span", { class: "label live", text: "Live local run" }));
    else L.append(el("span", { class: "label recorded", text: `Recorded run · ${last.run_id}` }));
  }
  L.append(el("span", { class: "label", text: "Lexical mode" }));
}

async function loadProject() {
  S.project = await api("GET", `/api/projects/${S.projectId}`);
  S.comparison = await api("GET", `/api/projects/${S.projectId}/comparison`);
  $("project-title").textContent = S.project.title;
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
      el("p", {}, el("b", { text: c.title }), " ", badge, " ", el("span", { class: "pill", text: "Sample data" })),
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
  const box = $("sources"); box.replaceChildren();
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
  box.append(el("p", { class: "muted", text: `Searchable index: ${S.project.searchable_index.passages} passages from ${S.project.searchable_index.source_versions.join(", ")}.` }));
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
  check_criterion: "Check criterion", commit_assessment: "Commit assessment", reuse_valid_result: "Reuse valid result", error: "Error" };
async function openRun(runId) {
  const r = await api("GET", `/api/runs/${runId}`);
  const recorded = S.liveRunId !== runId;
  $("run-detail").replaceChildren(el("div", { class: "card" },
    el("h3", { text: `${r.run_id} · ${r.kind}` }),
    el("p", {}, el("span", { class: `label ${recorded ? "recorded" : "live"}`, text: recorded ? "Recorded run" : "Live local run" }),
      ` execution_mode=${r.execution_mode} · data_origin=${r.data_origin} · strategy=${r.strategy} · invoked via ${r.invoked_via} · ${r.status} (${r.stop_reason})`),
    el("p", { text: `Limits: ${r.limits.max_acquisition_actions} acquisition actions, ${r.limits.max_source_reads} source reads, ${r.limits.max_wall_seconds} s. ` +
      `Used: ${r.counters.acquisition_actions} acquisition action(s), ${r.counters.source_reads} source read(s). No paid model calls enabled.` }),
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
  for (const c of S.project.changes) {
    const card = el("div", { class: "card" }, el("h3", { text: `${c.event_id}: ${c.source_id} ${c.supersedes_version_id} → ${c.version_id}` }),
      el("p", { text: `Type: source revision · status: ${c.status}` }));
    if (c.result) {
      const res = c.result;
      card.append(el("p", {}, "Processed by run ", el("button", { class: "cite", onclick: () => openRun(res.run_id) }, res.run_id), ` (${res.execution_strategy}).`));
      card.append(el("h4", { text: "Affected" }));
      for (const a of res.affected) {
        card.append(el("div", { class: "grid2" },
          changeSide("Before", a.before), changeSide("After", a.after)));
      }
      card.append(el("h4", { text: "Unchanged" }),
        el("ul", {}, ...res.revalidated_by_search.map((k) => el("li", { text: `${k}: search re-executed on the new current sources; same evidence, assessment kept.` })),
          ...res.outside_changed_scope.map((k) => el("li", { text: `${k}: the changed source is outside this candidate's search scope; not re-run.` }))));
    } else card.append(el("p", { class: "muted", text: "Not applied yet." }));
    box.append(card);
  }
  box.append(el("p", { class: "muted", text: "Planned (not in this goal): new document, withdrawal and effective-date events." }));
}
function changeSide(title, cell) {
  const c = cell.citation;
  return el("div", { class: "card" }, el("b", { text: `${title}: ${cell.candidate_id}/${cell.requirement_id}` }), " ",
    el("span", { class: `badge ${cell.outcome}`, text: `${ICON[cell.outcome]} ${cell.outcome.replaceAll("_", " ")}` }),
    el("p", { text: cell.explanation }),
    c ? el("button", { class: "cite", onclick: (ev) => openCitation(c.source_id, c.version_id, c.passage_id, ev.currentTarget) }, `${c.source_id} · ${c.version_id}`) : null);
}

async function renderProviders() {
  S.caps = S.caps || await api("GET", "/api/capabilities");
  const c = S.caps;
  $("providers").replaceChildren(
    ...[["Lexical", c.lexical], ["Local model", c.local_model], ["API model", c.api_model]].map(([n, p]) =>
      el("div", { class: "card" }, el("h3", { text: `${n} — ${p.state === "active" ? "Active" : "Not enabled"}` }), el("p", { text: p.description }))),
    el("p", { class: "muted", text: `Remote calls allowed: ${c.remote_calls_allowed ? "yes" : "no"} · model downloads allowed: ${c.model_downloads_allowed ? "yes" : "no"} · parser ${c.parser_profile}` }),
    el("p", { class: "muted mono", text: `store ${c.store_path}` }));
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
    await loadProject();
    status(r.reopened ? "Sample project reopened from the local store." : "Sample project created. Four sources imported; nothing has been run yet.");
    show("workbench");
  } catch (e) { status(`Could not open the sample: ${e.message}`, true); }
}

async function init() {
  for (const b of document.querySelectorAll(".tab")) b.addEventListener("click", () => S.projectId ? show(b.dataset.view) : status("Open the sample project first."));
  $("open-sample").addEventListener("click", openSample);
  $("run").addEventListener("click", run);
  $("apply-change").addEventListener("click", applyChange);
  $("trace-link").addEventListener("click", (e) => { e.preventDefault(); if (S.comparison.last_run) openRun(S.comparison.last_run.run_id); });
  $("drawer-close").addEventListener("click", closeDrawer);
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && !$("drawer").hidden) closeDrawer(); });
  try {
    const { projects } = await api("GET", "/api/projects");
    if (projects.length) { S.projectId = projects[0].project_id; await loadProject(); status("Reopened the saved sample project (recorded results)."); }
  } catch (e) { status(`Server not reachable: ${e.message}`, true); }
  show("workbench");
}
init();
