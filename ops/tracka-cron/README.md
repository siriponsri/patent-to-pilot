# Track A cron

This scheduled Cloudflare Worker checks for the canonical 12- and 24-month readout issues and calls **Score Track A** when a mature readout is still missing. It has no public HTTP route. The Worker dispatches from 01:13 UTC on 27 November 2027 and 27 November 2028 respectively, and retries missing horizons daily. It re-enables a workflow marked `disabled_inactivity`. A maintainer's manual disable remains in effect. [Cloudflare Cron Triggers](https://developers.cloudflare.com/workers/configuration/cron-triggers/) · [GitHub workflow REST endpoints](https://docs.github.com/en/rest/actions/workflows?apiVersion=2026-03-10).

The Worker checks both open and closed issues. Only a canonical `SCORED` marker from GitHub Actions or a repository maintainer stops dispatches. A `PENDING` or `BLOCKED_SOURCE` issue leaves that horizon due. [Public scoring guide](../../docs/loe-bench/HOW-TO-SCORE-TRACK-A.md).

## Owner setup

1. After Planner integration to the default branch, set `TRACKA_RELEASE_DOI` to `10.5281/zenodo.24629100` and `TRACKA_FREEZE_SHA256` to `8a78b318a8791649edbee2daab12a4db2d8aa72e33758cd27ae2145a9114c38d` in repository Actions variables. The workflow runs the integrated readout code at its Git revision. Set `GITHUB_REPOSITORY` to `siriponsri/patent-to-pilot` and confirm that `GITHUB_REF` names its default branch in [wrangler.toml](wrangler.toml). Enable Actions and Issues and allow the workflow job `contents: write` for the release and `issues: write` for the record. [Zenodo version record](https://doi.org/10.5281/zenodo.24629100).
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

An accepted dispatch confirms GitHub queued the request. The Worker keeps retrying while a result is absent, including after an Actions failure. The 12-month workflow first publishes the results, SHA-256, FDA manifest, report and draws to a release scoped to the Zenodo record and freeze digest. Then it writes the canonical scored marker and digests to the issue. A retry after publication verifies and links the existing release. The 24-month run discovers and verifies the first result and its FDA manifest from the release. The Worker continues to send only the horizon. The full Actions artifacts expire after 90 days. The release assets have no Actions retention timer. [GitHub CLI release publication](https://cli.github.com/manual/gh_release_create).

When the first archive is missing or fails verification, the 24-month report labels H3 `REVISED_VINTAGE` and gives the available original date and the revised FDA edition and scoring date. Keep any original report. If a first-publication tag survives a release or asset failure, recover the original bytes and check them against the issue digest. HTTP access and transport failures prompt another attempt. [Scoring and recovery guide](../../docs/loe-bench/HOW-TO-SCORE-TRACK-A.md).

Local Worker checks use mock GitHub responses through `npm test`. A **Score Track A** dispatch with `synthetic=true` runs only the fictional readout fixtures. That job has read-only permissions and uses no live FDA inputs or publication steps. The deploy steps require the owner account. [Worker receipt](../../docs/loe-bench/receipts/TRACKA-AUTO.md) · [Readout implementation receipt](../../docs/loe-bench/receipts/TRACKA-READOUT2.md).
