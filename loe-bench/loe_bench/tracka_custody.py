"""Verify scoped Track A release bundles and their independent Actions provenance."""

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from os import environ
from pathlib import Path
import re
from shutil import copyfileobj
from subprocess import TimeoutExpired, run
from tempfile import TemporaryDirectory
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from zipfile import ZipFile

from .common import add_months
from .tracka_release import DIGEST, HORIZONS, T0, digest, require, safe_name

WORKFLOW = ".github/workflows/score-track-a.yml"
REF = "refs/heads/main"
BUNDLE_LIMIT = 512 * 2**20
PIN = "Track A bundle SHA-256: "
PROVENANCE = "Track A attestation: "
HOLD = "UNRESOLVED_CONTINUITY"


@dataclass(frozen=True)
class Scope:
    repository: str
    doi: str
    freeze: str
    horizon: int
    kind: str

    def __post_init__(self):
        require(re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", self.repository)
                and re.fullmatch(r"10\.5281/zenodo\.\d+", self.doi)
                and DIGEST.fullmatch(self.freeze) and self.horizon in HORIZONS
                and self.kind in ("capture", "result"), "Invalid Track A custody scope")

    @property
    def api(self):
        return f"https://api.github.com/repos/{self.repository}"

    @property
    def tag(self):
        prefix = "track-a-capture" if self.kind == "capture" else "track-a"
        return f"{prefix}-{self.horizon}m-{self.doi.rsplit('.', 1)[1]}-{self.freeze}"

    @property
    def archive(self):
        return f"track-a-{self.kind}.zip"

    @property
    def identity(self):
        return f"{self.repository}/{WORKFLOW}@{REF}"

    @property
    def maturity(self):
        return add_months(T0, self.horizon)

    def witness(self):
        # The digest is calculable even if every release asset has disappeared.
        return (json.dumps({"schema": 1, **vars(self)}, sort_keys=True, separators=(",", ":")) + "\n").encode()


def utc_time(value):
    at = datetime.fromisoformat(value)
    require(at.utcoffset() is not None, "Track A timestamp is missing its offset")
    return at.astimezone(timezone.utc)


def fetch(url, limit, *, accept="application/vnd.github+json"):
    request = Request(url, headers={"User-Agent": "loe-bench-tracka-readout", "Accept": accept})
    if url.startswith("https://api.github.com/"):
        request.add_unredirected_header("X-GitHub-Api-Version", "2026-03-10")
        if token := environ.get("GH_TOKEN"):
            request.add_unredirected_header("Authorization", f"Bearer {token}")
    try:
        with urlopen(request, timeout=60) as response:
            data = response.read(limit + 1)
    except HTTPError as exc:
        if exc.code == 404:
            return None
        raise
    require(len(data) <= limit, "Track A download exceeds its size limit")
    return data


def verified_claim(scope, witness, verified):
    result = verified["verificationResult"]
    claims = result["signature"]["certificate"]
    run_uri = re.fullmatch(rf"https://github\.com/{re.escape(scope.repository)}/actions/runs/(\d+)/attempts/(\d+)",
                           claims["runInvocationURI"])
    revision = claims["sourceRepositoryDigest"]
    require(run_uri and re.fullmatch(r"[a-f0-9]{40}", revision)
            and claims["buildConfigURI"] == f"https://github.com/{scope.identity}"
            and claims["sourceRepositoryVisibilityAtSigning"] == "public",
            "Unexpected Track A certificate workflow, run, commit or repository visibility")
    subjects = {item["name"]: item["digest"]["sha256"] for item in result["statement"]["subject"]}
    require(subjects.get(witness.name) == digest(witness) and len(subjects) == 2
            and DIGEST.fullmatch(subjects.get(scope.archive, "")),
            "Track A attestation does not bind the scope and bundle together")
    log_times = [utc_time(value["timestamp"]) for value in result["verifiedTimestamps"] if value["type"] == "Tlog"]
    require(log_times, "Track A attestation lacks a verified transparency log timestamp")
    timestamp = min(log_times)
    require(timestamp.date() >= scope.maturity, "Track A bundle was signed before maturity")
    return {"bundle_sha256": subjects[scope.archive], "signed_at_utc": timestamp.isoformat(),
            "run_id": run_uri[1], "run_attempt": run_uri[2], "commit": revision, "workflow_ref": scope.identity}


def verify_statements(scope, witness, count):
    # The CLI handles GitHub's compressed hosted Sigstore bundles.
    verification = run(["gh", "attestation", "verify", str(witness), "--repo", scope.repository,
                        "--cert-identity", f"https://github.com/{scope.identity}", "--source-ref", REF,
                        "--deny-self-hosted-runners", "--limit", str(count), "--format", "json"],
                       capture_output=True, text=True, check=False, timeout=90)
    require(verification.returncode == 0, "GitHub CLI could not verify the scoped Track A attestation")
    verified = json.loads(verification.stdout)
    require(isinstance(verified, list) and len(verified) == count, "Some indexed Track A attestations could not be verified")
    return [verified_claim(scope, witness, item) for item in verified]


