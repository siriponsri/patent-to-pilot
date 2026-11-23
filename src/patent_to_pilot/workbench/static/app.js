// Patent-to-Pilot Workbench (PTP-2026-11-21/G01–G02; P4-T01 Search, Compare and Inspect). All results come from the local server; nothing is computed
// or pre-written here. Data are rendered with textContent (no HTML injection).
"use strict";

const S = { projectId: null, project: null, comparison: null, caps: null, liveRunId: null, view: "workbench",
  lastFocus: null, retrieval: null, providers: null, showRemoved: false, undoTimer: null, mode: null };
const isSample = () => S.project && S.project.data_origin === "synthetic_fixture";
const isSynthetic = () => S.project && S.project.data_origin === "synthetic_demo";
const VIEWS = ["workbench", "search", "compare", "evidence", "runs", "changes", "providers"];

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
  for (const v of VIEWS) $("view-" + v).hidden = !S.projectId || v !== view;
  $("welcome").hidden = !!S.projectId;
  if (view === "search") renderSearch();
  if (view === "compare") renderCompare();
  if (view === "evidence") renderSources();
  if (view === "runs") renderRuns();
  if (view === "changes") renderChanges();
  if (view === "providers") renderProviders();
}

function labels() {
  const L = $("labels"); L.replaceChildren();
  if (!S.projectId) return;
  L.append(el("span", { class: "label", text: isSample() ? "Sample data" : isSynthetic() ? "Synthetic example" : "Your files" }));
  const last = S.comparison && S.comparison.last_run;
  if (last) {
    if (S.liveRunId === last.run_id) L.append(el("span", { class: "label live", text: "Live local run" }));
    else L.append(el("span", { class: "label recorded", text: `Recorded run · ${last.run_id}` }));
  }
  // P4-T02: the active execution mode and exact model, from the server (no network probe)
  const M = S.mode && S.mode.active;
  if (M) {
    const fallback = M.effective === "lexical_fallback";
    const txt = `Mode: ${M.mode_text}` + (M.model_id && !fallback ? ` · ${M.model_id}` : "") +
      (M.retrieval_mode === "hybrid" ? (fallback ? ` · hybrid requested, ${M.model_id || M.profile_id} unavailable → lexical` :
        (M.index_fresh ? " · hybrid" : " · hybrid, index out of date (rebuilt on next run)")) : " · lexical search");
    L.append(el("span", { class: `label mode ${fallback ? "warn" : ""}`, id: "mode-label", title: M.summary, text: txt }));
  }
  const miss = S.mode ? S.mode.missing.length : 0;
  if (miss) L.append(el("button", { class: "label linkish", title: "Open Providers to see what is missing and why",
    onclick: () => show("providers") }, `${miss} optional capabilit${miss === 1 ? "y" : "ies"} missing`));
}

async function loadMode() {
  try { S.mode = await api("GET", S.projectId ? `/api/projects/${S.projectId}/execution-mode` : "/api/execution-mode"); }
  catch (e) { S.mode = null; }
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
  await loadMode();
  $("project-title").textContent = $("project-select").hidden ? S.project.title : "";
  renderWorkbench(); labels();
}

function reqLabel(rid) { const r = S.project.mission.requirements.find((x) => x.requirement_id === rid); return r ? r.label : rid; }

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
  if (!P.mission.requirements.length) { wrap.replaceChildren(el("p", { class: "muted", text: "No active requirements. Add one on the Compare page; removed requirements can be restored there." })); return; }
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

const ICON = { meets: "✓", does_not_meet: "✕", unknown: "?", needs_review: "!", evidence_found: "•" };
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
      el("p", {}, el("button", { onclick: (ev) => openSpan(sid, vid, c.start_char, c.end_char, ev.currentTarget) }, "Inspect source (page and original file)")),
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

