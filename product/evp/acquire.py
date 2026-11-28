"""Save permitted public evidence and log each anonymous, rate-limited lookup."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sys
from time import monotonic, sleep
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
from urllib.robotparser import RobotFileParser

from select_cases import PRIVATE

OUT = PRIVATE / "evp"
USER_AGENT = "PatentToPilotEVP/1.0 (academic evidence verification)"
MAX_BYTES = 12_000_000


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class Acquisition:
    def __init__(self):
        self.opener = build_opener(NoRedirect())
        self.last_request = -10.0
        self.robots = {}
        self.path = OUT / "lookups.jsonl"
        self.log = {item["id"]: item for line in self.path.read_text(encoding="utf-8").splitlines()
                    if (item := json.loads(line))} if self.path.exists() else {}
        self.blocked_hosts = {urlsplit(item["url"]).netloc for item in self.log.values()
                              if item["access"] == "blocked" and item.get("http")}

    def request(self, url):
        sleep(max(0, 2.1 - (monotonic() - self.last_request)))
        timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self.last_request = monotonic()
        try:
            with self.opener.open(Request(url, headers={"User-Agent": USER_AGENT}), timeout=12) as response:
                body = response.read(MAX_BYTES + 1)
                if len(body) > MAX_BYTES:
                    return timestamp, response.status, "size limit", None, None
                return timestamp, response.status, response.headers.get_content_type(), body, None
        except HTTPError as error:
            return timestamp, error.code, "HTTP error", None, error.headers.get("Location")
        except (URLError, TimeoutError, OSError) as error:
            return timestamp, None, type(error).__name__, None, None

    def save(self, item, body=None):
        if body is not None:
            digest = sha256(body).hexdigest()
            (OUT / digest).write_bytes(body)
            item.update(sha256=digest, file=digest)
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(item, ensure_ascii=False) + "\n")
        self.log[item["id"]] = item
        print(item["id"], item["access"], item.get("http"), flush=True)
        return item

    def allowed(self, url):
        parts = urlsplit(url)
        host = f"{parts.scheme}://{parts.netloc}"
        if host not in self.robots:
            robots_url = host + "/robots.txt"
            robots_id = f"robots:{host}"
            prior = self.log.get(robots_id)
            if prior:
                code = prior["http"]
                body = (OUT / prior["file"]).read_bytes() if prior.get("file") else None
            else:
                stamp, code, result, body, location = self.request(robots_url)
                self.save(dict(id=robots_id, url=robots_url, query="robots.txt", retrieved=stamp,
                               http=code, access="read" if body is not None else "unavailable",
                               result=result, redirect=location), body)
            parser = RobotFileParser()
            if code == 200 and body is not None:
                parser.parse(body.decode("utf-8", errors="replace").splitlines())
            elif code == 404:
                parser.parse([])
            else:
                parser.disallow_all = True
            self.robots[host] = parser
        return self.robots[host].can_fetch(USER_AGENT, url)

    def lookup(self, item):
        if item["id"] in self.log:
            return self.log[item["id"]]
        url = item["url"]
        host = urlsplit(url).netloc
        if host in self.blocked_hosts or not self.allowed(url):
            return self.save(dict(item, retrieved=datetime.now(timezone.utc).isoformat(timespec="seconds"),
                                  access="blocked", result="host blocked or robots permission unavailable"))
        stamp, code, result, body, location = self.request(url)
        blocked = code in {401, 403, 429, 503} or (body is not None and any(
            marker in body[:40_000].lower() for marker in (b"cf-chl-", b"captcha-container", b"verify you are human")))
        if blocked:
            self.blocked_hosts.add(host)
        return self.save(dict(item, retrieved=stamp, http=code, redirect=location, result=result,
                              access="blocked" if blocked else "read" if body is not None else "unavailable"),
                         None if blocked else body)


if __name__ == "__main__":
    acquisition = Acquisition()
    for query in json.loads(Path(sys.argv[1]).read_text(encoding="utf-8-sig")):
        acquisition.lookup(query)
