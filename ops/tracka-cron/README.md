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

An accepted dispatch confirms GitHub queued the request. The Worker keeps retrying while a result is absent, including after an Actions failure. At either horizon the workflow publishes the results, checksum, FDA manifest, draws and report under `track-a-<12 or 24>m-<Zenodo record ID>-<freeze SHA-256>`. The release notes pin the four content files. After verifying the assets and every available publication witness, the workflow writes those digests and the scored marker to the issue. A retry after an interrupted issue write recovers the first release from its notes. The Worker sends only the horizon. Actions artifacts expire after 90 days. The first 24-month aggregate, including the safety fields, and its pinned assets remain in the release. [GitHub CLI release publication](https://cli.github.com/manual/gh_release_create).

At 24 months the workflow recovers a verified first 24-month publication when present. For the first 24-month calculation it uses the verified 12-month publication or records `REVISED_VINTAGE` after confirming the 12-month release and tag are absent. A surviving tag, missing publication digest or integrity disagreement requires recovery. The 24-month job retains the descriptive run artifact and withholds the canonical publication when H3 is `UNVERIFIED_INPUT`. Recover the original bytes and compare them with the publication digests. GitHub access and transport failures prompt another attempt. [Scoring and recovery guide](../../docs/loe-bench/HOW-TO-SCORE-TRACK-A.md).

Local Worker checks use mock GitHub responses through `npm test`. A **Score Track A** dispatch with `synthetic=true` runs only the fictional readout fixtures. That job has read-only permissions and uses no live FDA inputs or publication steps. The deploy steps require the owner account. [Worker receipt](../../docs/loe-bench/receipts/TRACKA-AUTO.md) · [Readout implementation receipt](../../docs/loe-bench/receipts/TRACKA-READOUT2.md).