// ---------------- P4-T01: Inspect any span of a stored source version
async function openSpan(sid, vid, start, end, trigger) {
  S.lastFocus = trigger || document.activeElement;
  const body = $("drawer-body"); body.replaceChildren(el("p", { text: "Loading the source version…" }));
  $("drawer").hidden = false; $("drawer-close").focus();
  try {
    const x = await api("GET", `/api/projects/${S.projectId}/sources/${sid}/versions/${vid}/spans/${start}/${end}`);
    $("drawer-title").textContent = `Inspect · ${x.source_id} · ${x.version_id}`;
    const badge = x.status === "current" ? el("span", { class: "pill current", text: "Current" }) : el("span", { class: "pill historical", text: `Superseded (current: ${x.current_version})` });
    const M = x.page_mapping, O = x.original_artifact;
    const pageInfo = M.state === "regions" ? el("div", {},
        el("p", {}, el("b", { text: `Page ${M.pages.join(", ")}` }), ` — ${M.regions.length} recorded region(s).`),
        el("ul", {}, ...M.regions.map((r) => el("li", { class: "mono", text: `${r.node_id} (${r.kind}): page ${r.page}, box ${r.bbox.map((v) => v.toFixed(3)).join(", ")}` }))),
        el("p", { class: "muted", text: M.basis }))
      : M.state === "page_only" ? el("div", {}, el("p", {}, el("b", { text: `Page ${M.pages.join("–")}` }), " (no region inside the page)."), el("p", { class: "muted", text: M.basis }))
      : el("p", { class: "muted", text: `No page or region mapping: ${M.reason}` });
    const origInfo = O.state === "kept"
      ? el("p", {}, el("a", { href: O.url, target: "_blank", rel: "noopener" }, `Open the original file (${O.media_type}, ${O.size_bytes} bytes)`),
          ` · integrity ${O.integrity}` + (O.same_bytes_as_canonical_text ? " · the original is the stored text itself" : " · stored separately from the extracted text"))
      : el("p", { class: "muted", text: O.note });
    body.replaceChildren(
      el("p", {}, el("b", { text: x.title }), " ", badge, " ", el("span", { class: "pill", text: x.data_origin === "synthetic_fixture" ? "Sample data" : x.data_origin === "synthetic_demo" ? "Synthetic example" : "Your file" })),
      el("h3", { text: "Page and region" }), pageInfo,
      el("h3", { text: "Original file" }), origInfo,
      el("h3", { text: "Exact text" }),
      el("p", { class: "muted", text: "The stored text of this version; the highlighted span is the evidence. Its hash was re-checked just now." }),
      el("pre", { class: "source", lang: "und" }, x.text_before, el("mark", { text: x.quote }), x.text_after),
      x.passages.length ? el("p", {}, "Passages here: ", ...x.passages.map((p) => el("button", { class: "cite", onclick: (ev) => openCitation(sid, vid, p.passage_id, ev.currentTarget) }, p.passage_id))) : null,
      el("details", {}, el("summary", { text: "Technical details" }),
        el("p", { class: "mono", text: `sha256 ${x.sha256} (${x.stored_text_integrity})` }),
        el("p", { class: "mono", text: `offsets ${x.start_char}–${x.end_char} (${x.offset_convention})` }),
        el("p", { class: "mono", text: `${x.source_kind} · ${x.license} · ${x.origin_path}` }),
        O.state === "kept" ? el("p", { class: "mono", text: `original sha256 ${O.sha256} · ${O.storage_ref}` }) : null));
    const m = body.querySelector("mark"); if (m) m.scrollIntoView({ block: "center" });
  } catch (e) { body.replaceChildren(el("p", { class: "status error", text: `Could not open this span: ${e.message} (${e.code}).` })); }
}

// ---------------- P4-T01: Search
function marked(text, offset, matches) {
  // server offsets are Unicode code points (not UTF-16 units): slice an array of code points (P4-T01a)
  const cp = Array.from(text), cut = (a, b) => cp.slice(a, b).join("");
  const out = []; let pos = 0;
  for (const m of matches) {
    const a = m.start_char - offset, b = m.end_char - offset;
    if (b <= pos || a >= cp.length) continue;
    const s = Math.max(a, pos), e = Math.min(b, cp.length);
    out.push(cut(pos, s), el("mark", { text: cut(s, e) })); pos = e;
  }
  out.push(cut(pos, cp.length));
  return out;
}

function renderSearch() {
  const sel = $("search-cand"), keep = sel.value;
  sel.replaceChildren(el("option", { value: "", text: "All candidates" }), ...S.project.mission.candidates.map((c) => el("option", { value: c.candidate_id, text: c.label })));
  sel.value = keep;
  $("search-q").focus();
}

const ROUTE_LABEL = { identifier: "section number", all_words: "all words", any_word: "some words", phrase: "phrase", substring: "text inside a longer word", legacy_any_word: "some words (no Thai segmentation)" };

