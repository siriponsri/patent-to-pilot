# Diagram and branding notes

These documentation assets were created for Patent-to-Pilot. They are not a product UI, an institutional identity, or a claim of clinical or legal approval.

## Files

- **logo.svg** — original document/branching-route mark and wordmark; self-contained SVG with an accessible title and description.
- **workflow.mmd** — product-vision workflow, also embedded in the repository README.
- **architecture.mmd** — implemented module boundaries and the separate, explicitly gated provider-transport path.
- **logo-preview.png** — a local raster preview, when rendering support is available. The SVG remains the source asset.

## Product workflow: readable alternative

A person supplies a brief and permitted organization sources. Important capability and policy interpretations are reviewed. Source-linked opportunities are compared as routes, with unknowns and conflicts visible. The output is a draft pilot or R&D handoff. A confirmed change leads to a new revision and a traceable diff.

This is the **product vision**. Current implementations cover bounded, deterministic development packets and revision mechanics. The dashed confirmed-feedback memory path is planned product work, not demonstrated cross-task learning.

## Architecture: readable alternative

Public development packets and fictional profiles enter the public adapter and typed staging boundary. The integration and evaluation packages produce bounded deterministic or mocked outputs. Shared checks and diffs feed JSON, Markdown, and HTML artifacts. The typed core manages versioned records and SQLite round-trips where actually exercised.

The provider adapter, attempt ledger, mock transport, and approved OpenRouter echo path form a **separate transport-verification seam**. The diagram deliberately does not draw an implemented general-purpose R&D generation connection between that seam and the comparison runner.

Ingestion, lexical retrieval, and literal extraction utilities exist as separate bounded modules. The fixed span-packet comparison does not exercise the full ingestion/retrieval pipeline. No web UI, FastAPI product service, general organization extractor, or confirmed-feedback memory runtime is depicted as implemented.

## Visual choices and accessibility

- Ink / route: **#123c3b**; secondary text: **#435e57**.
- Accent: **#ba6c28**; paper: **#f5f7f2**.
- System fonts only; no remote fonts, image URLs, scripts, or linked resources in the SVG.
- The document represents source material. The branching route represents explicit alternatives and revision; it is not a certification symbol.
- The opaque paper background preserves wordmark contrast on light and dark README surfaces.
- Mermaid sources carry the technical meaning; the readable alternatives above remain available when a Markdown renderer does not support Mermaid.

## Editing and reuse

Keep the two Mermaid blocks in README.md synchronized with their .mmd source files. Preserve the distinction between implemented, bounded/mock, and planned components. Do not add green badges, affiliations, accuracy claims, or a licence identifier without evidence and authorization.

No separate asset licence is assigned here. These original project assets follow the repository's eventual declared terms; third-party data and documents retain their own terms.