def attestations(scope, query):
    """Distinguish an empty public index from a failed verification or unavailable index."""
    witness_bytes = scope.witness()
    witness_sha = sha256(witness_bytes).hexdigest()
    url = f"{scope.api}/attestations/sha256:{witness_sha}?per_page=100&page=1"
    data = query(url, 16 * 2**20)
    if data is None:
        # GitHub returns 404 for an unknown subject digest, including in public repositories.
        repository = query(scope.api, 2**20)
        require(repository is not None, "Track A repository is unavailable")
        identity = json.loads(repository)
        require(identity["full_name"] == scope.repository and identity["visibility"] == "public",
                "Track A attestation lookup lacks a verified public repository")
        return []
    batch = json.loads(data)["attestations"]
    require(isinstance(batch, list) and len(batch) <= 30, "Malformed or oversized Track A attestation index")
    if not batch:
        return []
    with TemporaryDirectory() as temp:
        witness = Path(temp) / "track-a-scope.json"
        witness.write_bytes(witness_bytes)
        records = verify_statements(scope, witness, len(batch))
    return sorted(records, key=lambda item: (utc_time(item["signed_at_utc"]), int(item["run_id"]), int(item["run_attempt"])))


def locate(scope, query):
    raw = query(f"{scope.api}/releases/tags/{scope.tag}", 2**20)
    if raw is not None:
        return json.loads(raw)
    # Only callers with write access see drafts. Public discovery can still see signed intent.
    for page in range(1, 31):
        raw = query(f"{scope.api}/releases?per_page=100&page={page}", 16 * 2**20)
        require(raw is not None, "Track A release listing is unavailable")
        batch = json.loads(raw)
        require(isinstance(batch, list), "Malformed Track A release listing")
        matches = [item for item in batch if item["tag_name"] == scope.tag]
        require(len(matches) <= 1, "Several releases claim the same Track A scope")
        if matches:
            return matches[0]
        if len(batch) < 100:
            return None
    raise ValueError("Track A release listing exceeded its page limit")


def note_value(release, prefix, *, required=True):
    values = [line.removeprefix(prefix) for line in (release.get("body") or "").splitlines()
              if line.startswith(prefix)]
    require(len(values) == 1 or (not required and not values), "Missing or ambiguous Track A release metadata")
    return values[0] if values else None


def inspect(scope, folder, *, query=None, include_draft=False):
    """Return a verified release, a resumable draft, a clean scope or a continuity hold."""
    query = query or fetch
    evidence = {"status": HOLD, "scope_sha256": sha256(scope.witness()).hexdigest(), "tag": scope.tag}
    try:
        records = attestations(scope, query)
        evidence["attestations"] = records
        require(len({item["bundle_sha256"] for item in records}) <= 1, "Conflicting attested Track A bundle digests")
        release = locate(scope, query)
        refs = query(f"{scope.api}/git/matching-refs/tags/{scope.tag}", 2**20)
        require(refs is not None, "Track A tag listing is unavailable")
        tags = [item for item in json.loads(refs) if item["ref"] == f"refs/tags/{scope.tag}"]
        if release is None:
            require(not tags and not records, "Track A tag or signed intent survives without its release")
            return {**evidence, "status": "EMPTY"}
        require(release["tag_name"] == scope.tag, "Unexpected Track A release tag")
        draft = release["draft"]
        require(not draft or (include_draft and not tags), "Track A release is still a draft or has a conflicting tag")
        pin = note_value(release, PIN)
        require(DIGEST.fullmatch(pin) and (not records or records[0]["bundle_sha256"] == pin),
                "Track A release digest disagrees with its signed intent")
        if not draft:
            require(records and isinstance(release["id"], int), "Track A release lacks signed intent")
            provenance = json.loads(note_value(release, PROVENANCE))
            require(provenance in records, "Track A release metadata disagrees with the verified run, ref or commit")
            published = utc_time(release["published_at"])
            require(published >= utc_time(provenance["signed_at_utc"]) and len(tags) == 1
                    and tags[0]["object"]["type"] == "commit" and tags[0]["object"]["sha"] == provenance["commit"],
                    "Track A release timestamp or Git tag differs from its signed provenance")
            evidence.update(provenance=provenance, published_at_utc=published.isoformat(),
                            release_url=f"https://github.com/{scope.repository}/releases/tag/{scope.tag}")
        assets = [asset for asset in release["assets"] if asset["name"] == scope.archive]
        require(len(assets) == 1 and assets[0]["state"] == "uploaded", "Track A bundle asset is missing")
        asset = assets[0]
        require(type(asset["id"]) is int and 0 < asset["size"] <= BUNDLE_LIMIT
                and asset.get("digest") in (None, f"sha256:{pin}"), "Unexpected Track A asset metadata")
        if draft:
            data = query(f"{scope.api}/releases/assets/{asset['id']}", asset["size"],
                         accept="application/octet-stream")
        else:
            data = query(f"https://github.com/{scope.repository}/releases/download/{scope.tag}/{scope.archive}",
                         asset["size"])
        require(data is not None and len(data) == asset["size"] and sha256(data).hexdigest() == pin,
                "Track A bundle bytes disagree with release metadata")
        folder.mkdir(parents=True, exist_ok=True)
        (folder / scope.archive).write_bytes(data)
        return {**evidence, "status": "DRAFT" if draft else "VERIFIED", "release_id": release["id"],
                "bundle_sha256": pin}
    except (OSError, KeyError, TypeError, ValueError, TimeoutExpired) as exc:
        return {**evidence, "detail": str(exc)}


def pack(folder, names, target):
    with ZipFile(target, "x") as archive:
        for name in sorted(names):
            archive.write(folder / name, name)


def unpack(bundle, folder, allowed):
    folder.mkdir()
    with ZipFile(bundle) as archive:
        members = archive.infolist()
        names = {safe_name(item.filename) for item in members}
        require(len(names) == len(members) and allowed(names)
                and sum(item.file_size for item in members) <= BUNDLE_LIMIT, "Unexpected Track A bundle contents")
        for item in members:
            with archive.open(item) as source, (folder / item.filename).open("xb") as target:
                copyfileobj(source, target)
