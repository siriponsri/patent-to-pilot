"""Rebuild the canonical OSF registration record and its SHA-256 (the PREREG_LOCK key).

OSF registration p2smd has no file attachments and no OSF-generated PDF, so the lock binds the
immutable registration record itself: id, DOI, registration time, template, title, description
and every form response, serialized as sorted, compact UTF-8 JSON.

Usage: python scripts/osf_lock.py [--out data/OSF_REGISTRATION_P2SMD.json]
"""
import argparse
import hashlib
import json
import urllib.request

REG_ID = "p2smd"
API = f"https://api.osf.io/v2/registrations/{REG_ID}/"
# The lock binds the ORIGINAL registration responses (schema response marked is_original_response),
# so later OSF registration updates do not change the digest.


def fetch(url):
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.load(r)


def original_responses():
    rows = fetch(API + "schema_responses/")["data"]
    orig = [r for r in rows if r["attributes"].get("is_original_response")]
    if not orig:
        raise RuntimeError("original schema response not found")
    return orig[0]["attributes"]["revision_responses"]


def canonical_record():
    data = fetch(API)["data"]
    attrs = data["attributes"]
    ids = fetch(API + "identifiers/")["data"]
    doi = next(i["attributes"]["value"] for i in ids if i["attributes"]["category"] == "doi")
    record = {
        "id": data["id"],
        "doi": doi,
        "date_registered": attrs["date_registered"],
        "registration_supplement": attrs["registration_supplement"],
        "title": attrs["title"],
        "description": attrs["description"],
        "registration_responses": original_responses(),
    }
    return json.dumps(record, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out")
    args = ap.parse_args()
    raw = canonical_record()
    if args.out:
        with open(args.out, "wb") as fh:
            fh.write(raw)
    print(hashlib.sha256(raw).hexdigest())


if __name__ == "__main__":
    main()
