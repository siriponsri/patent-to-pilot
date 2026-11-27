"""FDA PSG observations and a cutoff-safe view of archived evidence."""

from calendar import monthrange
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from html.parser import HTMLParser
from pathlib import PurePosixPath
import re
from urllib.parse import urljoin, urlsplit

from .common import add_months, years_between

PSG_FIELDS = ("has_psg", "years_since_first_psg", "n_psgs", "revised_within_1y")
PSG_FEATURES = tuple(name for field in PSG_FIELDS for name in (field, field + "_missing"))


def _normalized(text):
    return re.sub(r"[^a-z0-9]+", "", text.casefold())


@dataclass(frozen=True)
class Guidance:
    ingredient: str
    route: str
    form: str
    applications: tuple[str, ...]
    link: str
    date_text: str
    recommended_by: date | None
    kind: str
    stage: str
    source: str
    line: int
    row: int
    table: int

    @property
    def document(self):
        return PurePosixPath(urlsplit(self.link).path).name.casefold()

    @property
    def formulation(self):
        names = tuple(sorted(_normalized(name) for name in self.ingredient.split(";")))
        return names, _normalized(self.route), _normalized(self.form)

    @property
    def identity(self):
        return (*self.formulation, self.applications or (self.document,))

    @property
    def recommended_from(self):
        if self.recommended_by and self.date_text.count("/") == 1:
            return self.recommended_by.replace(day=1)
        return self.recommended_by


def _recommendation(text):
    for fmt in ("%m/%d/%Y", "%m/%Y"):
        try:
            value = datetime.strptime(text, fmt).date()
        except ValueError:
            continue
        if fmt == "%m/%Y":
            value = value.replace(day=monthrange(value.year, value.month)[1])
        return value
    return None


class _TableReader(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tables = []
        self.table = None
        self.row = None
        self.cell = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "table":
            self.table = (attrs, [])
        if self.table is None:
            return
        if tag == "tr":
            self.row = (self.getpos()[0], [])
        if tag in ("td", "th") and self.row is not None:
            self.cell = (tag, [], [])
        if self.cell is not None:
            if tag == "a" and attrs.get("href"):
                self.cell[2].append(attrs["href"])
            if tag in ("br", "p", "span", "div"):
                self.cell[1].append(" ")

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self.cell is not None:
            kind, text, links = self.cell
            self.row[1].append((kind, " ".join("".join(text).split()), links))
            self.cell = None
        if tag == "tr" and self.row is not None:
            self.table[1].append(self.row)
            self.row = None
        if tag == "table" and self.table is not None:
            self.tables.append(self.table)
            self.table = None

    def handle_data(self, data):
        if self.cell is not None:
            self.cell[1].append(data)


def parse_listing(html, source, original_url, *, archived=False):
    """Read the listing rows, preserving the displayed version date and exact row locator."""
    reader = _TableReader()
    reader.feed(html)
    reader.close()
    result = []
    for table, (attrs, rows) in enumerate(reader.tables, 1):
        table_id = attrs.get("id", "")
        hint = attrs.get("summary", "").casefold()
        if not archived and table_id not in ("drugTable", "drugTableNewlyAdded", "drugTableNewlyRevised"):
            continue
        header = next((cells for _, cells in rows if cells and cells[0][0] == "th"
                       and "active ingredient" in cells[0][1].casefold()), [])
        header_text = [cell[1].casefold() for cell in header]
        if not header_text or "active ingredient" not in header_text[0] or header_text[-1] != "date recommended":
            continue
        latest = table_id == "drugTable"
        revisions_table = "revision" in hint or "Revised" in table_id or any(
            cells and cells[0][:2] == ("th", "Revisions") for _, cells in rows
        )
        for index, (line, cells) in enumerate(rows, 1):
            if len(cells) != len(header) or cells[0][0] != "td":
                continue
            raw_name, links = cells[0][1:]
            pdfs = [link for link in links if urlsplit(link).path.lower().endswith(".pdf")]
            if len(pdfs) != 1:
                raise ValueError(f"expected a single PSG PDF at {source}:{line} row {index}")
            name = re.split(r"\s*\(PDF\b[^)]*\)", raw_name, maxsplit=1, flags=re.I)[0].strip()
            revision = revisions_table or re.search(r"\brevised\s*\*?$", raw_name, re.I)
            kind = "revision" if revision else ("latest" if latest else "new")
            apps = tuple(sorted({value.zfill(6) for value in re.findall(r"\b\d{4,6}\b", cells[-2][1])}))
            date_text = cells[-1][1]
            if not name:
                raise ValueError(f"missing ingredient at {source}:{line} row {index}")
            result.append(Guidance(name, cells[-4][1], cells[-3][1], apps,
                                   urljoin(original_url, pdfs[0]), date_text, _recommendation(date_text),
                                   kind, cells[-5][1], source, line, index, table))
    return result


def link_key(guidance, linker):
    """Apply FIX2c full-composition resolution with canonical aliases."""
    composition = linker.registry.composition(guidance.ingredient.split(";"))
    key = linker.canonical(composition.key)
    # The listing provides application numbers. FIX2c's fallback requires a product number.
    return key if key in linker.entities else None


@dataclass(frozen=True)
class Capture:
    captured: date
    rows: tuple[tuple[str, Guidance], ...]
    complete: bool = False


class PSGHistory:
    def __init__(self, captures):
        self.captures = tuple(sorted(captures, key=lambda snapshot: snapshot.captured))
        self.keys = defaultdict(list)
        for capture in self.captures:
            for key, row in capture.rows:
                self.keys[key].append((capture.captured, row))
        self.complete_membership = [
            (capture.captured, {(key, row.identity) for key, row in capture.rows})
            for capture in self.captures if capture.complete
        ]

    def psg_asof(self, key, cutoff):
        complete = next((item for item in reversed(self.complete_membership) if item[0] <= cutoff), None)
        observed = [
            row for captured, row in self.keys.get(key, ())
            if row.recommended_by is not None and row.recommended_from <= captured <= cutoff
            and row.recommended_by <= cutoff
            and (complete is None or (key, row.identity) in complete[1])
        ]
        if not observed:
            return dict(zip(PSG_FIELDS, (None, None, None, None)))
        first = min((row.recommended_by for row in observed if row.kind == "new"), default=None)
        floor = add_months(cutoff, -12)
        revision = any(row.kind == "revision" and row.recommended_from > floor for row in observed)
        return dict(zip(PSG_FIELDS, (
            True, years_between(first, cutoff) if first else None,
            len({row.identity for row in observed}), True if revision else None,
        )))

    def model_values(self, key, cutoff):
        values = self.psg_asof(key, cutoff)
        return {name: encoded for field, value in values.items()
                for name, encoded in ((field, float(value or 0)), (field + "_missing", float(value is None)))}
