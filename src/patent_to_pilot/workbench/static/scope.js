"use strict";

const scopeReader = (() => {
  let catalog;
  let current;
  let loading;
  let busy = false;
  const byId = (items, id) => items.find(item => item.id === id);
  const selected = () => catalog && byId(catalog.examples, $("scope-example").value);
  const option = (value, text) => el("option", {value, text});
  function sourceLink(url) {
    if (typeof url === "string" && /^https?:\/\//i.test(url)) {
      return el("a", {href: url, target: "_blank", rel: "noopener noreferrer", text: "เปิดแหล่งต้นฉบับ"});
    }
    return null;
  }
  const origin = value => ({
    authored_demo: "เอกสารสมมติสำหรับสาธิต", synthetic_fixture: "เอกสารสมมติสำหรับสาธิต",
    synthetic_demo: "เอกสารสมมติสำหรับสาธิต", public_source: "ตัวอย่างจากเอกสารสาธารณะ"
  }[value] || value || "ไม่ระบุที่มาของตัวอย่าง");
  function notice(message, error = false) {
    const box = $("scope-notice");
    box.textContent = message;
    box.classList.toggle("error", error);
  }
  function checkQuestion() {
    const sample = selected();
    const supported = sample && $("scope-question").value.trim() === sample.question_th.trim();
    $("scope-submit").disabled = busy || !supported;
    $("scope-help").textContent = !sample || supported ?
      "รุ่นทดลองนี้รองรับคำถามตัวอย่างของแต่ละชุดเอกสาร" :
      "ยังตอบคำถามนี้ไม่ได้ กด “ใช้คำถามตัวอย่าง” เพื่อดูคำถามที่มีหลักฐานในชุดนี้";
  }
  function controls(disabled) {
    busy = disabled;
    for (const id of ["scope-family", "scope-example", "scope-question", "scope-restore", "scope-runs"]) $(id).disabled = disabled;
    $("scope-reopen").querySelector("button").disabled = disabled || !$("scope-runs").options.length;
    checkQuestion();
  }
  function setHistory() {
    $("scope-runs").replaceChildren(...catalog.runs.map(run => {
      const sample = byId(catalog.examples, run.example_id);
      const title = sample ? [sample.family_title_th, sample.title_th].filter(Boolean).join(" · ") : run.example_id;
      return option(run.id, title + " · " + run.version + " · " + run.id);
    }));
    if (current && byId(catalog.runs, current.id)) $("scope-runs").value = current.id;
  }
  function loadQuestions(preferred) {
    const samples = catalog.examples.filter(item => item.family_id === $("scope-family").value);
    $("scope-example").replaceChildren(...samples.map(item => option(item.id, item.title_th + " · " + item.version)));
    if (samples.some(item => item.id === preferred)) $("scope-example").value = preferred;
    $("scope-question").value = selected()?.question_th || "";
    checkQuestion();
  }
  function familyOptions(examples) {
    const groups = new Map(), seen = new Set();
    const domains = {thai_law: "กฎหมายไทย", en_patent: "สิทธิบัตรภาษาอังกฤษ"};
    for (const item of examples) {
      if (seen.has(item.family_id)) continue;
      seen.add(item.family_id);
      if (!groups.has(item.domain)) {
        groups.set(item.domain, el("optgroup", {label: domains[item.domain] || item.domain}));
      }
      groups.get(item.domain).append(option(item.family_id, (item.family_title_th || item.source_id) +
        " · " + origin(item.data_origin)));
    }
    return [...groups.values()];
  }
  async function open() {
    if (catalog || loading) return;
    controls(true);
    notice("กำลังเปิดรายการเอกสาร…");
    try {
      loading = api("GET", "/api/scope/catalog");
      catalog = await loading;
      $("scope-family").replaceChildren(...familyOptions(catalog.examples));
      loadQuestions();
      setHistory();
      notice(catalog.examples.length ? "" : "ยังไม่มีชุดเอกสารในเครื่องนี้");
    } catch (e) { catalog = null; notice("เปิดรายการเอกสารไม่ได้ · " + e.message, true); }
    finally { loading = null; controls(false); }
  }
  const evidenceFor = (trace, id) => byId(trace.evidence, id);
  const words = (trace, req) => evidenceFor(trace, req.evidence_id)?.meaning_th || req.reason_th;
  const edgeType = edge => edge.type === "stated" ? "ต้นฉบับระบุ" : "ระบบอนุมาน";
  function inspect(trigger, title, children) {
    S.lastFocus = trigger;
    $("drawer-title").textContent = title;
    $("drawer-body").replaceChildren(el("div", {lang: "th"}, children));
    $("drawer").hidden = false;
    $("drawer-close").focus();
  }
  function inspectEvidence(trace, id, trigger) {
    const ev = evidenceFor(trace, id);
    if (!ev) return inspect(trigger, "หลักฐาน", [el("p", {text: "ผลที่บันทึกไม่มีข้อความอ้างอิงสำหรับรายการนี้"})]);
    const facts = el("dl", {class: "scope-facts"});
    const rows = [["แหล่งเอกสาร", ev.source_id], ["ฉบับ", ev.version], ["ตำแหน่ง", ev.locator],
      ["ช่วงอักขระ (เริ่มที่ 0 ไม่รวมตำแหน่งท้าย)", ev.start + "–" + ev.end], ["ข้อแม่หรือบทที่อ้างถึง", ev.parent],
      ["วันที่กำกับ", ev.date], ["ตัวอย่างที่อ้างถึง", ev.example], ["SHA-256 ชุดข้อความที่คัดมา", ev.sha256],
      ["SHA-256 ข้อความที่ยกมา", ev.quote_sha256]];
    for (const [label, value] of rows) if (value !== null && value !== undefined && value !== "") {
      facts.append(el("dt", {text: label}), el("dd", {text: String(value)}));
    }
    const children = [el("h3", {text: "ข้อความต้นฉบับ"}), el("blockquote", {
      class: "scope-quote", lang: /patent/i.test(trace.domain) ? "en" : "th",
      text: ev.quote ?? "ตัวอย่างนี้เก็บเฉพาะตำแหน่งอ้างอิง โปรดเปิดเอกสารจากแหล่งที่มา"
    }), el("h3", {text: "คำอธิบายภาษาไทย"}), el("p", {text: ev.meaning_th || "ผลนี้เผยแพร่เฉพาะตำแหน่งอ้างอิง"}), facts];
    const cited = trace.edges.filter(edge => edge.type === "stated" && edge.from === ev.id)
      .map(edge => evidenceFor(trace, edge.to)).filter(Boolean);
    if (cited.length) children.push(el("h3", {text: "ตามข้อที่ต้นฉบับอ้างถึง"}),
      el("ul", {}, cited.map(target => el("li", {}, el("button", {text: target.locator,
        onclick: () => inspectEvidence(trace, target.id, trigger)})))));
    children.push(sourceLink(ev.source_url || trace.source_url));
    inspect(trigger, ev.locator || ev.source_id, children);
  }
  function inspectNode(trace, node, trigger) {
    if (evidenceFor(trace, node.id)) return inspectEvidence(trace, node.id, trigger);
    const ids = new Set(trace.edges.filter(edge => edge.from === node.id || edge.to === node.id).map(edge => edge.evidence_id));
    const req = trace.requirements.find(item => "req:" + item.id === node.id);
    if (req?.evidence_id) ids.add(req.evidence_id);
    const found = [...ids].map(id => evidenceFor(trace, id)).filter(Boolean);
    if (found.length === 1) return inspectEvidence(trace, found[0].id, trigger);
    const items = found.map(ev => el("li", {}, el("button", {text: ev.locator, onclick: () => inspectEvidence(trace, ev.id, trigger)})));
    inspect(trigger, node.label_th, [items.length ? el("ul", {}, items) : el("p", {text: req?.reason_th || "ยังไม่มีข้อความรองรับจุดนี้"})]);
  }
  function graph(trace) {
    const map = el("div", {class: "scope-map", "aria-label": "แผนผังความสัมพันธ์"});
    const list = el("ul", {class: "scope-links"});
    const nodeButton = node => el("button", {class: "scope-node", text: node.label_th, onclick: e => inspectNode(trace, node, e.currentTarget)});
    const connected = new Set();
    for (const edge of trace.edges) {
      const left = byId(trace.nodes, edge.from), right = byId(trace.nodes, edge.to);
      if (!left || !right) continue;
      connected.add(left.id); connected.add(right.id);
      const label = edge.label_th + " · " + edgeType(edge);
      const click = e => inspectEvidence(trace, edge.evidence_id, e.currentTarget);
      map.append(el("div", {class: "scope-connection " + (edge.type === "stated" ? "stated" : "inferred")},
        nodeButton(left), el("button", {class: "scope-edge", text: label + " →", onclick: click}), nodeButton(right)));
      list.append(el("li", {}, el("button", {text: left.label_th + " → " + label + " → " + right.label_th, onclick: click})));
    }
    for (const node of trace.nodes.filter(item => !connected.has(item.id))) {
      map.append(nodeButton(node));
      list.append(el("li", {}, nodeButton(node)));
    }
    const section = el("section", {class: "card"}, el("h3", {text: "ความสัมพันธ์ของหลักฐาน"}), map,
      el("details", {}, el("summary", {text: "อ่านเป็นรายการข้อความ"}), list));
    if (trace.unresolved_relations?.length) {
      section.append(el("h4", {text: "ความสัมพันธ์ที่ยังตามหลักฐานไม่ครบ"}),
        el("ul", {}, trace.unresolved_relations.map(rel => el("li", {
          text: (byId(trace.nodes, rel.from)?.label_th || rel.from) + " → " + rel.locator + " · ยังยืนยันปลายทางไม่ได้"}))));
    }
    return section;
  }
  function compare(before, after) {
    const list = el("ul", {class: "scope-changes"});
    const ids = new Set([...before.requirements, ...after.requirements].map(req => req.id));
    for (const id of ids) {
      const a = byId(before.requirements, id), b = byId(after.requirements, id);
      const from = a && evidenceFor(before, a.evidence_id), to = b && evidenceFor(after, b.evidence_id);
      const label = (b || a).label_th;
      let change;
      if (!a) change = "เพิ่มในผลครั้งนี้";
      else if (!b) change = "ไม่มีในผลครั้งนี้";
      else if (a.status !== b.status) change = "สถานะหลักฐานเปลี่ยน";
      else if (words(before, a) !== words(after, b)) change = "คำอธิบายเปลี่ยน";
      else if (a.status === "unresolved") change = "ทั้งสองฉบับยังไม่มีหลักฐานครบ";
      else if ((from?.quote_sha256 ?? from?.quote) !== (to?.quote_sha256 ?? to?.quote)) change = "คำอธิบายคงเดิม แต่ถ้อยคำต้นฉบับเปลี่ยน";
      else change = "คำอธิบายและข้อความอ้างอิงคงเดิม";
      const row = el("li", {}, el("strong", {text: label}), el("span", {class: "scope-outcome", text: change}));
      for (const [name, trace, req, ev] of [["ก่อน", before, a, from], ["หลัง", after, b, to]]) {
        const line = el("div", {}, el("b", {text: name + " "}), req ? words(trace, req) : "ไม่มีประเด็นนี้");
        if (ev) line.append(" ", el("button", {class: "cite", text: ev.locator, onclick: e => inspectEvidence(trace, ev.id, e.currentTarget)}));
        row.append(line);
      }
      list.append(row);
    }
    return el("section", {class: "card"}, el("h3", {text: "เทียบกับผลก่อนหน้า"}), el("p", {text: before.title_th + " (" + before.version + ") → " + after.title_th + " (" + after.version + ")"}), list);
  }
  function exportTrace(trace) {
    const a = el("a", {download: "scope-" + trace.id + ".json", href: "/api/scope/run/" + encodeURIComponent(trace.id)});
    document.body.append(a); a.click(); a.remove();
  }
  function render(trace, previous) {
    const result = $("scope-result");
    const summary = el("section", {class: "card"}, el("h2", {text: trace.title_th}), el("p", {text: trace.question_th}),
      el("p", {class: "muted", text: [trace.family_title_th, origin(trace.data_origin), trace.source_id, trace.version].filter(Boolean).join(" · ")}),
      el("strong", {text: trace.status === "complete" ? "พบหลักฐานครบตามคำถามตัวอย่าง" : "พบหลักฐานเพียงบางส่วน"}));
    if (!/patent/i.test(trace.domain)) summary.append(el("p", {class: "muted"},
      "ข้อมูลกำกับฉบับ · วันประกาศ " + (trace.issue_date || "ยังไม่ทราบ") + " · วันมีผล " + (trace.effective_date || "ยังไม่ทราบ") + " ",
      sourceLink(trace.source_url)));
    if (Number.isInteger(trace.publication_claim_count)) {
      const selectedClaims = trace.selected_claim_numbers || [];
      const selection = selectedClaims.length ? " · ชุดตัวอย่างคัดข้อ " + selectedClaims.join(", ") : "";
      summary.append(el("p", {class: "muted"}, "เอกสารสิทธิบัตรฉบับเผยแพร่มีข้อถือสิทธิทั้งหมด " +
        trace.publication_claim_count + " ข้อ" + selection + " ", sourceLink(trace.source_url)));
    }
    const answers = el("ul", {class: "scope-answers"});
    for (const req of trace.requirements) {
      const ev = evidenceFor(trace, req.evidence_id);
      const row = el("li", {}, el("strong", {text: req.label_th}), el("p", {text: words(trace, req)}));
      if (req.status === "bound" && ev) row.append(el("button", {class: "cite", text: "เปิดหลักฐาน · " + ev.locator,
        onclick: e => inspectEvidence(trace, ev.id, e.currentTarget)}));
      else row.append(el("small", {class: "scope-unresolved", text: "ยังยืนยันไม่ได้"}));
      answers.append(row);
    }
    summary.append(answers);
    result.replaceChildren(summary);
    if (previous && previous.family_id === trace.family_id && previous.id !== trace.id) result.append(compare(previous, trace));
    result.append(graph(trace));
    const actionNames = {keep: "ใช้ข้อความเดิม", rerank: "จัดอันดับหลักฐานใหม่", acquire: "ค้นหลักฐานเพิ่ม", qualify: "ระบุข้อจำกัด"};
    const actions = trace.actions.map(step => el("li", {}, el("strong", {text: (actionNames[step.action] || step.action) + " · " + step.requirement_id}),
      el("div", {text: step.reason_th}), el("div", {class: "muted", text: "ก่อน " + step.before.join(", ") + " → หลัง " + step.after.join(", ") + " · ใช้งบ " + step.cost})));
    result.append(el("details", {class: "card"}, el("summary", {text: "ดูขั้นตอนที่ระบบใช้หาหลักฐาน"}),
      el("p", {text: "งบค้นเพิ่มเติมที่ใช้ " + trace.budget.used + " / " + trace.budget.limit}), el("ol", {}, actions)),
      el("div", {class: "actions"}, el("button", {text: "ส่งออกผลและหลักฐาน (JSON)", onclick: () => exportTrace(trace)}),
      el("small", {class: "muted", text: trace.contract + " · " + trace.id})));
    result.hidden = false;
  }
  async function read(id) {
    if (busy || (!id && !selected())) return;
    const previous = current;
    controls(true);
    notice(id ? "กำลังเปิดผลเดิม…" : "กำลังอ่านข้อความที่เลือก…");
    try {
      const trace = id ? await api("GET", "/api/scope/run/" + encodeURIComponent(id)) :
        await api("POST", "/api/scope/run", {example_id: selected().id, question_th: $("scope-question").value.trim()});
      if (id && byId(catalog.examples, trace.example_id)) {
        $("scope-family").value = trace.family_id;
        loadQuestions(trace.example_id);
        $("scope-question").value = trace.question_th;
      }
      render(trace, previous);
      current = trace;
      if (!byId(catalog.runs, trace.id)) catalog.runs.unshift({id: trace.id, example_id: trace.example_id, version: trace.version});
      setHistory();
      notice(id ? "เปิดผลที่บันทึกพร้อมแหล่งอ้างอิงเดิมแล้ว" : "บันทึกผลการอ่านในเครื่องนี้แล้ว");
    } catch (e) { notice("เปิดผลการอ่านไม่ได้ · " + e.message, true); }
    finally { controls(false); }
  }
  function changed() {
    $("scope-question").value = selected()?.question_th || "";
    checkQuestion();
    if (current) { $("scope-result").hidden = true; read(); }
  }
  function init() {
    $("scope-family").addEventListener("change", () => { loadQuestions(); changed(); });
    $("scope-example").addEventListener("change", changed);
    $("scope-question").addEventListener("input", () => { checkQuestion(); $("scope-result").hidden = true; });
    $("scope-restore").addEventListener("click", () => { $("scope-question").value = selected()?.question_th || ""; checkQuestion(); });
    $("scope-form").addEventListener("submit", e => { e.preventDefault(); if (!$("scope-submit").disabled) read(); });
    $("scope-reopen").addEventListener("submit", e => { e.preventDefault(); if ($("scope-runs").value) read($("scope-runs").value); });
  }
  return {init, open};
})();
