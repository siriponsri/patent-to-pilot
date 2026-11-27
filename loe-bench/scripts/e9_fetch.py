"""Pin publicly served FDA PSG pages and Wayback CDX or replay responses."""

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
from time import monotonic, sleep
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

RAW = Path("C:/Users/User/Desktop/myProject/_private_artifacts/loe-bench/psg")
FDA = "https://www.accessdata.fda.gov/scripts/cder/psg/index.cfm"
TERMS = {
    "fda.gov": "https://www.fda.gov/about-fda/about-website/website-policies",
    "archive.org": "https://archive.org/about/terms",
}
HOSTS = {"www.fda.gov", "www.accessdata.fda.gov", "accessdata.fda.gov", "web.archive.org"}


def check_url(url):
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.netloc not in HOSTS:
        raise ValueError(f"URL outside the public FDA/Wayback source scope: {url}")


class RateLimitedRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        check_url(newurl)
        sleep(1.1)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch(sources, output):
    output.mkdir(parents=True, exist_ok=True)
    opener = build_opener(RateLimitedRedirect())
    next_request = monotonic()
    for filename, url in sources.items():
        check_url(url)
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", filename):
            raise ValueError(f"invalid filename: {filename}")
        target = output / filename
        metadata = target.with_name(target.name + ".fetch.json")
        if metadata.exists() or target.exists():
            raise FileExistsError(target)
        sleep(max(0, next_request - monotonic()))
        entry = {
            "file": filename, "url": url,
            "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
            "terms": next(link for domain, link in TERMS.items() if urlsplit(url).hostname.endswith(domain)),
        }
        try:
            try:
                response = opener.open(Request(url, headers={"User-Agent": "LOE-Bench PSG research/1.0"}), timeout=35)
            except HTTPError as error:
                response = error
            with response:
                payload = response.read()
                entry.update(status=response.code, final_url=response.url, bytes=len(payload),
                             http_date=response.headers.get("Date"),
                             last_modified=response.headers.get("Last-Modified"),
                             content_type=response.headers.get("Content-Type"),
                             sha256=sha256(payload).hexdigest())
                target.write_bytes(payload)
        except (URLError, TimeoutError) as error:
            entry.update(status=None, error=str(error))
        metadata.write_text(json.dumps(entry, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(entry), flush=True)
        next_request = monotonic() + 1.1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", nargs="+", help="local-filename=https://source-url")
    parser.add_argument("--output", type=Path, default=RAW)
    args = parser.parse_args()
    fetch(dict(source.split("=", 1) for source in args.source), args.output)


if __name__ == "__main__":
    main()
