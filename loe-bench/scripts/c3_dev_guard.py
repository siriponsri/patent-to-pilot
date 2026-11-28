"""Keep NDA identities while omitting later approval values before JSON decoding."""

import json
from pathlib import Path
import re


def nda_reader(path, fallback, *, projector, redact_dates):
    path = Path(path)
    if path.name not in {"df_nda.jsonl", "ob_nda.jsonl"}:
        yield from fallback(path)
        return
    with path.open("rb") as stream:
        for line in stream:
            if not line.strip():
                continue
            line = redact_dates(line)
            if path.name == "df_nda.jsonl":
                fields = dict(projector.composite_items(line))
                submissions = fields.get(b"submissions", b"null")
                if submissions != b"null":
                    kept = []
                    for _, raw in projector.composite_items(submissions):
                        sub = dict(projector.composite_items(raw))
                        when = sub.get(b"submission_status_date")
                        if projector.approved_by(when):
                            kept.append(projector.select_members(sub, {
                                b"submission_type", b"submission_status", b"submission_status_date",
                                b"submission_class_code", b"review_priority", b"submission_property_type",
                            }))
                    fields[b"submissions"] = b"[" + b",".join(kept) + b"]"
                line = projector.select_members(fields, fields)
            # The pinned redactor must replace all post-development product dates.
            if any(value > b"20160101" for value in re.findall(rb'"approval_date"\s*:\s*"([0-9]{8})"', line)):
                raise ValueError("NDA development projection retained a later approval")
            yield json.loads(line)
