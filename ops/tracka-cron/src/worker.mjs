const API = "https://api.github.com";
const DAILY = "13 1 * * *";
const MONTHLY = "23 1 1 * *";
const MATURITY = { 12: "2027-11-27", 24: "2028-11-27" };
const HEALTH_TITLE = "Track A automation needs attention";
const HEALTH_MARKER = "<!-- tracka:token-health -->";
const DAY_MS = 86_400_000;
const REQUIRED_PINS = ["First result SHA-256", "FDA source manifest SHA-256"];
const OPTIONAL_PINS = ["Bootstrap draws SHA-256", "Report SHA-256"];
const PIN_SUFFIX = /^ `([0-9a-f]{64})`\.$/;

function github(env, token, fetcher) {
  if (!token) throw new Error("GitHub secret is missing");
  if (!/^[\w.-]+\/[\w.-]+$/.test(env.GITHUB_REPOSITORY)) {
    throw new Error("Configure the GitHub repository");
  }
  const base = `${API}/repos/${env.GITHUB_REPOSITORY}`;
  return async (path, method = "GET", data) => {
    const response = await fetcher(base + path, {
      method,
      redirect: "error",
      headers: {
        Accept: "application/vnd.github+json",
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
        "User-Agent": "tracka-cron",
        "X-GitHub-Api-Version": "2026-03-10",
      },
      body: data === undefined ? undefined : JSON.stringify(data),
    });
    if (!response.ok) {
      throw new Error(`GitHub ${method} ${path.split("?")[0]} returned HTTP ${response.status}`);
    }
    return response;
  };
}

async function listIssues(request, state) {
  const issues = [];
  for (let page = 1; page <= 30; page++) {
    const response = await request(`/issues?state=${state}&per_page=100&page=${page}`);
    issues.push(...(await response.json()).filter(issue => !issue.pull_request));
    if (!/rel="next"/.test(response.headers.get("Link") ?? "")) return issues;
  }
  throw new Error("Track A issue scan exceeded 30 pages");
}

function canonicalRecord(env) {
  const recordId = /^(?:https:\/\/doi\.org\/)?10\.5281\/zenodo\.(\d+)$/.exec(env.TRACKA_RELEASE_DOI)?.[1];
  if (!recordId || !/^[a-f0-9]{64}$/.test(env.TRACKA_FREEZE_SHA256)) {
    throw new Error("Configure the exact Zenodo version DOI and OSF freeze SHA-256");
  }
  return `${env.TRACKA_FREEZE_SHA256}:${recordId}`;
}

function hasCompletePins(lines) {
  return [...REQUIRED_PINS, ...OPTIONAL_PINS].every(label => {
    const pins = lines.filter(line => line.startsWith(label));
    if (pins.length === 0) return !REQUIRED_PINS.includes(label);
    const digests = pins.map(line => PIN_SUFFIX.exec(line.slice(label.length))?.[1]);
    return !digests.includes(undefined) && new Set(digests).size === 1;
  });
}

function isRecorded(issues, horizon, record) {
  const marker = `<!-- tracka:${horizon}:SCORED:${record} -->`;
  let recorded = false;
  for (const issue of issues) {
    const trusted = issue.user?.login === "github-actions[bot]" ||
      ["OWNER", "MEMBER", "COLLABORATOR"].includes(issue.author_association);
    if (!trusted || issue.title !== `Track A ${horizon}-month readout`) continue;
    const lines = (issue.body ?? "").split(/\r\n|[\n\r]/);
    if (!lines.includes(marker)) continue;
    if (hasCompletePins(lines)) {
      recorded = true;
    } else {
      console.warn(`Incomplete Track A ${horizon}-month SCORED issue #${issue.number}. ` +
        "Verify the published release and correct its digest lines using the Track A scoring guide.");
    }
  }
  return recorded;
}

async function dispatchDue(env, today, fetcher) {
  const due = Object.keys(MATURITY).filter(horizon => today >= MATURITY[horizon]);
  if (due.length === 0) return;
  const record = canonicalRecord(env);
  const request = github(env, env.GITHUB_TOKEN, fetcher);
  const issues = await listIssues(request, "all");
  const missing = due.filter(horizon => !isRecorded(issues, horizon, record));
  if (missing.length === 0) return;

  const workflow = "/actions/workflows/score-track-a.yml";
  const { state } = await (await request(workflow)).json();
  if (state === "disabled_inactivity") {
    await request(`${workflow}/enable`, "PUT");
  } else if (state !== "active") {
    throw new Error(`Score Track A workflow is ${state}; check repository settings`);
  }

  const failures = [];
  for (const horizon of missing) {
    try {
      await request(`${workflow}/dispatches`, "POST", { ref: env.GITHUB_REF, inputs: { horizon } });
    } catch (error) {
      failures.push(`${horizon} months: ${error.message}`);
    }
  }
  if (failures.length) throw new Error(failures.join("\n"));
}

async function reportHealth(request, reason) {
  const issues = await listIssues(request, "open");
  const existing = issues.find(issue =>
    issue.title === HEALTH_TITLE && issue.body?.includes(HEALTH_MARKER) &&
    ["OWNER", "MEMBER", "COLLABORATOR"].includes(issue.author_association));
  const body = `${HEALTH_MARKER}\n\n${reason}\n\n` +
    "Renew the Worker secret and update its expiry. See the Track A cron deployment guide.";
  if (!existing) await request("/issues", "POST", { title: HEALTH_TITLE, body });
  else if (existing.body !== body) await request(`/issues/${existing.number}`, "PATCH", { body });
}

async function checkToken(env, today, fetcher) {
  const expires = env.GITHUB_TOKEN_EXPIRES_ON;
  const expiry = Date.parse(expires);
  const daysLeft = (expiry - Date.parse(today)) / DAY_MS;
  const primary = () => github(env, env.GITHUB_TOKEN, fetcher);
  try {
    // A bad token gets an authentication error even on a public repository.
    await primary()("/actions/workflows/score-track-a.yml");
  } catch (error) {
    if (env.GITHUB_ALERT_TOKEN) {
      await reportHealth(github(env, env.GITHUB_ALERT_TOKEN, fetcher),
        "The primary Worker token or workflow access check failed. Check the scheduled Worker logs.");
    }
    throw error;
  }

  if (!/^\d{4}-\d{2}-\d{2}$/.test(expires) || !Number.isFinite(expiry) ||
      new Date(expiry).toISOString().slice(0, 10) !== expires) {
    await reportHealth(primary(), "The Worker is missing a valid token expiry date.");
  } else if (daysLeft <= 45) {
    await reportHealth(primary(), `The primary Worker token is configured to expire on ${expires} UTC.`);
  }
}

export async function runScheduled(controller, env, fetcher = fetch) {
  const today = new Date(controller.scheduledTime).toISOString().slice(0, 10);
  if (controller.cron === MONTHLY) return checkToken(env, today, fetcher);
  if (controller.cron === DAILY) return dispatchDue(env, today, fetcher);
  throw new Error("Unrecognized Track A cron trigger");
}

export default {
  scheduled(controller, env) {
    return runScheduled(controller, env);
  },
};
