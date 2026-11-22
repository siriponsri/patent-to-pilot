# -*- coding: utf-8 -*-
"""Typesetting helpers shared by content_th.py and content_en.py.

TH SarabunPSK has no Greek or math glyphs, so Word substitutes a heavy fallback font for them. greek() puts
pi, Delta, >= and the like in Cambria, 2 pt smaller than the surrounding text so the x-heights match.
"""
import re

GREEK = "πΔ≥±×"
_SPLIT = re.compile(f"([{GREEK}])")


def greek(spec, size):
    items = [spec] if isinstance(spec, str) else list(spec)
    out = []
    for it in items:
        t, o = (it[0], dict(it[1])) if isinstance(it, tuple) else (it, {})
        for part in _SPLIT.split(t):
            if not part:
                continue
            if part in GREEK:
                oo = dict(o)
                oo["font"] = "Cambria"
                oo["size"] = o.get("size", size) - 4
                out.append((part, oo))
            else:
                out.append((part, o) if o else part)
    return out


def typeset(body):
    """Apply greek() to every text field of a paperkit BODY list."""
    res = []
    for item in body:
        k = item[0]
        if k in ("p", "pi", "rq"):
            res.append((k, greek(item[1], 28)))
        elif k == "fig":
            res.append(item[:3] + (greek(item[3], 24),) + item[4:])
        elif k == "tbl":
            _, cap, rows, widths, full, note, aligns = item
            rows = [[greek(c, 24) for c in r] for r in rows]
            res.append(("tbl", greek(cap, 24), rows, widths, full, greek(note, 22) if note else note, aligns))
        else:
            res.append(item)
    return res
