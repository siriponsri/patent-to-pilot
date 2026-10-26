# Luna W1-W8 closeout

Status: **READY_FOR_PEPO_AUDIT**
Source revision: `612483f` (`main`) plus uncommitted working-tree artifacts; no clean-tree or remote claim
Writer: Luna; audit owner: Pepo
Date: 26 ตุลาคม 2026

## Executive result

The requested offline work and the explicitly approved fresh paired revalidation are complete. Phase A history is preserved byte-for-byte. The new pair used only the two approved synthetic echo payloads, one Gemini attempt and one GPT attempt, zero retries, and the cumulative actual debit remained USD 0.0001464 including the historical USD 0.0000732, below the USD 0.60 cap.

W2 remains **BLOCKED** because the previously denied external preflight file was not reread and no ACL change was approved. Scientific pilot, held-out evaluation, product UI/API implementation, Gemini-only recovery, cross-task learning, Phase B and G01-G22 full completion remain **NOT_RUN**.

## W1-W8 status register

| Work package | Status | Evidence |
|---|---|---|
| W1 Reconcile repo and baseline | **PASS** | `docs/provider-pilot/W1_RECONCILIATION.json`; old journal/marker/approval hashes match; separate pair state was absent before run; old lock probe passed |
| W2 Access blocker | **BLOCKED** | Exact denied path and prior descriptor facts are preserved in the handoff; no content retry, elevation, ACL edit, copy, or substitute evidence |
| W3 Paired identity/routing/ledger | **PASS** | `src/patent_to_pilot/providers/paired.py`, plan/approval, pair journal; strict identity, route, reservation, budget and stop gates exercised by tests and live pair |
| W4 Offline regression/replay | **PASS** | Affected suite `107 passed`; pair-only tests `10 passed`; compile and whitespace checks passed; JUnit reports under `docs/provider-pilot/` |
| W5 Fresh paired revalidation | **PASS** | Live `PAIR_COMPLETE`; exactly two settled rows, one per model, retries `0`, no unknown pending, actual pair debit USD 0.0000732 |
| W6 Research pilot readiness | **PASS** | `docs/provider-pilot/PAIRED_REVALIDATION_READINESS.md`; engineering echo separated from scientific pilot, same-input matrix and next gates recorded |
| W7 Claude UI/API brief | **PASS** | `docs/product/CLAUDE_UI_HANDOFF_TH.md`; real Pydantic/provider fields mapped and proposed view model semantics labeled |
| W8 Pepo evidence package | **PASS** | This report plus `docs/handoff/LUNA_CLOSEOUT_EVIDENCE.json`; one focused audit remains |

## PASS / FAIL / BLOCKED / NOT_RUN separation

- **PASS:** W1, W3, W4, W5, W6 preparation, W7 preparation, W8 package assembly; Phase A historical integrity; fresh pair terminal accounting.
- **FAIL (repaired, no provider attempt):** first live CLI invocation hit a local context-manager `TypeError` before transport construction; pair journal had zero attempts and zero debit. The wrapper was corrected, pair-only tests became `10 passed`, and the one approved live pair was then dispatched once.
- **BLOCKED:** W2 access repair for `C:\Users\User\Documents\Codex\2026-10-24\task-6\gemini-recovery-tests-6z1vrhbe\preflight.json`; no new owner security approval or effective access change was supplied.
- **NOT_RUN:** Gemini-only recovery; any retry; third attempt; Phase B; scientific/main/held-out study; G12 cross-task learning; full UI/API/FastAPI; GPU/RunPod; publication/deploy/push; full G01-G22 closure.

## Historical Phase A

- Attempts: `2`
- Status: `PHASE_FAILED`
- API-reported debit: **USD 0.0000732**
- Gemini historical row: model-drift failure with USD 0.0000132; original identity cause remains unknown because the old row predates identity capture.
- GPT historical row: exact `openai/gpt-4.1-mini` / `OpenAI` identity and schema success with USD 0.0000600.
- Historical journal: `results/development/provider-pilot/live.sqlite3`
- Historical journal SHA256: `a10f81d79a37a39b53547cb4417437499aa81b69a896048f352ff3a8ba8e9d36`
- Historical marker SHA256: `d4f14044b31fcba12da30f9209fde1333afb2a6ee768d7f57494aee5fb4720f7`
- Historical approval SHA256: `be94ee6db17384d308188cf61072d9eff8f8e39f4ed819e67c831445f1110b0f`
- No old journal, marker, approval or Phase A plan was modified.

