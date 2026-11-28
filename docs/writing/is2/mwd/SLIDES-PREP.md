# IS2 slide preparation notes

These are the main planner's notes from 28 November 2026. Claude designs and builds the IS2 slides (owner rule). The owner reads the report and the short paper first, and slide work starts after that.

## Owner brief

- The talk is in **Thai**, told as a **story through animation**, in 15 minutes with 10 minutes of questions.
- The style reference is the IS1 deck by Claude at `C:\Users\User\Desktop\myDegree\IS\IS_1\presentation-is-shortpaper\hf-deck\v3`.
- The second reference is the Paper 53 deck at `C:\Users\User\Desktop\myDegree\IS\IS_1\presentation-isainlp2026\output` (v5 pptx and handout).

## IS1 v3 deck (HyperFrames)

- **Stack.** HyperFrames 0.9.33, one GSAP timeline per section, with the build in `tools/build.cjs` (`src/scenes`, `src/timeline`, `src/appendix.html`). Frames are captured with puppeteer (`tools/capture.cjs`). The script source is `script/*.cjs`. A backup PDF holds every click state, and the deck is deployed to Vercel (is1-presentation).
- **Structure.** 26 main slides, a thank-you slide and appendix A0–A26. A 7-segment section bar and RQ chips (RQ1 ✓, RQ2) run on every slide, the source line sits at the bottom right, and no slide needs more than 2 clicks. Multi-step sequences play automatically.
- **Look.** White background, navy and blue structure, orange as the single accent for the key item, with document glyph "swarms" (icons of 692 queries) used as data visuals.
- **Story moves.** It opens with a concrete case (surgical stapler 2013 vs DC motor 1982) and explains AI search through a metaphor ("basket, then table"). Prior work is placed on a pipeline grid whose empty cell becomes the RQ. The method is shown as "everything frozen except one thing", the results as "three suspects, checked in order", and the close as one summary image.
- **Controls.** Clicker support, F/B/G/A/R/P keys and the appendix jump.

## Paper 53 v5 deck (pptx)

- 17 slides plus appendix B1–B3, in a blue (#1f4fa3-like) title band style with orange highlights and English text.
- It moves from objective to RQ to method (a frozen pipeline) to results 1–3 (exposure, change, aggregate) to the conclusion. Large-number callouts (435 of 692) sit beside square-grid visuals, and the source footer sits at the bottom left.

## Skills ready

These are installed in `~/.claude/skills`: `hyperframes`, `hyperframes-cli`, `hyperframes-registry`, `slideshow`, `gsap-*`, `media-use`, `academic-figures`, `thai-natural-writing`, `kmitl-is-paper`, `pptx-motion-lite`, `officecli-pptx`.

## Proposed IS2 story (draft; to be revised after the owner reads)

1. A pharma team must choose molecules years before launch. Two pains: FTO evaluators are scarce, and the market can be gone at launch.
2. Bridge from IS1: improving the reranker did not help because the target never reached the pool. Lesson: fix what enters review first.
3. LOE-Bench: a time-machine benchmark with as-of evidence, a seal and preregistration.
4. The review queue: 1 in 5 capacity, with an animation of drugs entering the queue.
5. The result: H1 passed (+20.37 pp), H2 failed (the graph adds no confirmed value over M1), and the LLM fell far below.
6. The dossier: traceable claims, with Thai status unknown and routed to a specialist.
7. Prospective Track A, the prior-method arms and next steps.

Reuse the IS1 HyperFrames toolchain (build, capture, backup PDF, script check) with Thai text in Noto Sans Thai or Sarabun.