async function doSearch(ev) {
  ev.preventDefault();
  const q = $("search-q").value;
  if (!q.trim()) { status("Type something to search for.", true); return; }
  status("Searching the local index…");
  try {
    const r = await api("POST", `/api/projects/${S.projectId}/search`, { query: q, mode: $("search-mode").value, candidate_id: $("search-cand").value || null, limit: 20 });
    $("search-meta").replaceChildren(
      el("p", { text: `${r.result_count} result(s) from ${r.index.passages} current passages (${r.index.source_versions.join(", ") || "no sources"}). Route: ${r.route}.` + (r.fts_match ? ` Issued: ${r.fts_match}` : "") + (r.elapsed_ms != null ? ` (${r.elapsed_ms} ms)` : "") }),
      ...(r.lexical_trace && r.lexical_trace.fallback.triggered ? [el("p", { class: "muted", text: `Bounded text check: ${r.lexical_trace.fallback.reasons.join(", ")}; ${r.lexical_trace.fallback.scanned} passages scanned, ${r.lexical_trace.fallback.returned} found.` })] : []),
      ...r.notes.map((n) => el("p", { class: "status", text: n })));
    $("search-results").replaceChildren(...r.results.map((h) => el("div", { class: "card result" },
      el("h3", { text: `${h.rank}. ${h.title}` }),
      el("p", { class: "meta", text: `${h.source_id} · ${h.version_id} · passage ${h.passage_id} · ${h.candidate_id}` + (h.route ? ` · ${ROUTE_LABEL[h.route] || h.route}` : "") + (h.score_bm25 != null ? ` · BM25 ${h.score_bm25}` : "") + ` · characters ${h.start_char}–${h.end_char}` }),
      el("p", { class: "quote", lang: "und" }, h.snippet_truncated && h.snippet_start_char > h.start_char ? "… " : "", ...marked(h.snippet, h.snippet_start_char, h.matches), h.snippet_truncated && h.snippet_end_char < h.end_char ? " …" : ""),
      el("button", { onclick: (e) => openSpan(h.source_id, h.version_id, h.start_char, h.end_char, e.currentTarget) }, "Inspect source"))));
    status(`${r.result_count} result(s) for "${q}".`);
  } catch (e) { status(`Search failed: ${e.message} (${e.code}).`, true); }
}

// ---------------- P4-T01: Compare
async function renderCompare() {
  try {
    const R = await api("GET", `/api/projects/${S.projectId}/requirements`);
    const list = $("req-list");
    if (R.bound_requirements) list.replaceChildren(...R.bound_requirements.map((b) => el("div", { class: "card" },
      el("b", { text: b.requirement_id }), ` — "${b.text}" (span ${b.start_char}–${b.end_char} of the question "${b.query_text}")`)));
    else if (!R.requirements.length) list.replaceChildren(el("p", { class: "muted", text: "No requirements yet." }));
    else list.replaceChildren(el("table", { class: "matrix" },
      el("thead", {}, el("tr", {}, ...["ID", "Requirement", "Kind", "Search", ""].map((h) => el("th", { scope: "col", text: h })))),
      el("tbody", {}, ...R.requirements.map((r) => el("tr", {},
        el("td", { text: r.requirement_id }), el("td", { text: r.label }),
        el("td", { text: r.kind === "text" ? "Free text (evidence only)" : `Bounded field: ${r.field}` }),
        el("td", { class: "mono", text: r.fts_match }),
        el("td", {}, R.editable && r.kind === "text" ? el("button", { onclick: () => editRequirement(r) }, "Edit") : null,
          R.editable ? " " : null,
          R.editable ? el("button", { "aria-label": `Remove requirement ${r.requirement_id}`, onclick: (e) => removeRequirement(r, e.currentTarget) }, "Remove") : null))))));
    if (R.editable && R.removed && R.removed.length) list.append(removedList(R.removed));
    $("req-form").hidden = !R.editable;
    $("req-fixed").hidden = R.editable; $("req-fixed").textContent = R.note || "";
  } catch (e) { status(`Could not load requirements: ${e.message}`, true); }
}

