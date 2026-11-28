/* Market Window Dossier: report layout for the print view and the PDF export (card PO-PDF, PRD R2).
 *
 * One implementation serves both paths, so the browser print and the generated PDF match:
 *   - the app calls MWDPrint.build() on "beforeprint" and mounts the result (product/demo/app.js);
 *   - product/mwd/render.py loads this file in headless Chrome and calls MWDPrint.document().
 * No DOM access and no network: the input is one dossier JSON (mwd.dossier.v1) and the output is a string.
 * Design: DESIGN.md F2 "Regulatory agency". English headings and labels; the body follows the TH or EN choice.
 * Fonts (Source Sans 3, Noto Sans Thai) come from assets/fonts/fonts.css, self-hosted under the SIL OFL.
 */
(function (root, factory) {
  var api = factory();
  if (typeof module === "object" && module.exports) module.exports = api; else root.MWDPrint = api;
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  var DISCLAIMER = {
    th: "เอกสารนี้ใช้จัดลำดับงานตรวจจากข้อมูลที่ระบุ ณ วันที่แสดง แบบจำลองประเมินโอกาสการอนุมัติยาสามัญครั้งแรกในสหรัฐฯ สถานะสิทธิในไทยและการประเมินเสรีภาพในการดำเนินการด้านสิทธิบัตร (FTO) ต้องให้ผู้เชี่ยวชาญตรวจข้อถือสิทธิ ผลิตภัณฑ์ ประเทศ และสถานะกฎหมายปัจจุบัน เอกสารนี้ไม่ใช่ความเห็นทางกฎหมายหรือความเห็น FTO",
    en: "This dossier prioritizes review using the evidence available as of the displayed date. The model estimates the chance of first US generic approval. Qualified experts must verify Thai rights and assess freedom to operate (FTO) against the claims, product, jurisdiction and current legal status. This dossier is neither a legal opinion nor an FTO opinion."
  };
  var SECTIONS = [
    { id: "decision", label: "Decision summary" },
    { id: "market", label: "Market window" },
    { id: "competition", label: "Competition" },
    { id: "patents", label: "Patents" },
    { id: "thai_asean", label: "Thailand and ASEAN" },
    { id: "handoff", label: "FTO hand-off" },
    { id: "references", label: "References" }
  ];
  var MONTHS_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  var MONTHS_TH = ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."];
  /* Long lists move to the appendix. A section keeps this many rows in the body. */
  var CAP_STATEMENTS = 8, CAP_TASKS = 6, REF_INLINE = 12;

  /* Body text only. Headings, labels and column heads stay English (DESIGN.md). Wording matches the app. */
  var T = {
    th: {
      endpoint: "เหตุการณ์ที่พยากรณ์คือการอนุมัติขั้นสุดท้ายของยาสามัญรายแรกในสหรัฐฯ ไม่ใช่การวางจำหน่าย ความต้องการใช้ยา หรือการอนุญาตในประเทศไทย",
      method: "ผลการทดสอบที่ลงทะเบียนไว้ (ช่วงพยากรณ์ 24 เดือน ตรวจ 1 ใน 5 ของยา): M3 พบการอนุมัติยาสามัญรายแรกจริง 66.85% โดยมีค่าความแม่นยำเชิงบวก (precision) 26.62% ผลของคิวนี้ยังไม่ทราบจนกว่าจะรันตัวให้คะแนนในเดือนพฤศจิกายน 2027 และ 2028",
      devUncertainty: "ข้อมูลช่วงพัฒนา (วันตัดข้อมูลก่อนปี 2017) ผลจริงของกรณีนี้ยังไม่แสดงจนกว่าจะเปิดดูผล",
      devRevealed: "ข้อมูลช่วงพัฒนา (วันตัดข้อมูลก่อนปี 2017) เอกสารนี้ส่งออกหลังเปิดดูผลจริงแล้ว และแสดงผลไว้ในหัวข้อ Outcome",
      outsideBody: function (d, e) { return "วันเปิดตัวที่วางแผนไว้ " + d + " ช้ากว่าวันสุดท้ายของช่วงพยากรณ์ (" + e + ") จึงไม่แสดงค่าพยากรณ์ ลำดับ หรือตำแหน่งในคิว"; },
      status: { known: "ทราบ", verify: "ต้องตรวจ", assumption: "สมมติฐาน", na: "ไม่เกี่ยวข้อง" },
      estimate: "ค่าประมาณ",
      owner: { "FTO evaluator": "ผู้ประเมิน FTO", "Patent reviewer": "ผู้ตรวจสิทธิบัตร", "R&D": "ฝ่ายวิจัยและพัฒนา", "BD": "ฝ่ายพัฒนาธุรกิจ",
        "Thai patent reviewer": "ผู้ตรวจสิทธิบัตรไทย", "Thai regulatory reviewer": "ผู้ตรวจทะเบียนยาไทย" },
      nextFallback: "ตรวจรายการในหัวข้อ FTO hand-off",
      emptyClaims: "ไม่มีข้อความในหัวข้อนี้",
      unknown: "ยังไม่ทราบ", openState: "รอดำเนินการ", done: "ตรวจแล้ว",
      terms: "คำค้น", wo: "เลข WO", priority: "เลขคำขอที่ใช้อ้างสิทธิครั้งแรก",
      inclusion: function (p) { return "โอกาสเข้าคิว " + p; },
      noEvent: function (d) { return "ไม่มียาสามัญรายแรกได้รับอนุมัติภายในช่วงพยากรณ์ (สิ้นสุด " + d + ")"; },
      firstApproval: function (d, h) { return "ยาสามัญรายแรกได้รับอนุมัติขั้นสุดท้ายเมื่อ " + d + " ภายในช่วงพยากรณ์ " + h + " เดือน"; },
      result: { caught: "อยู่ในคิวตรวจ และเกิดเหตุการณ์จริง", missed: "อยู่นอกคิวตรวจ แต่เกิดเหตุการณ์จริง ระบบพลาดกรณีนี้",
        falseAlarm: "อยู่ในคิวตรวจ แต่ไม่เกิดเหตุการณ์ภายในช่วงพยากรณ์", quiet: "อยู่นอกคิวตรวจ และไม่เกิดเหตุการณ์" },
      outcomeNote: "ผลลัพธ์นี้เป็นข้อมูลช่วงพัฒนา ใช้ทบทวนย้อนหลังเท่านั้น ระบบไม่เห็นผลนี้ตอนจัดอันดับ",
      moreIn: function (n, ref) { return "มีอีก " + n + " รายการใน " + ref; },
      refsIn: function (n, ref) { return "แหล่งข้อมูลทั้ง " + n + " รายการอยู่ใน " + ref; }
    },
    en: {
      endpoint: "The forecast event is the first final US generic approval. It is not launch, demand or Thai permission.",
      method: "Registered test (24-month horizon, 1-in-5 review capacity): M3 found 66.85% of first generic approvals, with precision 26.62%. Outcomes for this queue stay pending until the scorer runs in November 2027 and November 2028.",
      devUncertainty: "Development data (cutoff before 2017). The real outcome of this case is not shown until it is revealed.",
      devRevealed: "Development data (cutoff before 2017). This export was made after the reveal and shows the real outcome under Outcome.",
      outsideBody: function (d, e) { return "The planned launch date " + d + " is later than the last forecast date (" + e + "). No forecast, rank or queue position is shown."; },
      status: { known: "known", verify: "verify", assumption: "assumption", na: "not applicable" },
      estimate: "estimate",
      owner: {},
      nextFallback: "Work through the FTO hand-off items.",
      emptyClaims: "No statements in this section.",
      unknown: "unknown", openState: "Open", done: "Checked",
      terms: "Search terms", wo: "WO numbers", priority: "Priority numbers",
      inclusion: function (p) { return "Inclusion probability " + p; },
      noEvent: function (d) { return "No first generic approval within the horizon (ended " + d + ")."; },
      firstApproval: function (d, h) { return "First generic final approval on " + d + ", within the " + h + "-month horizon."; },
      result: { caught: "In the review queue, and the event happened.", missed: "Outside the review queue, but the event happened. The system missed this case.",
        falseAlarm: "In the review queue, but no event within the horizon.", quiet: "Outside the review queue, and no event." },
      outcomeNote: "Development outcome, for retrospective review only. The ranking did not see it.",
      moreIn: function (n, ref) { return n + " more in " + ref; },
      refsIn: function (n, ref) { return "All " + n + " sources are listed in " + ref; }
    }
  };

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function pct(p, digits) { return p == null ? "—" : (p * 100).toFixed(digits == null ? 1 : digits) + "%"; }
  function pad(n) { return (n < 10 ? "0" : "") + n; }
  function fmtDate(iso, lang) {
    if (!iso) return "—";
    var m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso);
    if (!m) return iso;
    var d = Number(m[3]), mo = Number(m[2]) - 1, y = Number(m[1]);
    return lang === "th" ? d + " " + MONTHS_TH[mo] + " " + (y + 543) : d + " " + MONTHS_EN[mo] + " " + y;
  }
  function addMonths(iso, n) {
    var m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso || "");
    if (!m) return null;
    var mo = Number(m[2]) - 1 + n, y = Number(m[1]) + Math.floor(mo / 12);
    mo = ((mo % 12) + 12) % 12;
    var last = new Date(Date.UTC(y, mo + 1, 0)).getUTCDate();
    return y + "-" + pad(mo + 1) + "-" + pad(Math.min(Number(m[3]), last));
  }
  function niceName(n) {
    if (!n) return "—";
    if (n !== n.toUpperCase()) return n;
    var s = n.toLowerCase(), i = s.search(/[a-z]/);
    return i < 0 ? s : s.slice(0, i) + s.charAt(i).toUpperCase() + s.slice(i + 1);
  }
  function niceForm(f) {
    return String(f).toLowerCase().replace(/\b(iv|im|sc|er|xr|dr|odt)\b/g, function (w) { return w.toUpperCase(); })
      .replace(/^./, function (c) { return c.toUpperCase(); });
  }
  function webUrl(u) { return typeof u === "string" && /^https?:\/\/[^\s]+$/i.test(u); }
  function host(u) { var m = /^https?:\/\/([^\/?#]+)/i.exec(u); return m ? m[1] : u; }
  /* A CSS string for @page content. Angle brackets become escapes so a drug name can never close the <style> element. */
  function cssString(s) {
    return '"' + String(s).replace(/\\/g, "\\\\").replace(/"/g, '\\"').replace(/[\r\n]+/g, " ").replace(/</g, "\\3c ").replace(/>/g, "\\3e ") + '"';
  }

  function statusOf(c) {
    if (c.state === "unknown") return "verify";
    if (c.state === "not_applicable") return "na";
    if (c.kind === "assumption") return "assumption";
    return "known";
  }

  /* The current dossier holds both horizons. Choose the requested horizon the way the app does, and drop the
     other horizon's queue-* and entry-* statements. The step is idempotent, so the app can pass its derived copy. */
  function derive(d, o) {
    var h = o.horizon ? Number(o.horizon) : null, outside = !!(o.outside || d.outside), forecast = d.forecast;
    if (h === 12 && d.forecast_12m) forecast = d.forecast_12m;
    if (outside) forecast = null;
    else if (!forecast || (h && forecast.horizon_months !== h)) {
      throw new Error("Dossier cannot be rendered for the " + h + "-month horizon");
    }
    var claims = (d.claims || []).filter(function (c) {
      var m = /^(queue|entry)-(12|24)$/.exec(c.id);
      return !m || (!outside && forecast && Number(m[2]) === forecast.horizon_months);
    });
    return { forecast: forecast, claims: claims, outside: outside, horizon: forecast ? forecast.horizon_months : null };
  }

  function isCurrent(d) {
    var status = ((d.forecast || d.forecast_12m || {}).status) || "";
    return !!(d.version || d.label || /^TRACK_A/.test(status));
  }

  function sourceIndex(sources) {
    var m = {};
    (sources || []).forEach(function (s, i) { m[s.id] = i + 1; });
    return m;
  }
  /* Citation numbers, with runs such as [5-40] collapsed so a task that cites hundreds of rows stays one line. */
  function cites(ids, idx) {
    var seen = {}, nums = [];
    (ids || []).forEach(function (id) { var n = idx[id]; if (n && !seen[n]) { seen[n] = 1; nums.push(n); } });
    nums.sort(function (a, b) { return a - b; });
    if (!nums.length) return '<span class="pd-none">None</span>';
    var tokens = [], i = 0;
    while (i < nums.length) {
      var e = i;
      while (e + 1 < nums.length && nums[e + 1] === nums[e] + 1) e++;
      if (e - i >= 2) tokens.push({ a: nums[i], b: nums[e], n: e - i + 1 });
      else for (var q = i; q <= e; q++) tokens.push({ a: nums[q], b: nums[q], n: 1 });
      i = e + 1;
    }
    var limit = 6, shown = tokens.slice(0, limit), rest = 0;
    tokens.slice(limit).forEach(function (t) { rest += t.n; });
    var html = shown.map(function (t) {
      return '<a href="#pd-ref-' + t.a + '">[' + (t.a === t.b ? t.a : t.a + "–" + t.b) + "]</a>";
    }).join(" ");
    return '<span class="pd-cites">' + html + (rest ? ' <span class="pd-more">+' + rest + " more</span>" : "") + "</span>";
  }

  function statementsTable(claims, ctx, withSection) {
    var t = ctx.t;
    if (!claims.length) return '<p class="pd-empty">' + esc(t.emptyClaims) + "</p>";
    return '<table class="pd-st"><thead><tr>' + (withSection ? '<th class="pd-c-sec" scope="col">Section</th>' : "") +
      '<th scope="col">Statement</th><th class="pd-c-status" scope="col">Status</th><th class="pd-c-src" scope="col">Source</th></tr></thead><tbody>' +
      claims.map(function (c) {
        var s = statusOf(c);
        return "<tr>" + (withSection ? '<td class="pd-c-sec">' + esc(ctx.sectionLabel[c.section] || c.section) + "</td>" : "") +
          "<td>" + esc(c["text_" + ctx.lang] || c.text_en || c.text_th || "") +
          (c.kind === "estimate" ? '<span class="pd-kind">' + esc(t.estimate) + "</span>" : "") + "</td>" +
          '<td><span class="pd-tag pd-tag-' + s + '">' + esc(t.status[s]) + "</span></td><td>" + cites(c.source_ids, ctx.idx) + "</td></tr>";
      }).join("") + "</tbody></table>";
  }

  function statCells(cells) {
    return '<div class="pd-stats">' + cells.map(function (c) {
      return '<div class="pd-stat"><div class="pd-k">' + c[0] + '</div><div class="pd-v' + (c[3] ? " " + c[3] : "") + '">' + c[1] + "</div>" +
        (c[2] ? '<div class="pd-s">' + c[2] + "</div>" : "") + "</div>";
    }).join("") + "</div>";
  }

  function taskRow(c, ctx) {
    var t = ctx.t, lang = ctx.lang, meta = "";
    var text = esc(c["text_" + lang] || c.text_en || c.text_th || "");
    if (webUrl(c.lookup_url)) text = '<a href="' + esc(c.lookup_url) + '">' + text + "</a>";
    if (c.search_terms) {
      var unknown = t.unknown;
      meta = '<span class="pd-lookup">' + esc(t.terms) + " " + esc((c.search_terms || []).join(", ") || unknown) +
        " · " + esc(t.wo) + " " + esc((c.wo_numbers || []).join(", ") || unknown) +
        " · " + esc(t.priority) + " " + esc((c.priority_numbers || []).join(", ") || unknown) + "</span>";
    }
    var isDone = !!ctx.checked[c.id];
    var status = isDone ? t.done : (c.state === "unknown" ? t.unknown : t.openState);
    return '<tr><td class="pd-c-box"><span class="pd-box' + (isDone ? " is-on" : "") + '"></span></td><td>' + text + meta + "</td><td>" +
      esc(c.agency || "—") + "</td><td>" + esc(t.owner[c.owner] || c.owner || "—") + '</td><td><span class="pd-tag pd-tag-' +
      (isDone ? "known" : c.state === "unknown" ? "verify" : "neutral") + '">' + esc(status) + "</span></td><td>" + cites(c.source_ids, ctx.idx) + "</td></tr>";
  }
  function tasksTable(items, ctx) {
    return '<table class="pd-st pd-tasks"><thead><tr><th class="pd-c-box" scope="col"><span class="pd-sr">Done</span></th><th scope="col">Task</th>' +
      '<th class="pd-c-agency" scope="col">Agency</th><th class="pd-c-owner" scope="col">Owner</th><th class="pd-c-status" scope="col">Status</th>' +
      '<th class="pd-c-src" scope="col">Source</th></tr></thead><tbody>' + items.map(function (c) { return taskRow(c, ctx); }).join("") + "</tbody></table>";
  }

  function sourcesTable(sources) {
    return '<table class="pd-st pd-refs"><thead><tr><th class="pd-c-no" scope="col">No.</th><th scope="col">Source</th>' +
      '<th class="pd-c-pub" scope="col">Published</th><th class="pd-c-sha" scope="col">SHA-256</th></tr></thead><tbody>' +
      sources.map(function (s, i) {
        var link = webUrl(s.url) ? ' · <a href="' + esc(s.url) + '">' + esc(host(s.url)) + "</a>" : "";
        var date = s.public_date ? fmtDate(s.public_date, "en") : s.evidence_cutoff ? "Cutoff " + fmtDate(s.evidence_cutoff, "en") : "Not dated";
        return '<tr id="pd-ref-' + (i + 1) + '"><td class="pd-num">' + (i + 1) + "</td><td><b>" + esc(s.issuer) + "</b>, " + esc(s.title) +
          '<span class="pd-kind">Edition ' + esc(s.version || "—") + " · " + esc(s.locator || "—") + link + "</span></td>" +
          '<td class="pd-num">' + esc(date) + '</td><td><code>' + esc(s.sha256 || "—") + "</code></td></tr>";
      }).join("") + "</tbody></table>";
  }

  function versionText(d, current) {
    var v = d.version;
    if (!current) return "Development build, no freeze tag";
    if (v && v.freeze === "verified") return "Freeze tag " + v.tag + " (verified) · manifest SHA-256 " + (v.manifest_sha256 || "").slice(0, 16) + "…";
    return "Freeze pending · core manifest SHA-256 " + ((v && v.core_manifest_sha256) || "").slice(0, 16) + "…";
  }

  /* Returns { html, css, title, summary }. html is the body of the report; css the scoped styles plus @page. */
  function build(dossier, o) {
    o = o || {};
    var lang = o.lang === "en" ? "en" : "th", t = T[lang];
    var current = isCurrent(dossier);
    if (current && (dossier.outcome_reveal || o.revealed)) throw new Error("A current export never contains outcome fields");
    var dv = derive(dossier, o), f = dv.forecast, h = dv.horizon, claims = dv.claims;
    var revealed = !!(o.revealed && dossier.outcome_reveal);
    /* Before the reveal, the outcome's own source (its locator carries the outcome date) is left out of the source list. */
    var hidden = {};
    if (!revealed && dossier.outcome_reveal) (dossier.outcome_reveal.source_ids || []).forEach(function (id) { hidden[id] = 1; });
    var sources = (dossier.sources || []).filter(function (s) { return !hidden[s.id]; }), idx = sourceIndex(sources);
    var checklist = dossier.checklist || [];
    var checked = {};
    (o.checked || []).forEach(function (id) { checked[id] = 1; });
    var ctx = { lang: lang, t: t, idx: idx, checked: checked, sectionLabel: {} };
    SECTIONS.forEach(function (s) { ctx.sectionLabel[s.id] = s.label; });

    var name = niceName(dossier.molecule.display_name);
    var asOf = dossier.as_of, windowEnd = h ? addMonths(asOf, h) : null;
    var modeLabel = current ? (dossier.label || "Track A t0 forecast, outcome pending") : "Development data";
    var disclaimer = (dossier.disclaimer && dossier.disclaimer[lang]) || DISCLAIMER[lang];
    var n = o.queueTotal || null;
    var open = claims.filter(function (c) { return c.state === "unknown"; }).length;
    var assume = claims.find(function (c) { return c.section === "decision" && c.kind === "assumption"; }) ||
      claims.find(function (c) { return c.kind === "assumption"; });
    var next = checklist[0];
    var openTasks = checklist.filter(function (c) { return !checked[c.id]; }).length;
    var incl = f && f.queue_inclusion_probability, fractional = incl != null && incl > 0 && incl < 1;
    var horizonText = dv.outside ? "Outside the forecast horizon" : h + " months";

    /* Which long lists leave the body. Appendix letters follow the order below. */
    var bySection = {};
    SECTIONS.forEach(function (s) { bySection[s.id] = claims.filter(function (c) { return c.section === s.id; }); });
    var overflow = {};
    ["decision", "market", "competition", "patents", "thai_asean", "handoff"].forEach(function (id) {
      if (bySection[id].length > CAP_STATEMENTS) overflow[id] = bySection[id].slice(CAP_STATEMENTS);
    });
    var lookups = checklist.filter(function (c) { return c.agency || c.search_terms; });
    var otherTasks = checklist.filter(function (c) { return !(c.agency || c.search_terms); });
    var tasksOver = otherTasks.length > CAP_TASKS ? otherTasks.slice(CAP_TASKS) : [];
    var refsAppendix = sources.length > REF_INLINE;
    var letters = "ABCD", used = 0, appx = {};
    if (Object.keys(overflow).length) appx.statements = "Appendix " + letters[used++];
    if (tasksOver.length) appx.tasks = "Appendix " + letters[used++];
    if (refsAppendix) appx.sources = "Appendix " + letters[used++];
    var overflowTotal = 0;
    Object.keys(overflow).forEach(function (k) { overflowTotal += overflow[k].length; });

    function sectionHead(i, s) {
      return '<h2 class="pd-h2" id="pd-s-' + s.id + '"><span class="pd-no">' + (i + 1) + "</span>" + esc(s.label) + "</h2>";
    }
    function more(id) {
      return overflow[id] ? '<p class="pd-note pd-moreline" lang="' + lang + '">' + esc(t.moreIn(overflow[id].length, appx.statements)) + "</p>" : "";
    }
    function body(id) {
      var list = bySection[id].slice(0, CAP_STATEMENTS);
      return statementsTable(list, ctx) + more(id);
    }

    /* ---- header block and page one ---- */
    var chips = "";
    if (!dv.outside) chips += f.in_queue ? '<span class="pd-chip pd-chip-navy">In review queue</span>' : '<span class="pd-chip">Outside review queue</span>';
    chips += '<span class="pd-chip">' + esc(modeLabel) + "</span>";
    if (current === false && revealed) chips += '<span class="pd-chip pd-chip-red">Revealed export</span>';
    if (o.fixture || dossier.fixture) chips += '<span class="pd-chip">FIXTURE</span>';
    var forms = (dossier.molecule.dosage_forms || []).map(niceForm).join("; ");
    var meta = '<p class="pd-meta"><span>As of <b>' + esc(fmtDate(asOf, "en")) + "</b></span><span>Horizon <b>" + esc(horizonText) +
      (windowEnd ? " (to " + esc(fmtDate(windowEnd, "en")) + ")" : "") + "</b></span><span>Jurisdiction <b>" + esc(dossier.jurisdiction || "—") + "</b></span>" +
      (forms ? "<span>Dosage forms <b>" + esc(forms) + "</b></span>" : "") + "</p>";

    var stats = dv.outside ? statCells([
      ["First generic approval forecast (M3)", "—", "Outside the forecast horizon"],
      ["Drug-age baseline (B1)", "—", "Outside the forecast horizon"],
      ["Queue position", "—", "Outside the forecast horizon"],
      ["To verify", String(open), "Statements across all sections", open ? "pd-verify" : ""]
    ]) : statCells([
      ["First generic within " + h + " months (M3)", pct(f.m3_p_entry), "Evidence model"],
      ["Drug-age baseline (B1)", pct(f.b1_p_entry), "Same horizon"],
      ["Queue position", f.m3_rank + (n ? " <small>of " + n + "</small>" : ""),
        (f.in_queue ? "Inside" : "Outside") + " review capacity (" + (f.queue_size || "—") + ")" + (fractional ? ", inclusion probability " + pct(incl, 0) : "")],
      ["To verify", String(open), "Statements across all sections", open ? "pd-verify" : ""]
    ]);

    var capacityText = dv.outside ? "—" : (f.in_queue ? "Inside" : "Outside") + " the review queue of " + (f.queue_size || "—") + (n ? " in " + n + " drugs" : "") +
      (fractional ? " · inclusion probability " + pct(incl, 0) : "");
    var uncertainty = current ? t.method : (revealed ? t.devRevealed : t.devUncertainty);
    var kv = '<dl class="pd-kv">' +
      "<dt>Mode</dt><dd>" + esc(modeLabel) + "</dd>" +
      "<dt>Review capacity</dt><dd>" + esc(capacityText) + "</dd>" +
      "<dt>Version</dt><dd>" + esc(versionText(dossier, current)) + "</dd>" +
      "<dt>Next action</dt><dd>" + esc(next ? (next["text_" + lang] || next.text_en || next.text_th) : t.nextFallback) +
      (next ? ' <span class="pd-kind">Owner: ' + esc(t.owner[next.owner] || next.owner) + "</span>" : "") + "</dd>" +
      "<dt>Key assumption</dt><dd>" + esc(assume ? (assume["text_" + lang] || assume.text_en) : "—") + "</dd>" +
      "<dt>Open tasks</dt><dd>" + openTasks + " of " + checklist.length + " in the FTO hand-off checklist</dd></dl>";
    var outsideBox = "";
    if (dv.outside) {
      var le = o.windowEnd || addMonths(asOf, 24);
      outsideBox = '<div class="pd-callout pd-callout-amber"><b>Outside the forecast horizon</b><p lang="' + lang + '">' +
        esc(t.outsideBody(fmtDate(o.launch, lang), fmtDate(le, lang))) + "</p></div>";
    }
    var callouts = outsideBox +
      '<div class="pd-callout"><b>Forecast event</b><p lang="' + lang + '">' + esc(t.endpoint) + "</p></div>" +
      '<div class="pd-callout"><b>Uncertainty</b><p lang="' + lang + '">' + esc(uncertainty) + "</p></div>" +
      '<div class="pd-callout pd-callout-amber pd-disclaimer"><b>Disclaimer</b><p lang="' + lang + '">' + esc(disclaimer) + "</p></div>";

    var out = [];
    var revealTag = current ? modeLabel : (revealed ? "REVEALED: development outcome shown" : "Development data: outcome hidden");
    out.push('<header class="pd-brand"><span class="pd-wordmark">Market Window Dossier</span><span class="pd-mode">' + esc(revealTag) + "</span></header>");
    out.push('<div class="pd-cover"><h1 class="pd-h1">' + esc(name) + "</h1>" + meta + '<p class="pd-chips">' + chips + "</p>" +
      sectionHead(0, SECTIONS[0]) + stats + kv + callouts + "</div>");

    /* ---- section 1 continues after page one ---- */
    var openBy = '<h3 class="pd-h3">Open items by section</h3><table class="pd-st pd-open"><thead><tr><th scope="col">Section</th><th class="pd-c-num" scope="col">Statements</th>' +
      '<th class="pd-c-num" scope="col">To verify</th></tr></thead><tbody>' + SECTIONS.map(function (s) {
        var cs = bySection[s.id], u = cs.filter(function (c) { return c.state === "unknown"; }).length;
        return "<tr><td>" + esc(s.label) + '</td><td class="pd-c-num pd-num">' + cs.length + '</td><td class="pd-c-num pd-num">' + u + "</td></tr>";
      }).join("") + "</tbody></table>";
    out.push('<section class="pd-sec pd-sec-first">' + openBy + '<h3 class="pd-h3">Statements</h3>' + body("decision") + "</section>");

    if (revealed) {
      var r = dossier.outcome_reveal, kind = f.in_queue ? (r.first_final_anda_date ? "caught" : "falseAlarm") : (r.first_final_anda_date ? "missed" : "quiet");
      var what = r.first_final_anda_date ? t.firstApproval(fmtDate(r.first_final_anda_date, lang), h) : t.noEvent(fmtDate(r.window_end, lang));
      out.push('<section class="pd-sec pd-outcome" id="pd-outcome"><h2 class="pd-h2 pd-h2-red">Outcome <span class="pd-revealed">Revealed · development data</span></h2>' +
        '<dl class="pd-kv"><dt>What happened</dt><dd>' + esc(what) + " " + cites(r.source_ids, idx) + "</dd><dt>Queue result</dt><dd>" + esc(t.result[kind]) +
        "</dd><dt>Note</dt><dd>" + esc(t.outcomeNote) + "</dd></dl></section>");
    }

    /* ---- sections 2 to 7 ---- */
    for (var i = 1; i < SECTIONS.length; i++) {
      var s = SECTIONS[i], inner = "";
      if (s.id === "handoff") {
        inner = (bySection.handoff.length ? statementsTable(bySection.handoff.slice(0, CAP_STATEMENTS), ctx) + more("handoff") : "") +
          '<h3 class="pd-h3">Evaluator checklist <span class="pd-progress">' + openTasks + " open of " + checklist.length + "</span></h3>" +
          (checklist.length ? tasksTable(lookups.concat(otherTasks.slice(0, CAP_TASKS)), ctx) : '<p class="pd-empty">' + esc(t.emptyClaims) + "</p>") +
          (tasksOver.length ? '<p class="pd-note pd-moreline" lang="' + lang + '">' + esc(t.moreIn(tasksOver.length, appx.tasks)) + "</p>" : "");
      } else if (s.id === "references") {
        var srcCount = sources.length, hashed = sources.filter(function (x) { return /^[a-f0-9]{64}$/.test(x.sha256 || ""); }).length;
        var dated = sources.filter(function (x) { return x.public_date; }).length;
        inner = statCells([["Sources", String(srcCount)], ["With SHA-256", String(hashed)], ["With a public date", String(dated)],
          ["Contract", esc(dossier.schema_version || "mwd.dossier.v1").replace("mwd.", "")]]) + (bySection.references.length ? statementsTable(bySection.references, ctx) : "") +
          (refsAppendix ? '<p class="pd-note pd-moreline" lang="' + lang + '">' + esc(t.refsIn(srcCount, appx.sources)) + "</p>" : '<h3 class="pd-h3">All sources</h3>' + sourcesTable(sources));
      } else {
        inner = body(s.id);
      }
      out.push('<section class="pd-sec">' + sectionHead(i, s) + inner + "</section>");
    }

    /* ---- appendix ---- */
    if (appx.statements) {
      var rows = [];
      SECTIONS.forEach(function (x) { (overflow[x.id] || []).forEach(function (c) { rows.push(c); }); });
      out.push('<section class="pd-sec pd-appx"><h2 class="pd-h2"><span class="pd-no">' + appx.statements.replace("Appendix ", "") + "</span>Statements continued</h2>" +
        '<p class="pd-note">' + overflowTotal + " statements that did not fit the section tables. Source numbers refer to the source table.</p>" + statementsTable(rows, ctx, true) + "</section>");
    }
    if (appx.tasks) {
      out.push('<section class="pd-sec pd-appx"><h2 class="pd-h2"><span class="pd-no">' + appx.tasks.replace("Appendix ", "") + "</span>Further checklist items</h2>" +
        tasksTable(tasksOver, ctx) + "</section>");
    }
    if (appx.sources) {
      out.push('<section class="pd-sec pd-appx"><h2 class="pd-h2"><span class="pd-no">' + appx.sources.replace("Appendix ", "") + "</span>Sources</h2>" + sourcesTable(sources) + "</section>");
    }
    var v = dossier.version;
    if (current && v) {
      out.push('<section class="pd-sec pd-appx-end"><h3 class="pd-h3">Version and integrity</h3><dl class="pd-kv"><dt>Freeze</dt><dd>' + esc(v.freeze || "—") +
        (v.tag ? " · tag " + esc(v.tag) : "") + "</dd>" + (v.manifest_sha256 ? "<dt>Manifest SHA-256</dt><dd><code>" + esc(v.manifest_sha256) + "</code></dd>" : "") +
        (v.core_manifest_sha256 ? "<dt>Core manifest SHA-256</dt><dd><code>" + esc(v.core_manifest_sha256) + "</code></dd>" : "") + "</dl></section>");
    }

    var footer = name + " · " + (dossier.jurisdiction || "US") + " · as of " + fmtDate(asOf, "en") + " · " + horizonText +
      (current && v && v.tag ? " · " + v.tag : "");
    var pageCss = "@page { size: A4; margin: 18mm 14mm 17mm; " +
      "@top-left { content: " + cssString("Market Window Dossier") + "; font: 600 7.5pt 'Source Sans 3', sans-serif; color: #0b2545; vertical-align: bottom; padding-bottom: 3mm; } " +
      "@top-right { content: " + cssString(revealTag) + "; font: 600 7.5pt 'Source Sans 3', 'Noto Sans Thai', sans-serif; color: " + (revealed ? "#b42318" : "#5b6474") + "; vertical-align: bottom; padding-bottom: 3mm; } " +
      "@bottom-left { content: " + cssString(footer) + "; font: 7.5pt 'Source Sans 3', 'Noto Sans Thai', sans-serif; color: #5b6474; vertical-align: top; padding-top: 3mm; } " +
      "@bottom-right { content: \"Page \" counter(page) \" of \" counter(pages); font: 7.5pt 'Source Sans 3', sans-serif; color: #5b6474; vertical-align: top; padding-top: 3mm; } } " +
      "@page :first { @top-left { content: none; } @top-right { content: none; } }";

    var summary = { name: name, jurisdiction: dossier.jurisdiction, as_of: asOf, horizon: h, window_end: windowEnd, lang: lang, mode: modeLabel,
      revealed: revealed, m3: f ? pct(f.m3_p_entry) : null, b1: f ? pct(f.b1_p_entry) : null, rank: f ? f.m3_rank : null, queue_total: n,
      disclaimer: disclaimer, open_tasks: openTasks, tasks: checklist.length, version: current && v ? v.tag || null : null,
      appendix: Object.keys(appx).length };
    return { html: '<div class="pd-doc" lang="' + lang + '">' + out.join("") + "</div>", css: CSS, pageCss: pageCss,
      title: name + " · Market Window Dossier", summary: summary };
  }

  /* A complete page for the PDF and the saved HTML. fontsCss is the text of assets/fonts/fonts.css. */
  function documentHtml(dossier, o) {
    o = o || {};
    var r = build(dossier, o), lang = r.summary.lang;
    var alt = o.alternate ? '<nav class="pd-alt"><a href="' + esc(o.alternate) + '" hreflang="' + (lang === "th" ? "en" : "th") + '">' +
      (lang === "th" ? "English" : "ภาษาไทย") + "</a></nav>" : "";
    return '<!doctype html>\n<html lang="' + lang + '"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">' +
      "<title>" + esc(r.title) + "</title><style>" + (o.fontsCss || "") + "\n" + r.css + "\n" + r.pageCss + "\n" + PAGE_CSS + "</style></head><body>" +
      alt + r.html + "</body></html>\n";
  }

  /* Page frame for a standalone document only. The app mounts the report inside its own page. */
  var PAGE_CSS =
    "html, body { margin: 0; background: #f3f5f8; }\n" +
    ".pd-alt { max-width: 182mm; margin: 12px auto 0; font: 600 14px 'Source Sans 3', sans-serif; }\n" +
    "@media screen { .pd-doc { max-width: 182mm; margin: 12px auto 40px; background: #fff; padding: 12mm; border: 1px solid #d5dae1; } }\n" +
    "@media print { html, body { background: #fff; } .pd-alt { display: none; } }\n";

  var CSS =
    ".pd-doc { --navy: #0b2545; --navy2: #13315c; --ink: #1d2433; --muted: #5b6474; --line: #d5dae1; --link: #0b5cad; --green: #1d6b3a; --green-bg: #e6f3ea; --amber: #8a5a00; --amber-bg: #fff3d6; --neutral-bg: #eceff3; --red: #b42318;\n" +
    "  color: var(--ink); font: 400 9.5pt/1.55 'Source Sans 3', 'Noto Sans Thai', sans-serif; -webkit-print-color-adjust: exact; print-color-adjust: exact; font-variant-numeric: tabular-nums; text-align: left; }\n" +
    ".pd-doc *, .pd-doc *::before, .pd-doc *::after { box-sizing: border-box; line-height: inherit; text-wrap: wrap; }\n" +
    ".pd-doc h1, .pd-doc h2, .pd-doc h3, .pd-doc p, .pd-doc dl, .pd-doc dd, .pd-doc dt { margin: 0; padding: 0; font-weight: inherit; }\n" +
    ".pd-doc a { color: var(--link); text-decoration: none; }\n" +
    ".pd-doc code { font: 400 6.6pt/1.35 Consolas, 'Courier New', monospace; overflow-wrap: anywhere; color: var(--ink); }\n" +
    ".pd-doc b { font-weight: 600; }\n" +
    ".pd-doc .pd-brand { display: flex; justify-content: space-between; align-items: center; gap: 12px; background: var(--navy); color: #fff; padding: 2.4mm 4mm; border-radius: 3px; }\n" +
    ".pd-doc .pd-wordmark { font: 700 11pt/1.2 'Source Sans 3', sans-serif; letter-spacing: .01em; }\n" +
    ".pd-doc .pd-mode { font: 600 8pt/1.2 'Source Sans 3', sans-serif; color: #dbe4f0; text-align: right; }\n" +
    ".pd-doc .pd-cover { break-after: page; }\n" +
    ".pd-doc .pd-h1 { font: 700 24pt/1.12 'Source Sans 3', sans-serif; color: var(--navy); margin: 5mm 0 1.5mm; overflow-wrap: anywhere; text-wrap: balance; letter-spacing: -.005em; }\n" +
    ".pd-doc .pd-meta { display: flex; flex-wrap: wrap; gap: 1mm 5mm; font: 400 9pt/1.4 'Source Sans 3', 'Noto Sans Thai', sans-serif; color: var(--muted); }\n" +
    ".pd-doc .pd-meta b { color: var(--ink); }\n" +
    ".pd-doc .pd-chips { display: flex; flex-wrap: wrap; gap: 1.5mm; margin: 2.5mm 0 4mm; }\n" +
    ".pd-doc .pd-chip { display: inline-block; padding: .4mm 2.2mm; border: 1px solid var(--line); background: var(--neutral-bg); border-radius: 3px; font: 600 7.5pt/1.5 'Source Sans 3', sans-serif; color: var(--ink); }\n" +
    ".pd-doc .pd-chip-navy { background: var(--navy); border-color: var(--navy); color: #fff; }\n" +
    ".pd-doc .pd-chip-red { background: #fde8e6; border-color: var(--red); color: var(--red); }\n" +
    ".pd-doc .pd-h2 { font: 700 13pt/1.25 'Source Sans 3', sans-serif; color: var(--navy); margin: 0 0 3mm; padding-bottom: 1.5mm; border-bottom: 1.5px solid var(--navy); break-after: avoid; text-wrap: balance; display: flex; align-items: baseline; gap: 2.5mm; }\n" +
    ".pd-doc .pd-h2-red { border-bottom-color: var(--red); color: var(--red); }\n" +
    ".pd-doc .pd-revealed { font: 600 8pt/1 'Source Sans 3', sans-serif; margin-left: auto; text-transform: uppercase; letter-spacing: .04em; }\n" +
    ".pd-doc .pd-no { font: 700 9pt/1 'Source Sans 3', sans-serif; color: #fff; background: var(--navy2); border-radius: 3px; padding: 1mm 2mm; min-width: 6mm; text-align: center; }\n" +
    ".pd-doc .pd-h3 { font: 700 10pt/1.3 'Source Sans 3', sans-serif; color: var(--navy); margin: 5mm 0 2mm; break-after: avoid; text-wrap: balance; }\n" +
    ".pd-doc .pd-progress { font-weight: 400; color: var(--muted); margin-left: 2mm; font-size: 8.5pt; }\n" +
    ".pd-doc .pd-sec { margin: 0 0 6mm; }\n" +
    ".pd-doc .pd-sec-first { margin-top: 0; }\n" +
    ".pd-doc .pd-appx { break-before: page; }\n" +
    ".pd-doc .pd-appx ~ .pd-appx { break-before: page; }\n" +
    ".pd-doc .pd-stats { display: grid; grid-template-columns: repeat(4, 1fr); border: 1px solid var(--line); border-radius: 4px; margin: 0 0 4mm; }\n" +
    ".pd-doc .pd-stat { padding: 2.5mm 3mm; border-left: 1px solid var(--line); min-width: 0; }\n" +
    ".pd-doc .pd-stat:first-child { border-left: 0; }\n" +
    ".pd-doc .pd-k { font: 600 7.5pt/1.3 'Source Sans 3', sans-serif; color: var(--muted); min-height: 2.6em; }\n" +
    ".pd-doc .pd-v { font: 700 19pt/1.15 'Source Sans 3', sans-serif; color: var(--navy); margin-top: 1mm; }\n" +
    ".pd-doc .pd-v small { font: 400 9pt/1 'Source Sans 3', sans-serif; color: var(--muted); }\n" +
    ".pd-doc .pd-v.pd-verify { color: var(--amber); }\n" +
    ".pd-doc .pd-s { font: 400 7.5pt/1.35 'Source Sans 3', 'Noto Sans Thai', sans-serif; color: var(--muted); margin-top: 1mm; }\n" +
    ".pd-doc .pd-kv { display: grid; grid-template-columns: 31mm 1fr; border-top: 1px solid var(--line); margin: 0 0 4mm; }\n" +
    ".pd-doc .pd-kv dt, .pd-doc .pd-kv dd { padding: 1.8mm 0; border-bottom: 1px solid var(--line); }\n" +
    ".pd-doc .pd-kv dt { font: 600 8pt/1.5 'Source Sans 3', sans-serif; color: var(--muted); padding-right: 3mm; }\n" +
    ".pd-doc .pd-kv dd { overflow-wrap: anywhere; }\n" +
    ".pd-doc .pd-kind { display: block; font: 400 7.5pt/1.4 'Source Sans 3', 'Noto Sans Thai', sans-serif; color: var(--muted); margin-top: .6mm; overflow-wrap: anywhere; }\n" +
    ".pd-doc .pd-lookup { display: block; font: 400 8pt/1.45 'Source Sans 3', 'Noto Sans Thai', sans-serif; color: var(--muted); margin-top: .8mm; overflow-wrap: anywhere; }\n" +
    ".pd-doc .pd-callout { border: 1px solid var(--line); border-left: 3px solid var(--navy); border-radius: 3px; padding: 2mm 3.5mm; margin: 0 0 2.5mm; break-inside: avoid; }\n" +
    ".pd-doc .pd-callout > b { display: block; font: 700 8pt/1.4 'Source Sans 3', sans-serif; color: var(--navy); text-transform: none; }\n" +
    ".pd-doc .pd-callout p { font-size: 9pt; line-height: 1.55; }\n" +
    ".pd-doc .pd-callout-amber { background: var(--amber-bg); border-color: #e3c27a; border-left-color: var(--amber); }\n" +
    ".pd-doc .pd-callout-amber > b { color: var(--amber); }\n" +
    ".pd-doc table { width: 100%; border-collapse: collapse; table-layout: auto; font-size: 9pt; }\n" +
    ".pd-doc thead { display: table-header-group; }\n" +
    ".pd-doc th { text-align: left; font: 600 7.5pt/1.3 'Source Sans 3', sans-serif; color: var(--muted); padding: 1.2mm 2mm 1.2mm 0; border-bottom: 1.5px solid var(--navy); }\n" +
    ".pd-doc td { padding: 1.8mm 2mm 1.8mm 0; border-bottom: 1px solid var(--line); vertical-align: top; overflow-wrap: anywhere; }\n" +
    ".pd-doc tr { break-inside: avoid; }\n" +
    ".pd-doc .pd-c-status { width: 20mm; } .pd-doc .pd-c-src { width: 24mm; } .pd-doc .pd-c-sec { width: 24mm; } .pd-doc .pd-c-box { width: 6mm; }\n" +
    ".pd-doc .pd-c-agency { width: 25mm; } .pd-doc .pd-c-owner { width: 24mm; } .pd-doc .pd-c-num { width: 22mm; text-align: right; } .pd-doc .pd-c-no { width: 9mm; }\n" +
    ".pd-doc .pd-c-pub { width: 21mm; } .pd-doc .pd-c-sha { width: 52mm; }\n" +
    ".pd-doc .pd-num { font-variant-numeric: tabular-nums; }\n" +
    ".pd-doc .pd-tag { display: inline-block; padding: .2mm 1.8mm; border-radius: 3px; font: 600 7.5pt/1.5 'Source Sans 3', 'Noto Sans Thai', sans-serif; white-space: nowrap; }\n" +
    ".pd-doc .pd-tag-known { background: var(--green-bg); color: var(--green); }\n" +
    ".pd-doc .pd-tag-verify { background: var(--amber-bg); color: var(--amber); }\n" +
    ".pd-doc .pd-tag-assumption, .pd-doc .pd-tag-neutral, .pd-doc .pd-tag-na { background: var(--neutral-bg); color: var(--ink); }\n" +
    ".pd-doc .pd-cites { font: 400 8pt/1.5 'Source Sans 3', sans-serif; }\n" +
    ".pd-doc .pd-more, .pd-doc .pd-none { color: var(--muted); }\n" +
    ".pd-doc .pd-box { display: block; width: 3.4mm; height: 3.4mm; border: 1.2px solid var(--navy); border-radius: 1px; margin-top: .8mm; }\n" +
    ".pd-doc .pd-box.is-on { background: var(--navy); }\n" +
    ".pd-doc .pd-note { font-size: 8.5pt; color: var(--muted); margin: 1.5mm 0 0; }\n" +
    ".pd-doc .pd-moreline { margin-top: 2mm; font-style: normal; break-before: avoid; }\n" +
    ".pd-doc .pd-empty { color: var(--muted); }\n" +
    ".pd-doc .pd-sr { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); }\n" +
    ".pd-doc .pd-refs td { font-size: 8pt; }\n" +
    ".pd-doc .pd-appx-end { margin-top: 4mm; break-inside: avoid; }\n" +
    /* The appendix holds the long evidence tables, so its rows are set tighter than the body. */
    ".pd-doc .pd-appx td { padding: .8mm 1.6mm .8mm 0; font-size: 8pt; line-height: 1.38; }\n" +
    ".pd-doc .pd-appx th { padding: 1mm 1.6mm 1mm 0; }\n" +
    ".pd-doc .pd-appx .pd-tag { font-size: 7pt; padding: 0 1.4mm; }\n" +
    ".pd-doc .pd-appx .pd-kind, .pd-doc .pd-appx .pd-lookup { display: inline; margin-left: 1.5mm; font-size: 7.4pt; }\n" +
    ".pd-doc .pd-appx .pd-cites { font-size: 7.4pt; }\n" +
    ".pd-doc .pd-appx .pd-refs td { font-size: 7.6pt; }\n" +
    ".pd-doc .pd-appx code { font-size: 6.2pt; }\n" +
    ".pd-doc .pd-appx .pd-c-sec { width: 19mm; } .pd-doc .pd-appx .pd-c-status { width: 17mm; } .pd-doc .pd-appx .pd-c-src { width: 22mm; }\n" +
    ".pd-doc .pd-appx .pd-box { margin-top: 0; width: 3mm; height: 3mm; }\n";

  /* App print: mount the report in the page, hide everything else, and unmount afterwards. */
  var MOUNT_CSS =
    "#pd-print-root { display: none; }\n" +
    "@media print { html, body { height: auto !important; overflow: visible !important; display: block !important; background: #fff !important; }\n" +
    "  body.pd-printing > *:not(#pd-print-root):not(#pd-print-style) { display: none !important; }\n" +
    "  body.pd-printing > #pd-print-root { display: block !important; } }\n";
  function mount(doc, result) {
    unmount(doc);
    var style = doc.createElement("style");
    style.id = "pd-print-style";
    style.textContent = result.css + "\n" + result.pageCss + "\n" + MOUNT_CSS;
    var rootEl = doc.createElement("div");
    rootEl.id = "pd-print-root";
    rootEl.innerHTML = result.html;
    doc.body.appendChild(style);
    doc.body.appendChild(rootEl);
    doc.body.classList.add("pd-printing");
  }
  function unmount(doc) {
    var a = doc.getElementById("pd-print-style"), b = doc.getElementById("pd-print-root");
    if (a) a.remove();
    if (b) b.remove();
    doc.body.classList.remove("pd-printing");
  }

  return { build: build, document: documentHtml, mount: mount, unmount: unmount, DISCLAIMER: DISCLAIMER, SECTIONS: SECTIONS, fmtDate: fmtDate };
});
