// RA Pharma dossier view. Every value shown comes from a stored snapshot on the local server.
// Text is rendered with textContent only.
"use strict";

const dossierView = (() => {
  let catalog = null, snap = null, letter = null, busy = false;
  const STATUS = {supported: "มีหลักฐาน", missing: "ยังขาด", conflict: "ขัดกัน", needs_review: "ต้องตรวจ",
    meets: "ตรง", does_not_meet: "ไม่ตรง", read: "อ่านได้", uncertain: "ไม่แน่ใจ", absent: "ไม่พบ",
    all_elements_met_on_record: "ตรงทุกองค์ประกอบตามบันทึก"};
  const ROLE = {patent_disclosure: "ข้อเปิดเผยในสิทธิบัตร", claim_limitation: "ข้อจำกัดของข้อถือสิทธิ",
    applicant_result: "ผลของผู้ยื่น", regulatory_requirement: "ข้อกำหนดด้านทะเบียน", incoming_request: "คำขอในหนังสือ",
    needs_review: "ต้องตรวจ"};
  const AGENT = {patent: "ผู้เชี่ยวชาญสิทธิบัตร", regulatory: "ผู้เชี่ยวชาญทะเบียนยา", correspondence: "ผู้เชี่ยวชาญหนังสือ",
    operator: "ผู้ปฏิบัติงาน", system: "ระบบ"};
  const badge = (s) => el("span", {class: "status-badge " + s, text: STATUS[s] || s});
  const item = (id) => snap.items.find(i => i.item_id === id);
  function notice(msg, error = false) { const n = $("dossier-notice"); n.textContent = msg; n.classList.toggle("error", error); }
  function setBusy(v) { busy = v; for (const b of document.querySelectorAll("#view-dossier button")) b.disabled = v; }

  async function run(label, fn) {
    if (busy) return;
    setBusy(true); notice(label + "…");
    try { await fn(); notice(""); }
    catch (e) { notice(e.message || String(e), true); }
    finally { setBusy(false); }
  }

  // ---------------------------------------------------------------- controls
  function fillControls() {
    const d = catalog.dossier;
    $("dossier-summary").textContent = `${d.dossier_id} · ผู้ยื่น ${d.applicant.name_th} · ผลิตภัณฑ์ ${d.product.name_th} · ` +
      `ตลาด ${d.market} · ณ วันที่ ${d.as_of} · ${d.note_th}`;
    const incoming = catalog.documents.filter(x => x.role === "incoming_letter");
    $("dossier-incoming").replaceChildren(...incoming.map(x => el("option", {value: x.doc_id, text: x.title_th})));
    $("dossier-attachments").replaceChildren(el("legend", {text: "เอกสารของผู้ยื่นที่แนบ"}),
      ...catalog.documents.filter(x => x.role === "applicant_document").map(x => el("label", {},
        el("input", {type: "checkbox", value: x.doc_id, checked: x.always_attached || null, disabled: x.always_attached || null}),
        x.title_th + (x.always_attached ? " (แนบเสมอ)" : ""))));
    $("dossier-skill").replaceChildren(...catalog.skills.map(s => el("option", {value: s.version,
      text: `${s.version}${s.version === catalog.active_skill ? " (ใช้งานอยู่)" : ""} · ${s.description_th}`})));
    $("dossier-skill").value = catalog.active_skill;
    const opts = catalog.snapshots.slice().reverse().map(s => el("option", {value: s.id,
      text: `ฉบับที่ ${s.seq} · ${s.created_at}${s.label ? " · " + s.label : ""}`}));
    $("dossier-snapshots").replaceChildren(...opts);
    $("dossier-compare").replaceChildren(...opts.map(o => o.cloneNode(true)));
    if (catalog.snapshots.length > 1) $("dossier-compare").selectedIndex = 1;
  }

  function inputs() {
    const body = {incoming_doc_id: $("dossier-incoming").value, claim_branch: $("dossier-branch").value,
      skill_version: $("dossier-skill").value,
      attachments: [...$("dossier-attachments").querySelectorAll("input:checked:not(:disabled)")].map(i => i.value)};
    const edition = $("dossier-edition").value;
    if (edition && !$("dossier-edition-wrap").hidden) body.edition_choice = {[$("dossier-edition").dataset.report]: edition};
    return body;
  }

  async function refresh() { catalog = await api("GET", "/api/dossier/catalog"); fillControls(); }

  async function open() {
    if (catalog) return;
    await run("กำลังเปิดแฟ้ม", async () => {
      await refresh();
      if (catalog.pack_error) throw new Error(catalog.pack_error.message);
      if (catalog.snapshots.length) await load(catalog.snapshots[catalog.snapshots.length - 1].id);
    });
  }

  async function load(id) {
    snap = await api("GET", `/api/dossier/snapshots/${id}`);
    letter = await api("GET", `/api/dossier/snapshots/${id}/letter`);
    render();
  }

  // ---------------------------------------------------------------- evidence drill-down
  async function showSource(itemId, index) {
    const box = $("dossier-evidence");
    const page = await api("GET", `/api/dossier/snapshots/${snap.snapshot_id}/items/${encodeURIComponent(itemId)}/sources/${index}`);
    const r = page.ref, t = page.page_text;
    const text = el("div", {class: "page-text", lang: r.language === "en" ? "en" : "th"},
      t.slice(0, r.start), el("mark", {text: t.slice(r.start, r.end)}), t.slice(r.end));
    box.replaceChildren(
      el("div", {class: "actions"}, el("strong", {text: `หลักฐานของ ${itemId}`}),
        el("button", {type: "button", onclick: () => { box.hidden = true; }}, "ปิด")),
      el("dl", {class: "scope-facts"},
        el("dt", {text: "แหล่ง"}), el("dd", {text: `${r.source_id} · ${r.part}`}),
        el("dt", {text: "เจ้าของหรือผู้ออก"}), el("dd", {text: r.owner || "-"}),
        el("dt", {text: "ฉบับ"}), el("dd", {text: r.edition || "-"}),
        el("dt", {text: "ตำแหน่ง"}), el("dd", {text: `${r.locator || ""}${r.page ? " · หน้า " + r.page : ""}${r.y != null ? " · y " + r.y + " pt" : ""}`}),
        el("dt", {text: "SHA-256"}), el("dd", {text: r.sha256}),
        el("dt", {text: "การถอดข้อความ"}), el("dd", {text: r.transcription}),
        el("dt", {text: "ข้อความตรงตำแหน่ง"}), el("dd", {text: page.verified ? "ตรงกับไบต์ที่เก็บไว้" : "ไม่ตรง ต้องตรวจ"})),
      page.open_url ? el("p", {}, el("a", {href: page.open_url, target: "_blank", rel: "noopener noreferrer",
        text: r.file_sha256 ? `เปิด PDF หน้า ${r.page}` : "เปิดต้นฉบับทางการ"})) : null,
      el("p", {class: "muted", text: "ตำแหน่งข้อความยืนยันที่มาเท่านั้น ผู้ตรวจยังต้องตัดสินว่าข้อความรองรับประโยคหรือไม่"}),
      text);
    box.hidden = false;
  }

  function sourceButtons(it) {
    return it.sources.map((r, i) => el("button", {type: "button", class: "ev-link",
      onclick: () => run("กำลังเปิดหลักฐาน", () => showSource(it.item_id, i))},
      `${r.source_id}${r.page ? " · หน้า " + r.page : ""}`));
  }

  // ---------------------------------------------------------------- sections
  function incomingSection() {
    const inc = snap.incoming, f = inc.fields;
    const names = {number: "ที่", date: "วันที่", subject: "เรื่อง", salutation: "เรียน", reference: "อ้างถึง",
      enclosures: "สิ่งที่ส่งมาด้วย", closing: "คำลงท้าย", signer: "ผู้ลงนาม", signer_position: "ตำแหน่ง",
      signature_image: "ภาพลายมือชื่อ"};
    const sender = item("corr.incoming.sender");
    return el("section", {id: "dossier-incoming-sec"},
      el("h2", {text: "หนังสือที่ได้รับ"}),
      el("p", {}, `ประเภท: ${inc.document_type} · ผู้ส่ง: ${inc.sender.name || "-"} (${inc.sender.kind}) · `, badge(sender.status),
        " ", el("a", {href: `/api/dossier/documents/${snap.inputs.incoming_doc_id}`, target: "_blank", text: "เปิด PDF"})),
      el("p", {class: "muted", text: inc.sender.basis_th}),
      inc.emblem ? el("p", {text: `ภาพที่หัวกระดาษ: x ${inc.emblem.x} pt, y ${inc.emblem.y} pt, สูง ${inc.emblem.height_cm} ซม. ` +
        `(${inc.emblem.position}) · ${inc.emblem.note_th}`}) : el("p", {text: "ไม่พบภาพที่หัวกระดาษ"}),
      inc.fictional_marker ? el("p", {class: "demo", text: inc.fictional_marker}) : null,
      el("table", {class: "matrix"}, el("thead", {}, el("tr", {}, ...["ส่วนของหนังสือ", "ค่าที่อ่านได้", "สถานะ", "ตำแหน่ง (pt)"]
        .map(h => el("th", {scope: "col", text: h})))),
        el("tbody", {}, ...Object.entries(names).map(([k, label]) => el("tr", {},
          el("th", {scope: "row", text: label}), el("td", {text: (f[k].value || "-") + (f[k].note_th ? " — " + f[k].note_th : "")}),
          el("td", {}, badge(f[k].status)), el("td", {text: f[k].x != null ? `หน้า ${f[k].page} · x ${f[k].x} · y ${f[k].y}` : "-"}))))),
      el("h3", {text: "คำขอในหนังสือ"}),
      el("ol", {}, ...inc.requests.map(r => {
        const it = item(`corr.incoming.request-${r.number}`);
        return el("li", {}, r.text, " ", ...sourceButtons(it));
      })));
  }

  function patentSection() {
    const rows = snap.items.filter(i => i.item_id.startsWith("patent.claim."));
    const fto = item("patent.fto-th"), ex6 = item("patent.example-6"), pub = item("patent.publication-status");
    return el("section", {id: "dossier-patent-sec"},
      el("h2", {text: "ตารางเทียบข้อถือสิทธิและ FTO"}),
      el("p", {}, `สาขา ${snap.claim_branch}: `, badge(snap.branch_status), " ", fto.statement),
      el("table", {class: "matrix"}, el("thead", {}, el("tr", {}, ...["ข้อ", "องค์ประกอบ (ต้นฉบับ)", "ข้อมูลผลิตภัณฑ์", "ผลเทียบ", "หลักฐาน"]
        .map(h => el("th", {scope: "col", text: h})))),
        el("tbody", {}, ...rows.map(r => el("tr", {},
          el("th", {scope: "row", text: r.claim}),
          el("td", {}, el("span", {class: "quote-en", lang: "en", text: r.sources[0].quote})),
          el("td", {}, r.statement.split(" — ")[1] || "",
            r.calculation ? el("p", {class: "muted", text: `กรด ${r.calculation.acid_mmol} mmol · ด่าง ${r.calculation.base_mmol} mmol · ` +
              `นับโปรตอน: กรด ${r.calculation.acid_proton_mmol} · ด่าง ${r.calculation.base_proton_mmol}`}) : null),
          el("td", {}, badge(r.comparison), r.reason_th ? el("p", {class: "muted", text: r.reason_th}) : null),
          el("td", {}, ...sourceButtons(r)))))),
      el("h3", {text: "สิ่งที่ยังต้องตรวจก่อนสรุป FTO ในประเทศไทย"}),
      el("ul", {}, ...fto.missing.map(m => el("li", {text: m})), ...pub.missing.map(m => el("li", {text: m}))),
      el("h3", {text: "ผลในตัวอย่างของสิทธิบัตร"}),
      el("p", {}, badge(ex6.status), " ", ROLE[ex6.evidence_role], ": ", ex6.statement, " ", ...sourceButtons(ex6)),
      el("p", {class: "muted", text: ex6.reading_note_th}));
  }

  function regulatorySection() {
    const req = item("reg.R-P54.requirement"), res = item("reg.R-P54.applicant-result"), coa = item("reg.R-COA.attachment");
    const cands = res.candidates.map(c => el("tr", {},
      el("td", {text: c.passage_id}), el("td", {text: c.value}),
      el("td", {}, c.accepted ? badge("supported") : badge("missing"), " ", ROLE[c.role] || c.role),
      el("td", {text: c.reason_th})));
    return el("section", {id: "dossier-reg-sec"},
      el("h2", {text: "รายการตรวจการขึ้นทะเบียน"}),
      el("table", {class: "matrix coverage"}, el("thead", {}, el("tr", {}, ...["เขตอำนาจ", "ความครอบคลุมในแฟ้มนี้", "หมายเหตุ"]
        .map(h => el("th", {scope: "col", text: h})))),
        el("tbody", {}, ...snap.jurisdictions.map(j => el("tr", {}, el("th", {scope: "row", text: `${j.code} · ${j.label_th}`}),
          el("td", {text: {demo: "ตัวอย่างสาธิต", reference_only: "อ้างอิงเท่านั้น", patent_publication_only: "เฉพาะเอกสารสิทธิบัตร",
            not_covered: "ไม่รองรับ"}[j.coverage]}),
          el("td", {text: j.note_th || j.instruments.map(x => x.note_th).join(" ")}))))),
      el("h3", {text: "1. ผลการวิเคราะห์รุ่นการผลิต (ACTD P 5.4)"}),
      el("p", {}, badge(req.status), " ", req.statement, " ", ...sourceButtons(req)),
      el("p", {class: "muted", text: req.applicability_note_th + " " + req.edition_note_th}),
      el("p", {}, el("strong", {text: "ผลของผู้ยื่น: "}), badge(res.status), " ", res.statement, " ", ...sourceButtons(res)),
      res.missing.length ? el("p", {text: "ไฟล์แนบที่ยังขาด: " + res.missing.join(", ")}) : null,
      el("details", {open: true}, el("summary", {text: `ทักษะ ${res.skill.version} พิจารณาข้อความที่มีค่าผลทดสอบ ${res.candidates.length} แห่ง`}),
        el("table", {class: "matrix"}, el("thead", {}, el("tr", {}, ...["ข้อความ", "ค่า", "บทบาทที่ให้", "เหตุผล"]
          .map(h => el("th", {scope: "col", text: h})))), el("tbody", {}, ...cands))),
      el("h3", {text: "2. หนังสือรับรองผลการวิเคราะห์"}),
      el("p", {}, badge(coa.status), " ", coa.statement, " — ", coa.missing.join(", ")));
  }

  function letterSection() {
    const tpl = snap.template;
    const blocks = letter.blocks.map(b => {
      const area = el("textarea", {rows: 1, "data-block": b.block_id, "aria-label": `ข้อความส่วน ${b.block_id}`});
      area.value = b.text;
      const cls = ["letter-block", b.operator_edited ? "edited" : "", b.needs_signer ? "signer" : "", b.blocking ? "blocking" : ""];
      return el("div", {class: cls.join(" ")}, area, b.item_ids.length ? el("button", {type: "button", class: "ev-link",
        onclick: () => reviewBlock(b)}, "หลักฐาน") : el("span"));
    });
    return el("section", {id: "dossier-letter-sec"},
      el("h2", {text: "ร่างหนังสือตอบ"}),
      el("p", {}, `แบบที่เลือก: ${tpl.template.label_th} (${tpl.template.template_id} ${tpl.template.version}) — ${tpl.template.basis_th}`),
      el("ul", {class: "muted"}, ...tpl.rejected.map(r => el("li", {text: `ไม่ใช้ ${r.template_id}: ${r.reason_th}`}))),
      el("p", {class: "muted", text: "พื้นสีฟ้า: ผู้ลงนามต้องกรอก · พื้นสีเหลือง: แก้ไขโดยผู้ปฏิบัติงาน · พื้นสีแดง: ต้องตัดสินใจก่อนส่ง"}),
      el("div", {class: "letter-sheet", lang: "th"}, ...blocks),
      el("p", {class: "muted", text: letter.notice}),
      el("div", {class: "actions"},
        el("button", {type: "button", class: "primary", onclick: saveLetter}, "บันทึกฉบับแก้ไข"),
        el("a", {href: `/api/dossier/snapshots/${snap.snapshot_id}/export/docx`, download: ""}, "ดาวน์โหลด DOCX"),
        el("a", {href: `/api/dossier/snapshots/${snap.snapshot_id}/export/html`, target: "_blank"}, "เปิดหน้าพิมพ์"),
        el("span", {class: "muted", text: letter.revision ? `ฉบับแก้ไข ${letter.revision.slice(0, 8)} (${letter.revisions.length} ครั้ง)` : "ยังไม่แก้ไข"})));
  }

  function reviewBlock(b) {
    const box = $("dossier-evidence");
    box.replaceChildren(el("div", {class: "actions"}, el("strong", {text: "ประโยคนี้มาจาก"}),
      el("button", {type: "button", onclick: () => { box.hidden = true; }}, "ปิด")),
      el("p", {class: "page-text", text: b.text}),
      b.operator_edited ? el("p", {class: "demo", text: "ข้อความถูกแก้ไขหลังสร้างร่าง ต้องตรวจว่าหลักฐานยังรองรับ"}) : null,
      el("ul", {}, ...b.item_ids.map(id => {
        const it = item(id);
        return el("li", {}, badge(it.status), ` ${AGENT[it.agent]} · ${ROLE[it.evidence_role] || it.evidence_role} · ${it.statement} `,
          ...sourceButtons(it));
      })));
    box.hidden = false;
  }

  async function saveLetter() {
    const blocks = [...document.querySelectorAll("#dossier-letter-sec textarea")].map(t => ({block_id: t.dataset.block, text: t.value}));
    await run("กำลังบันทึกฉบับแก้ไข", async () => {
      letter = await api("POST", `/api/dossier/snapshots/${snap.snapshot_id}/letter`, {blocks});
      render();
    });
  }

  function skillSection() {
    const res = item("reg.R-P54.applicant-result");
    const patentAccepted = res.candidates.find(c => c.accepted && c.source_kind === "patent");
    const corrections = catalog.events.filter(e => e.kind === "correction");
    const proposals = catalog.events.filter(e => e.kind === "proposal");
    const evaluations = catalog.events.filter(e => e.kind === "evaluation");
    const last = evaluations[evaluations.length - 1];
    return el("section", {id: "dossier-skill-sec"},
      el("h2", {text: "ทักษะการอ่านบทบาทหลักฐาน"}),
      el("p", {}, `แฟ้มนี้ใช้ ${snap.identity.skill.skill_id} ${snap.identity.skill.version} (SHA-256 ${snap.identity.skill.spec_sha256.slice(0, 12)}…) · ` +
        `รุ่นที่ใช้งานอยู่ ${catalog.active_skill}`),
      el("ul", {}, ...catalog.skills.map(s => el("li", {text: `${s.version}${s.parent ? " (ต่อจาก " + s.parent + ")" : ""}: ${s.description_th}`}))),
      patentAccepted ? el("div", {class: "card"},
        el("p", {text: `ทักษะรุ่นนี้รับค่าร้อยละ ${patentAccepted.value} จาก ${patentAccepted.passage_id} เป็นผลของผู้ยื่น`}),
        el("button", {type: "button", class: "primary", onclick: () => run("กำลังบันทึกการแก้ไข", async () => {
          await api("POST", "/api/dossier/skills/corrections", {snapshot_id: snap.snapshot_id, item_id: res.item_id,
            passage_id: patentAccepted.passage_id, to_role: "patent_disclosure",
            note: "ผลของตัวอย่างในสิทธิบัตรไม่ใช่ผลของผลิตภัณฑ์ผู้ยื่น"});
          await refresh(); render();
        })}, "ปฏิเสธ: เป็นข้อเปิดเผยของสิทธิบัตร")) : null,
      el("ol", {}, ...catalog.events.map(e => el("li", {text: `${e.created_at} · ${e.kind} · ${e.version || ""}` +
        (e.kind === "evaluation" ? ` · ผ่าน ${e.passed} · ผิด ${e.candidate_errors} (รุ่นเดิมผิด ${e.parent_errors}) · ชุดพัฒนา ${e.dev_family}` : "") +
        (e.kind === "correction" ? ` · ${e.passage_id}: ${e.from_role} → ${e.to_role}` : "")}))),
      el("div", {class: "actions"},
        corrections.length ? el("button", {type: "button", onclick: () => run("กำลังเสนอรุ่นใหม่", async () => {
          await api("POST", "/api/dossier/skills/proposals", {correction_id: corrections[corrections.length - 1].id});
          await refresh(); render();
        })}, "เสนอรุ่นทักษะจากการแก้ไข") : null,
        proposals.length ? el("button", {type: "button", onclick: () => run("กำลังทดสอบกับชุดพัฒนาแยก", async () => {
          await api("POST", "/api/dossier/skills/evaluations", {version: proposals[proposals.length - 1].version});
          await refresh(); render();
        })}, "ทดสอบกับชุดพัฒนาแยก") : null,
        last && last.passed && last.version !== catalog.active_skill ? el("button", {type: "button", class: "primary",
          onclick: () => run("กำลังนำรุ่นใหม่ไปใช้", async () => {
            await api("POST", "/api/dossier/skills/promotions", {version: last.version});
            await refresh(); render();
          })}, `นำรุ่น ${last.version} ไปใช้`) : null),
      last ? el("table", {class: "matrix"}, el("thead", {}, el("tr", {}, ...["กรณีทดสอบ", "ชุด", "คาดหวัง", "รุ่นใหม่", "รุ่นเดิม"]
        .map(h => el("th", {scope: "col", text: h})))),
        el("tbody", {}, ...last.cases.map(c => el("tr", {}, el("th", {scope: "row", text: c.case_id}), el("td", {text: c.family}),
          el("td", {text: c.expected.join(", ") || "(ไม่มี)"}),
          el("td", {}, badge(c.candidate_correct ? "supported" : "missing"), " ", c.candidate.join(", ")),
          el("td", {text: c.parent ? (c.parent_correct ? "ถูก" : "ผิด") + " " + c.parent.join(", ") : "-"}))))) : null);
  }

  function replaySection() {
    const id = snap.identity;
    const actions = snap.actions.map(a => el("li", {text: `${AGENT[a.agent] || a.agent} · ${a.action} · ` +
      `${{deterministic: "โปรแกรมกำหนดแน่นอน", operator: "ผู้ปฏิบัติงานตัดสินใจ", model: "แบบจำลองช่วย"}[a.kind]} · ${a.implementation}`}));
    const out = el("div");
    return el("section", {id: "dossier-replay-sec"},
      el("h2", {text: "ตรวจซ้ำและที่มาของการทำงาน"}),
      el("p", {text: `แฟ้ม ${snap.snapshot_id} · ฉบับที่ ${snap.seq} · สร้าง ${snap.created_at} · ชุดข้อมูล ${snap.pack.pack_version} · ` +
        `เนื้อหา SHA-256 ${snap.content_sha256.slice(0, 16)}…`}),
      el("p", {text: `แบบจำลอง: ${id.model || "ไม่ใช้"} · เรียกแบบจำลอง ${id.model_calls} ครั้ง · บริการมีค่าใช้จ่าย ${id.paid_calls} ครั้ง · ` +
        `ตัวอ่าน ${id.reader} · ${id.pdf_library} · ${id.harness}`}),
      el("ol", {start: 0}, ...actions),
      el("div", {class: "actions"},
        el("button", {type: "button", onclick: () => run("กำลังตรวจซ้ำ", async () => {
          const v = await api("GET", `/api/dossier/snapshots/${snap.snapshot_id}/verify`);
          out.replaceChildren(el("p", {text: `อ้างอิง ${v.citations.length} รายการ ${v.citations_ok ? "ตรงทั้งหมด" : "มีรายการไม่ตรง"} · ` +
            `สร้างใหม่ด้วยข้อมูลเดิมและทักษะ ${v.skill_version}: ${v.rebuild_matches ? "ได้เนื้อหาเดียวกัน" : "ได้ผลต่างจากเดิม"}`}));
        })}, "ตรวจซ้ำแฟ้มนี้"),
        el("a", {href: `/api/dossier/snapshots/${snap.snapshot_id}`, download: `dossier-${snap.snapshot_id}.json`}, "ส่งออกแฟ้ม (JSON)")),
      out);
  }

  function render() {
    const edWrap = $("dossier-edition-wrap");
    const res = item("reg.R-P54.applicant-result");
    if (res.conflict) {
      const rid = res.candidates.find(c => c.report_id)?.report_id;
      $("dossier-edition").dataset.report = rid;
      $("dossier-edition").replaceChildren(el("option", {value: "", text: "ยังไม่เลือก"}),
        ...res.conflict.map(c => el("option", {value: c.edition, text: `${rid} ฉบับที่ ${c.edition} (ร้อยละ ${c.value})`})));
    }
    edWrap.hidden = !res.conflict && !Object.keys(snap.inputs.edition_choice || {}).length;
    $("dossier-incoming").value = snap.inputs.incoming_doc_id;
    $("dossier-branch").value = snap.claim_branch;
    for (const box of $("dossier-attachments").querySelectorAll("input")) box.checked = snap.inputs.attachments.includes(box.value);
    $("dossier-result").replaceChildren(
      el("p", {}, el("strong", {text: `ฉบับที่ ${snap.seq}`}), ` · ${snap.label || ""} · ทักษะ ${snap.identity.skill.version} · ` +
        `เอกสารแนบ ${snap.inputs.attachments.length} รายการ`),
      incomingSection(), patentSection(), regulatorySection(), letterSection(), skillSection(), replaySection());
    $("dossier-result").hidden = false;
    $("dossier-nav").hidden = false;
    $("dossier-snapshots").value = snap.snapshot_id;
  }

  async function diff() {
    const a = $("dossier-compare").value, b = $("dossier-snapshots").value;
    await run("กำลังเทียบ", async () => {
      const d = await api("GET", `/api/dossier/diff/${a}/${b}`);
      $("dossier-diff-result").replaceChildren(
        el("h3", {text: "รายการที่เปลี่ยน"}),
        el("ul", {}, ...d.changed_items.map(c => el("li", {text: `${c.item_id}: ${c.before ? STATUS[c.before.status] + " · " + c.before.statement : "(ไม่มี)"} → ` +
          `${c.after ? STATUS[c.after.status] + " · " + c.after.statement : "(ไม่มี)"}`}))),
        el("h3", {text: "ประโยคในหนังสือที่เปลี่ยน"}),
        el("ul", {}, ...d.letter_changes.map(c => el("li", {}, el("del", {text: c.before || "(ไม่มี)"}), " → ", el("ins", {text: c.after || "(ไม่มี)"})))),
        el("p", {class: "muted", text: `รายการที่เหมือนเดิมทุกไบต์ ${d.unchanged_items.length} รายการ: ${d.unchanged_items.join(", ")}`}));
    });
  }

  function init() {
    $("dossier-form").addEventListener("submit", (e) => {
      e.preventDefault();
      run("กำลังสร้างแฟ้ม", async () => {
        const s = await api("POST", "/api/dossier/snapshots", inputs());
        await refresh(); await load(s.snapshot_id);
      });
    });
    $("dossier-reopen").addEventListener("submit", (e) => { e.preventDefault(); run("กำลังเปิดฉบับเดิม", () => load($("dossier-snapshots").value)); });
    $("dossier-diff").addEventListener("click", diff);
    document.addEventListener("keydown", (e) => { if (e.key === "Escape") $("dossier-evidence").hidden = true; });
  }

  return {init, open};
})();
