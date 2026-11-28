import assert from "node:assert/strict";
import test from "node:test";

import { runScheduled } from "../src/worker.mjs";

const sha = "a".repeat(64);
const env = {
  GITHUB_REPOSITORY: "someone/repo",
  GITHUB_REF: "main",
  TRACKA_RELEASE_DOI: "https://doi.org/10.5281/zenodo.123",
  TRACKA_FREEZE_SHA256: sha,
  GITHUB_TOKEN: "primary",
  GITHUB_ALERT_TOKEN: "alert",
  GITHUB_TOKEN_EXPIRES_ON: "2027-11-20",
};
const workflow = "/actions/workflows/score-track-a.yml";
const daily = "13 1 * * *";
const monthly = "23 1 1 * *";

function run(date, cron, fetcher, vars = {}) {
  return runScheduled({ cron, scheduledTime: Date.parse(date) }, { ...env, ...vars }, fetcher);
}

function mock(...expected) {
  const calls = [];
  return {
    async fetch(url, init) {
      const path = url.replace("https://api.github.com/repos/someone/repo", "");
      const [method, route, result, code = 200, headers, token = "primary"] = expected[calls.length] ?? [];
      assert.equal(init.method, method, path);
      assert.equal(path, route);
      assert.equal(init.headers.Authorization, `Bearer ${token}`);
      calls.push(init.body === undefined ? null : JSON.parse(init.body));
      return new Response(code === 204 ? null : JSON.stringify(result), { status: code, headers });
    },
    verify() {
      assert.equal(calls.length, expected.length);
      return calls;
    },
  };
}

function issue(horizon, status, author = "github-actions[bot]", freeze = sha) {
  return {
    number: horizon,
    title: `Track A ${horizon}-month readout`,
    user: { login: author },
    body: `<!-- tracka:${horizon}:${status}:${freeze}:123 -->\n\nReadout report.`,
  };
}

test("prematurity uses UTC and leaves GitHub untouched", async () => {
  const api = mock();
  await run("2027-11-27T00:00:00+07:00", daily, api.fetch);
  api.verify();
});

test("maturity re-enables an inactivity-disabled workflow and dispatches 12 with canonical defaults", async () => {
  const api = mock(
    ["GET", "/issues?state=all&per_page=100&page=1", [issue(12, "BLOCKED_SOURCE")]],
    ["GET", workflow, { state: "disabled_inactivity" }],
    ["PUT", `${workflow}/enable`, null, 204],
    ["POST", `${workflow}/dispatches`, {}, 200],
  );
  await run("2027-11-27", daily, api.fetch);
  assert.deepEqual(api.verify().at(-1), { ref: "main", inputs: { horizon: "12" } });
});

test("searches all issue pages and counts closed scored issues with matching pins", async () => {
  const api = mock(
    ["GET", "/issues?state=all&per_page=100&page=1", [], 200, { Link: '<url>; rel="next"' }],
    ["GET", "/issues?state=all&per_page=100&page=2", [{ ...issue(12, "SCORED"), state: "closed" }]],
    ["GET", workflow, { state: "active" }],
    ["POST", `${workflow}/dispatches`, null, 204],
  );
  await run("2028-11-27", daily, api.fetch);
  assert.deepEqual(api.verify().at(-1), { ref: "main", inputs: { horizon: "24" } });
});

test("ignores PENDING, wrong pins, pull requests and untrusted markers", async () => {
  const api = mock(
    ["GET", "/issues?state=all&per_page=100&page=1", [
      issue(12, "PENDING"),
      issue(12, "SCORED", "commenter"),
      issue(12, "SCORED", "github-actions[bot]", "b".repeat(64)),
      { ...issue(24, "SCORED"), pull_request: {} },
    ]],
    ["GET", workflow, { state: "active" }],
    ["POST", `${workflow}/dispatches`, {}, 500],
    ["POST", `${workflow}/dispatches`, null, 204],
  );
  await assert.rejects(run("2028-12-27", daily, api.fetch), /12 months:.*500/);
  assert.deepEqual(api.verify().slice(-2).map(call => call.inputs.horizon), ["12", "24"]);
});