// ---------------- P4-T01b: Remove / Undo (the server keeps the ID, text and history; nothing is deleted)
function removedList(removed) {
  const box = el("div", { class: "removed" });
  const toggle = el("button", { "aria-expanded": String(S.showRemoved), onclick: () => { S.showRemoved = !S.showRemoved; renderCompare(); } },
    S.showRemoved ? `Hide removed (${removed.length})` : `Show removed (${removed.length})`);
  box.append(toggle);
  if (S.showRemoved) box.append(el("ul", {}, ...removed.map((x) => el("li", {},
    el("span", { text: `${x.requirement_id} — ${x.requirement.label} ` }),
    el("span", { class: "muted", text: `(removed ${new Date(x.removed_at).toLocaleString()}) ` }),
    el("button", { onclick: () => restoreRequirement(x.requirement_id, x.lifecycle_revision) }, "Restore")))));
  return box;
}

async function removeRequirement(r, btn) {
  if (btn) btn.disabled = true;   // one click is enough; a repeated request is answered "already removed"
  try {
    const res = await api("POST", `/api/projects/${S.projectId}/requirements/${encodeURIComponent(r.requirement_id)}/archive`,
      { expected_revision: r.lifecycle_revision });
    status(`Requirement ${res.requirement_id} removed. Its earlier results stay in history; Undo or Show removed brings it back.`);
    showUndo(res.requirement_id, res.status === "removed" ? res.lifecycle_revision : null, r.label);
    await loadProject(); await renderCompare();
  } catch (e) {
    status(`Requirement not removed: ${e.message} (${e.code}).`, true);
    if (btn) btn.disabled = false;
  }
}

async function restoreRequirement(rid, revision) {
  hideUndo();
  try {
    const body = revision == null ? {} : { expected_revision: revision };
    const res = await api("POST", `/api/projects/${S.projectId}/requirements/${encodeURIComponent(rid)}/restore`, body);
    status(res.status === "already_active" ? `Requirement ${rid} is already active.` : `Requirement ${rid} restored. Run compare to assess it against the current sources.`);
    await loadProject(); await renderCompare();
  } catch (e) { status(`Requirement not restored: ${e.message} (${e.code}).`, true); }
}

function hideUndo() { const t = $("undo-toast"); if (t) t.remove(); if (S.undoTimer) { clearTimeout(S.undoTimer); S.undoTimer = null; } }

function showUndo(rid, revision, label) {
  hideUndo();
  const t = el("div", { id: "undo-toast", class: "toast", role: "status", "aria-live": "polite" },
    el("span", { text: `Removed ${rid}${label ? ` — ${label}` : ""}. ` }),
    el("button", { class: "primary", onclick: () => restoreRequirement(rid, revision) }, "Undo"),
    el("button", { "aria-label": "Dismiss", onclick: hideUndo }, "×"));
  document.body.append(t);
  S.undoTimer = setTimeout(hideUndo, 10000);
}

function editRequirement(r) {
  $("req-form-title").textContent = `Edit requirement ${r.requirement_id}`;
  $("req-id").value = r.requirement_id; $("req-label").value = r.label; $("req-query").value = r.query === r.label ? "" : r.query;
  $("req-match").value = r.match || "terms"; $("req-label").focus();
}

async function saveRequirement(ev) {
  ev.preventDefault();
  const body = { label: $("req-label").value, query: $("req-query").value || null, match: $("req-match").value };
  if ($("req-id").value.trim()) body.requirement_id = $("req-id").value.trim();
  try {
    const r = await api("POST", `/api/projects/${S.projectId}/requirements`, body);
    status(r.status === "unchanged" ? `Requirement ${r.requirement.requirement_id} is unchanged.` : `Requirement ${r.requirement.requirement_id} ${r.status}. Run compare to assess it.`);
    $("req-form").reset(); $("req-form-title").textContent = "Add a requirement";
    await loadProject(); await renderCompare();
  } catch (e) { status(`Requirement not saved: ${e.message} (${e.code}).`, true); }
}

function candList(cards, newIds) {
  if (!cards.length) return el("p", { class: "muted", text: "No candidate." });
  return el("ol", { class: "cands" }, ...cards.map((c) => {
    const isNew = !!(newIds && newIds.includes(c.node_id));
    return el("li", {},
      isNew ? el("span", { class: "pill new", text: "New" }) : null, isNew ? " " : null,
      el("span", { class: "mono", text: c.node_id }),
      el("div", { class: "quote", lang: "und", text: c.quote.length > 220 ? c.quote.slice(0, 220) + " …" : c.quote }),
      el("button", { class: "cite", onclick: (e) => openSpan(c.source_id, c.version_id, c.start_char, c.end_char, e.currentTarget) }, "Inspect source"));
  }));
}

