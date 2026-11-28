/* Market Window Dossier app. Vanilla JS, no build step, no dependencies.
 *
 * Data: http(s) reads data/index.json and the files it lists; file:// and failures fall back to
 * data.bundle.js (browsers block fetch() for file:// pages). Contracts: mwd.index.v1, mwd.queue.v1
 * (PRD1 `ranked_rows`, or the older fixture `rows`) and mwd.dossier.v1.
 *
 * Interface labels are English. Body content (statements, checklist items, notes) follows the
 * TH/EN toggle, Thai by default, and the <html lang> attribute follows it.
 *
 * Two data sets: "current" (data/current/, the frozen Track A t0 forecast of 27 Nov 2026, 651 drugs, 12 and 24
 * months) and "history" (data/, the development time machine). Mode is in the hash (mode=current|history).
 *
 * URL hash keeps state, e.g. #view=queue&lang=en&h=24&c=2014&m=U%3AU188XYD42P&tab=patents&reveal=1&src=patent-1
 */
(function () {
  "use strict";

  var SECTIONS = [
    { id: "decision", label: "Decision summary" },
    { id: "market", label: "Market window" },
    { id: "competition", label: "Competition" },
    { id: "patents", label: "Patents" },
    { id: "thai_asean", label: "Thailand and ASEAN" },
    { id: "handoff", label: "FTO hand-off" },
    { id: "references", label: "References" }
  ];
  var SECTION_IDS = SECTIONS.map(function (s) { return s.id; });
  var VIEWS = ["queue", "dossiers", "sources", "settings"];
  var MONTHS_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  var MONTHS_TH = ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."];

  /* Body content only. Every heading, label and button stays English (DESIGN.md). */
  var T = {
    th: {
      notice: "แอปนี้ใช้ข้อมูลช่วงพัฒนา (วันตัดข้อมูลก่อนปี 2017) ผู้เชี่ยวชาญกฎหมายที่มีคุณสมบัติเป็นผู้ประเมินเสรีภาพในการดำเนินการ (FTO)",
      intro: {
        decision: "อันดับในคิวตรวจ โอกาสที่ยาสามัญรายแรกจะได้รับอนุมัติภายในช่วงพยากรณ์ และสิ่งที่ต้องทำต่อ",
        market: "โอกาสเข้าตลาดภายในช่วงพยากรณ์ สมมติฐานด้านราคา และข้อมูลความต้องการใช้ยาย้อนหลัง",
        competition: "ผู้ยื่นขอยาสามัญที่ได้รับอนุมัติแล้ว รูปแบบยา และวันอนุมัติยาต้นแบบ",
        patents: "สิทธิบัตรและสิทธิผูกขาดใน Orange Book ฉบับที่เผยแพร่ก่อนวันตัดข้อมูล และคดีความที่เกี่ยวข้อง",
        thai_asean: "ตระกูลสิทธิบัตร สถานะในไทย และทะเบียนตำรับยา รายการที่ยังยืนยันไม่ได้จะแสดงว่า “ต้องตรวจ”",
        handoff: "รายการที่ส่งต่อให้ผู้ประเมิน FTO และผู้ตรวจที่เกี่ยวข้อง ช่องที่ทำเครื่องหมายบันทึกไว้ในเบราว์เซอร์นี้เท่านั้น",
        references: "แหล่งข้อมูลทุกรายการ พร้อมฉบับ ตำแหน่งข้อมูล และค่า SHA-256 สำหรับตรวจซ้ำ"
      },
      noticeCur: function (d) { return "ค่าพยากรณ์ ณ วันที่ " + d + " เป็นค่าพยากรณ์ Track A ที่ล็อกไว้แล้ว ยังไม่ทราบผลลัพธ์ ผู้เชี่ยวชาญกฎหมายที่มีคุณสมบัติเป็นผู้ประเมินเสรีภาพในการดำเนินการ (FTO)"; },
      endpoint: "เหตุการณ์ที่พยากรณ์คือการอนุมัติขั้นสุดท้ายของยาสามัญรายแรกในสหรัฐฯ ไม่ใช่การวางจำหน่าย ความต้องการใช้ยา หรือการอนุญาตในประเทศไทย",
      method: "ผลการทดสอบที่ลงทะเบียนไว้ (ช่วงพยากรณ์ 24 เดือน ตรวจ 1 ใน 5 ของยา): M3 พบการอนุมัติยาสามัญรายแรกจริง 66.85% โดยมีค่าความแม่นยำเชิงบวก (precision) 26.62% ผลของคิวนี้ยังไม่ทราบจนกว่าจะรันตัวให้คะแนนในเดือนพฤศจิกายน 2027 และ 2028",
      search: {
        none: function (q) { return "ไม่พบยาที่ตรงกับ “" + q + "” ชื่อยาในข้อมูลเป็นภาษาอังกฤษ (ชื่อสารออกฤทธิ์หรือชื่อที่แสดง)"; },
        help: "ค้นหาแบบตรงบางส่วน ไม่แยกตัวพิมพ์ใหญ่เล็ก ใช้ชื่อสารออกฤทธิ์หรือชื่อที่แสดงเป็นภาษาอังกฤษ กด Enter เพื่อเปิดรายการแรก",
        count: function (n, all) { return "ตรงกัน " + n + " จาก " + all; }
      },
      launch: {
        h12: function (d, e) { return "วันเปิดตัว " + d + " อยู่ในช่วงพยากรณ์ 12 เดือน (ถึง " + e + ") จึงแสดงค่าพยากรณ์ 12 เดือน ค่านี้คือโอกาสที่ยาสามัญรายแรกได้รับอนุมัติขั้นสุดท้ายในสหรัฐฯ ไม่ใช่วันเปิดตัว"; },
        h24: function (d, e) { return "วันเปิดตัว " + d + " อยู่ในช่วงพยากรณ์ 24 เดือน (ถึง " + e + ") จึงแสดงค่าพยากรณ์ 24 เดือน ค่านี้คือโอกาสที่ยาสามัญรายแรกได้รับอนุมัติขั้นสุดท้ายในสหรัฐฯ ไม่ใช่วันเปิดตัว"; },
        out: function (d, e) { return "วันเปิดตัว " + d + " อยู่นอกช่วงพยากรณ์ ค่าพยากรณ์สิ้นสุด " + e + " จึงไม่แสดงตัวเลข"; },
        before: function (d) { return "วันที่นี้ไม่เกินวันอ้างอิง (" + d + ") โปรดเลือกวันที่หลังจากนั้น"; }
      },
      outsideBody: function (d, e) { return "วันเปิดตัวที่วางแผนไว้ " + d + " ช้ากว่าวันสุดท้ายของช่วงพยากรณ์ (" + e + ") จึงไม่แสดงค่าพยากรณ์ ลำดับ หรือตำแหน่งในคิว"; },
      ties: function (b, size, n) {
        return "คะแนน M3 ที่เท่ากันใช้ลำดับเดียวกัน และรายการที่คะแนนเท่ากับเส้นตัดที่ช่องที่ " + size + " จะแบ่งช่องที่เหลือเท่า ๆ กัน (แสดงเป็นโอกาสเข้าคิวระหว่าง 0 ถึง 100%) " +
          "ในฉบับนี้มี " + b.above_boundary + " รายการที่คะแนนสูงกว่าเส้นตัด (" + pct(b.boundary_native_score, 2) + ") และ " + b.boundary_rows + " รายการอยู่ที่เส้นตัด โอกาสเข้าคิว " + pct(b.boundary_inclusion_probability, 0) +
          (b.boundary_rows > b.slots_at_boundary ? "" : " จึงไม่มียารายการใดเข้าคิวแบบเศษส่วน") + " จากทั้งหมด " + n + " รายการ";
      },
      inclusion: function (p) { return "โอกาสเข้าคิว " + pct(p, 0); },
      status: { known: "ทราบ", verify: "ต้องตรวจ", assumption: "สมมติฐาน", na: "ไม่เกี่ยวข้อง" },
      estimate: "ค่าประมาณ",
      owner: { "FTO evaluator": "ผู้ประเมิน FTO", "Patent reviewer": "ผู้ตรวจสิทธิบัตร", "R&D": "ฝ่ายวิจัยและพัฒนา", "BD": "ฝ่ายพัฒนาธุรกิจ",
        "Thai patent reviewer": "ผู้ตรวจสิทธิบัตรไทย", "Thai regulatory reviewer": "ผู้ตรวจทะเบียนยาไทย" },
      outcomeTag: { caught: "จับได้", missed: "พลาด", none: "ไม่เกิด" },
      firstApproval: function (d, h) { return "ยาสามัญรายแรกได้รับอนุมัติขั้นสุดท้ายเมื่อ " + d + " ภายในช่วงพยากรณ์ " + h + " เดือน"; },
      noApproval: function (d) { return "ไม่มียาสามัญรายแรกได้รับอนุมัติภายในช่วงพยากรณ์ (สิ้นสุด " + d + ")"; },
      result: {
        caught: "อยู่ในคิวตรวจ และเกิดเหตุการณ์จริง",
        missed: "อยู่นอกคิวตรวจ แต่เกิดเหตุการณ์จริง ระบบพลาดกรณีนี้",
        falseAlarm: "อยู่ในคิวตรวจ แต่ไม่เกิดเหตุการณ์ภายในช่วงพยากรณ์",
        quiet: "อยู่นอกคิวตรวจ และไม่เกิดเหตุการณ์"
      },
      capture: function (m, n, b) { return "คิวนี้จับยาที่มียาสามัญรายแรกได้ " + m + " จาก " + n + " รายการ (M3) ส่วนเกณฑ์เทียบตามอายุยา (B1) จับได้ " + b + " รายการ (ค่าคาดหมาย แบ่งกรณีคะแนนเท่ากันที่เส้นขีดความสามารถ)"; },
      outcomeNote: "ผลลัพธ์นี้เป็นข้อมูลช่วงพัฒนา ใช้ทบทวนย้อนหลังเท่านั้น ระบบไม่เห็นผลนี้ตอนจัดอันดับ",
      nextFallback: "ตรวจรายการในหัวข้อ FTO hand-off",
      noDossier: function (n) { return "ยังไม่มีรายงานของ " + n + " สำหรับช่วงพยากรณ์และวันที่นี้"; },
      noDossierBody: function (r, n, m, b) { return "อันดับ " + r + " จาก " + n + " · M3 " + m + " · B1 " + b + " แอปนี้มีรายงานเฉพาะยาตัวอย่าง 6 รายการในข้อมูลช่วงพัฒนา"; },
      undated: "ไม่ระบุวันที่",
      checkNote: "ช่องที่ทำเครื่องหมายบันทึกไว้ในเบราว์เซอร์นี้เท่านั้น ไม่ได้ส่งไปที่ใด",
      progress: function (a, b) { return "ตรวจแล้ว " + a + " จาก " + b; },
      emptyClaims: "ไม่มีข้อความในหัวข้อนี้",
      emptyQueue: "ไม่มีรายงานสำหรับช่วงพยากรณ์และวันที่นี้",
      settingsLang: "ภาษาของเนื้อหา: ข้อความ รายการตรวจ และหมายเหตุ หัวข้อและปุ่มเป็นภาษาอังกฤษเสมอ",
      capacityText: "คิวตรวจรับได้ 1 ใน 5 ของยาที่เข้าเกณฑ์ในแต่ละวันตัดข้อมูล ซึ่งเป็นงบการตรวจเดียวกับที่ใช้ทดสอบความแม่นยำ",
      storageText: function (n) { return "มีรายการตรวจที่บันทึกไว้ในเบราว์เซอร์นี้ " + n + " รายงาน"; },
      cleared: "ล้างรายการตรวจที่บันทึกไว้แล้ว",
      copied: "คัดลอกค่า SHA-256 แล้ว"
    },
    en: {
      notice: "This app uses development data (cutoffs before 2017). Qualified counsel decides freedom to operate (FTO).",
      intro: {
        decision: "Queue position, the chance of a first generic approval within the horizon, and what to do next.",
        market: "Chance of market entry within the horizon, price assumptions and past demand.",
        competition: "Approved generic applicants, dosage forms and the originator's approval dates.",
        patents: "Patents and exclusivities in the Orange Book edition public before the cutoff, and related court cases.",
        thai_asean: "Patent families, Thai status and drug registration. Anything not yet confirmed is marked verify.",
        handoff: "Items handed to the FTO evaluator and other reviewers. Ticks are saved in this browser only.",
        references: "Every source with its edition, locator and SHA-256 hash, so the dossier can be reproduced."
      },
      noticeCur: function (d) { return "Forecasts as of " + d + " are the frozen Track A forecasts. Outcomes are pending. Qualified counsel decides freedom to operate (FTO)."; },
      endpoint: "The forecast event is the first final US generic approval. It is not launch, demand or Thai permission.",
      method: "Registered test (24-month horizon, 1-in-5 review capacity): M3 found 66.85% of first generic approvals, with precision 26.62%. Outcomes for this queue stay pending until the scorer runs in November 2027 and November 2028.",
      search: {
        none: function (q) { return "No drug matches “" + q + "”. Names are indexed in English (active moiety or display name)."; },
        help: "Partial match, not case-sensitive, on the active moiety or display name in English. Press Enter to open the first result.",
        count: function (n, all) { return n + " of " + all + " match"; }
      },
      launch: {
        h12: function (d, e) { return "A launch on " + d + " falls in the 12-month window (to " + e + "). Showing the 12-month forecast. It is the chance of the first final US generic approval, not a launch date."; },
        h24: function (d, e) { return "A launch on " + d + " falls in the 24-month window (to " + e + "). Showing the 24-month forecast. It is the chance of the first final US generic approval, not a launch date."; },
        out: function (d, e) { return "A launch on " + d + " is outside the forecast horizon. Forecasts end on " + e + ", so no number is shown."; },
        before: function (d) { return "This date is on or before the reference date (" + d + "). Choose a later date."; }
      },
      outsideBody: function (d, e) { return "The planned launch date " + d + " is later than the last forecast date (" + e + "). No forecast, rank or queue position is shown."; },
      ties: function (b, size, n) {
        return "Tied M3 scores share one rank. A drug tied at the boundary (slot " + size + ") shares the remaining slots equally, shown as an inclusion probability between 0 and 100%. " +
          "In this edition " + b.above_boundary + " drugs score above the boundary (" + pct(b.boundary_native_score, 2) + ") and " + b.boundary_rows + " sits at it with inclusion probability " + pct(b.boundary_inclusion_probability, 0) +
          (b.boundary_rows > b.slots_at_boundary ? "" : ", so no drug is included fractionally") + " (" + n + " drugs in all).";
      },
      inclusion: function (p) { return "Inclusion probability " + pct(p, 0); },
      status: { known: "known", verify: "verify", assumption: "assumption", na: "not applicable" },
      estimate: "estimate",
      owner: {},
      outcomeTag: { caught: "Caught", missed: "Missed", none: "No event" },
      firstApproval: function (d, h) { return "First generic final approval on " + d + ", within the " + h + "-month horizon."; },
      noApproval: function (d) { return "No first generic approval within the horizon (ended " + d + ")."; },
      result: {
        caught: "In the review queue, and the event happened.",
        missed: "Outside the review queue, but the event happened. The system missed this case.",
        falseAlarm: "In the review queue, but no event within the horizon.",
        quiet: "Outside the review queue, and no event."
      },
      capture: function (m, n, b) { return "This queue caught " + m + " of " + n + " molecules that got a first generic (M3). The drug-age baseline (B1) caught " + b + " (expected value, ties at the capacity line shared)."; },
      outcomeNote: "Development outcome, for retrospective review only. The ranking did not see it.",
      nextFallback: "Work through the FTO hand-off items.",
      noDossier: function (n) { return "No dossier for " + n + " at this horizon and date."; },
      noDossierBody: function (r, n, m, b) { return "Rank " + r + " of " + n + " · M3 " + m + " · B1 " + b + ". The app holds dossiers for six example molecules in the development data."; },
      undated: "Not dated",
      checkNote: "Ticks are saved in this browser only and are not sent anywhere.",
      progress: function (a, b) { return a + " of " + b + " checked"; },
      emptyClaims: "No statements in this section.",
      emptyQueue: "No dossiers for this horizon and date.",
      settingsLang: "Content language for statements, checklist items and notes. Headings and buttons are always English.",
      capacityText: "The review queue holds 1 in 5 eligible molecules at each cutoff, the same review budget used in accuracy testing.",
      storageText: function (n) { return "Checklist ticks are saved in this browser for " + n + (n === 1 ? " dossier." : " dossiers."); },
      cleared: "Saved checklist ticks cleared.",
      copied: "SHA-256 copied."
    }
  };

  var state = {
    lang: "th", view: "queue", horizon: 12, cutoff: null, key: null, tab: "decision", revealed: false,
    show: "dossiers", src: null, index: null, fetcher: null, via: "", queue: null, dossier: null,
    error: null, sourceFilter: "", dossierFilter: "",
    mode: "current", q: "", launch: "", outside: false, raw: null
  };
  var cache = {}, sets = {};

  /* ---------- helpers ---------- */
  function $(id) { return document.getElementById(id); }
  function tx() { return T[state.lang]; }
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function L(obj, base) { return obj[base + "_" + state.lang] || obj[base + "_en"] || obj[base + "_th"] || ""; }
  function pct(p, digits) { return p == null ? "—" : (p * 100).toFixed(digits == null ? 1 : digits) + "%"; }
  function store(k, v) {
    try {
      if (v === undefined) return window.localStorage.getItem(k);
      if (v === null) window.localStorage.removeItem(k); else window.localStorage.setItem(k, v);
    } catch (e) { /* storage blocked: the app still works, ticks just do not persist */ }
    return null;
  }
  function fmtDate(iso, lang) {
    if (!iso) return "—";
    var m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso);
    if (!m) return iso;
    var d = Number(m[3]), mo = Number(m[2]) - 1, y = Number(m[1]);
    return (lang || "en") === "th" ? d + " " + MONTHS_TH[mo] + " " + (y + 543) : d + " " + MONTHS_EN[mo] + " " + y;
  }
  function niceName(n) {
    if (!n) return "—";
    if (n !== n.toUpperCase()) return n;
    var s = n.toLowerCase();
    var i = s.search(/[a-z]/);
    return i < 0 ? s : s.slice(0, i) + s.charAt(i).toUpperCase() + s.slice(i + 1);
  }
  function niceForm(f) {
    return String(f).toLowerCase().replace(/\b(iv|im|sc|er|xr|dr|odt)\b/g, function (w) { return w.toUpperCase(); })
      .replace(/^./, function (c) { return c.toUpperCase(); });
  }
  function icon(name) {
    var p = {
      print: '<path d="M6 9V3h12v6"/><rect x="3" y="9" width="18" height="8" rx="1"/><path d="M6 14h12v7H6z"/>',
      eye: '<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
      link: '<path d="M14 4h6v6"/><path d="M20 4 11 13"/><path d="M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/>'
    }[name];
    return '<svg class="icon" aria-hidden="true" viewBox="0 0 24 24">' + p + "</svg>";
  }
  function announce(msg) { var a = $("announcer"); a.textContent = ""; setTimeout(function () { a.textContent = msg; }, 30); }

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
      s.src = src; s.onload = res; s.onerror = function () { rej(new Error("Missing " + src)); };
      document.head.appendChild(s);
    });
  }
  /* One loader per set: "history" reads data/ and data.bundle.js, "current" reads data/current/ and
     data.current.bundle.js (large, so it is only loaded in Current queue mode when opened from a file). */
  function loadSet(name) {
    var cur = name === "current", dir = cur ? "data/current/" : "data/";
    var file = cur ? "data.current.bundle.js" : "data.bundle.js", g = cur ? "MWD_CURRENT" : "MWD_DATA";
    function fromBundle() {
      var D = window[g];
      if (!D || !D.index) throw new Error(file + " has no index");
      return {
        via: file + " (" + D.base + ")", index: D.index,
        fetcher: function (p) { return D.files[p] ? Promise.resolve(D.files[p]) : Promise.reject(new Error("Not bundled: " + p)); }
      };
    }
    function bundle() { return window[g] ? Promise.resolve(fromBundle()) : loadScript(file).then(fromBundle); }
    if (location.protocol === "file:") return bundle();
    return getJSON(dir + "index.json").then(function (idx) {
      return { via: dir + "index.json", index: idx, fetcher: function (p) { return getJSON(dir + p); } };
    }).catch(bundle);
  }
  /* The current index lists one dossier per drug for both horizons and no cutoff. Expand it to the history shape. */
  function normCurrentIndex(idx) {
    var asOf = idx.as_of, out = Object.assign({}, idx);
    out.queues = idx.queues.map(function (q) { return Object.assign({ cutoff: asOf }, q); });
    out.dossiers = [];
    idx.dossiers.forEach(function (d) {
      (d.horizons || [12, 24]).forEach(function (h) {
        out.dossiers.push({ key: d.key, display_name: d.display_name, cutoff: asOf, as_of: asOf, horizon_months: h, path: d.path });
      });
    });
    return out;
  }
  function ensureSet(name) {
    if (sets[name]) return Promise.resolve(sets[name]);
    return loadSet(name).then(function (res) {
      if (name === "current") res.index = normCurrentIndex(res.index);
      sets[name] = res;
      return res;
    });
  }
  function activate(name) {
    var s = sets[name];
    state.mode = name; state.index = s.index; state.fetcher = s.fetcher; state.via = s.via;
    document.body.setAttribute("data-mode", name);
  }
  function curAsOf() { return sets.current ? sets.current.index.as_of : "2026-11-27"; }
  function load(path) {
    var k = state.mode + ":" + path;
    if (!cache[k]) cache[k] = state.fetcher(path);
    return cache[k];
  }
  /* Current mode: one dossier file holds both horizons. Pick the active horizon's forecast and statements. When the
     planned launch date is outside the horizon, drop every statement that carries a forecast number. */
  function deriveDossier(raw) {
    if (state.mode !== "current") return raw;
    var h = state.horizon, out = state.outside;
    var claims = (raw.claims || []).filter(function (c) {
      var m = /^(queue|entry)-(12|24)$/.exec(c.id);
      return !m || (!out && Number(m[2]) === h);
    });
    return Object.assign({}, raw, { forecast: out ? null : (h === 12 ? raw.forecast_12m : raw.forecast), claims: claims, outside: out, _idx: null });
  }
  function normQueue(q) {
    var rows = (q.ranked_rows || q.rows || []).slice().sort(function (a, b) {
      return (a.m3_rank || 0) - (b.m3_rank || 0) || (b.m3_p || 0) - (a.m3_p || 0);
    });
    rows.forEach(function (r, i) { if (!r.m3_rank) r.m3_rank = i + 1; });
    var size = q.queue_size || rows.filter(function (r) { return r.in_queue; }).length;
    var events = rows.filter(function (r) { return r.event; }).length;
    var caught = rows.filter(function (r) { return r.event && r.in_queue; }).length;
    return { as_of: q.as_of, horizon: q.horizon_months, window_end: q.window_end, size: size, rows: rows,
      events: events, caught: caught, b1: state.mode === "current" ? 0 : b1Capture(rows, size), boundary: q.boundary || null };
  }
  /* B1 queue at the same capacity: rank by B1; molecules tied at the capacity line share the
     remaining slots, so the capture is an expected value (as in the registered analysis). */
  function b1Capture(rows, size) {
    var sorted = rows.slice().sort(function (a, b) { return (b.b1_p || 0) - (a.b1_p || 0); });
    if (!sorted.length || !size) return 0;
    var line = sorted[Math.min(size, sorted.length) - 1].b1_p;
    var above = sorted.filter(function (r) { return r.b1_p > line; });
    var tied = sorted.filter(function (r) { return r.b1_p === line; });
    var share = (size - above.length) / tied.length;
    return above.filter(function (r) { return r.event; }).length + share * tied.filter(function (r) { return r.event; }).length;
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
  function dossierEntry(key, h, c) {
    h = h || state.horizon; c = c || state.cutoff;
    return (state.index.dossiers || []).find(function (d) { return d.key === key && d.horizon_months === h && String(d.cutoff) === c; });
  }
  function norm(s) { return String(s == null ? "" : s).normalize("NFKC").toLowerCase().trim(); }
  function matchRow(r) {
    var q = norm(state.q);
    if (!q) return true;
    var hay = norm(r.display_name + " " + r.key);
    return q.split(/\s+/).every(function (w) { return hay.indexOf(w) >= 0; });
  }
  function pad2(n) { return (n < 10 ? "0" : "") + n; }
  function addMonths(iso, n) {
    var m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso), y = Number(m[1]), mo = Number(m[2]) - 1 + n, d = Number(m[3]);
    y += Math.floor(mo / 12); mo = ((mo % 12) + 12) % 12;
    var last = new Date(Date.UTC(y, mo + 1, 0)).getUTCDate();
    return y + "-" + pad2(mo + 1) + "-" + pad2(Math.min(d, last));
  }
  /* A planned launch date maps to the forecast window that covers it: (t0, t0+12m] is the 12-month window,
     (t0+12m, t0+24m] the 24-month window, later is outside the horizon. No new forecast is computed. */
  function launchInfo() {
    if (state.mode !== "current" || !state.launch) return null;
    var t0 = curAsOf(), d = state.launch;
    if (d <= t0) return { kind: "before" };
    if (d <= addMonths(t0, 12)) return { kind: "h12", h: 12, end: addMonths(t0, 12) };
    if (d <= addMonths(t0, 24)) return { kind: "h24", h: 24, end: addMonths(t0, 24) };
    return { kind: "out", end: addMonths(t0, 24) };
  }
  function applyLaunch() {
    var w = launchInfo();
    state.outside = !!(w && w.kind === "out");
    if (w && w.h) state.horizon = w.h;
    renderLaunchMsg();
  }
  function renderLaunchMsg() {
    var el = $("launch-msg"), w = launchInfo(), t = tx().launch, L = state.lang, txt = "";
    if (w) {
      if (w.kind === "before") txt = t.before(fmtDate(curAsOf(), L));
      else txt = t[w.kind](fmtDate(state.launch, L), fmtDate(w.end, L));
    }
    el.lang = L; el.textContent = txt;
    el.className = "launch-msg cur-only" + (w ? (w.kind === "out" || w.kind === "before" ? " is-warn" : " is-ok") : "");
  }
  function asOfOf(c) {
    var q = state.index.queues.find(function (x) { return String(x.cutoff) === String(c); });
    return q ? q.as_of : c + "-01-01";
  }

  /* ---------- hash ---------- */
  function readHash() {
    var out = {};
    location.hash.replace(/^#/, "").split("&").forEach(function (kv) {
      if (!kv) return;
      var i = kv.indexOf("=");
      out[decodeURIComponent(kv.slice(0, i < 0 ? kv.length : i))] = i < 0 ? "" : decodeURIComponent(kv.slice(i + 1));
    });
    return out;
  }
  var writingHash = false;
  function writeHash() {
    var p = ["mode=" + state.mode, "view=" + state.view, "lang=" + state.lang, "h=" + state.horizon, "c=" + state.cutoff];
    if (state.mode === "current" && state.q) p.push("q=" + encodeURIComponent(state.q));
    if (state.mode === "current" && state.launch) p.push("ld=" + state.launch);
    if (state.key) p.push("m=" + encodeURIComponent(state.key));
    if (state.tab !== "decision") p.push("tab=" + state.tab);
    if (state.revealed) p.push("reveal=1");
    if (state.show !== "dossiers") p.push("show=" + state.show);
    if (state.src) p.push("src=" + encodeURIComponent(state.src));
    var h = "#" + p.join("&");
    if (location.hash === h) return;
    writingHash = true;
    try { history.replaceState(null, "", h); } catch (e) { location.hash = h; }
    setTimeout(function () { writingHash = false; }, 0);
  }

  /* ---------- language ---------- */
  function applyLang() {
    document.documentElement.lang = state.lang;
    document.querySelectorAll("[data-t]").forEach(function (el) {
      var k = el.getAttribute("data-t"), v = tx()[k];
      if (state.mode === "current" && tx()[k + "Cur"]) v = tx()[k + "Cur"](fmtDate(curAsOf(), state.lang));
      el.textContent = v;
    });
    document.querySelectorAll(".lang button").forEach(function (b) {
      b.setAttribute("aria-pressed", String(b.getAttribute("data-lang") === state.lang));
    });
  }

  /* ---------- queue panel ---------- */
  function renderFilters() {
    $("f-horizon").innerHTML = horizons().map(function (h) {
      return '<option value="' + h + '"' + (h === state.horizon ? " selected" : "") + ">" + h + " months</option>";
    }).join("");
    $("f-asof").innerHTML = cutoffsFor(state.horizon).map(function (c) {
      return '<option value="' + c + '"' + (c === state.cutoff ? " selected" : "") + ">" + fmtDate(asOfOf(c)) + "</option>";
    }).join("");
    $("f-show").value = state.show;
    if ($("f-search").value !== state.q) $("f-search").value = state.q;
    if ($("f-launch").value !== state.launch) $("f-launch").value = state.launch;
  }
  function obEdition() {
    var d = state.dossier;
    if (!d) return null;
    return (d.sources || []).find(function (s) { return s.issuer === "U.S. FDA" && /^ob-/.test(s.id) && s.version; }) || null;
  }
  function renderModebar() {
    document.querySelectorAll(".mode-switch button").forEach(function (b) {
      b.setAttribute("aria-pressed", String(b.getAttribute("data-mode") === state.mode));
    });
    var bits, foot;
    if (state.mode === "current") {
      var v = state.index.version || {}, ob = obEdition();
      bits = ["<b>" + esc(state.index.label || "Track A t0 forecast, outcome pending") + "</b>",
        "Reference date <b>" + fmtDate(curAsOf()) + "</b>",
        ob ? "Orange Book edition <b>" + fmtDate(ob.version) + "</b>" + (ob.public_date ? " (public " + fmtDate(ob.public_date) + ")" : "") : "",
        "Horizon <b>" + (state.outside ? "outside the forecast horizon" : state.horizon + " months") + "</b>",
        v.freeze === "verified" ? "Freeze tag <b>" + esc(v.tag) + "</b>" : "Freeze not verified"];
      foot = "Current queue: Track A t0 forecast of " + fmtDate(curAsOf()) + ", outcomes pending.";
    } else {
      bits = ["<b>Development data</b>, historical time machine",
        "Cutoff <b>" + (state.cutoff ? fmtDate(asOfOf(state.cutoff)) : "—") + "</b>",
        "Horizon <b>" + state.horizon + " months</b>"];
      foot = "Development data: US cutoffs before 2017.";
    }
    $("mode-facts").innerHTML = bits.filter(Boolean).map(function (x) { return "<span>" + x + "</span>"; }).join("");
    $("foot-data").textContent = foot;
  }
  function outcomeTag(r) {
    var o = tx().outcomeTag;
    if (r.event && r.in_queue) return '<span class="tag tag-known">' + esc(o.caught) + "</span>";
    if (r.event) return '<span class="tag tag-miss">' + esc(o.missed) + "</span>";
    return '<span class="tag tag-na">' + esc(o.none) + "</span>";
  }
  function renderQueue() {
    var q = state.queue, body = $("queue-body"), cur = state.mode === "current", hide = cur && state.outside;
    $("q-out-h").hidden = !state.revealed;
    if (!q) { body.innerHTML = ""; $("queue-meta").textContent = ""; return; }
    var rows = state.show === "all" || cur ? q.rows : q.rows.filter(function (r) { return dossierEntry(r.key); });
    if (cur) {
      if (state.q.trim()) rows = rows.filter(matchRow);
      if (hide) rows = rows.slice().sort(function (a, b) { return niceName(a.display_name).localeCompare(niceName(b.display_name)); });
      $("queue-meta").textContent = state.q.trim() ? tx().search.count(rows.length, q.rows.length) : hide ? q.rows.length + " drugs" : q.size + " of " + q.rows.length + " in queue";
      $("queue-help").textContent = hide ? "Listed alphabetically. No ranking or number is shown outside the forecast horizon." : "Ranked by M3. Use the arrow keys to move through the queue.";
      $("search-help").textContent = tx().search.help; $("search-help").lang = state.lang;
      var tb = $("ties-body");
      tb.textContent = q.boundary ? tx().ties(q.boundary, q.size, q.rows.length) : ""; tb.lang = state.lang;
    } else {
      $("queue-meta").textContent = q.size + " of " + q.rows.length + " reviewed";
      $("queue-help").textContent = "Ranked by M3. Use the arrow keys to move through the queue.";
    }
    var cols = state.revealed ? 4 : 3;
    if (!rows.length) {
      body.innerHTML = '<tr class="q-empty"><td colspan="' + cols + '">' + esc(cur && state.q.trim() ? tx().search.none(state.q.trim()) : tx().emptyQueue) + "</td></tr>";
      return;
    }
    var html = [], dividerDone = hide;
    rows.forEach(function (r) {
      if (!dividerDone && !r.in_queue) {
        html.push('<tr class="cap" lang="en"><td colspan="' + cols + '">Review capacity: ' + q.size + " of " + q.rows.length + " (1 in 5)</td></tr>");
        dividerDone = true;
      }
      var has = !!dossierEntry(r.key), cur = r.key === state.key;
      var label = niceName(r.display_name);
      html.push('<tr class="q-row' + (cur ? " is-current" : "") + (has ? "" : " q-nodoc") + '" data-key="' + esc(r.key) + '">' +
        '<td class="q-rank num">' + (hide ? "—" : r.m3_rank) + "</td>" +
        '<td class="q-name"><button type="button" class="q-btn" data-key="' + esc(r.key) + '"' + (cur ? ' aria-current="true"' : "") +
        ' tabindex="' + (cur ? 0 : -1) + '">' + esc(label) +
        (hide ? "" : '<span class="sr-only" lang="en">, rank ' + r.m3_rank + ", M3 " + pct(r.m3_p) + (r.in_queue ? ", in review queue" : ", outside review queue") + "</span>") +
        (has ? "" : '<span class="q-doc-mark" lang="en">No dossier</span>') + "</button></td>" +
        '<td class="q-pct c-num num">' + (hide ? "—" : pct(r.m3_p)) + "</td>" +
        (state.revealed ? '<td class="q-out">' + outcomeTag(r) + "</td>" : "") + "</tr>");
    });
    if (!dividerDone && state.show === "all" && !cur) {
      html.push('<tr class="cap" lang="en"><td colspan="' + cols + '">Review capacity: ' + q.size + " of " + q.rows.length + "</td></tr>");
    }
    body.innerHTML = html.join("");
    if (!body.querySelector(".q-btn[tabindex='0']")) { var f = body.querySelector(".q-btn"); if (f) f.tabIndex = 0; }
  }
  function scrollQueueToCurrent() {
    var cur = $("queue-body").querySelector("tr.is-current");
    if (cur && cur.scrollIntoView) cur.scrollIntoView({ block: "nearest" });
  }

  /* ---------- dossier ---------- */
  function statusOf(c) {
    if (c.state === "unknown") return "verify";
    if (c.state === "not_applicable") return "na";
    if (c.kind === "assumption") return "assumption";
    return "known";
  }
  function statusTag(s) {
    var cls = { known: "tag-known", verify: "tag-verify", assumption: "tag-assumption", na: "tag-na" }[s];
    return '<span class="tag ' + cls + '">' + esc(tx().status[s]) + "</span>";
  }
  function srcIndex(d) {
    if (d._idx) return d._idx;
    var m = {};
    (d.sources || []).forEach(function (s, i) { m[s.id] = i + 1; });
    d._idx = m;
    return m;
  }
  function citeButtons(ids, d, limit) {
    var idx = srcIndex(d);
    ids = (ids || []).filter(function (id) { return idx[id]; });
    if (!ids.length) return '<span class="cite-more" lang="en">None</span>';
    limit = limit || 6;
    var shown = ids.slice(0, limit);
    return '<span class="cites">' + shown.map(function (id) {
      var s = d.sources[idx[id] - 1];
      return '<button type="button" class="cite' + (id === state.src ? " is-on" : "") + '" data-src="' + esc(id) + '" aria-label="' +
        esc("Source " + idx[id] + ": " + s.issuer + ", " + s.title) + '" lang="en">[' + idx[id] + "]</button>";
    }).join("") + (ids.length > limit ? '<span class="cite-more" lang="en">+' + (ids.length - limit) + " more</span>" : "") + "</span>";
  }
  function claimsIn(d, sec) { return (d.claims || []).filter(function (c) { return c.section === sec; }); }
  function statementsTable(d, claims) {
    if (!claims.length) return '<p class="st-empty">' + esc(tx().emptyClaims) + "</p>";
    return '<table class="st"><thead lang="en"><tr><th scope="col">Statement</th><th scope="col" class="c-status">Status</th><th scope="col" class="c-src">Source</th></tr></thead><tbody>' +
      claims.map(function (c) {
        var cited = state.src && (c.source_ids || []).indexOf(state.src) >= 0;
        return "<tr" + (cited ? ' class="is-cited"' : "") + "><td>" + esc(L(c, "text")) +
          (c.kind === "estimate" ? '<span class="kind">' + esc(tx().estimate) + "</span>" : "") + "</td>" +
          "<td>" + statusTag(statusOf(c)) + "</td><td>" + citeButtons(c.source_ids, d) + "</td></tr>";
      }).join("") + "</tbody></table>";
  }
  function countStatus(claims) {
    var out = { known: 0, verify: 0, assumption: 0, na: 0 };
    claims.forEach(function (c) { out[statusOf(c)]++; });
    return out;
  }
  function citedIds(d, items) {
    var seen = {}, out = [];
    items.forEach(function (c) { (c.source_ids || []).forEach(function (id) { if (!seen[id]) { seen[id] = 1; out.push(id); } }); });
    var idx = srcIndex(d);
    return out.filter(function (id) { return idx[id]; }).sort(function (a, b) { return idx[a] - idx[b]; });
  }
  function itemsForTab(d, sec) {
    var items = claimsIn(d, sec);
    if (sec === "handoff") items = items.concat(d.checklist || []);
    return items;
  }

  function outcomeKind(f, o) {
    var event = !!(o && o.first_final_anda_date);
    if (f.in_queue) return event ? "caught" : "falseAlarm";
    return event ? "missed" : "quiet";
  }
  function outcomeBlock(d) {
    var o = d.outcome_reveal, f = d.forecast || {}, q = state.queue;
    if (!o || !state.revealed) return "";
    var k = outcomeKind(f, o), t = tx();
    var tagCls = k === "caught" ? "tag-known" : k === "missed" ? "tag-miss" : "tag-na";
    var tagTxt = k === "caught" ? t.outcomeTag.caught : k === "missed" ? t.outcomeTag.missed : t.outcomeTag.none;
    var main = o.first_final_anda_date ? t.firstApproval(fmtDate(o.first_final_anda_date, state.lang), f.horizon_months)
      : t.noApproval(fmtDate(o.window_end, state.lang));
    return '<section class="outcome" id="outcome" aria-labelledby="outcome-h">' +
      '<div class="outcome-head" lang="en"><h2 id="outcome-h">Outcome</h2><span class="panel-meta">Development data</span></div><dl>' +
      '<dt lang="en">What happened</dt><dd>' + esc(main) + (o.source_ids && o.source_ids.length ? " " + citeButtons(o.source_ids, d) : "") + "</dd>" +
      '<dt lang="en">Queue result</dt><dd class="result">' + '<span class="tag ' + tagCls + '">' + esc(tagTxt) + "</span><span>" + esc(t.result[k]) + "</span></dd>" +
      (q ? '<dt lang="en">This queue</dt><dd>' + esc(t.capture(q.caught, q.events, (Math.round(q.b1 * 10) / 10).toFixed(1))) + "</dd>" : "") +
      '<dt lang="en">Note</dt><dd>' + esc(t.outcomeNote) + "</dd></dl></section>";
  }

  function statsRow(cells) {
    return '<div class="stats" lang="en">' + cells.map(function (c) {
      return '<div><div class="k">' + c[0] + '</div><div class="v num' + (c[3] ? " " + c[3] : "") + '">' + c[1] + "</div>" + (c[2] ? '<div class="s">' + c[2] + "</div>" : "") + "</div>";
    }).join("") + "</div>";
  }

  function decisionPanel(d) {
    var f = d.forecast || {}, h = f.horizon_months || state.horizon, claims = d.claims || [];
    var q = state.queue, n = q ? q.rows.length : null;
    var open = claims.filter(function (c) { return c.state === "unknown"; }).length;
    var assume = claims.find(function (c) { return c.section === "decision" && c.kind === "assumption"; }) ||
      claims.find(function (c) { return c.kind === "assumption"; });
    var next = (d.checklist || [])[0];
    var incl = f.queue_inclusion_probability, fractional = incl != null && incl > 0 && incl < 1;
    var html = d.outside ? statsRow([
      ["First generic approval forecast (M3)", "—", "Outside the forecast horizon"],
      ["Drug-age baseline (B1)", "—", "Outside the forecast horizon"],
      ["Queue position", "—", "Outside the forecast horizon"],
      ["To verify", String(open), "Statements across all sections", open ? "v-verify" : ""]
    ]) : statsRow([
      ["First generic within " + h + " months (M3)", pct(f.m3_p_entry), "Evidence model"],
      ["Drug-age baseline (B1)", pct(f.b1_p_entry), "Same horizon"],
      ["Queue position", f.m3_rank + (n ? " <small>of " + n + "</small>" : ""), (f.in_queue ? "Inside" : "Outside") + " review capacity (" + (f.queue_size || "—") + ")" + (fractional ? ", inclusion probability " + pct(incl, 0) : "")],
      ["To verify", String(open), "Statements across all sections", open ? "v-verify" : ""]
    ]);
    if (state.mode === "current") {
      html += '<p class="note method-note">' + esc(tx().endpoint) + "</p>" + '<p class="note method-note">' + esc(tx().method) + "</p>";
    }
    html += '<dl class="kv">' +
      '<dt lang="en">Next action</dt><dd>' + esc(next ? L(next, "text") : tx().nextFallback) +
      (next ? ' <span class="kind" lang="en">Owner: ' + esc(next.owner) + "</span>" : "") + "</dd>" +
      '<dt lang="en">Key assumption</dt><dd>' + esc(assume ? L(assume, "text") : "—") + "</dd></dl>";
    html += '<h3 class="sub" lang="en">Open items by section</h3><table class="open-by"><thead lang="en"><tr><th scope="col">Section</th><th scope="col" class="c-num">Statements</th><th scope="col" class="c-num">To verify</th></tr></thead><tbody lang="en">' +
      SECTIONS.map(function (s) {
        var cs = claimsIn(d, s.id), u = cs.filter(function (c) { return c.state === "unknown"; }).length;
        return '<tr><td><a href="#" data-goto="' + s.id + '">' + s.label + '</a></td><td class="c-num num">' + cs.length + '</td><td class="c-num num">' +
          (u ? '<span class="tag tag-verify">' + u + "</span>" : "0") + "</td></tr>";
      }).join("") + "</tbody></table>";
    html += '<h3 class="sub" lang="en">Statements</h3>' + statementsTable(d, claimsIn(d, "decision"));
    return html;
  }
  function genericPanel(d, sec) {
    var cs = claimsIn(d, sec), n = countStatus(cs);
    return statsRow([
      ["Statements", String(cs.length)], ["Known", String(n.known)],
      ["To verify", String(n.verify), "", n.verify ? "v-verify" : ""], ["Sources cited", String(citedIds(d, cs).length)]
    ]) + statementsTable(d, cs);
  }
  function checkKey(d) { return "mwd.check." + d.molecule.key + "." + d.as_of + "." + ((d.forecast || {}).horizon_months || "outside"); }
  function handoffPanel(d) {
    var items = d.checklist || [], key = checkKey(d), saved = {};
    try { saved = JSON.parse(store(key) || "{}") || {}; } catch (e) { saved = {}; }
    var done = items.filter(function (c) { return saved[c.id]; }).length;
    var cs = claimsIn(d, "handoff");
    var html = statsRow([
      ["Checklist items", String(items.length)], ["Checked", '<span id="check-done">' + done + "</span>"],
      ["FTO evaluator items", String(items.filter(function (c) { return c.owner === "FTO evaluator"; }).length)],
      ["Sources cited", String(citedIds(d, items.concat(cs)).length)]
    ]);
    if (cs.length) html += statementsTable(d, cs);
    html += '<h3 class="sub"><span lang="en">Evaluator checklist</span><span class="progress" id="check-progress">' + esc(tx().progress(done, items.length)) + "</span></h3>";
    html += '<table class="st checklist" data-store="' + esc(key) + '"><thead lang="en"><tr><th scope="col" class="c-check"><span class="sr-only">Done</span></th><th scope="col">Task</th><th scope="col" class="c-owner">Owner</th><th scope="col" class="c-src">Source</th></tr></thead><tbody>' +
      items.map(function (c) {
        var id = "chk-" + c.id;
        return '<tr class="' + (saved[c.id] ? "done" : "") + '"><td><input type="checkbox" class="cb" id="' + esc(id) + '" data-id="' + esc(c.id) + '"' + (saved[c.id] ? " checked" : "") + "></td>" +
          '<td><label class="task-text" for="' + esc(id) + '">' + esc(L(c, "text")) + "</label></td>" +
          "<td>" + esc(tx().owner[c.owner] || c.owner) + "</td><td>" + citeButtons(c.source_ids, d, 4) + "</td></tr>";
      }).join("") + "</tbody></table>" +
      '<p class="note cb-note">' + esc(tx().checkNote) + "</p>";
    return html;
  }
  function referencesPanel(d) {
    var cs = claimsIn(d, "references"), srcs = d.sources || [];
    var hashed = srcs.filter(function (s) { return /^[a-f0-9]{64}$/.test(s.sha256 || ""); }).length;
    var dated = srcs.filter(function (s) { return s.public_date; }).length;
    var html = statsRow([
      ["Sources", String(srcs.length)], ["With SHA-256", String(hashed)], ["With a public date", String(dated)],
      ["Contract", esc(d.schema_version || d.schema || "mwd.dossier.v1").replace("mwd.", "")]
    ]);
    html += statementsTable(d, cs);
    html += '<h3 class="sub" lang="en">All sources</h3><table class="st refs" lang="en"><thead><tr><th scope="col" class="c-no">No.</th><th scope="col">Source</th><th scope="col" class="c-pub">Published</th><th scope="col" class="c-sha">SHA-256</th></tr></thead><tbody>' +
      srcs.map(function (s, i) {
        return "<tr><td class=\"num\">" + (i + 1) + "</td><td><b>" + esc(s.issuer) + "</b>, " + esc(s.title) +
          '<span class="kind">Edition ' + esc(s.version || "—") + " · " + esc(s.locator || "—") + "</span></td>" +
          '<td class="num">' + (s.public_date ? fmtDate(s.public_date) : "Not dated") + "</td>" +
          '<td><code class="hash-short" title="' + esc(s.sha256 || "") + '">' + (s.sha256 ? esc(s.sha256.slice(0, 12)) + "…" : "—") + "</code></td></tr>";
      }).join("") + "</tbody></table>";
    return html;
  }

  function renderDossier() {
    var main = $("dossier");
    main.setAttribute("aria-busy", "false");
    if (state.error) { main.innerHTML = errorState(state.error); return; }
    if (state.view !== "queue") { main.innerHTML = renderView(); bindViewAfterRender(); return; }
    var d = state.dossier;
    if (!d) { main.innerHTML = emptyState(); return; }
    var f = d.forecast || {}, name = niceName(d.molecule.display_name);
    var hz = d.outside ? "Outside the forecast horizon" : (f.horizon_months || state.horizon) + " months";
    var crumb = '<nav class="crumb" aria-label="Breadcrumb" lang="en"><a href="#" data-focus="queue">Queue</a><span class="sep" aria-hidden="true">›</span>' +
      '<a href="#" data-focus="queue">' + hz + ", as of " + fmtDate(d.as_of) + '</a><span class="sep" aria-hidden="true">›</span><span aria-current="page">' + esc(name) + "</span></nav>";
    var actions = '<div class="d-actions" lang="en">' +
      (d.outcome_reveal ? '<button type="button" class="btn btn-secondary" id="reveal-btn" aria-pressed="' + state.revealed + '" aria-controls="outcome-slot">' + icon("eye") + (state.revealed ? "Hide outcome" : "Show outcome") + "</button>" : "") +
      '<button type="button" class="btn btn-secondary" id="print-btn">' + icon("print") + "Print dossier</button></div>";
    var forms = (d.molecule.dosage_forms || []).map(niceForm).join("; ");
    var meta = '<div class="d-meta" lang="en"><span>As of <b>' + fmtDate(d.as_of) + "</b></span><span>Horizon <b>" + hz + "</b></span>" +
      "<span>Jurisdiction <b>" + esc(d.jurisdiction || "—") + "</b></span>" + (forms ? "<span>Dosage forms <b>" + esc(forms) + "</b></span>" : "") + "</div>";
    var queueChip = d.outside ? "" : (f.in_queue ? '<span class="chip chip-navy">In review queue</span>' : '<span class="chip">Outside review queue</span>');
    var modeChip = state.mode === "current" ? '<span class="chip">' + esc(state.index.label || "Track A t0 forecast, outcome pending") + "</span>" : '<span class="chip">Development data</span>';
    var chips = '<div class="chips" lang="en">' + queueChip + modeChip + (state.index.fixture || d.fixture ? '<span class="chip chip-fixture">FIXTURE</span>' : "") + "</div>";
    if (d.outside) {
      var w = launchInfo();
      chips += '<div class="outside" role="status"><b lang="en">Outside the forecast horizon</b><p lang="' + state.lang + '">' +
        esc(tx().outsideBody(fmtDate(state.launch, state.lang), fmtDate(w ? w.end : curAsOf(), state.lang))) + "</p></div>";
    }
    var printHead = '<p class="print-only note" lang="en">Market Window Dossier · printed ' + fmtDate(new Date().toISOString().slice(0, 10)) + " · " + esc(d.molecule.key) + "</p>";
    var tabs = '<div class="tabs" role="tablist" aria-label="Dossier sections" lang="en">' + SECTIONS.map(function (s) {
      var on = s.id === state.tab;
      return '<button type="button" class="tab" role="tab" id="tab-' + s.id + '" aria-controls="panel-' + s.id + '" aria-selected="' + on + '" tabindex="' + (on ? 0 : -1) + '" data-tab="' + s.id + '">' + s.label + "</button>";
    }).join("") + "</div>";
    var panels = SECTIONS.map(function (s) {
      var body = s.id === "decision" ? decisionPanel(d) : s.id === "handoff" ? handoffPanel(d) : s.id === "references" ? referencesPanel(d) : genericPanel(d, s.id);
      return '<section class="tabpanel" role="tabpanel" id="panel-' + s.id + '" aria-labelledby="tab-' + s.id + '" tabindex="0"' + (s.id === state.tab ? "" : " hidden") + ">" +
        '<h2 lang="en">' + s.label + '</h2><p class="tab-intro">' + esc(tx().intro[s.id]) + "</p>" + body + "</section>";
    }).join("");
    main.innerHTML = '<div class="d-wrap">' + printHead + crumb + '<div class="d-head"><h1>' + esc(name) + "</h1>" + actions + "</div>" + meta + chips +
      '<div id="outcome-slot">' + outcomeBlock(d) + "</div>" + tabs + panels + "</div>";
  }

  function emptyState() {
    var q = state.queue, r = q && q.rows.find(function (x) { return x.key === state.key; });
    if (!r) return '<div class="state" lang="en"><p class="state-title">Choose a molecule</p><p>Select a molecule in the review queue to open its dossier.</p></div>';
    var t = tx();
    return '<div class="state"><p class="state-title">' + esc(t.noDossier(niceName(r.display_name))) + "</p><p>" +
      esc(t.noDossierBody(r.m3_rank, q.rows.length, pct(r.m3_p), pct(r.b1_p))) + '</p><div class="state-actions" lang="en">' +
      '<button type="button" class="btn" data-action="show-dossiers">Show molecules with a dossier</button></div></div>';
  }
  function errorState(err) {
    return '<div class="state state-error" lang="en" role="alert"><p class="state-title">The data could not be loaded</p>' +
      "<p>The app needs <code>data/index.json</code> (on a web server) or <code>data.bundle.js</code> (when opened from a file). " +
      "Run <code>python product/demo/bundle.py</code> to create them, then reload this page.</p>" +
      '<p class="note">Details: ' + esc(err && err.message ? err.message : String(err)) + "</p></div>";
  }

  /* ---------- sources panel ---------- */
  function srcEntry(d, s, n, focus) {
    var short = s.sha256 ? s.sha256.slice(0, 10) + "…" + s.sha256.slice(-6) : null;
    var host = "";
    if (s.url) { try { host = new URL(s.url).hostname.replace(/^www\./, ""); } catch (e) { host = s.url; } }
    return '<li class="src' + (focus ? " is-focus" : "") + '" id="src-' + esc(s.id) + '" tabindex="-1">' +
      '<div class="src-title"><span class="src-n">[' + n + ']</span><span><b>' + esc(s.issuer) + "</b>, " + esc(s.title) + "</span></div>" +
      '<dl lang="en"><dt>Edition</dt><dd>' + esc(s.version || "—") + "</dd>" +
      "<dt>Published</dt><dd>" + (s.public_date ? fmtDate(s.public_date) : '<span lang="' + state.lang + '">' + esc(tx().undated) + "</span>") + "</dd>" +
      "<dt>Locator</dt><dd>" + esc(s.locator || "—") + "</dd>" +
      (s.retrieved ? "<dt>Retrieved</dt><dd>" + fmtDate(String(s.retrieved).slice(0, 10)) + "</dd>" : "") +
      "<dt>SHA-256</dt><dd>" + (short ? '<span class="hash"><code title="' + esc(s.sha256) + '">' + esc(short) + '</code><button type="button" class="copy" data-copy="' + esc(s.sha256) + '" aria-label="Copy SHA-256 of source ' + n + '">Copy</button></span>' : "None") + "</dd>" +
      (s.url ? '<dt>Link</dt><dd><a href="' + esc(s.url) + '" target="_blank" rel="noopener noreferrer">' + esc(host) + '<span class="sr-only"> (opens in a new tab)</span></a></dd>' : "") +
      "</dl></li>";
  }
  function renderSources() {
    var list = $("sources-list"), meta = $("sources-meta"), d = state.dossier;
    if (state.view !== "queue") return;
    if (!d) { list.innerHTML = '<li class="src-empty" lang="en">Sources appear here when a dossier is open.</li>'; meta.textContent = ""; return; }
    var idx = srcIndex(d);
    var ids = state.tab === "references" ? (d.sources || []).map(function (s) { return s.id; }) : citedIds(d, itemsForTab(d, state.tab));
    var inSection = ids.length;
    if (state.revealed && d.outcome_reveal) {
      (d.outcome_reveal.source_ids || []).forEach(function (id) { if (ids.indexOf(id) < 0 && idx[id]) ids.push(id); });
    }
    if (state.src && ids.indexOf(state.src) < 0 && idx[state.src]) ids.unshift(state.src);
    var extra = ids.length - inSection;
    meta.textContent = state.tab === "references" ? ids.length + " in this dossier"
      : inSection + " cited in this section" + (extra ? ", " + extra + " more" : "");
    list.innerHTML = ids.length ? ids.map(function (id) { return srcEntry(d, d.sources[idx[id] - 1], idx[id], id === state.src); }).join("")
      : '<li class="src-empty" lang="en">No sources cited in this section.</li>';
  }
  function focusSource(id, move) {
    state.src = id;
    renderSources();
    document.querySelectorAll("#dossier .cite").forEach(function (b) { b.classList.toggle("is-on", b.getAttribute("data-src") === id); });
    document.querySelectorAll("#dossier table.st tbody tr").forEach(function (tr) {
      var hit = !!tr.querySelector('.cite[data-src="' + (window.CSS && CSS.escape ? CSS.escape(id) : id) + '"]');
      tr.classList.toggle("is-cited", hit);
    });
    var el = document.getElementById("src-" + id);
    if (el) {
      el.scrollIntoView({ block: window.matchMedia("(max-width: 1279px)").matches ? "start" : "nearest", behavior: reduced() ? "auto" : "smooth" });
      if (move) el.focus({ preventScroll: true });
    }
    writeHash();
  }
  function reduced() { return window.matchMedia("(prefers-reduced-motion: reduce)").matches; }

  /* ---------- other views (Dossiers, Sources, Settings) ---------- */
  function renderView() {
    if (state.view === "dossiers") return dossiersView();
    if (state.view === "sources") return sourcesView();
    return settingsView();
  }
  function dossiersViewCurrent() {
    var q = state.queue, f = norm(state.dossierFilter), hide = state.outside;
    var rows = q ? q.rows.filter(function (r) { return !f || norm(r.display_name + " " + r.key).indexOf(f) >= 0; }) : [];
    rows = rows.slice().sort(function (a, b) { return niceName(a.display_name).localeCompare(niceName(b.display_name)); });
    var html = '<div class="view" lang="en"><h1>Dossiers</h1><p class="lead">All ' + (q ? q.rows.length : 651) + ' drugs in the current queue as of ' + fmtDate(curAsOf()) + ', ' +
      (hide ? "outside the forecast horizon (no numbers shown)" : state.horizon + "-month horizon") + '. Open one to see its dossier with the queue.</p>' +
      '<div class="view-tools"><label class="field"><span>Find a drug</span><input type="search" id="dossier-filter" value="' + esc(state.dossierFilter) + '" placeholder="Name"></label><span class="panel-meta">' + rows.length + " shown</span></div>" +
      '<table class="reg"><thead><tr><th scope="col">Drug</th><th scope="col" class="c-num">Rank</th><th scope="col" class="c-num">M3</th><th scope="col" class="c-num">B1</th><th scope="col">Queue</th></tr></thead><tbody>';
    html += rows.map(function (r) {
      return '<tr><td><a href="#" data-open="' + esc(r.key) + '" data-h="' + state.horizon + '" data-c="' + esc(state.cutoff) + '">' + esc(niceName(r.display_name)) + "</a></td>" +
        '<td class="c-num num">' + (hide ? "—" : r.m3_rank) + '</td><td class="c-num num">' + (hide ? "—" : pct(r.m3_p)) + '</td><td class="c-num num">' + (hide ? "—" : pct(r.b1_p)) + "</td><td>" +
        (hide ? "—" : r.in_queue ? '<span class="chip chip-navy">In queue</span>' : '<span class="chip">Outside</span>') + "</td></tr>";
    }).join("");
    if (!rows.length) html += '<tr><td colspan="5" class="st-empty">No drug matches “' + esc(state.dossierFilter) + "”.</td></tr>";
    return html + "</tbody></table></div>";
  }
  function dossiersView() {
    if (state.mode === "current") return dossiersViewCurrent();
    var list = (state.index.dossiers || []).slice();
    var f = state.dossierFilter.trim().toLowerCase();
    var html = '<div class="view" lang="en"><h1>Dossiers</h1><p class="lead">Every dossier in the development data, one per molecule, horizon and as-of date. Open one to see it with its review queue.</p>' +
      '<div class="view-tools"><label class="field"><span>Find a molecule</span><input type="search" id="dossier-filter" value="' + esc(state.dossierFilter) + '" placeholder="Name or key"></label></div>' +
      '<table class="reg"><thead><tr><th scope="col">Molecule</th><th scope="col">As of</th><th scope="col">Horizon</th><th scope="col" class="c-num">Rank</th><th scope="col" class="c-num">M3</th><th scope="col" class="c-num">B1</th><th scope="col">Queue</th></tr></thead><tbody id="dossier-rows">';
    var rows = list.filter(function (e) {
      return !f || niceName(e.display_name || "").toLowerCase().indexOf(f) >= 0 || e.key.toLowerCase().indexOf(f) >= 0;
    }).sort(function (a, b) {
      return niceName(a.display_name || a.key).localeCompare(niceName(b.display_name || b.key)) || a.horizon_months - b.horizon_months || String(a.cutoff).localeCompare(String(b.cutoff));
    });
    html += rows.map(function (e) {
      var d = e._d, fc = d ? d.forecast : null;
      var cur = e.key === state.key && e.horizon_months === state.horizon && String(e.cutoff) === state.cutoff;
      return "<tr" + (cur ? ' class="is-current"' : "") + '><td><a href="#" data-open="' + esc(e.key) + '" data-h="' + e.horizon_months + '" data-c="' + esc(e.cutoff) + '">' + esc(niceName(e.display_name || e.key)) + "</a></td>" +
        "<td>" + fmtDate(e.as_of || asOfOf(e.cutoff)) + "</td><td>" + e.horizon_months + ' months</td><td class="c-num num">' + (fc ? fc.m3_rank : "—") +
        '</td><td class="c-num num">' + (fc ? pct(fc.m3_p_entry) : "—") + '</td><td class="c-num num">' + (fc ? pct(fc.b1_p_entry) : "—") + "</td><td>" +
        (fc ? (fc.in_queue ? '<span class="chip chip-navy">In queue</span>' : '<span class="chip">Outside</span>') : "—") + "</td></tr>";
    }).join("");
    if (!rows.length) html += '<tr><td colspan="7" class="st-empty">No dossier matches “' + esc(state.dossierFilter) + "”.</td></tr>";
    return html + "</tbody></table></div>";
  }
  function sourcesView() {
    var d = state.dossier;
    if (!d) return '<div class="view" lang="en"><h1>Sources</h1><p class="lead">Open a dossier first. This page lists every source behind it.</p></div>';
    var f = state.sourceFilter.trim().toLowerCase();
    var counts = {};
    (d.claims || []).concat(d.checklist || []).forEach(function (c) { (c.source_ids || []).forEach(function (id) { counts[id] = (counts[id] || 0) + 1; }); });
    var rows = (d.sources || []).map(function (s, i) { return { s: s, n: i + 1 }; }).filter(function (x) {
      return !f || [x.s.issuer, x.s.title, x.s.version, x.s.locator, x.s.sha256, x.s.id].join(" ").toLowerCase().indexOf(f) >= 0;
    });
    return '<div class="view" lang="en"><nav class="crumb" aria-label="Breadcrumb"><a href="#view=queue" data-nav-link="queue">Queue</a><span class="sep" aria-hidden="true">›</span><span>' + esc(niceName(d.molecule.display_name)) + "</span></nav>" +
      "<h1>Sources</h1><p class=\"lead\">All " + (d.sources || []).length + " sources behind the " + esc(niceName(d.molecule.display_name)) + " dossier as of " + fmtDate(d.as_of) + ", " + (d.forecast || {}).horizon_months + "-month horizon. Each has an issuer, an edition, a locator and, where the file was captured, a SHA-256 hash.</p>" +
      '<div class="view-tools"><label class="field"><span>Filter sources</span><input type="search" id="source-filter" value="' + esc(state.sourceFilter) + '" placeholder="Issuer, title, locator or hash"></label><span class="panel-meta">' + rows.length + " shown</span></div>" +
      '<table class="reg"><thead><tr><th scope="col" class="c-num">No.</th><th scope="col">Issuer and title</th><th scope="col">Edition</th><th scope="col">Published</th><th scope="col">Locator</th><th scope="col">SHA-256</th><th scope="col" class="c-num">Cited by</th></tr></thead><tbody>' +
      rows.map(function (x) {
        var s = x.s;
        return '<tr><td class="c-num num">' + x.n + "</td><td><b>" + esc(s.issuer) + "</b><br>" + (s.url ? '<a href="' + esc(s.url) + '" target="_blank" rel="noopener noreferrer">' + esc(s.title) + "</a>" : esc(s.title)) + "</td><td>" + esc(s.version || "—") +
          "</td><td>" + (s.public_date ? fmtDate(s.public_date) : "Not dated") + "</td><td>" + esc(s.locator || "—") + "</td><td>" +
          (s.sha256 ? '<span class="hash"><code title="' + esc(s.sha256) + '">' + esc(s.sha256.slice(0, 12)) + '…</code><button type="button" class="copy" data-copy="' + esc(s.sha256) + '" aria-label="Copy SHA-256 of source ' + x.n + '">Copy</button></span>' : "None") +
          '</td><td class="c-num num">' + (counts[s.id] || 0) + "</td></tr>";
      }).join("") + (rows.length ? "" : '<tr><td colspan="7" class="st-empty">No source matches “' + esc(state.sourceFilter) + "”.</td></tr>") + "</tbody></table></div>";
  }
  function savedChecklists() {
    var n = 0;
    try { for (var i = 0; i < localStorage.length; i++) if (/^mwd\.check\./.test(localStorage.key(i))) n++; } catch (e) { n = 0; }
    return n;
  }
  function settingsView() {
    var t = tx(), idx = state.index;
    return '<div class="view settings" lang="en"><h1>Settings</h1><p class="lead">Settings are kept in this browser only.</p>' +
      '<section><h2>Content language</h2><p class="tab-intro" lang="' + state.lang + '">' + esc(t.settingsLang) + '</p><div class="radios" role="radiogroup" aria-label="Content language">' +
      '<label><input type="radio" name="set-lang" value="th"' + (state.lang === "th" ? " checked" : "") + "> Thai</label>" +
      '<label><input type="radio" name="set-lang" value="en"' + (state.lang === "en" ? " checked" : "") + "> English</label></div></section>" +
      '<section><h2>Review capacity</h2><p class="tab-intro" lang="' + state.lang + '">' + esc(t.capacityText) + "</p></section>" +
      '<section><h2>Saved checklist ticks</h2><p class="tab-intro" lang="' + state.lang + '" id="saved-count">' + esc(t.storageText(savedChecklists())) + '</p><button type="button" class="btn btn-secondary" id="clear-checks">Clear saved ticks</button></section>' +
      '<section><h2>Keyboard shortcuts</h2><table class="reg"><thead><tr><th scope="col">Keys</th><th scope="col">Action</th></tr></thead><tbody>' +
      "<tr><td><kbd>↑</kbd> <kbd>↓</kbd>, <kbd>Home</kbd> <kbd>End</kbd></td><td>Move through the review queue (when it has focus)</td></tr>" +
      "<tr><td><kbd>Alt</kbd> + <kbd>↓</kbd> / <kbd>↑</kbd></td><td>Open the next or previous molecule that has a dossier</td></tr>" +
      "<tr><td><kbd>←</kbd> <kbd>→</kbd></td><td>Move between dossier sections (when a section tab has focus)</td></tr>" +
      "<tr><td><kbd>Alt</kbd> + <kbd>1</kbd>–<kbd>7</kbd></td><td>Open a dossier section</td></tr>" +
      "<tr><td><kbd>Ctrl</kbd> + <kbd>P</kbd></td><td>Print the open dossier</td></tr></tbody></table></section>" +
      '<section><h2>Data</h2><dl class="kv"><dt>Mode</dt><dd>' + (state.mode === "current" ? "Current queue, Track A t0 forecast, outcome pending (reference date " + fmtDate(curAsOf()) + ")" : "Historical time machine") + "</dd><dt>Status</dt><dd>" + (idx.fixture ? "FIXTURE (synthetic)" : state.mode === "current" ? "Frozen Track A forecast (" + esc((idx.version || {}).tag || "freeze not verified") + ")" : "Development data, US cutoffs before 2017") + "</dd>" +
      "<dt>Loaded from</dt><dd>" + esc(state.via) + "</dd><dt>Queues</dt><dd>" + idx.queues.length + "</dd><dt>Dossiers</dt><dd>" + (state.mode === "current" ? idx.dossiers.length / 2 + " drugs, both horizons in one file each" : (idx.dossiers || []).length) + "</dd>" +
      "<dt>Contracts</dt><dd>mwd.index.v1, mwd.queue.v1, mwd.dossier.v1</dd></dl></section>" +
      (state.mode === "current" ? '<section><h2>Data rights</h2><table class="reg"><thead><tr><th scope="col">Source</th><th scope="col">Terms</th></tr></thead><tbody>' +
        "<tr><td>U.S. FDA Orange Book and Drugs@FDA</td><td>US government work, public domain</td></tr>" +
        "<tr><td>District court filings, Rai et al. (Harvard Dataverse v1.0)</td><td>CC0 1.0</td></tr>" +
        "<tr><td>LOE-Bench forecasts and evidence coverage</td><td>Project-generated from the sources above, frozen Track A bytes. No NBER data.</td></tr></tbody></table></section>" : "") + "</div>";
  }
  function bindViewAfterRender() {
    if (state.view === "dossiers" && state.mode !== "current") {
      var need = (state.index.dossiers || []).filter(function (e) { return !e._d; });
      if (need.length) {
        Promise.all(need.map(function (e) { return load(e.path).then(function (d) { e._d = d; }, function () { e._d = null; }); }))
          .then(function () { if (state.view === "dossiers") { var a = document.activeElement && document.activeElement.id; renderDossier(); restoreFocus(a); } });
      }
    }
  }
  function restoreFocus(id) {
    if (!id) return;
    var el = $(id);
    if (el) { el.focus(); if (el.setSelectionRange) { var n = el.value.length; el.setSelectionRange(n, n); } }
  }

  /* ---------- layout and nav ---------- */
  function renderLayout() {
    $("app").classList.toggle("wide", state.view !== "queue");
    document.querySelectorAll(".topnav a").forEach(function (a) {
      var on = a.getAttribute("data-nav") === state.view;
      if (on) a.setAttribute("aria-current", "page"); else a.removeAttribute("aria-current");
    });
  }
  function renderAll() {
    renderLayout(); renderFilters(); renderQueue(); renderDossier(); renderSources(); renderModebar(); renderLaunchMsg(); writeHash();
  }

  /* ---------- selection ---------- */
  function selectQueue() {
    var entry = queueEntry();
    if (!entry) { state.queue = null; state.dossier = null; renderAll(); return Promise.resolve(); }
    return load(entry.path).then(function (raw) {
      state.queue = normQueue(raw);
      var rows = state.queue.rows;
      if (!state.key || !rows.some(function (r) { return r.key === state.key; })) {
        var first = rows.find(function (r) { return dossierEntry(r.key); }) || rows[0];
        state.key = first ? first.key : null;
      }
      return selectDossier(state.key, true);
    });
  }
  function selectDossier(key, keepSrc) {
    state.key = key;
    if (!keepSrc) state.src = null;
    var entry = key && dossierEntry(key);
    if (!entry) { state.dossier = null; renderAll(); return Promise.resolve(); }
    return load(entry.path).then(function (raw) {
      var d = deriveDossier(raw);
      state.raw = raw; state.dossier = d;
      if (state.src && !srcIndex(d)[state.src]) state.src = null;
      renderAll();
    }, function (err) { state.dossier = null; state.error = err; renderAll(); });
  }
  function setTab(id, focus) {
    if (SECTION_IDS.indexOf(id) < 0) return;
    state.tab = id;
    document.querySelectorAll(".tab").forEach(function (b) {
      var on = b.getAttribute("data-tab") === id;
      b.setAttribute("aria-selected", String(on)); b.tabIndex = on ? 0 : -1;
      if (on && focus) b.focus();
    });
    document.querySelectorAll(".tabpanel").forEach(function (p) { p.hidden = p.id !== "panel-" + id; });
    renderSources(); writeHash();
  }
  function setLang(l) {
    if (l !== "th" && l !== "en") return;
    var active = document.activeElement && document.activeElement.id;
    state.lang = l; store("mwd.lang", l);
    applyLang(); renderQueue(); renderDossier(); renderSources(); renderLaunchMsg(); writeHash();
    restoreFocus(active);
  }
  function setMode(m) {
    if (m !== "current" && m !== "history") return;
    if (m === state.mode && state.index) return;
    ensureSet(m).then(function () {
      state.mode = m; activate(m);
      state.key = null; state.dossier = null; state.raw = null; state.queue = null; state.revealed = false; state.src = null;
      state.error = null;
      var hs = horizons(); state.horizon = hs.indexOf(24) >= 0 ? 24 : hs[0];
      if (m === "current") applyLaunch(); else state.outside = false;
      var cs = cutoffsFor(state.horizon); state.cutoff = cs[cs.length - 1];
      applyLang(); renderFilters();
      return selectQueue().then(function () { scrollQueueToCurrent(); announce(m === "current" ? "Current queue" : "Historical time machine"); });
    }).catch(function (err) { state.error = err; renderDossier(); });
  }
  function setView(v, focus) {
    if (VIEWS.indexOf(v) < 0) v = "queue";
    state.view = v;
    renderLayout(); renderDossier(); renderSources(); writeHash();
    if (focus) {
      var target = v === "queue" ? $("queue-panel") : $("dossier");
      target.focus({ preventScroll: false });
      if (v !== "queue") $("dossier").scrollTop = 0;
    }
  }
  function stepDossier(dir) {
    var q = state.queue; if (!q) return;
    var withDoc = q.rows.filter(function (r) { return dossierEntry(r.key); });
    var i = withDoc.findIndex(function (r) { return r.key === state.key; });
    var next = withDoc[i < 0 ? 0 : Math.max(0, Math.min(withDoc.length - 1, i + dir))];
    if (next && next.key !== state.key) {
      selectDossier(next.key).then(function () {
        scrollQueueToCurrent();
        announce(niceName(next.display_name));
      });
    }
  }

  function copyText(text, btn) {
    function done() {
      var old = btn.textContent; btn.textContent = "Copied";
      announce(tx().copied);
      setTimeout(function () { btn.textContent = old; }, 1400);
    }
    function fallback() {
      var ta = document.createElement("textarea");
      ta.value = text; ta.setAttribute("readonly", ""); ta.style.position = "fixed"; ta.style.opacity = "0";
      document.body.appendChild(ta); ta.select();
      try { document.execCommand("copy"); done(); } catch (e) { /* ignore */ }
      document.body.removeChild(ta);
    }
    if (navigator.clipboard && window.isSecureContext) navigator.clipboard.writeText(text).then(done, fallback);
    else fallback();
  }

  /* ---------- events ---------- */
  function bind() {
    document.querySelector(".lang").addEventListener("click", function (e) {
      var b = e.target.closest("button[data-lang]"); if (b) setLang(b.getAttribute("data-lang"));
    });
    document.querySelectorAll("[data-nav]").forEach(function (a) {
      a.addEventListener("click", function (e) { e.preventDefault(); setView(a.getAttribute("data-nav"), true); });
    });
    document.querySelector(".mode-switch").addEventListener("click", function (e) {
      var b = e.target.closest("button[data-mode]"); if (b) setMode(b.getAttribute("data-mode"));
    });
    $("f-search").addEventListener("input", function () {
      state.q = this.value; renderQueue(); writeHash();
      announce(state.q.trim() ? tx().search.count($("queue-body").querySelectorAll(".q-btn").length, state.queue ? state.queue.rows.length : 0) : "");
    });
    $("f-search").addEventListener("keydown", function (e) {
      var first = $("queue-body").querySelector(".q-btn");
      if (e.key === "Enter" && first) {
        e.preventDefault();
        selectDossier(first.getAttribute("data-key")).then(function () { if (state.view !== "queue") setView("queue"); scrollQueueToCurrent(); });
      } else if (e.key === "ArrowDown" && first && !e.altKey) { e.preventDefault(); first.tabIndex = 0; first.focus(); }
    });
    $("f-launch").addEventListener("change", function () {
      state.launch = this.value || ""; state.revealed = false;
      applyLaunch(); renderFilters(); selectQueue();
    });
    $("f-horizon").addEventListener("change", function () {
      var h = Number(this.value), list = cutoffsFor(h);
      if (state.mode === "current") { state.launch = ""; state.outside = false; $("f-launch").value = ""; renderLaunchMsg(); }
      state.horizon = h; state.revealed = false;
      if (list.indexOf(state.cutoff) < 0) {
        var target = Number(state.cutoff);
        state.cutoff = list.slice().sort(function (a, b) { return Math.abs(a - target) - Math.abs(b - target); })[0];
      }
      selectQueue();
    });
    $("f-asof").addEventListener("change", function () { state.cutoff = this.value; state.revealed = false; selectQueue(); });
    $("f-show").addEventListener("change", function () { state.show = this.value; renderQueue(); writeHash(); scrollQueueToCurrent(); });

    var qb = $("queue-body");
    qb.addEventListener("click", function (e) {
      var row = e.target.closest("tr.q-row"); if (!row) return;
      var key = row.getAttribute("data-key");
      selectDossier(key).then(function () {
        if (state.view !== "queue") setView("queue");
        var b = qb.querySelector('.q-btn[data-key="' + (window.CSS && CSS.escape ? CSS.escape(key) : key) + '"]'); if (b) b.focus();
      });
    });
    qb.addEventListener("keydown", function (e) {
      var btn = e.target.closest(".q-btn"); if (!btn) return;
      var all = Array.prototype.slice.call(qb.querySelectorAll(".q-btn")), i = all.indexOf(btn), j = null;
      if (e.key === "ArrowDown") j = Math.min(all.length - 1, i + 1);
      else if (e.key === "ArrowUp") j = Math.max(0, i - 1);
      else if (e.key === "Home") j = 0;
      else if (e.key === "End") j = all.length - 1;
      if (j === null || e.altKey) return;
      e.preventDefault();
      var key = all[j].getAttribute("data-key");
      selectDossier(key).then(function () {
        var b = qb.querySelector('.q-btn[data-key="' + (window.CSS && CSS.escape ? CSS.escape(key) : key) + '"]');
        if (b) { b.focus(); scrollQueueToCurrent(); }
      });
    });

    var main = $("dossier");
    main.addEventListener("click", function (e) {
      var tab = e.target.closest(".tab");
      if (tab) { setTab(tab.getAttribute("data-tab")); return; }
      var go = e.target.closest("[data-goto]");
      if (go) { e.preventDefault(); setTab(go.getAttribute("data-goto"), true); return; }
      var cite = e.target.closest(".cite");
      if (cite) { e.preventDefault(); focusSource(cite.getAttribute("data-src"), false); return; }
      var copy = e.target.closest(".copy");
      if (copy) { copyText(copy.getAttribute("data-copy"), copy); return; }
      if (e.target.closest("#reveal-btn")) {
        state.revealed = !state.revealed;
        renderQueue(); renderDossier(); renderSources(); writeHash();
        var rb = $("reveal-btn"); if (rb) rb.focus();
        announce(state.revealed ? "Outcome shown" : "Outcome hidden");
        return;
      }
      if (e.target.closest("#print-btn")) { window.print(); return; }
      var foc = e.target.closest("[data-focus]");
      if (foc) { e.preventDefault(); $("queue-panel").focus(); return; }
      var nav = e.target.closest("[data-nav-link]");
      if (nav) { e.preventDefault(); setView(nav.getAttribute("data-nav-link"), true); return; }
      var open = e.target.closest("[data-open]");
      if (open) {
        e.preventDefault();
        state.horizon = Number(open.getAttribute("data-h")); state.cutoff = open.getAttribute("data-c"); state.key = open.getAttribute("data-open");
        state.revealed = false; state.view = "queue";
        renderFilters(); selectQueue().then(function () { scrollQueueToCurrent(); $("dossier").focus(); });
        return;
      }
      if (e.target.closest("[data-action='show-dossiers']")) {
        state.show = "dossiers"; renderFilters();
        var first = state.queue && state.queue.rows.find(function (r) { return dossierEntry(r.key); });
        if (first) selectDossier(first.key).then(scrollQueueToCurrent); else renderQueue();
        return;
      }
      if (e.target.closest("#clear-checks")) {
        try {
          var keys = [];
          for (var i = 0; i < localStorage.length; i++) if (/^mwd\.check\./.test(localStorage.key(i))) keys.push(localStorage.key(i));
          keys.forEach(function (k) { localStorage.removeItem(k); });
        } catch (err) { /* storage blocked */ }
        $("saved-count").textContent = tx().storageText(0);
        announce(tx().cleared);
      }
    });
    main.addEventListener("keydown", function (e) {
      var tab = e.target.closest && e.target.closest(".tab"); if (!tab) return;
      var i = SECTION_IDS.indexOf(state.tab), n = null;
      if (e.key === "ArrowRight") n = SECTION_IDS[(i + 1) % SECTION_IDS.length];
      else if (e.key === "ArrowLeft") n = SECTION_IDS[(i - 1 + SECTION_IDS.length) % SECTION_IDS.length];
      else if (e.key === "Home") n = SECTION_IDS[0];
      else if (e.key === "End") n = SECTION_IDS[SECTION_IDS.length - 1];
      if (n) { e.preventDefault(); setTab(n, true); }
    });
    main.addEventListener("change", function (e) {
      var el = e.target;
      if (el.name === "set-lang") { setLang(el.value); return; }
      if (el.type !== "checkbox") return;
      var table = el.closest(".checklist"), key = table.getAttribute("data-store"), saved = {};
      table.querySelectorAll("input[type=checkbox]").forEach(function (x) { if (x.checked) saved[x.getAttribute("data-id")] = true; });
      store(key, Object.keys(saved).length ? JSON.stringify(saved) : null);
      el.closest("tr").classList.toggle("done", el.checked);
      var total = table.querySelectorAll("input[type=checkbox]").length, done = Object.keys(saved).length;
      $("check-progress").textContent = tx().progress(done, total);
      $("check-done").textContent = done;
    });
    main.addEventListener("input", function (e) {
      if (e.target.id === "source-filter") { state.sourceFilter = e.target.value; renderDossier(); restoreFocus("source-filter"); }
      if (e.target.id === "dossier-filter") { state.dossierFilter = e.target.value; renderDossier(); restoreFocus("dossier-filter"); }
    });

    $("sources-panel").addEventListener("click", function (e) {
      var copy = e.target.closest(".copy"); if (copy) copyText(copy.getAttribute("data-copy"), copy);
    });

    document.addEventListener("keydown", function (e) {
      if (!e.altKey || e.ctrlKey || e.metaKey) return;
      if (e.key === "ArrowDown" || e.key === "ArrowUp") { e.preventDefault(); if (state.view !== "queue") setView("queue"); stepDossier(e.key === "ArrowDown" ? 1 : -1); return; }
      var n = Number(e.key);
      if (n >= 1 && n <= 7 && state.dossier && state.view === "queue") { e.preventDefault(); setTab(SECTION_IDS[n - 1], true); }
    });
    window.addEventListener("hashchange", function () {
      if (writingHash) return;
      var h = readHash();
      if (h.lang && h.lang !== state.lang) setLang(h.lang);
      if (h.view && h.view !== state.view) setView(h.view);
    });
  }

  /* ---------- boot ---------- */
  function boot() {
    var h = readHash();
    var saved = store("mwd.lang");
    state.lang = h.lang === "en" || h.lang === "th" ? h.lang : (saved === "en" ? "en" : "th");
    state.view = VIEWS.indexOf(h.view) >= 0 ? h.view : "queue";
    state.show = h.show === "all" ? "all" : "dossiers";
    /* Links made before the current queue existed carry a four-digit cutoff year and no mode: they open the time machine. */
    var mode = h.mode === "history" || h.mode === "current" ? h.mode : (/^\d{4}$/.test(h.c || "") ? "history" : "current");
    state.mode = mode; document.body.setAttribute("data-mode", mode);
    applyLang(); bind(); renderLayout();
    ensureSet(mode).then(function () {
      activate(mode);
      applyLang();
      if (mode === "current") {
        state.q = h.q || "";
        state.launch = /^\d{4}-\d{2}-\d{2}$/.test(h.ld || "") ? h.ld : "";
      }
      var hs = horizons();
      if (!hs.length) throw new Error("The index lists no queues");
      state.horizon = hs.indexOf(Number(h.h)) >= 0 ? Number(h.h) : (hs.indexOf(24) >= 0 ? 24 : hs[0]);
      if (mode === "current") applyLaunch();
      var cs = cutoffsFor(state.horizon);
      state.cutoff = cs.indexOf(h.c) >= 0 ? h.c : cs[cs.length - 1];
      if (h.m) state.key = h.m;
      if (SECTION_IDS.indexOf(h.tab) >= 0) state.tab = h.tab;
      state.revealed = mode === "history" && h.reveal === "1";
      state.src = h.src || null;
      renderFilters();
      return selectQueue().then(function () {
        scrollQueueToCurrent();
        if (state.src) focusSource(state.src, false);
      });
    }).catch(function (err) {
      state.error = err;
      $("queue-body").innerHTML = '<tr class="q-empty"><td colspan="3" lang="en">No queue loaded.</td></tr>';
      renderDossier();
      $("sources-list").innerHTML = "";
    });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot); else boot();
})();