## Fresh pair

- Plan: `configs/provider-paired-revalidation-plan.json`
- Approval: `results/development/provider-pilot/approval-paired-revalidation-1.json`
- State: `results/development/provider-pilot/paired-revalidation-1.sqlite3`
- Marker: `results/development/provider-pilot/paired-revalidation-1.sqlite3.started.json`
- Plan SHA256: `36a54d85884094a3e4a04c2ca149e8c3eb2b568af194446718751965e08f1ab2`
- Live terminal status: `PAIR_COMPLETE`
- Dispatched attempts: `2`; retries: `0`; duplicate requests: `0`; unknown pending: `0`
- Gemini: requested/reported model `google/gemini-2.5-flash-lite`; broker `openrouter`; requested/reported upstream `google-ai-studio` / `Google AI Studio`; usage `32 input + 25 output`; actual debit **USD 0.0000132**; schema valid.
- GPT: requested/reported model `openai/gpt-4.1-mini`; broker `openrouter`; requested/reported upstream `openai` / `OpenAI`; usage `86 input + 16 output`; actual debit **USD 0.0000600**; schema valid.
- Payload SHA256: Gemini `f31be6bc37b4c522b7bfa38a7e79d17e0000e9e129ee3ad332a90f1133fcadf9`; GPT `0696c7d66be448776810d1981129ffcf9849388330ec383e6a359bf8722e22ba`.
- Reservation bounds: Gemini USD 0.1054576; GPT USD 0.4214304; new-pair reserved total USD 0.5268880; cumulative reservation including history USD 0.5269612.
- Actual cumulative total including history: **USD 0.0001464**, below cap USD 0.60.
- The funded OpenRouter USD 10 balance was not used as authorization or as the project budget.

## Checks and commands

```text
rtk proxy python -B -m pytest -p no:cacheprovider tests/test_provider_recovery.py tests/test_provider_identity.py tests/test_provider_adapter.py tests/test_provider_pilot.py tests/test_provider_env_file.py tests/test_g11_adaptation.py tests/test_provider_paired.py --basetemp "$env:TEMP\ptp-provider-suite-final" --junitxml docs/provider-pilot/provider-suite-results.xml
exit code 0; 107 passed

rtk proxy python -B -m pytest -p no:cacheprovider tests/test_provider_paired.py --basetemp "$env:TEMP\ptp-paired-tests-3" --junitxml docs/provider-pilot/paired-test-results.xml
exit code 0; 10 passed

rtk proxy python -B -m compileall -q src/patent_to_pilot
exit code 0

rtk git diff --check
exit code 0

rtk proxy python -B scripts/run_provider_pair.py --live --env-file .env --approval results/development/provider-pilot/approval-paired-revalidation-1.json --state results/development/provider-pilot/paired-revalidation-1.sqlite3
exit code 0; terminal status PAIR_COMPLETE
```

Public endpoint capability/pricing metadata was refreshed without credentials and matched the plan for both pinned provider tags, context lengths, prices and required parameters. Receipt: `docs/provider-pilot/paired-public-preflight-2026-10-26.json`.

## Limits and Pepo audit focus

- The live pair is a transport/identity/schema/accounting echo, not a scientific evaluation or R&D quality result.
- W2 access denial is intentionally visible; it is not “fixed” by an agent-side account being able to inspect other metadata.
- Public endpoint metadata does not prove account spending limits, tokenizer guarantees, upstream retention, clinical validity, legal status, patentability or FTO.
- The repository remains an uncommitted working tree with broad pre-existing artifacts; no commit/push/deploy was performed.
- Audit the exact candidate files and hashes in `docs/handoff/LUNA_CLOSEOUT_EVIDENCE.json` once. Any further live call needs a new explicit owner scope.