function sideBySide(sb) {
  return el("div", { class: "card" },
    el("p", { class: "demo", text: sb.label }),
    el("p", { text: sb.summary }),
    el("div", { class: "grid2" },
      el("div", {}, el("h4", { text: `Baseline: seed search (${sb.baseline.ids.length})` }), el("p", { class: "mono", text: `Issued: ${sb.seed_query}` }), candList(sb.baseline.candidates)),
      el("div", {}, el("h4", { text: `With one relation search (${sb.action.after_ids.length}, ${sb.action.new_ids.length} new)` }),
        el("p", { class: "mono", text: sb.issued_query ? `Issued: ${sb.issued_query}` : "No extra search issued." }),
        candList(sb.action.candidates, sb.action.new_ids))),
    el("details", {}, el("summary", { text: "How this was found" }),
      el("ul", {},
        el("li", { text: `Form: ${sb.form}` }), el("li", { text: `Policy: ${sb.policy.name} (sha256 ${sb.policy.sha256.slice(0, 16)}…)` }),
        el("li", { text: `Coverage signal: ${sb.reference_detector}` }), el("li", { text: `Eligibility: ${sb.eligibility}` }),
        el("li", { text: `Selected relation: ${sb.selected_relation || "none"}` }),
        sb.requirement_status_before ? el("li", { text: `Runtime status (not gold): ${sb.requirement_status_before} → ${sb.requirement_status_after}` }) : null,
        el("li", { text: `Searches: ${sb.search_calls} (budget ${sb.budget.used}/${sb.budget.limit}) · paid model calls ${sb.paid_model_calls}` }),
        el("li", { text: sb.recorded_in_store ? `Recorded as run ${sb.run_id}.` : "Not recorded in the run history (read-only demonstration)." })),
      sb.query_terms.length ? el("ul", {}, ...sb.query_terms.map((t) => el("li", { class: "mono", text: `"${t.text}" — ${t.origin}${t.ref_id ? ` (${t.ref_id})` : ""}` }))) : null));
}

// P4-T03: the structural acquisition step as recorded in the run (persisted receipt), never recomputed here.
function acquisitionTrace(items, rows) {
  const label = (cid) => { const r = rows.find((x) => x.candidate_id === cid); return r ? r.candidate_label : cid; };
  return el("div", { class: "card" },
    el("h4", { text: "Extra step before the result was recorded" }),
    ...items.map((a) => {
      if (a.state !== "recorded") return el("p", { class: "muted", text: `${label(a.candidate_id)}: ${a.summary}` });
      const r = a.receipt;
      const states = (r.selection.candidates || []).filter((c) => !c.actionable && c.state !== "resolved_in_pool" && c.state !== "self_reference");
      return el("div", {},
        el("p", {}, el("strong", { text: `${label(a.candidate_id)}: ` }), a.summary,
          a.mode === "baseline" ? el("span", { class: "pill", text: " baseline mode" }) : null),
        a.new_units.length ? el("ul", { class: "cands" }, ...a.new_units.map((u) => el("li", {},
          el("span", { class: "pill new", text: u.gain === "new_document" ? "New document" : "Same document" }), " ",
          el("span", { class: "mono", text: u.unit_id }),
          el("div", { class: "quote", lang: "und", text: u.quote.length > 220 ? u.quote.slice(0, 220) + " …" : u.quote }),
          el("button", { class: "cite", onclick: (e) => openSpan(u.source_id, u.version_id, u.start_char, u.end_char, e.currentTarget) }, "Inspect source")))) : null,
        el("details", {}, el("summary", { text: "How this was recorded" }),
          el("ul", {},
            el("li", { text: `Gap signals: ${r.gaps.length ? r.gaps.join(", ") : "none"}` }),
            r.action ? el("li", { text: `Action: ${r.action} — ${r.reason}` }) : null,
            r.query ? el("li", { class: "mono", text: `Query: ${r.query}` }) : null,
            r.scope ? el("li", { class: "mono", text: `Scope: ${JSON.stringify(r.scope)}` }) : null,
            el("li", { text: `Policy: ${r.policy_version} (sha256 ${r.policy_sha256.slice(0, 16)}…) · budget ${r.budget_after ? r.budget_after.used + "/" + r.budget_after.limit : "0"}` }),
            el("li", { text: `Recorded in run ${a.run_id} (step ${a.seq}); commit: ${a.commit_status}${a.matches_current_assessment ? " (this result)" : ""}; receipt ${a.integrity}.` }),
            ...states.map((c) => el("li", { class: "muted", text: `Not used: ${c.reason}` })))));
    }));
}

