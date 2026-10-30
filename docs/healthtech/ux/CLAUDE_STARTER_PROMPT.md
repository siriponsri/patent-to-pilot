# Copyable bounded Claude Code goal

Paste this after opening the repository and granting only the intended local frontend scope. This is a proposed implementation instruction; no Claude session has been started by the documentation task.

```text
Implement the Patent-to-Pilot HealthTech local UX/UI package.

Read current AGENTS.md, GOAL.md sections 0–4 and HT-G3/HT-G7, PLAN.md
(HT-W13/HT-W16/HT-W19 and relevant contracts), README.md, progress and
next actions. Then read docs/healthtech/ux/README.md and documents 01–05.
Root HealthTech scope governs; do not revive pharma-factory or
Transfer-or-Retest workflows.

Before implementation use your own unique claude/healthtech-ux-* branch
in an isolated worktree at the agreed current base. Do not switch the
shared checkout, touch concurrent writers, or push/merge directly to main.
Preserve all dirty/untracked work; no reset/clean/stash. If the UX pack is
untracked, read it in place or copy only that authored pack with hashes.

Build a responsive, accessible TH/EN no-code frontend for named public
device/comparator → brief/source import → dossier/evidence comparison →
exact source inspection → uncertainty notes → local save/version/reopen →
edited TH/EN export and next-information request drafts. Primary personas
are entrepreneurs and MedTech investor analysts; market demand remains
unvalidated. Use the existing formal-light/formal-dark/kmitl-inspired/
ict-inspired theme keys without claiming official institutional branding.

Default implementation ownership: frontend/healthtech-web/** and
docs/healthtech/ux/implementation/**; inspect/reuse any newer frontend stack
and record path mapping before work. Keep backend, scripts, schemas,
provider/attempt/budget journals and governing docs read-only. Do not add
root tooling changes, a backend API, paid inference, live fetches, deployment,
outreach or automatic telemetry. No keys/email/private/patient data required.

Finish independently with labelled authored fixtures and selected-file
adapters; do not wait for G1/G2. Existing HealthTech API is dry-run/mock code,
not an HTTP service. Disable unavailable real start/cancel/resume/team
actions. Completed CLI artifacts can be imported; simulated progress must
remain labelled. Preserve source/raw/canonical IDs, kind codes, revision/hash,
jurisdiction/date and exact field/span locator. Runtime never reads gold.

Keep source facts, reported associations, system inference and unresolved/
unjudged separate. Retrieved candidates are not disclosed links, FTO, medical
or investment conclusions. Never show unknown as zero or synthetic as real.
Current three FDA public cases have patents=[] and zero candidates; say the
run had no patent corpus, not that no patents exist.

Implement browser-local autosave with acknowledged storage scope, atomic
expected-parent conflict handling and recovery JSON. Local UX snapshots
are separate from backend DossierVersion numbers. Audited backend history
can lose concurrent edits and backend Markdown omits user_edits: do not mask
either with success. Build a tested local edited Markdown renderer or mark
that export incomplete and preserve JSON recovery; keep source facts immutable.

Follow documents 02/05 task order and acceptance. Provide actual candidate
tests: import/hash/locator negatives, Thai/emoji code-point spans, save-close-
reopen, two-writer conflicts, denied/quota storage recovery, user note present
in TH/EN exports/reimport, safe source rendering, honest budget/capabilities,
keyboard/responsive/theme review. No fabricated screenshots or borrowed
historical test counts. Mark IMPLEMENTED/SIMULATED/PROPOSED/BLOCKED_LOCAL/
NOT_RUN per feature; no frontend PASS implies scientific or market validation.

Continue reversible local work autonomously. On a local blocker complete
unaffected paths and report exact missing action/target/reason/outcome. Finish
with local runbook, branch/base/candidate, owned diff, story acceptance matrix,
real test/evidence paths, remaining blockers and next action. End ready for
review; no merge or deployment in this task.
```

คำสั่งเริ่มงานสำหรับเจ้าของโครงการ: เปิด Claude Code ที่ repository นี้ แล้ววาง prompt ด้านบน ให้ Claude ทำ frontend ใน branch ของตัวเองจนมีหลักฐานทดสอบพร้อมตรวจ งาน backend, ข้อมูลสิทธิบัตรจริง และผลวิจัยให้คงเป็นงานแยกตามขอบเขตใน handoff
