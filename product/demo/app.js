/* Market Window Dossier demo. Vanilla JS, no build step, no dependencies.
 *
 * Data loading order:
 *   http(s): data/index.json (PRD1 output) -> fixtures/index.json -> data.bundle.js
 *   file:    data.bundle.js (browsers block fetch() for file:// pages)
 * The index lists queues per (cutoff, horizon) and dossiers per (molecule, cutoff, horizon);
 * paths are relative to the index's folder. Contract: mwd.dossier.v1 / mwd.queue.v1.
 *
 * URL hash keeps state, e.g. #lang=en&h=12&c=2013&m=talcoxib&tab=decision&reveal=1
 * (cite=<claim id> additionally opens the sources drawer for that claim; used for deep links.)
 */
(function () {
  "use strict";

  var SECTION_ORDER = ["decision", "market", "competition", "patents", "thai_asean", "handoff", "references"];
  var SECTION_FALLBACK = {
    decision: ["หน้าตัดสินใจ", "Decision"],
    market: ["ช่วงเวลาตลาด", "Market window"],
    competition: ["การแข่งขัน", "Competition"],
    patents: ["สิทธิบัตรและสิทธิผูกขาด", "Patents & exclusivity"],
    thai_asean: ["ไทยและอาเซียน", "Thailand & ASEAN"],
    handoff: ["ส่งต่อผู้ประเมิน FTO", "FTO hand-off"],
    references: ["เอกสารอ้างอิง", "References"]
  };

  var I18N = {
    th: {
      skip: "ข้ามไปที่รายงาน",
      pill: "ข้อมูลช่วงพัฒนา · ไม่ใช่ความเห็น FTO",
      fixture: "FIXTURE · ข้อมูลสังเคราะห์",
      langGroup: "ภาษา",
      timeMachine: "ย้อนเวลา",
      horizon: "ช่วงพยากรณ์",
      monthsShort: "เดือน",
      cutoff: "ปีตัดข้อมูล",
      prevYear: "ปีก่อนหน้า",
      nextYear: "ปีถัดไป",
      capacity: function (n) { return "ขีดความสามารถในการตรวจ: 1 ใน 5 (" + n + " ช่อง)"; },
      capacityDivider: "ขีดความสามารถ",
      queueLabel: "คิวจัดอันดับตามโอกาสเข้าตลาด (M3)",
      inQueue: "อยู่ในคิว",
      hasDossier: "มีรายงาน",
      legend: "● มีรายงานให้เปิดดู · แถบสีเขียวอมฟ้า = อยู่ในคิวตรวจ",
      railToggle: function (c, h) { return "ย้อนเวลา · ปี " + c + " · " + h + " เดือน"; },
      loading: "กำลังโหลดข้อมูล…",
      loadError: "โหลดข้อมูลไม่ได้ ถ้าเปิดจากไฟล์ในเครื่อง ให้รัน python product/demo/bundle.py เพื่อสร้าง data.bundle.js",
      asOf: "ข้อมูล ณ",
      horizonMeta: function (n) { return "พยากรณ์ " + n + " เดือน"; },
      jurisdiction: "เขตอำนาจ",
      forms: "รูปแบบยา",
      status: { DEVELOPMENT_ONLY: "ใช้ในการพัฒนาเท่านั้น", TRACK_A_FROZEN: "Track A ตรึงแล้ว" },
      tabsLabel: "ส่วนของรายงาน",
      state: { known: "ทราบ", unknown: "ต้องตรวจ", not_applicable: "ไม่เกี่ยวข้อง" },
      kind: { observed: "ข้อมูลสังเกต", estimate: "ค่าประมาณ", assumption: "สมมติฐาน" },
      openInTab: function (n) { return n + " ข้อต้องตรวจ"; },
      probTitle: function (h) { return "โอกาสที่ยาสามัญรายแรกได้รับอนุมัติภายใน " + h + " เดือน"; },
      b1: "เส้นฐาน",
      queueTitle: "อันดับในคิวผู้ประเมิน",
      rankOf: function (r, n) { return "จาก " + n; },
      slots: function (k) { return "คิวรับได้ " + k + " ช่อง"; },
      inQ: "อยู่ในคิว",
      outQ: "อยู่นอกคิว",
      decisive: "สมมติฐานชี้ขาด",
      openIssues: "ประเด็นที่ยังเปิด",
      openSub: "ข้อความที่ยังต้องตรวจยืนยันทั้งรายงาน",
      nextAction: "ขั้นต่อไป",
      reveal: "เปิดดูสิ่งที่เกิดขึ้นจริง",
      hideReveal: "ซ่อนผลลัพธ์",
      revealFirst: function (d) { return "ยาสามัญรายแรกได้รับอนุมัติขั้นสุดท้ายเมื่อ " + d; },
      revealNone: function (d) { return "ไม่มียาสามัญรายแรกภายในช่วงพยากรณ์ (ถึง " + d + ")"; },
      capture: function (x, y, z) { return "คิวนี้จับเหตุการณ์ได้ <b>" + x + " จาก " + y + "</b> เหตุการณ์ (M3) เทียบกับ <b>" + z + "</b> (B1)"; },
      captured: "เกิดเหตุการณ์ · อยู่ในคิว",
      missed: "เกิดเหตุการณ์ · พลาด (นอกคิว)",
      revealedNote: "ผลลัพธ์เป็นข้อมูลช่วงพัฒนา ใช้ทบทวนย้อนหลังเท่านั้น",
      sources: "แหล่งข้อมูล",
      close: "ปิด",
      citeLabel: function (n, issuer) { return "แหล่งข้อมูล " + n + ": " + issuer; },
      noSource: "ไม่มีแหล่งอ้างอิง",
      issuer: "ผู้ออก",
      version: "ฉบับ",
      publicDate: "วันที่เผยแพร่",
      undated: "ไม่ระบุวันที่ (ค้นแบบสด)",
      locator: "ตำแหน่ง",
      url: "ลิงก์",
      retrieved: "ดึงข้อมูลเมื่อ",
      copy: "คัดลอก",
      copied: "คัดลอกแล้ว",
      copyLabel: "คัดลอกค่า SHA-256",
      claimsEmpty: "ไม่มีข้อความในส่วนนี้",
      claimCount: function (n) { return n + " ข้อความ"; },
      checklist: "รายการตรวจสำหรับผู้ประเมิน",
      progress: function (a, b) { return "ตรวจแล้ว " + a + " จาก " + b; },
      checklistNote: "ช่องทำเครื่องหมายบันทึกไว้ในเบราว์เซอร์นี้เท่านั้น ไม่ได้ส่งไปที่ใด",
      owner: { "FTO evaluator": "ผู้ประเมิน FTO", "R&D": "R&D", "BD": "BD" },
      refsCount: function (n) { return n + " แหล่ง"; },
      repro: function (schema, asof, fx) { return "สัญญาข้อมูล " + schema + " · ข้อมูล ณ " + asof + (fx ? " · FIXTURE ข้อมูลสังเคราะห์ ไม่ใช่ผลจริง" : ""); },
      noDossierTitle: function (n) { return "ยังไม่มีรายงานของ " + n + " สำหรับปีตัดข้อมูลนี้"; },
      noDossierBody: function (p, b, r) { return "อันดับ " + r + " · M3 " + p + "% · B1 " + b + "% เลือกยาที่มีจุด ● ในคิวเพื่อเปิดรายงาน"; },
      footer1: "เครื่องมือประกอบการตัดสินใจ ไม่ใช่ความเห็นด้าน FTO หรือความเห็นทางกฎหมาย",
      footer2: "ข้อมูล: ปีตัดข้อมูลช่วงพัฒนาก่อนปี 2017 ชุดทดสอบที่ปิดผนึกและ Track A ยังรอดำเนินการ"
    },
    en: {
      skip: "Skip to dossier",
      pill: "Development data · not an FTO opinion",
      fixture: "FIXTURE · synthetic data",
      langGroup: "Language",
      timeMachine: "Time machine",
      horizon: "Horizon",
      monthsShort: "months",
      cutoff: "Cutoff year",
      prevYear: "Previous year",
      nextYear: "Next year",
      capacity: function (n) { return "Review capacity: 1 in 5 (" + n + " slots)"; },
      capacityDivider: "capacity",
      queueLabel: "Queue ranked by entry probability (M3)",
      inQueue: "in queue",
      hasDossier: "dossier available",
      legend: "● dossier available · teal bar = inside review capacity",
      railToggle: function (c, h) { return "Time machine · " + c + " · " + h + " months"; },
      loading: "Loading data…",
      loadError: "Could not load data. When opening from a local file, run python product/demo/bundle.py to create data.bundle.js.",
      asOf: "As of",
      horizonMeta: function (n) { return n + "-month horizon"; },
      jurisdiction: "Jurisdiction",
      forms: "Forms",
      status: { DEVELOPMENT_ONLY: "Development only", TRACK_A_FROZEN: "Track A frozen" },
      tabsLabel: "Dossier sections",
      state: { known: "known", unknown: "verify", not_applicable: "n/a" },
      kind: { observed: "observed", estimate: "estimate", assumption: "assumption" },
      openInTab: function (n) { return n + " to verify"; },
      probTitle: function (h) { return "Chance a first generic gets final approval within " + h + " months"; },
      b1: "baseline",
      queueTitle: "Evaluator queue rank",
      rankOf: function (r, n) { return "of " + n; },
      slots: function (k) { return k + " review slots"; },
      inQ: "In queue",
      outQ: "Outside queue",
      decisive: "Decisive assumption",
      openIssues: "Open issues",
      openSub: "claims still to verify across the dossier",
      nextAction: "Next action",
      reveal: "Reveal what happened",
      hideReveal: "Hide outcome",
      revealFirst: function (d) { return "First final ANDA approval on " + d; },
      revealNone: function (d) { return "No first generic in window (through " + d + ")"; },
      capture: function (x, y, z) { return "This queue captured <b>" + x + " of " + y + "</b> events (M3) vs <b>" + z + "</b> (B1)"; },
      captured: "event · in queue",
      missed: "event · missed (outside queue)",
      revealedNote: "Development outcome, for retrospective review only.",
      sources: "Sources",
      close: "Close",
      citeLabel: function (n, issuer) { return "Source " + n + ": " + issuer; },
      noSource: "no source",
      issuer: "Issuer",
      version: "Version",
      publicDate: "Public date",
      undated: "Undated (live lookup)",
      locator: "Locator",
      url: "URL",
      retrieved: "Retrieved",
      copy: "Copy",
      copied: "Copied",
      copyLabel: "Copy SHA-256",
      claimsEmpty: "No claims in this section.",
      claimCount: function (n) { return n + (n === 1 ? " claim" : " claims"); },
      checklist: "Evaluator checklist",
      progress: function (a, b) { return a + " of " + b + " checked"; },
      checklistNote: "Checkboxes are saved in this browser only and are not sent anywhere.",
      owner: { "FTO evaluator": "FTO evaluator", "R&D": "R&D", "BD": "BD" },
      refsCount: function (n) { return n + (n === 1 ? " source" : " sources"); },
      repro: function (schema, asof, fx) { return "Contract " + schema + " · as of " + asof + (fx ? " · FIXTURE synthetic data, not real results" : ""); },
      noDossierTitle: function (n) { return "No dossier for " + n + " at this cutoff yet"; },
      noDossierBody: function (p, b, r) { return "Rank " + r + " · M3 " + p + "% · B1 " + b + "%. Pick a drug marked ● in the queue to open its dossier."; },
      footer1: "Decision support, not an FTO or legal opinion",
      footer2: "Data: development cutoffs before 2017; sealed test and Track A pending"
    }
  };

  var state = {
    lang: "th", horizon: 12, cutoff: null, key: null, tab: "decision", revealed: false,
    index: null, fetcher: null, queue: null, dossier: null, fixture: false
  };
  var cache = {};
  var lastFocus = null;

  function $(id) { return document.getElementById(id); }
  function t(k) { return I18N[state.lang][k]; }
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function pct(p) { return p == null ? "—" : String(Math.round(p * 100)); }
  function L(obj, base) { return obj[base + "_" + state.lang] || obj[base + "_en"] || obj[base + "_th"] || ""; }
  function store(get, k, v) {
    try { if (get) return window.localStorage.getItem(k); window.localStorage.setItem(k, v); } catch (e) { return null; }
    return null;
  }

  /* ---------- data ---------- */
  function getJSON(url) {
    return fetch(url, { cache: "no-cache" }).then(function (r) {
      if (!r.ok) throw new Error(r.status + " " + url);
      return r.json();
    });
  }
  function loadScript(src) {
    return new Promise(function (res, rej) {
      var s = document.createElement("script");
      s.src = src; s.onload = res; s.onerror = function () { rej(new Error("missing " + src)); };
      document.head.appendChild(s);
    });
  }
  function fromBundle() {
    var D = window.MWD_DATA;
    return {
      index: D.index,
      fetcher: function (p) { return D.files[p] ? Promise.resolve(D.files[p]) : Promise.reject(new Error("not bundled: " + p)); }
    };
  }
  function loadData() {
    function bundle() {
      if (window.MWD_DATA) return Promise.resolve(fromBundle());
      return loadScript("data.bundle.js").then(fromBundle);
    }
    if (location.protocol === "file:") return bundle();
    function tryBase(base) {
      return getJSON(base + "/index.json").then(function (idx) {
        return { index: idx, fetcher: function (p) { return getJSON(base + "/" + p); } };
      });
    }
    return tryBase("data").catch(function () { return tryBase("fixtures"); }).catch(bundle);
  }
  function load(path) {
    if (!cache[path]) cache[path] = state.fetcher(path);
    return cache[path];
  }

  function horizons() {
    var seen = {};
    state.index.queues.forEach(function (q) { seen[q.horizon_months] = 1; });
    return Object.keys(seen).map(Number).sort(function (a, b) { return a - b; });
  }
  function cutoffsFor(h) {
    return state.index.queues.filter(function (q) { return q.horizon_months === h; })
      .map(function (q) { return String(q.cutoff); }).sort();
  }
  function queueEntry() {
    return state.index.queues.find(function (q) { return q.horizon_months === state.horizon && String(q.cutoff) === state.cutoff; });
  }
  function dossierEntry(key) {
    return (state.index.dossiers || []).find(function (d) {
      return d.key === key && d.horizon_months === state.horizon && String(d.cutoff) === state.cutoff;
    });
  }

  /* ---------- hash state ---------- */
  function readHash() {
    var out = {};
    location.hash.replace(/^#/, "").split("&").forEach(function (kv) {
      if (!kv) return;
      var i = kv.indexOf("=");
      out[decodeURIComponent(kv.slice(0, i < 0 ? kv.length : i))] = i < 0 ? "" : decodeURIComponent(kv.slice(i + 1));
    });
    return out;
  }
  function writeHash() {
    var parts = ["lang=" + state.lang, "h=" + state.horizon, "c=" + state.cutoff];
    if (state.key) parts.push("m=" + encodeURIComponent(state.key));
    if (state.tab !== "decision") parts.push("tab=" + state.tab);
    if (state.revealed) parts.push("reveal=1");
    try { history.replaceState(null, "", "#" + parts.join("&")); } catch (e) { /* file:// in some browsers */ }
  }

  /* ---------- language ---------- */
  function applyLang() {
    document.documentElement.lang = state.lang;
    document.querySelectorAll("[data-i18n]").forEach(function (el) {
      var v = t(el.getAttribute("data-i18n"));
      if (typeof v === "string") el.textContent = v;
    });
    document.querySelectorAll("[data-i18n-aria]").forEach(function (el) {
      var v = t(el.getAttribute("data-i18n-aria"));
      if (typeof v === "string") el.setAttribute("aria-label", v);
    });
    document.querySelectorAll(".lang-toggle button").forEach(function (b) {
      b.setAttribute("aria-pressed", String(b.getAttribute("data-lang") === state.lang));
    });
  }

  /* ---------- rail ---------- */
  function renderHorizon() {
    var g = $("horizon-group");
    g.innerHTML = horizons().map(function (h) {
      var on = h === state.horizon;
      return '<button type="button" role="radio" aria-checked="' + on + '" tabindex="' + (on ? 0 : -1) +
        '" data-h="' + h + '"><span class="num">' + h + "</span> " + esc(t("monthsShort")) + "</button>";
    }).join("");
  }
  function renderStepper() {
    var list = cutoffsFor(state.horizon), i = list.indexOf(state.cutoff);
    $("cutoff-value").textContent = state.cutoff || "—";
    $("cutoff-prev").disabled = i <= 0;
    $("cutoff-next").disabled = i < 0 || i >= list.length - 1;
  }
  function renderQueue() {
    var q = state.queue, ol = $("queue");
    if (!q) { ol.innerHTML = ""; return; }
    var slots = q.queue_size || q.rows.filter(function (r) { return r.in_queue; }).length;
    $("capacity").textContent = t("capacity")(slots);
    var html = [];
    q.rows.forEach(function (r, i) {
      var has = !!dossierEntry(r.key);
      var cls = "q-row" + (r.in_queue ? " in-queue" : "") + (has ? "" : " no-doc");
      var ev = "";
      if (r.event) {
        ev = r.in_queue ? '<span class="q-event captured">● ' + esc(t("captured")) + "</span>"
          : '<span class="q-event missed">✕ ' + esc(t("missed")) + "</span>";
      }
      var label = (i + 1) + ". " + r.display_name + ", M3 " + pct(r.m3_p) + "%" +
        (r.in_queue ? ", " + t("inQueue") : "") + (has ? ", " + t("hasDossier") : "");
      html.push('<li><button type="button" class="' + cls + '" data-key="' + esc(r.key) + '"' +
        (r.key === state.key ? ' aria-current="true"' : "") + ' aria-label="' + esc(label) + '">' +
        '<span class="q-rank num" aria-hidden="true">' + (i + 1) + "</span>" +
        '<span class="q-name" aria-hidden="true">' + esc(r.display_name) + (has ? '<span class="q-doc"></span>' : "") + "</span>" +
        '<span class="bar" aria-hidden="true"><span style="width:' + Math.max(1, Math.round(r.m3_p * 100)) + '%"></span></span>' +
        '<span class="q-pct num" aria-hidden="true">' + pct(r.m3_p) + "%</span>" +
        '<span class="q-tick" aria-hidden="true">' + (r.in_queue ? "✓" : "") + "</span>" + ev +
        "</button></li>");
      if (i === slots - 1 && i < q.rows.length - 1) {
        html.push('<li class="cap-divider" role="separator" aria-label="' + esc(t("capacityDivider")) + '">' + esc(t("capacityDivider")) + "</li>");
      }
    });
    ol.innerHTML = html.join("");
    ol.classList.toggle("revealed", state.revealed);
    $("rail-legend").textContent = t("legend");
    $("rail-toggle-label").textContent = t("railToggle")(state.cutoff, state.horizon);
  }

  /* ---------- dossier ---------- */
  function sectionsOf(d) {
    var byId = {};
    (d.sections || []).forEach(function (s) { byId[s.id] = s; });
    return SECTION_ORDER.map(function (id, i) {
      var s = byId[id] || { id: id, title_th: SECTION_FALLBACK[id][0], title_en: SECTION_FALLBACK[id][1] };
      return { id: id, n: i + 1, src: s, title: L(s, "title") || SECTION_FALLBACK[id][state.lang === "th" ? 0 : 1] };
    });
  }
  function sourceIndex(d) {
    var m = {};
    (d.sources || []).forEach(function (s, i) { m[s.id] = i + 1; });
    return m;
  }
  function stateChip(s) {
    var cls = s === "known" ? "chip-known" : s === "unknown" ? "chip-unknown" : "chip-na";
    return '<span class="chip chip-state ' + cls + '">' + esc((t("state")[s]) || s) + "</span>";
  }
  function kindChip(k) {
    return '<span class="chip chip-kind ' + esc(k) + '">' + esc((t("kind")[k]) || k) + "</span>";
  }
  function cites(ids, claimId, srcIdx, d) {
    if (!ids || !ids.length) return '<span class="cite-none">(' + esc(t("noSource")) + ")</span>";
    return '<span class="cites">' + ids.map(function (id) {
      var n = srcIdx[id], s = (d.sources || [])[n - 1];
      if (!n) return "";
      return '<button type="button" class="cite" data-src="' + esc(id) + '" data-claim="' + esc(claimId) +
        '" aria-label="' + esc(t("citeLabel")(n, s.issuer)) + '">' + n + "</button>";
    }).join("") + "</span>";
  }
  function claimList(d, section, srcIdx) {
    var cs = (d.claims || []).filter(function (c) { return c.section === section; });
    if (!cs.length) return '<div class="claims"><p class="claims-empty">' + esc(t("claimsEmpty")) + "</p></div>";
    return '<ul class="claims">' + cs.map(function (c) {
      return '<li class="claim state-' + esc(c.state) + '">' + stateChip(c.state) +
        '<p class="claim-text ' + esc(c.kind) + '">' + esc(L(c, "text")) + cites(c.source_ids, c.id, srcIdx, d) + "</p>" +
        kindChip(c.kind) + "</li>";
    }).join("") + "</ul>";
  }
  function srcCard(s, n, focus) {
    var short = s.sha256 ? s.sha256.slice(0, 10) + "…" + s.sha256.slice(-6) : "—";
    return '<li class="src' + (focus ? " focus" : "") + '" id="src-' + esc(s.id) + '">' +
      '<span class="src-n">' + n + "</span>" +
      '<span class="src-title">' + esc(s.title) + "</span>" +
      "<dl>" +
      "<dt>" + esc(t("issuer")) + "</dt><dd>" + esc(s.issuer) + "</dd>" +
      "<dt>" + esc(t("version")) + "</dt><dd>" + esc(s.version || "—") + "</dd>" +
      "<dt>" + esc(t("publicDate")) + "</dt><dd>" + (s.public_date ? '<time class="num">' + esc(s.public_date) + "</time>" : esc(t("undated"))) + "</dd>" +
      "<dt>" + esc(t("locator")) + "</dt><dd>" + esc(s.locator || "—") + "</dd>" +
      "<dt>" + esc(t("url")) + "</dt><dd>" + (s.url ? '<a href="' + esc(s.url) + '" target="_blank" rel="noopener noreferrer">' + esc(s.url.replace(/^https?:\/\//, "")) + "</a>" : "—") + "</dd>" +
      "<dt>SHA-256</dt><dd><span class=\"sha\"><code title=\"" + esc(s.sha256 || "") + "\">" + esc(short) + "</code>" +
      (s.sha256 ? '<button type="button" class="copy-btn" data-copy="' + esc(s.sha256) + '" aria-label="' + esc(t("copyLabel")) + '">' + esc(t("copy")) + "</button>" : "") +
      "</span></dd>" +
      (s.retrieved ? "<dt>" + esc(t("retrieved")) + '</dt><dd><time class="num">' + esc(s.retrieved) + "</time></dd>" : "") +
      "</dl></li>";
  }

  function decisionSummary(d, sec) {
    var f = d.forecast || {}, h = f.horizon_months || state.horizon;
    var claims = d.claims || [];
    var dec = sec.src.decisive_claim && claims.find(function (c) { return c.id === sec.src.decisive_claim; });
    if (!dec) dec = claims.find(function (c) { return c.section === "decision" && c.kind === "assumption"; }) ||
      claims.find(function (c) { return c.kind === "assumption"; });
    var open = claims.filter(function (c) { return c.state === "unknown"; }).length;
    var next = L(sec.src, "next_action") || ((d.checklist || [])[0] ? L(d.checklist[0], "text") : "—");
    var n = state.queue ? state.queue.n_candidates || state.queue.rows.length : null;
    function prob(who, p, sub, cls) {
      return '<div class="prob-row ' + cls + '"><span class="who">' + who + '</span>' +
        '<span class="bar" role="img" aria-label="' + who + " " + pct(p) + '%"><span style="width:' + Math.max(1, Math.round((p || 0) * 100)) + '%"></span></span>' +
        '<span class="pct num">' + pct(p) + "%</span></div>";
    }
    return '<div class="summary">' +
      '<section class="card card-prob" aria-label="' + esc(t("probTitle")(h)) + '"><div class="card-label">' + esc(t("probTitle")(h)) + "</div>" +
      prob("M3", f.m3_p_entry, "", "m3") + prob("B1", f.b1_p_entry, "", "b1") +
      '<div class="card-sub">B1 = ' + esc(t("b1")) + "</div></section>" +
      '<section class="card card-queue"><div class="card-label">' + esc(t("queueTitle")) + "</div>" +
      '<div class="big num">#' + esc(f.m3_rank || "—") + (n ? " <small>" + esc(t("rankOf")(f.m3_rank, n)) + "</small>" : "") + "</div>" +
      '<div class="card-sub"><span class="' + (f.in_queue ? "in-q" : "out-q") + '">' + (f.in_queue ? "✓ " + esc(t("inQ")) : esc(t("outQ"))) + "</span> · " + esc(t("slots")(f.queue_size || "—")) + "</div></section>" +
      '<section class="card card-assume"><div class="card-label">' + esc(t("decisive")) + "</div><p>" + esc(dec ? L(dec, "text") : "—") + "</p></section>" +
      '<section class="card card-open"><div class="card-label">' + esc(t("openIssues")) + "</div>" +
      '<div class="big num open-n">' + open + "</div><div class=\"card-sub\">" + esc(t("openSub")) + "</div></section>" +
      '<section class="card card-next"><div class="card-label">' + esc(t("nextAction")) + "</div><p>" + esc(next) + "</p></section>" +
      "</div>";
  }

  function checklistHtml(d) {
    var items = d.checklist || [];
    var key = "mwd.check." + d.molecule.key + "." + d.as_of + "." + (d.forecast || {}).horizon_months;
    var saved = {};
    try { saved = JSON.parse(store(true, key) || "{}") || {}; } catch (e) { saved = {}; }
    var done = items.filter(function (c) { return saved[c.id]; }).length;
    var srcIdx = sourceIndex(d);
    return '<div class="subhead"><h3>' + esc(t("checklist")) + '</h3><span class="panel-count num" id="check-progress">' + esc(t("progress")(done, items.length)) + "</span></div>" +
      '<ul class="checklist" data-store="' + esc(key) + '">' + items.map(function (c) {
        var fto = c.owner === "FTO evaluator";
        var id = "chk-" + esc(c.id);
        return '<li class="check' + (saved[c.id] ? " done" : "") + '"><input type="checkbox" id="' + id + '" data-id="' + esc(c.id) + '"' + (saved[c.id] ? " checked" : "") + ">" +
          '<label for="' + id + '">' + esc(L(c, "text")) + cites(c.source_ids, c.id, srcIdx, d) + "</label>" +
          '<span class="check-meta"><span class="chip chip-owner' + (fto ? " fto" : "") + '">' + esc((t("owner")[c.owner]) || c.owner) + "</span></span></li>";
      }).join("") + "</ul>" +
      '<p class="note">' + esc(t("checklistNote")) + "</p>";
  }

  function revealHtml(d) {
    var o = d.outcome_reveal, q = state.queue;
    if (!o || !state.revealed) return "";
    var main = o.first_final_anda_date
      ? '<div class="reveal-main hit">' + esc(t("revealFirst")(o.first_final_anda_date)) + "</div>"
      : '<div class="reveal-main none">' + esc(t("revealNone")(o.window_end || "—")) + "</div>";
    var cap = q && q.capture ? '<div class="reveal-sub">' + t("capture")(q.capture.m3_captured, q.capture.events_total, q.capture.b1_captured) + "</div>" : "";
    return '<div class="reveal" id="reveal-panel" role="status">' + main + cap + '<div class="reveal-sub">' + esc(t("revealedNote")) + "</div></div>";
  }

  function renderDossier() {
    var main = $("dossier"), d = state.dossier;
    if (!d) {
      var r = state.queue && state.queue.rows.find(function (x) { return x.key === state.key; });
      main.innerHTML = r ? '<div class="empty"><h2>' + esc(t("noDossierTitle")(r.display_name)) + "</h2><p>" +
        esc(t("noDossierBody")(pct(r.m3_p), pct(r.b1_p), state.queue.rows.indexOf(r) + 1)) + "</p></div>"
        : '<p class="loading">' + esc(t("loading")) + "</p>";
      return;
    }
    var f = d.forecast || {}, secs = sectionsOf(d), srcIdx = sourceIndex(d);
    var status = f.status || "DEVELOPMENT_ONLY";
    var unknownBy = {};
    (d.claims || []).forEach(function (c) { if (c.state === "unknown") unknownBy[c.section] = (unknownBy[c.section] || 0) + 1; });

    var head = '<div class="d-head"><div class="d-title">' +
      "<h1>" + esc(d.molecule.display_name) + ' <span class="chip chip-status' + (status === "TRACK_A_FROZEN" ? " frozen" : "") + '">' + esc((t("status")[status]) || status) + "</span>" +
      (d.fixture || state.fixture ? ' <span class="chip chip-unknown">FIXTURE</span>' : "") + "</h1>" +
      '<div class="d-meta"><span>' + esc(t("asOf")) + ' <b><time class="num">' + esc(d.as_of) + "</time></b></span>" +
      "<span><b>" + esc(t("horizonMeta")(f.horizon_months || state.horizon)) + "</b></span>" +
      "<span>" + esc(t("jurisdiction")) + " <b>" + esc(d.jurisdiction || "—") + "</b></span>" +
      "<span>" + esc(t("forms")) + " <b>" + esc((d.molecule.dosage_forms || []).join(", ") || "—") + "</b></span></div></div>" +
      (d.outcome_reveal ? '<button type="button" class="btn" id="reveal-btn" aria-expanded="' + state.revealed + '" aria-controls="reveal-slot">' +
        esc(state.revealed ? t("hideReveal") : t("reveal")) + "</button>" : "") + "</div>" +
      '<div id="reveal-slot">' + revealHtml(d) + "</div>";

    var tabs = '<div class="tabs" role="tablist" aria-label="' + esc(t("tabsLabel")) + '">' + secs.map(function (s) {
      var on = s.id === state.tab;
      return '<button type="button" class="tab" role="tab" id="tab-' + s.id + '" aria-controls="panel-' + s.id + '" aria-selected="' + on + '" tabindex="' + (on ? 0 : -1) + '" data-tab="' + s.id + '">' +
        '<span class="tab-n" aria-hidden="true">' + s.n + "</span>" + esc(s.title) +
        (unknownBy[s.id] ? '<span class="tab-flag" title="' + esc(t("openInTab")(unknownBy[s.id])) + '"></span><span class="sr-only">, ' + esc(t("openInTab")(unknownBy[s.id])) + "</span>" : "") +
        "</button>";
    }).join("") + "</div>";

    var panels = secs.map(function (s) {
      var count = (d.claims || []).filter(function (c) { return c.section === s.id; }).length;
      var body = "";
      if (s.id === "decision") body = decisionSummary(d, s) + claimList(d, s.id, srcIdx);
      else if (s.id === "handoff") body = (count ? claimList(d, s.id, srcIdx) : "") + checklistHtml(d);
      else if (s.id === "references") {
        body = '<ol class="src-list">' + (d.sources || []).map(function (src, i) { return srcCard(src, i + 1, false); }).join("") + "</ol>" +
          '<p class="note repro">' + esc(t("repro")(d.schema || "mwd.dossier.v1", d.as_of, d.fixture || state.fixture)) + "</p>";
        count = (d.sources || []).length;
      } else body = claimList(d, s.id, srcIdx);
      var countTxt = s.id === "references" ? t("refsCount")(count) : t("claimCount")(count);
      return '<section class="panel" role="tabpanel" id="panel-' + s.id + '" aria-labelledby="tab-' + s.id + '" tabindex="0"' + (s.id === state.tab ? "" : " hidden") + ">" +
        '<div class="panel-head"><span class="panel-n">' + s.n + '</span><h2>' + esc(s.title) + '</h2><span class="panel-count num">' + esc(countTxt) + "</span></div>" +
        body + "</section>";
    }).join("");

    main.innerHTML = head + tabs + panels;
  }

  /* ---------- drawer ---------- */
  function openDrawer(srcId, claimId, opener) {
    var d = state.dossier; if (!d) return;
    var claim = (d.claims || []).find(function (c) { return c.id === claimId; }) ||
      (d.checklist || []).find(function (c) { return c.id === claimId; });
    var ids = claim && claim.source_ids && claim.source_ids.length ? claim.source_ids : [srcId];
    var idx = sourceIndex(d);
    var body = (claim ? '<p class="drawer-claim">' + esc(L(claim, "text")) + "</p>" : "") +
      '<ol class="src-list">' + ids.map(function (id) {
        var s = d.sources[idx[id] - 1];
        return s ? srcCard(s, idx[id], id === srcId) : "";
      }).join("") + "</ol>";
    $("drawer-body").innerHTML = body;
    lastFocus = opener || document.activeElement;
    $("drawer").hidden = false; $("drawer-scrim").hidden = false;
    $("drawer-close").focus();
    var focused = $("drawer-body").querySelector(".src.focus");
    if (focused && focused.scrollIntoView) focused.scrollIntoView({ block: "nearest" });
  }
  function closeDrawer() {
    if ($("drawer").hidden) return;
    $("drawer").hidden = true; $("drawer-scrim").hidden = true;
    if (lastFocus && document.body.contains(lastFocus)) lastFocus.focus();
  }
  function trapFocus(e) {
    if ($("drawer").hidden || e.key !== "Tab") return;
    var f = $("drawer").querySelectorAll("button, a[href], [tabindex]:not([tabindex='-1'])");
    if (!f.length) return;
    var first = f[0], last = f[f.length - 1];
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
  }

  function copyText(text, btn) {
    function done() {
      var old = btn.textContent; btn.textContent = t("copied");
      $("announcer").textContent = t("copied");
      setTimeout(function () { btn.textContent = old; }, 1400);
    }
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(text).then(done, function () { fallback(); });
    } else fallback();
    function fallback() {
      var ta = document.createElement("textarea");
      ta.value = text; ta.setAttribute("readonly", ""); ta.style.position = "fixed"; ta.style.opacity = "0";
      document.body.appendChild(ta); ta.select();
      try { document.execCommand("copy"); done(); } catch (e) { /* ignore */ }
      document.body.removeChild(ta);
    }
  }

  /* ---------- selection ---------- */
  function selectQueue() {
    var entry = queueEntry();
    if (!entry) { state.queue = null; renderQueue(); return Promise.resolve(); }
    return load(entry.path).then(function (q) {
      q.rows = (q.rows || []).slice().sort(function (a, b) { return (b.m3_p || 0) - (a.m3_p || 0); });
      state.queue = q;
      if (!state.key || !q.rows.some(function (r) { return r.key === state.key; })) {
        var first = q.rows.find(function (r) { return dossierEntry(r.key); }) || q.rows[0];
        state.key = first ? first.key : null;
      }
      renderQueue();
      return selectDossier(state.key);
    });
  }
  function selectDossier(key) {
    state.key = key;
    var entry = key && dossierEntry(key);
    if (!entry) { state.dossier = null; renderQueue(); renderDossier(); writeHash(); return Promise.resolve(); }
    return load(entry.path).then(function (d) {
      state.dossier = d;
      renderQueue(); renderDossier(); writeHash();
    }, function () { state.dossier = null; renderDossier(); });
  }
  function setCutoff(c) {
    if (c === state.cutoff) return;
    state.cutoff = c; state.revealed = false;
    renderStepper(); selectQueue();
  }
  function setHorizon(h) {
    if (h === state.horizon) return;
    state.horizon = h; state.revealed = false;
    var list = cutoffsFor(h);
    if (list.indexOf(state.cutoff) < 0) {
      var target = Number(state.cutoff);
      state.cutoff = list.slice().sort(function (a, b) { return Math.abs(a - target) - Math.abs(b - target); })[0];
    }
    renderHorizon(); renderStepper(); selectQueue();
  }
  function setTab(id, focus) {
    state.tab = id;
    document.querySelectorAll(".tab").forEach(function (b) {
      var on = b.getAttribute("data-tab") === id;
      b.setAttribute("aria-selected", String(on)); b.tabIndex = on ? 0 : -1;
      if (on && focus) b.focus();
    });
    document.querySelectorAll(".panel").forEach(function (p) { p.hidden = p.id !== "panel-" + id; });
    writeHash();
  }
  function setLang(l) {
    state.lang = l; store(false, "mwd.lang", l);
    applyLang(); renderHorizon(); renderQueue(); renderDossier(); writeHash();
  }
  function closeRailOnMobile() {
    if (window.matchMedia("(max-width: 899px)").matches) {
      $("rail").classList.remove("open"); $("rail-toggle").setAttribute("aria-expanded", "false");
    }
  }

  /* ---------- events ---------- */
  function bind() {
    document.querySelector(".lang-toggle").addEventListener("click", function (e) {
      var b = e.target.closest("button[data-lang]"); if (b) setLang(b.getAttribute("data-lang"));
    });
    var hg = $("horizon-group");
    hg.addEventListener("click", function (e) {
      var b = e.target.closest("button[data-h]"); if (b) setHorizon(Number(b.getAttribute("data-h")));
    });
    hg.addEventListener("keydown", function (e) {
      if (["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"].indexOf(e.key) < 0) return;
      e.preventDefault();
      var hs = horizons(), i = hs.indexOf(state.horizon);
      i = (i + (e.key === "ArrowLeft" || e.key === "ArrowUp" ? -1 : 1) + hs.length) % hs.length;
      setHorizon(hs[i]);
      var nb = hg.querySelector('[data-h="' + hs[i] + '"]'); if (nb) nb.focus();
    });
    $("cutoff-prev").addEventListener("click", function () {
      var l = cutoffsFor(state.horizon), i = l.indexOf(state.cutoff); if (i > 0) setCutoff(l[i - 1]);
    });
    $("cutoff-next").addEventListener("click", function () {
      var l = cutoffsFor(state.horizon), i = l.indexOf(state.cutoff); if (i < l.length - 1) setCutoff(l[i + 1]);
    });
    $("queue").addEventListener("click", function (e) {
      var b = e.target.closest("button[data-key]"); if (!b) return;
      selectDossier(b.getAttribute("data-key")).then(function () {
        closeRailOnMobile();
        if (window.matchMedia("(max-width: 899px)").matches) $("dossier").focus();
      });
    });
    $("rail-toggle").addEventListener("click", function () {
      var open = !$("rail").classList.contains("open");
      $("rail").classList.toggle("open", open); this.setAttribute("aria-expanded", String(open));
    });

    var main = $("dossier");
    main.addEventListener("click", function (e) {
      var tab = e.target.closest(".tab");
      if (tab) { setTab(tab.getAttribute("data-tab")); return; }
      var cite = e.target.closest(".cite");
      if (cite) { e.preventDefault(); openDrawer(cite.getAttribute("data-src"), cite.getAttribute("data-claim"), cite); return; }
      var copy = e.target.closest(".copy-btn");
      if (copy) { copyText(copy.getAttribute("data-copy"), copy); return; }
      if (e.target.closest("#reveal-btn")) {
        state.revealed = !state.revealed;
        renderQueue(); renderDossier(); writeHash();
        var btn = $("reveal-btn"); if (btn) btn.focus();
      }
    });
    main.addEventListener("keydown", function (e) {
      var tab = e.target.closest && e.target.closest(".tab"); if (!tab) return;
      var ids = SECTION_ORDER, i = ids.indexOf(state.tab), n = null;
      if (e.key === "ArrowRight") n = ids[(i + 1) % ids.length];
      else if (e.key === "ArrowLeft") n = ids[(i - 1 + ids.length) % ids.length];
      else if (e.key === "Home") n = ids[0];
      else if (e.key === "End") n = ids[ids.length - 1];
      if (n) { e.preventDefault(); setTab(n, true); }
    });
    main.addEventListener("change", function (e) {
      var cb = e.target; if (cb.type !== "checkbox") return;
      var list = cb.closest(".checklist"), key = list.getAttribute("data-store"), saved = {};
      list.querySelectorAll("input[type=checkbox]").forEach(function (x) { if (x.checked) saved[x.getAttribute("data-id")] = true; });
      store(false, key, JSON.stringify(saved));
      cb.closest(".check").classList.toggle("done", cb.checked);
      var total = list.querySelectorAll("input").length;
      $("check-progress").textContent = t("progress")(Object.keys(saved).length, total);
    });

    $("drawer").addEventListener("click", function (e) {
      var copy = e.target.closest(".copy-btn"); if (copy) copyText(copy.getAttribute("data-copy"), copy);
    });
    $("drawer-close").addEventListener("click", closeDrawer);
    $("drawer-scrim").addEventListener("click", closeDrawer);
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") closeDrawer();
      trapFocus(e);
    });
  }

  /* ---------- boot ---------- */
  function boot() {
    var h = readHash();
    var savedLang = store(true, "mwd.lang");
    state.lang = h.lang === "en" || h.lang === "th" ? h.lang : (savedLang === "en" ? "en" : "th");
    applyLang();
    bind();
    loadData().then(function (res) {
      state.index = res.index; state.fetcher = res.fetcher; state.fixture = !!res.index.fixture;
      $("fixture-pill").hidden = !state.fixture;
      var hs = horizons();
      state.horizon = hs.indexOf(Number(h.h)) >= 0 ? Number(h.h) : (hs.indexOf(12) >= 0 ? 12 : hs[0]);
      var cs = cutoffsFor(state.horizon);
      state.cutoff = cs.indexOf(h.c) >= 0 ? h.c : cs[Math.min(1, cs.length - 1)];
      if (h.m) state.key = h.m;
      if (SECTION_ORDER.indexOf(h.tab) >= 0) state.tab = h.tab;
      state.revealed = h.reveal === "1";
      renderHorizon(); renderStepper();
      return selectQueue().then(function () {
        var c = h.cite && state.dossier && (state.dossier.claims || []).concat(state.dossier.checklist || [])
          .find(function (x) { return x.id === h.cite; });
        if (c && c.source_ids && c.source_ids.length) openDrawer(c.source_ids[0], c.id, null);
      });
    }).catch(function (err) {
      $("dossier").innerHTML = '<div class="empty"><h2>' + esc(t("loadError")) + "</h2><p class=\"note\">" + esc(err && err.message) + "</p></div>";
    });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot); else boot();
})();
