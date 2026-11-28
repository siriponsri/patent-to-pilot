# Track A cron

This scheduled Cloudflare Worker checks for the canonical 12- and 24-month readout issues and calls **Score Track A** when a mature readout is still missing. When both horizons are due it requests the earlier one first. It has no public HTTP route. The Worker dispatches from 01:13 UTC on 27 November 2027 and 27 November 2028 respectively, and retries missing horizons daily. It re-enables a workflow marked `disabled_inactivity`. A maintainer's manual disable remains in effect. [Cloudflare Cron Triggers](https://developers.cloudflare.com/workers/configuration/cron-triggers/) · [GitHub workflow REST endpoints](https://docs.github.com/en/rest/actions/workflows?apiVersion=2026-03-10).

The Worker checks both open and closed issues. Only a canonical `SCORED` marker from GitHub Actions or a repository maintainer stops dispatches. A `PENDING` or `BLOCKED_SOURCE` issue leaves that horizon due. [Public scoring guide](../../docs/loe-bench/HOW-TO-SCORE-TRACK-A.md).

## Owner setup

1. After Planner integration to the default branch, set `TRACKA_RELEASE_DOI` to `10.5281/zenodo.24629100` and `TRACKA_FREEZE_SHA256` to `8a78b318a8791649edbee2daab12a4db2d8aa72e33758cd27ae2145a9114c38d` in repository Actions variables. The workflow runs the integrated readout code at its Git revision. Set `GITHUB_REPOSITORY` to `siriponsri/patent-to-pilot` and confirm that `GITHUB_REF` names its default branch in [wrangler.toml](wrangler.toml). Enable Actions and Issues and allow the workflow job `contents: write` for the release, `issues: write` for the record, and `id-token: write` plus `attestations: write` for signing. [Zenodo version record](https://doi.org/10.5281/zenodo.24629100).
2. In GitHub Settings → Developer settings → Personal access tokens → Fine-grained tokens, select the repository owner as the resource owner and grant access to **Only select repositories → patent-to-pilot**. Grant the primary token **Actions: Read and write**, **Contents: Read-only**, and **Issues: Read and write**. GitHub adds read-only Metadata. Choose the longest expiring lifetime allowed by the account and record the actual expiry in `GITHUB_TOKEN_EXPIRES_ON` as `YYYY-MM-DD`. Create a second token restricted to the same repository with **Issues: Read and write** only, plus GitHub's automatic Metadata access. Stagger expiry dates so the second token can report the first token's loss of access. Allow about 10 minutes. [GitHub token creation and expiry](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens).
3. From `ops/tracka-cron/`, run the tests and issue the following commands from your Cloudflare account. Paste each token at its corresponding secret prompt. Allow 10–15 minutes of operator time. Cloudflare may take up to 15 minutes more to propagate trigger changes. [Worker secrets](https://developers.cloudflare.com/workers/configuration/secrets/) · [Trigger propagation](https://developers.cloudflare.com/workers/configuration/cron-triggers/).

   ```sh
   npm test
   npx wrangler@4.169.0 deploy --dry-run
   npx wrangler@4.169.0 deploy
   npx wrangler@4.169.0 secret put GITHUB_TOKEN
   npx wrangler@4.169.0 secret put GITHUB_ALERT_TOKEN
   ```

4. Confirm both triggers in the dashboard. Watch the repository for issues and check **Workers & Pages → tracka-readouts → Observability** after the first monthly trigger. Allow 5 minutes for this check. Import [track-a-readouts.ics](../../docs/loe-bench/reminders/track-a-readouts.ics) into an Asia/Bangkok calendar, and confirm the two maturity dates and the 1 November recurrence.

## Renew and recover

The monthly check runs at 01:23 UTC on the first day. It probes primary workflow access and opens or updates **Track A automation needs attention** within 45 days of the configured expiry. If the primary is invalid, the alert token posts the issue. If both tokens fail or Issues is unavailable, the Worker records a failed cron invocation in Cloudflare. The read-only probe checks authentication and workflow access. The first actual dispatch verifies write permission.

Replace each secret with `npx wrangler@4.169.0 secret put` before it expires. Update `GITHUB_TOKEN_EXPIRES_ON` in the local configuration and redeploy after each primary renewal. Set a renewal reminder for both tokens and verify the following monthly run before closing the warning issue. Keep each token value in its Cloudflare secret binding.

An accepted dispatch confirms GitHub queued the request. The workflow runs blind FDA capture before scoring. It stages the first admissible bytes in a draft, verifies their Actions attestation and publishes the capture. It then scores the preserved bytes and attests the result. A retry resumes the same capture or result draft. The Worker sends only the horizon. The capture and result releases hold the durable bytes. The optional run artifact expires after 90 days.

The automatic capture window closes seven UTC days after maturity. Later dispatches can verify or resume an existing capture. If required continuity is missing, the workflow records `UNRESOLVED_CONTINUITY`, and any available estimates are descriptive. For known loss, set the repository Actions variable `TRACKA_CONTINUITY_HOLD=true` while establishing the first publication independently. [Scoring and recovery guide](../../docs/loe-bench/HOW-TO-SCORE-TRACK-A.md).

Local Worker checks use mock GitHub responses through `npm test`. A branch dispatch with `synthetic=true` tests fictional readouts and signs only two run-specific text files. It skips the production jobs. The deploy steps require the owner account. [Worker receipt](../../docs/loe-bench/receipts/TRACKA-AUTO.md) · [Readout protocol](../../docs/loe-bench/receipts/TRACKA-READOUT5-PROTOCOL.md).
