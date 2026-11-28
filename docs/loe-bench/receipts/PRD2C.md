# PRD2C | Market Window Dossier time-machine demo UI

## Result

**PASS for UI delivery on FIXTURE data.** The static demo in [`product/demo/`](../../../product/demo/README.md) implements the planner's design: top bar, 360 px time-machine rail, seven-tab dossier, claim state and kind chips, a sources drawer, an FTO hand-off checklist, a reveal panel, a footer disclaimer, a dark theme, a layout below 900 px, keyboard support and a print stylesheet. It runs from `file://` through a generated `data.bundle.js` and from any static host. It uses plain HTML, CSS and JavaScript with no build step, dependencies or runtime CDN.

All data shown are **FIXTURE** data: 6 queues, 36 dossiers and 25 invented molecule names per queue. Real PRD1 data are not yet available because `loe/PRD1` had no product files on the remote at the start of the card. The fixtures make no claim about forecast skill or real outcomes.

| Screenshot (headless Chrome, inspected) | State |
|---|---|
| [desktop-th.png](../../../product/demo/screenshots/desktop-th.png) | 1440×1000, Thai, 12 months, cutoff 2013, Talcoxib, Decision tab |
| [desktop-en.png](../../../product/demo/screenshots/desktop-en.png) | Same state in English; all seven tabs fit at 1440 px |
| [reveal-th.png](../../../product/demo/screenshots/reveal-th.png) | Reveal state: first final ANDA date, capture "2 of 8 (M3) vs 3 (B1)", captured and missed events marked in the rail |
| [mobile-th.png](../../../product/demo/screenshots/mobile-th.png) | 390×844, rail collapsed into the top drawer toggle |
| [mobile-rail-en.png](../../../product/demo/screenshots/mobile-rail-en.png) | 390×844, drawer open, 24 months, cutoff 2014 (the stepper's + button is disabled at the last index year) |
| [sources-drawer-en.png](../../../product/demo/screenshots/sources-drawer-en.png) | Sources drawer opened from a citation, with the cited source highlighted and a shortened SHA-256 with a copy button |
| [dark-en.png](../../../product/demo/screenshots/dark-en.png) | `prefers-color-scheme: dark`, Thailand & ASEAN tab with known, verify and n/a chips |

## Evidence

- **Files.** `index.html`, `styles.css`, `app.js` (vanilla ES5-compatible JS), `bundle.py` and `fixtures/make_fixtures.py` (standard library, seed 20261128). The fixture output is `fixtures/index.json`, `fixtures/queues/*.json` and `fixtures/dossiers/*.json`. The `data.bundle.js` file is 500,595 bytes and contains 42 bundled files. The logo is copied from `docs/assets/logo.svg`.
- **Data contract.** The app reads an index (`mwd.index.v1`) that lists queues per cutoff and horizon and dossiers per molecule, cutoff and horizon. Paths are relative to the index. On HTTP the app tries `data/index.json`, then `fixtures/index.json`, then the bundle; on `file://` it uses the bundle. This card leaves `product/demo/data/` empty so PRD1 can write there without a conflict. Queue rows are sorted by `m3_p` inside the app. Missing optional fields (`queue_size`, `capture`, `next_action_*`, `decisive_claim`) fall back as described in the README.
- **Checks run.** `node -e "new Function(...)"` parsed `app.js` without error. Headless Chrome rendered all seven screenshots above, and each image was opened and inspected. Chrome `--print-to-pdf` of the English Talcoxib dossier produced 6 pages. Text extraction with pypdf 6.21.4 found all seven section headings, the evaluator checklist, the first source title and the footer disclaimer. It found no rail text ("Time machine", queue names) and no reveal button. Mobile screenshots were taken through a 390 px iframe harness, because headless Chrome lays out narrow windows wider than the requested size.
- **Contrast (WCAG 2.x ratio, computed from the tokens).** Light: ink on paper 13.28, muted on paper 6.20, accent on white 5.47, white on accent chip 5.47, warn on white 5.02, warn on paper 4.68, miss on paper 7.47, grey bar on white 3.22 (graphic, 3:1 rule). Dark: ink 15.26, muted 7.80, accent 8.94, accent-ink on accent 9.88, warn 7.74, miss 6.83. All text pairs meet AA at 4.5:1.
- **Accessibility features.** The page includes a skip link, a visible 2 px accent focus ring, a radiogroup horizon control with arrow keys, and a tablist with arrow, Home and End keys and roving tabindex. Queue rows are buttons with full aria labels, and the capacity divider uses `role=separator`. The drawer is a modal dialog with a focus trap; Esc closes it and focus returns to the opener. The checklist uses real labelled checkboxes. The reveal panel uses `role=status`. `lang` switches between `th` and `en`, and both the 250 ms reveal fade and the drawer slide respect `prefers-reduced-motion`.
- **Product references (external, no head-to-head measured).** The seven-part hierarchy and the "FTO undetermined" cover wording follow the WIPO *Guidelines for Preparing Patent Landscape Reports* (2015) and the WIPO FTO guide (pub. 1062), as cited in the [D41 plan](../PLAN.md#d41-market-window-dossier-owner-approved-28-november-2026). This card implements that report structure and measures nothing against commercial generic-intelligence tools.

## Design decisions and limitations

- **Thai type size changed from the spec.** The design asks for Thai at 1.25×. TH Sarabun New is installed on this machine, and at 1.25× Thai glyphs still looked clearly smaller than Segoe UI on mixed Thai/Latin lines (see the first-pass screenshot comparison in this session). The Sarabun faces now render at 1.4× through `@font-face size-adjust`, limited by `unicode-range` to Thai code points so Latin text and numbers stay in Segoe UI at 1×. The Leelawadee UI fallback stays at 1×. The planner can restore 1.25× by editing one value in `styles.css`.
- **Fixture names are invented** (for example Talcoxib, Zentrapine) so that synthetic outcome dates are never attached to real drugs. Companies, digests and dates are invented as well. Source URLs point to the real public pages of each issuer.
- **Added beyond the spec:** URL-hash state (`lang`, `h`, `c`, `m`, `tab`, `reveal`, `cite`) for deep links and screenshots, a ● marker for queue rows that have a dossier, a "no dossier yet" panel for the other rows, and orange dots on tabs that contain claims to verify. After a reveal, events outside the queue are marked in `--miss`, which is the only place that colour appears.
- **Not verified:** screen-reader testing (NVDA or VoiceOver), Firefox, Safari, an axe audit, and real GitHub Pages hosting (only `file://` was exercised). Clipboard copy uses `navigator.clipboard` on secure origins and falls back to `execCommand` on `file://`; it was not exercised headlessly.
- One headless Chrome screenshot process (the drawer shot) wrote its PNG but did not exit. I stopped it; it was a process from this session's scratch profile.

## Next action

When PRD1 pushes `product/demo/data/index.json`, run `python product/demo/bundle.py`, re-take the four core screenshots on real data, and check how the decision summary reads PRD1's actual decision-section fields. The planner reviews this UI, decides whether to keep the Thai 1.4× size, and integrates `loe/PRD2C`. The planner owns the lane HANDOFF and MEMORY updates at integration.
