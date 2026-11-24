# P2-T02 D19 follow-up receipt, P1-DEV

**Runtime state:** PatEmbed upload verified, first launch stopped during transfer setup. Qwen3 NOT_RUN.
Both C1 evaluations are NOT_RUN.
**Protocol:** P2-T02 coverage control `bd30d3f7` with A2 declared in `ffae7a99` and verified implementation
`d30d9d51`. D26 authorizes launch and up to USD 20 inside R2. The local stage is pinned in the
[D19 readiness receipt](P2-T02_D19_readiness.md).

| Model | Pod / region | Hourly price | Start (UTC) | Reservation | Receipt |
|---|---|---|---|---|---|
| PatEmbed | `arm09wy8rok4qk`, Secure A100 SXM 80 GB / US-MD-1 | USD 2.19 compute, up to USD 0.03 disk budget | 2026-11-24 13:47:49 | USD 9.50 | Active |
| Qwen3 | Secure L40S 48 GB / US-MO-1 create returned HTTP 400, account lists no Qwen3 pod | USD 1.09 compute, up to USD 0.03 disk budget | — | USD 8.50 planned | NOT_RUN |

Operational PatEmbed deadline 17:47:49 UTC includes transfers. The in-container timer reported armed for
17:55:49 UTC as a fallback. SSH upload started 13:49:10 UTC. Settlement will record actual disk, compute,
retrieval evidence, termination and any retries here.

Qwen3's planned operating deadline is 7 h 15 min from creation, including transfers. This bounds the combined
reservations at USD 18. The provider's lower-cost qualifying stock appeared after PatEmbed provisioning. Dispatch is
independent of any score, and the frozen A2 gates and endpoints apply unchanged.

## Incidents before any model result

- PatEmbed transfer finished and the remote input manifest passed at 13:54:45 UTC. Attempt 1 reached model
  provisioning and stopped at `models-patembed-pins` at 13:55:20 UTC. The downloader reported that
  `HF_HUB_ENABLE_HF_TRANSFER=1` required the absent optional `hf_transfer` package. Weight hashes had not yet been
  compared. Retry once on the same pod using the normal transfer path with this acceleration toggle set to zero.
  Preserve attempt 1 logs. The pinned files, verification requirements and teardown deadline stay fixed.
- Qwen3's quote was lost during scheduling. The 13:54 UTC create returned HTTP 400, the account enumerated only
  PatEmbed, and a fresh US L40S catalog check returned NONE. No Qwen3 resource exists. Billing remains pending.