function assessmentTable(rows) {
  return el("table", { class: "matrix" },
    el("thead", {}, el("tr", {}, el("th", { scope: "col", text: "Candidate" }), el("th", { scope: "col", text: "Result" }), el("th", { scope: "col", text: "Evidence" }))),
    el("tbody", {}, ...rows.map((a) => {
      const c = a.cell, ci = c && c.citation;
      return el("tr", {},
        el("th", { scope: "row", text: a.candidate_label }),
        el("td", { class: "cell" }, c ? el("span", { class: `badge ${c.display_outcome}` }, el("span", { "aria-hidden": "true", text: ICON[c.display_outcome] }), c.label) : el("span", { class: "muted", text: "Not assessed" }),
          c ? el("p", { text: c.explanation }) : null),
        el("td", {}, ci ? el("div", {}, el("div", { class: "quote", lang: "und", text: ci.quote }),
          el("button", { class: "cite", onclick: (e) => openSpan(ci.source_id, ci.version_id, ci.start_char, ci.end_char, e.currentTarget) }, `Inspect ${ci.source_id} · ${ci.version_id}`))
          : el("span", { class: "muted", text: "No cited passage" })));
    })));
}

async function runCompare() {
  const b = $("compare-run"); b.disabled = true; status("Running the requirements against the current sources…");
  try {
    const baseline = $("compare-baseline") && $("compare-baseline").checked;
    const r = await api("POST", `/api/projects/${S.projectId}/compare`, baseline ? { acquisition: "baseline" } : {});
    if (r.run && r.run.run_id) S.liveRunId = r.run.run_id;
    $("compare-results").replaceChildren(r.synthetic_label ? el("p", { class: "demo", text: r.synthetic_label }) : "",
      el("p", { class: "muted", text: `Assessment path: ${r.assessment_path}.` + (r.run ? ` Run ${r.run.run_id} (${r.run.status}).` : "") + ` Paid model calls: ${r.paid_model_calls}.` }),
      ...r.requirements.map((x) => {
        const q = x.requirement;
        return el("section", { class: "card" },
          el("h3", { text: `${q.requirement_id} · ${q.label}` }),
          q.fts_match ? el("p", { class: "mono muted", text: `Assessment search: ${q.fts_match}` }) : null,
          x.assessments.length ? assessmentTable(x.assessments) : null,
          x.runtime_assessment ? el("p", { text: `Runtime assessment (structural signal, not gold): ${x.runtime_assessment.status}; ${x.runtime_assessment.evidence.length} evidence span(s).` }) : null,
          x.acquisition && x.acquisition.length ? acquisitionTrace(x.acquisition, x.assessments) : null,
          x.side_by_side ? sideBySide(x.side_by_side) : null);
      }));
    await loadProject();
    status(`Compare finished` + (r.run ? ` (run ${r.run.run_id}).` : "."));
  } catch (e) { status(`Compare failed: ${e.message} (${e.code}). Previous results stay available.`, true); }
  finally { b.disabled = false; }
}

