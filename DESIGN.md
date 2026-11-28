# Design

Visual system for Market Window Dossier. The owner chose direction "F2, Regulatory agency" on 28 November 2026, after rejecting three editorial or novel directions (A Journal, B Technical plate, C Monograph) and one institutional variant (F1). The design is modelled on formal public-sector and regulatory sites (GOV.UK and the USWDS for plain language and accessible tokens, the EMA for navigation by workflow stage). Product truth lives in [PRODUCT.md](PRODUCT.md). The approved sample is `docs/product/design/F2-agency.html` with its screenshot.

## Principles

- Formal and plain. Use direct wording and no buzzwords: say what the thing does, with numbers and dates.
- **All headings, navigation, labels and buttons are in English.** Body content (statements, descriptions, checklist items, notes) switches between Thai and English with a TH/EN toggle. Thai is the default content language.
- One task per screen region. Use tables and label/value lists for facts, not decorative cards.
- The "Decision support only, not legal advice" notice is always visible on the landing page and the app.

## Tokens

| Token | Value | Use |
|---|---|---|
| `--navy` | #0b2545 | Top bar, primary buttons, headings |
| `--navy-2` | #13315c | Secondary bar (workflow-stage navigation) |
| `--ink` | #1d2433 | Body text |
| `--muted` | #5b6474 | Secondary text, labels |
| `--line` | #d5dae1 | Borders and rules |
| `--page` | #f3f5f8 | Page background |
| `--surface` | #ffffff | Panels |
| `--link` | #0b5cad | Links, selected-row indicator |
| `--green` / `--green-bg` | #1d6b3a / #e6f3ea | Status "known" |
| `--amber` / `--amber-bg` | #8a5a00 / #fff3d6 | Status "verify", the notice |
| `--neutral-bg` | #eceff3 | Status "assumption", neutral chips |
| `--red` | #b42318 | Errors and a missed event only |

- **Radius and depth.** Radius is 3 px on controls and 4 px on panels. Panels have 1 px borders; there are no decorative shadows. The focus ring is 2 px `--link` with a 2 px offset.
- **Type.** English headings and UI use Source Sans 3 (600/700). Thai content uses Noto Sans Thai (400/500/600). Numbers are tabular. Fonts are self-hosted (SIL OFL), with no CDN at runtime.
- **Scale.** Page H1 is 48 px on the landing page and 36 px in the app. Section H2 is 16–20 px semibold. Body text is 16–17 px with line height 1.6, and table text is 15 px.
- **Status tags** are small rectangular tags (3 px radius): known, verify, assumption, not applicable. Their text follows the content language.
- **Icons** are drawn SVG line icons (2 px stroke) from one set. Never use Unicode glyphs or emoji.

## Layout

- **Landing page.**
  - Navy top bar: wordmark, then Overview, Method, Evidence, Download, then the TH/EN toggle.
  - Secondary navy-2 bar organised by workflow stage: Before development, Patent review, Thailand and ASEAN, Accuracy testing.
  - Hero: an H1 and a plain lead on the left; an "Evidence summary" panel on the right, as a label/value table of real figures.
  - Three columns of plain explanations, then the amber "Decision support only" notice.
- **App.** Navy top bar (Queue, Dossiers, Sources, Settings, then TH/EN), on three columns:
  1. A "Review queue" panel with horizon and as-of filters, a ranked table and a "Review capacity" divider.
  2. A "Dossier" panel with breadcrumb, H1, chips, tabs (Decision summary, Market window, Competition, Patents, Thailand and ASEAN, FTO hand-off, References), a stats row and a statements table with Status and Source columns.
  3. A "Sources" panel with numbered entries: issuer, edition, locator and hash.
- **Desktop GUI (Tauri).** The same app in a native window at a minimum of 1280×800. Keyboard shortcuts for queue navigation; no browser chrome.