test("a maintainer can mark a verified public readout as recorded", async () => {
  const api = mock(
    ["GET", "/issues?state=all&per_page=100&page=1", [
      { ...issue(12, "SCORED", "maintainer"), author_association: "OWNER" },
    ]],
  );
  await run("2027-11-28", daily, api.fetch);
  api.verify();
});

test("waits for the earlier horizon dispatch response before requesting the later horizon", async () => {
  const api = mock(
    ["GET", "/issues?state=all&per_page=100&page=1", []],
    ["GET", workflow, { state: "active" }],
    ["POST", `${workflow}/dispatches`, null, 204],
    ["POST", `${workflow}/dispatches`, null, 204],
  );
  let unblock;
  let firstSent;
  const firstPending = new Promise(resolve => { unblock = resolve; });
  const reachedFirst = new Promise(resolve => { firstSent = resolve; });
  const horizons = [];
  const dispatch = run("2028-11-27", daily, async (url, init) => {
    if (init.method === "POST") {
      const { inputs: { horizon } } = JSON.parse(init.body);
      horizons.push(horizon);
      if (horizon === "12") {
        firstSent();
        await firstPending;
      }
    }
    return api.fetch(url, init);
  });
  await reachedFirst;
  try {
    assert.deepEqual(horizons, ["12"]);
  } finally {
    unblock();
    await dispatch;
  }
  assert.deepEqual(horizons, ["12", "24"]);
  api.verify();
});

test("leaves an explicitly disabled workflow disabled", async () => {
  const api = mock(
    ["GET", "/issues?state=all&per_page=100&page=1", []],
    ["GET", workflow, { state: "disabled_manually" }],
  );
  await assert.rejects(run("2027-11-27", daily, api.fetch), /disabled_manually/);
  api.verify();
});

test("missing release pins fail closed at maturity", async () => {
  const api = mock();
  await assert.rejects(run("2027-11-27", daily, api.fetch, { TRACKA_FREEZE_SHA256: "" }), /freeze SHA-256/);
  api.verify();
});

test("monthly check opens a near-expiry issue before scoring starts", async () => {
  const api = mock(
    ["GET", workflow, { state: "active" }],
    ["GET", "/issues?state=open&per_page=100&page=1", []],
    ["POST", "/issues", {}],
  );
  await run("2027-11-01", monthly, api.fetch);
  assert.match(api.verify().at(-1).body, /expire on 2027-11-20 UTC/);
});

test("monthly check reconciles an existing warning and validates the expiry date", async () => {
  const api = mock(
    ["GET", workflow, { state: "active" }],
    ["GET", "/issues?state=open&per_page=100&page=1", [{
      number: 54, title: "Track A automation needs attention", author_association: "OWNER",
      body: "<!-- tracka:token-health -->\nOld warning.",
    }]],
    ["PATCH", "/issues/54", {}],
  );
  await run("2027-11-01", monthly, api.fetch, { GITHUB_TOKEN_EXPIRES_ON: "2027-02-30" });
  assert.match(api.verify().at(-1).body, /missing a valid token expiry/);
});

test("invalid primary reports using the alert-only token and fails the cron visibly", async () => {
  const api = mock(
    ["GET", workflow, {}, 401],
    ["GET", "/issues?state=open&per_page=100&page=1", [], 200, {}, "alert"],
    ["POST", "/issues", {}, 201, {}, "alert"],
  );
  await assert.rejects(run("2027-11-01", monthly, api.fetch), /HTTP 401/);
  assert.match(api.verify().at(-1).body, /primary Worker token or workflow access check failed/);
});

test("healthy primary makes only the monthly probe", async () => {
  const api = mock(["GET", workflow, { state: "active" }]);
  await run("2027-09-01", monthly, api.fetch);
  api.verify();
});
