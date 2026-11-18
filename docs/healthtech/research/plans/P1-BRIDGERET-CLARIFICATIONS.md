# P1-BridgeRet pre-declaration clarifications (logged before the affected run)

| # | Date (UTC) | Item | Clarification | Why | Statistical impact |
|---|---|---|---|---|---|
| CL-1 | 2026-11-18 17:30 | Z-PatEmbed-large prompts (optional comparator C3) | Use the developer's `retrieval_MIXED` pair: query `"encode query for mixed document retrieval: "`, document `"encode document for mixed retrieval: "`; mean pooling; cap 512 BERT tokens counted with the prompt | PatenTEB ships several task prompts; examiner citations mix IN and OUT documents, so MIXED is the general prior-art pair; choosing `retrieval_OUT` would tailor the comparator to the primary endpoint after seeing other DEV numbers | none on C1/C2; fixes C3's comparator before any PatEmbed number exists |
| CL-2 | 2026-11-18 17:30 | Z-Qwen3 batch/memory | batch 8, memory cap 0.15, expandable segments after an OOM at batch 32 (cap 0.12) | engineering only; same model, prompt, text | none |