async function loadSynthetic() {
  status("Loading the synthetic relation-search example…");
  try {
    const r = await api("POST", "/api/synthetic/relation-search", {});
    S.projectId = r.project_id; S.liveRunId = r.side_by_side.run_id;
    await loadProjectList(); await loadProject();
    status(`${r.created ? "Synthetic example created" : "Synthetic example reopened"}: ${r.side_by_side.summary}`);
    show("compare");
  } catch (e) { status(`Could not load the example: ${e.message} (${e.code}).`, true); }
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
  if (!S.project.sources.length) box.append(el("p", { class: "muted", text: "No documents yet. Add a text, Markdown or PDF file above." }));
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

const ACTION_LABEL = { skip_stale_obligation: "Skipped (requirement changed or removed)", plan_obligation: "Plan obligation", search_current_sources: "Search current sources", read_passage: "Read passage",
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
  index_generation_switch: "Index generation", requirement_change: "Requirement", requirement_removed: "Requirement removed",
  requirement_restored: "Requirement restored" };
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
  await loadMode(); renderMode(); labels();
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

const CRED_TEXT = { set: "Set (name only shown)", set_restart_needed: "Set for your Windows user — restart the Workbench to use it",
  not_set: "Not set" };
const CAP_TEXT = { available: "Available", unavailable: "Unavailable", not_configured: "Not configured" };

function renderMode() {
  const box = $("exec-mode"), M = S.mode;
  if (!M) { box.replaceChildren(el("p", { class: "muted", text: "Execution mode not available." })); return; }
  const A = M.active;
  const facts = [];
  if (A.model_id) facts.push(`Model: ${A.model_id}` + (A.served_model_name && A.served_model_name !== A.model_id ? ` (served as ${A.served_model_name})` : "") + (A.model_digest ? ` · ${A.model_digest}` : ""));
  if (A.where) facts.push(`Endpoint: ${A.where}`);
  if (A.last_run) facts.push(`Last run ${A.last_run.run_id}: retrieval ${A.last_run.retrieval_effective}, paid model calls ${A.last_run.paid_model_calls}, remote calls ${A.last_run.remote_calls}` + (A.last_run.retrieval_note ? ` — ${A.last_run.retrieval_note}` : ""));
  box.replaceChildren(
    el("div", { class: "card mode-card" },
      el("h3", { text: `Active mode: ${A.mode_text}` + (A.requested_mode ? " (fallback)" : "") }),
      el("p", { text: A.summary }),
      facts.length ? el("ul", { class: "mono-list" }, ...facts.map((f) => el("li", { text: f }))) : null,
      el("p", { class: "muted", text: `Modes: ${Object.values(M.modes).join(" · ")}. ${M.reachability_note}` })),
    el("h3", { text: "Capabilities" }),
    el("table", { class: "matrix" },
      el("thead", {}, el("tr", {}, ...["Capability", "State", "Details"].map((h) => el("th", { scope: "col", text: h })))),
      el("tbody", {}, ...M.capabilities.map((c) => el("tr", {},
        el("td", { text: c.title + (c.optional ? " (optional)" : "") }),
        el("td", {}, el("span", { class: `pill ${c.state === "available" ? "current" : "historical"}`, text: CAP_TEXT[c.state] || c.state })),
        el("td", { text: [c.detail, c.use].filter(Boolean).join(" ") }))))),
    el("h3", { text: "Missing capabilities" }),
    M.missing.length ? el("ul", { id: "missing-list" }, ...M.missing.map((m) => el("li", { text: m })))
      : el("p", { class: "muted", text: "Nothing is missing." }),
    el("h3", { text: "Credentials (set once, outside the Workbench)" }),
    el("p", { class: "muted", text: M.secrets_policy + " A key is set once as a Windows user environment variable in your own PowerShell window; every profile that names it uses it after the Workbench restarts." }),
    el("table", { class: "matrix" },
      el("thead", {}, el("tr", {}, ...["Variable", "State", "Used by", "Set up"].map((h) => el("th", { scope: "col", text: h })))),
      el("tbody", {}, ...M.credentials.map((c) => el("tr", {},
        el("td", { class: "mono", text: c.name }),
        el("td", {}, el("span", { class: `pill ${c.state === "set" ? "current" : "historical"}`, text: CRED_TEXT[c.state] || c.state })),
        el("td", { text: c.used_by.length ? c.used_by.join(", ") : c.purpose }),
        el("td", {}, el("details", {}, el("summary", { text: c.state === "set" ? "Change or remove" : "How to set it once" }),
          el("p", { text: "1. Open PowerShell (not as administrator) and run this line. It asks for the key with hidden input; the key never passes through the Workbench or the browser." }),
          el("pre", { class: "source mono" }, c.setup.set_powershell),
          el("button", { onclick: () => copyText(c.setup.set_powershell) }, "Copy command"),
          el("p", { text: `2. ${c.setup.after}` }),
          el("p", { class: "muted", text: c.setup.never }),
          el("p", { class: "muted" }, "To remove it later: ", el("code", { text: c.setup.remove_powershell })))))))));
}

async function copyText(t) {
  try { await navigator.clipboard.writeText(t); status("Command copied. Paste it into PowerShell; it will ask for the key."); }
  catch (e) { status("Copy is not available here; select the command and copy it manually.", true); }
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
  $("load-synthetic").addEventListener("click", loadSynthetic);
  $("search-form").addEventListener("submit", doSearch);
  $("req-form").addEventListener("submit", saveRequirement);
  $("compare-run").addEventListener("click", runCompare);
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
