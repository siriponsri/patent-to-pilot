"""Validate this documentation package; no runtime imports, data reads or network.

Run from the repository: python docs/healthtech/audits/ptp-three-study-planning-20261110/validate_docs.py --root .
Optional --overlay is for guarded pre-application document review.
"""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import re
from urllib.parse import unquote


RUN = "docs/healthtech/audits/ptp-three-study-planning-20261110"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--overlay", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    overlay = args.overlay.resolve() if args.overlay else None

    def physical(rel):
        return overlay / rel if overlay and (overlay / rel).exists() else root / rel

    files = json.loads(physical(RUN + "/package-files.json").read_text(encoding="utf-8"))["files"]
    broken, inherited, json_files, links = [], [], [RUN + "/package-files.json"], 0
    hashes = {}
    link_pattern = re.compile(r"(?<!!)\[[^\]\n]*\]\(([^)\n]+)\)")

    def bad_links(rel, text, use_overlay):
        bad = []
        for match in link_pattern.finditer(text):
            raw = match.group(1).strip().strip("<>")
            if re.match(r"[a-zA-Z][a-zA-Z0-9+.-]*:", raw) or raw.startswith("#"):
                continue
            target = unquote(raw.split("#", 1)[0])
            path = (root / rel).parent / target
            path = path.resolve()
            if not path.is_relative_to(root):
                bad.append(raw)
                continue
            dest = path.relative_to(root)
            if not ((overlay / dest).exists() if use_overlay and overlay and (overlay / dest).exists() else path.exists()):
                bad.append(raw)
        return set(bad)

    for rel in files:
        p = physical(rel)
        assert p.is_file(), "missing package file: " + rel
        data = p.read_bytes()
        hashes[rel] = hashlib.sha256(data).hexdigest()
        if p.suffix == ".md":
            text = data.decode("utf-8-sig")
            links += len(link_pattern.findall(text))
            bad = bad_links(rel, text, True)
            old = bad_links(rel, (root / rel).read_text(encoding="utf-8-sig"), False) if (root / rel).is_file() else set()
            broken.extend({"file": rel, "target": x} for x in sorted(bad - old))
            inherited.extend({"file": rel, "target": x} for x in sorted(bad & old))
        if p.suffix == ".json":
            json.loads(data)
            json_files.append(rel)

    assert not broken, "introduced unresolved local links: " + json.dumps(broken)
    index = physical("INDEX-PLAN.md").read_text(encoding="utf-8")
    ids = re.findall(r"^\| (HT-(?:IDX|RES)\d+) \|", index, re.M)
    assert len(ids) == len(set(ids)) == 39, "component/result row IDs"
    for rel in ("AGENTS.md", "CLAUDE.md", "HANDOFF.md"):
        text = physical(rel).read_text(encoding="utf-8-sig")
        assert "INDEX-PLAN.md" in text
        assert "memory/research/patent-to-pilot/INDEX.md" in text
        assert "30" in text and "NOT_RUN" in text
    for n in (1, 2, 3):
        rel = f"docs/healthtech/research/plans/PAPER-{n}-" + {1: "DAPFAM", 2: "MTM", 3: "ADAPTIVE"}[n] + ".md"
        text = physical(rel).read_text(encoding="utf-8")
        assert all(word in text.lower() for word in ("hypoth", "resource", "stop", "rights", "not_run")), rel
    assert not (root / "CLUADE.md").exists(), "unexpected duplicate instruction file"
    inventory = json.loads(physical(RUN + "/component-inventory.json").read_text())
    assert len(inventory["entries"]) == 48
    for row in inventory["entries"]:
        assert hashlib.sha256((root / row["path"]).read_bytes()).hexdigest() == row["sha256"], row["path"]
    sources = json.loads(physical(RUN + "/source-review.json").read_text())
    assert sum(row["pages"] for row in sources["supplied_pdfs"]) == 50
    for row in sources["supplied_pdfs"]:
        assert row["read_pages"] == list(range(1, row["pages"] + 1))
        assert hashlib.sha256((root / row["path"]).read_bytes()).hexdigest() == row["sha256"]
    preserved = json.loads(physical(RUN + "/preservation.json").read_text())
    for row in preserved["unchanged"]:
        assert hashlib.sha256((root / row["path"]).read_bytes()).hexdigest() == row["sha256"], row["path"]
    partial = physical(preserved["completed_partial"]["path"]).read_bytes()
    assert hashlib.sha256(partial[:preserved["completed_partial"]["original_bytes"]]).hexdigest() == preserved["completed_partial"]["original_sha256"], "partial note original prefix changed"
    progress = json.loads(physical("docs/healthtech/progress.json").read_text())
    assert progress["three_study_planning_20261110"]["experiments"] == "NOT_RUN"
    assert progress["three_study_planning_20261110"]["publication"] == "NOT_COMMITTED_NOT_PUSHED"
    result = {
        "format": "ptp-documentation-verification-v1",
        "observed_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "status": "PASS_DOCUMENTATION_ONLY",
        "files_checked": len(files),
        "markdown_links_seen": links,
        "introduced_broken_local_links": broken,
        "inherited_broken_local_links": inherited,
        "json_files_parsed": json_files,
        "unique_index_rows": len(ids),
        "source_files_unchanged": len(inventory["entries"]),
        "supplied_pdfs_hash_matched": 3,
        "protected_data_read": False,
        "experiments": "NOT_RUN",
        "runtime_tests": "NOT_RUN_DOCUMENTATION_ONLY",
        "agent_startup_integration": "NOT_RUN_STATIC_ENTRY_POINT_LINKS_ONLY",
        "remote_state": "NOT_VERIFIED_NETWORK_FAILURE",
        "publication": "NOT_COMMITTED_NOT_PUSHED",
        "file_sha256": hashes,
    }
    if args.output:
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key != "file_sha256"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
