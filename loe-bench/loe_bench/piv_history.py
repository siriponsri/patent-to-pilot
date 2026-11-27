"""Point-in-time FDA Paragraph IV list evidence and entity linkage."""
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from functools import lru_cache
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import re
from xml.etree import ElementTree as ET
from zipfile import BadZipFile, ZipFile
import zlib

from .common import add_months, ingredient_key
from .kleene import T3


@dataclass(frozen=True)
class PIVEntry:
    ingredient: str
    dosage_form: str
    rld: str
    nda: str | None
    first_submission: date | None
    locator: str
    submission_text: str = ""


def words(text):
    return " ".join(text.split())


def heading(text):
    return re.sub(r"[^A-Z0-9]", "", text.upper())


HEADINGS = {
    "name": {"DRUGNAME", "ACTIVEINGREDIENTNAME", "NAMEOFDRUGPRODUCT"},
    "form": {"DOSAGEFORM"},
    "rld": {"RLD", "RLDNDA", "RLDNAMEANDNDANUMBER", "REFERENCELISTEDDRUG"},
    "nda": {"NDA", "NDANUMBER"},
    "date": {"DATEOFSUBMISSION", "DATEOFFIRSTPIVSUBMISSION", "SUBMISSIONDATE"},
}
UNDATED = {"", "-", "–", "—", "PRE-MMA", "PRE MMA", "N/A", "NA", "UNKNOWN"}


def is_heading(text, field):
    normalized = heading(text)
    # Some PDF exporters reference the repeated header on every page from one cell.
    return any(normalized and normalized.replace(label, "") == "" for label in HEADINGS[field])


def submission_date(value, epoch):
    if (value.upper() in UNDATED or heading(value) == "PREMMA"
            or value.upper().startswith("PIV RECEIVED PRIOR TO ")):
        return None
    if re.fullmatch(r"\d{4,6}(?:\.0+)?", value):
        return epoch + timedelta(days=int(float(value)))
    for fmt in ("%m/%d/%Y", "%m/%d/%y", "%Y-%m-%d", "%m-%d-%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def table_columns(cells):
    columns = {}
    for i, cell in enumerate(cells):
        for key in HEADINGS:
            if is_heading(cell, key):
                columns.setdefault(key, i)
    return columns


def table_entries(rows, epoch=date(1899, 12, 30), columns=None):
    entries = []
    for locator, cells in rows:
        cells = [words(cell) for cell in cells]
        found = table_columns(cells)
        if {"name", "form", "date"} <= found.keys():
            columns = found
            continue
        if not columns or not any(cells):
            continue
        nonempty = [cell for cell in cells if cell]
        if len(nonempty) == 1 and re.match(
                r"^(?:page\s+\d+|updated\b|last updated\b|current as of\b|\*\s*ANDA withdrawn\b)",
                nonempty[0], re.I):
            continue
        if len(cells) == columns["date"] == max(columns.values()) and "rld" in columns:
            cells.append("")  # Legacy tagged rows sometimes omit the final blank date cell.
        if len(cells) <= max(columns.values()):
            raise ValueError(f"incomplete table row at {locator}")
        name, form, when = (cells[columns[key]] for key in ("name", "form", "date"))
        if not name:
            raise ValueError(f"missing ingredient at {locator}")
        rld = cells[columns["rld"]] if "rld" in columns else ""
        number = cells[columns["nda"]] if "nda" in columns else rld
        match = re.search(r"(?<!\d)\d{4,6}$", number)
        entries.append(PIVEntry(name, form, rld, match[0].zfill(6) if match else None,
                                submission_date(when, epoch), locator, when))
    if not entries:
        raise ValueError("no recognized FDA PIV table rows")
    return tuple(entries)


def xlsx_entries(data):
    """Read OOXML cells by coordinate, including shared strings and date serials."""
    with ZipFile(BytesIO(data)) as archive:
        shared = []
        if "xl/sharedStrings.xml" in archive.namelist():
            strings = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            shared = ["".join(n.text or "" for n in item.iterfind(".//{*}t")) for item in strings]
        book = ET.fromstring(archive.read("xl/workbook.xml"))
        props = book.find("{*}workbookPr")
        epoch = date(1899, 12, 30)
        if props is not None and props.get("date1904") in {"1", "true"}:
            epoch = date(1904, 1, 1)
        sheets = book.findall("./{*}sheets/{*}sheet")
        rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        targets = {rel.attrib["Id"]: rel.attrib["Target"] for rel in rels
                   if rel.attrib["Type"].endswith("/worksheet")}
        tables = []
        for sheet in sheets:
            rid = next(value for key, value in sheet.attrib.items() if key.endswith("}id"))
            target = targets[rid]
            path = target.lstrip("/") if target.startswith("/") else f"xl/{target}"
            rows = []
            for row in ET.fromstring(archive.read(path)).iterfind("./{*}sheetData/{*}row"):
                values = {}
                for cell in row.findall("{*}c"):
                    col = 0
                    for char in re.match(r"[A-Z]+", cell.attrib["r"])[0]:
                        col = col * 26 + ord(char) - ord("A") + 1
                    kind = cell.get("t")
                    value = cell.findtext("{*}v", "")
                    if kind == "s":
                        value = shared[int(value)]
                    elif kind == "inlineStr":
                        value = "".join(n.text or "" for n in cell.iterfind(".//{*}t"))
                    if kind in {"s", "str", "inlineStr"}:
                        value = re.sub(r"_x([0-9A-Fa-f]{4})_", lambda match: chr(int(match[1], 16)), value)
                    values[col - 1] = value
                rows.append((f"{sheet.attrib['name']}!{row.attrib['r']}",
                             [values.get(i, "") for i in range(max(values, default=-1) + 1)]))
            if any(any(is_heading(cell, "date") for cell in cells) for _, cells in rows):
                tables.extend(table_entries(rows, epoch))
    if not tables:
        raise ValueError("workbook contains no recognized PIV worksheet")
    return tuple(tables)


_PDF_OBJECT = re.compile(rb"(?:\A|[\r\n])[ \t]*(\d+)\s+0\s+obj\b(.*?)\bendobj\b", re.S)
_PDF_REF = re.compile(rb"(\d+)\s+0\s+R\b")
_PDF_TEXT = rb"\((?:\\[\s\S]|[^\\()])*\)|<[0-9A-Fa-f\s]+>"


def _pdf_objects(data):
    """Decode the standard and Flate-compressed objects used by FDA's tagged PDFs."""
    objects = {}
    streams = {}
    for match in _PDF_OBJECT.finditer(data):
        number, content = int(match[1]), match[2]
        header, stream, payload = re.split(rb"(\bstream\r?\n)", content, maxsplit=1) if (
            re.search(rb"\bstream\r?\n", content)) else (content, b"", b"")
        objects[number] = header
        if not stream:
            continue
        payload, _, _ = payload.rpartition(b"endstream")
        if b"/FlateDecode" in header:
            payload = zlib.decompress(payload)
        elif b"/Filter" in header:
            continue
        if re.search(rb"/Type\s*/ObjStm\b", header):
            first = int(re.search(rb"/First\s+(\d+)", header)[1])
            index = list(map(int, payload[:first].split()))
            for i in range(0, len(index), 2):
                start = first + index[i + 1]
                end = first + index[i + 3] if i + 3 < len(index) else len(payload)
                objects[index[i]] = payload[start:end]
        else:
            streams[number] = payload
    return objects, streams


def _pdf_string(token, font):
    escapes = {b"n": b"\n", b"r": b"\r", b"t": b"\t", b"b": b"\b", b"f": b"\f"}

    def unescape(match):
        value = match[1]
        if re.fullmatch(rb"[0-7]{1,3}", value):
            return bytes([int(value, 8)])
        return escapes.get(value, b"" if value in {b"\n", b"\r", b"\r\n"} else value)

    if token.startswith(b"<"):
        raw = bytes.fromhex(token[1:-1].decode())
    else:
        raw = re.sub(rb"\\([0-7]{1,3}|\r\n|[\s\S])", unescape, token[1:-1])
    width, cmap = font
    if width == 1:
        return "".join(cmap[code] if code in cmap else bytes([code]).decode("cp1252") for code in raw)
    if not cmap or len(raw) % width:
        raise ValueError("unsupported PDF text encoding")
    return "".join(cmap[int.from_bytes(raw[i:i + width])] for i in range(0, len(raw), width))


def _pdf_cmap(data):
    cmap = {}
    for block in re.findall(rb"beginbfchar(.*?)endbfchar", data, re.S):
        for code, target in re.findall(rb"<(\w+)>\s*<(\w+)>", block):
            cmap[int(code, 16)] = bytes.fromhex(target.decode()).decode("utf-16-be", errors="replace")
    for block in re.findall(rb"beginbfrange(.*?)endbfrange", data, re.S):
        for first, last, target in re.findall(rb"<(\w+)>\s*<(\w+)>\s*(<\w+>|\[[^\]]*\])", block):
            codes = range(int(first, 16), int(last, 16) + 1)
            if target.startswith(b"["):
                values = (bytes.fromhex(x.decode()).decode("utf-16-be", errors="replace")
                          for x in re.findall(rb"<(\w+)>", target))
            else:
                start = int(target[1:-1], 16)
                size = (len(target) - 2) // 2
                values = ((start + offset).to_bytes(size).decode("utf-16-be", errors="replace")
                          for offset in range(len(codes)))
            cmap.update(zip(codes, values, strict=True))
    return cmap


def _pdf_shown_text(data, fonts, font):
    fragments = []
    for operator in re.finditer(rb"/([\w.]+)\s+[\d.]+\s+Tf\b|(\[(?:" + _PDF_TEXT + rb"|[^\]])*\]|"
                                + _PDF_TEXT + rb")\s*T[Jj]\b", data, re.S):
        if operator[1]:
            font = fonts.get(operator[1], (1, {}))
        else:
            fragments.append("".join(_pdf_string(token, font)
                                     for token in re.findall(_PDF_TEXT, operator[2])))
    return words(" ".join(fragments)), font


def _pdf_page_streams(objects, streams):
    for number, obj in objects.items():
        if not re.search(rb"/Type\s*/Page\b", obj):
            continue
        contents = re.search(rb"/Contents\s*(\[[^\]]*\]|\d+\s+0\s+R)", obj)
        if not contents:
            continue
        yield number, b"\n".join(streams[int(ref)] for ref in _PDF_REF.findall(contents[1]))


def _pdf_page_text(objects, streams):
    cmaps = {num: _pdf_cmap(value) for num, value in streams.items() if b"begincmap" in value}
    page_text = {}
    for number, data in _pdf_page_streams(objects, streams):
        resource = re.search(rb"/Resources\s+(\d+)\s+0\s+R", objects[number])
        obj = objects[int(resource[1])] if resource else objects[number]
        ref = re.search(rb"/Font\s*<<(.*?)>>", obj, re.S)
        fonts = {}
        if ref:
            for alias, code in re.findall(rb"/([\w.]+)\s+(\d+)\s+0\s+R", ref[1]):
                info = objects[int(code)]
                to_unicode = re.search(rb"/ToUnicode\s+(\d+)\s+0\s+R", info)
                width = 2 if re.search(rb"/Subtype\s*/Type0\b", info) else 1
                fonts[alias] = width, cmaps[int(to_unicode[1])] if to_unicode else {}
        font = (1, {})
        for tagged in re.finditer(rb"/MCID\s+(\d+)[^>]*>>\s*BDC\b(.*?)\bEMC\b", data, re.S):
            value, font = _pdf_shown_text(tagged[2], fonts, font)
            page_text[number, int(tagged[1])] = value
    return page_text


def pdf_entries(data):
    """Extract tagged FDA table rows. Unsupported layouts fail admission."""
    objects, streams = _pdf_objects(data)
    text = _pdf_page_text(objects, streams)

    def cell_text(number, page=None):
        obj = objects[number]
        page_ref = re.search(rb"/Pg\s+(\d+)\s+0\s+R", obj)
        if page_ref:
            page = int(page_ref[1])
        kids = re.search(rb"/K\s*(\[[^\]]*\]|\d+\s+0\s+R|\d+)", obj)
        if not kids:
            return ""
        body = kids[1]
        fragments = []
        for token in re.finditer(rb"<<.*?>>|\d+\s+0\s+R|\d+", body, re.S):
            value = token[0]
            if value.startswith(b"<<"):
                marked = re.search(rb"/MCID\s+(\d+)", value)
                if not marked:
                    raise ValueError("unsupported PDF tagged table node")
                pg = re.search(rb"/Pg\s+(\d+)\s+0\s+R", value)
                fragments.append(text[int(pg[1]) if pg else page, int(marked[1])])
            elif value.endswith(b"R"):
                fragments.append(cell_text(int(value.split()[0]), page))
            else:
                fragments.append(text[page, int(value)])
        return words(" ".join(fragments))

    def table_rows(refs, page=None):
        for row_ref in refs:
            row = objects[int(row_ref)]
            pg = re.search(rb"/Pg\s+(\d+)\s+0\s+R", row)
            row_page = int(pg[1]) if pg else page
            kids = re.search(rb"/K\s*(\[[^\]]*\]|\d+\s+0\s+R)", row)
            if re.search(rb"/S\s*/T(?:Head|Body|Foot)\b", row) and kids:
                yield from table_rows(_PDF_REF.findall(kids[1]), row_page)
                continue
            if not re.search(rb"/S\s*/TR\b", row):
                raise ValueError("unsupported PDF table row tree")
            if not kids:
                if not re.search(rb"/K\s*\S", row):
                    continue  # Empty structural row, without any content references.
                raise ValueError("missing PDF row cells")
            cells = [cell_text(int(cell), row_page) for cell in _PDF_REF.findall(kids[1])]
            yield f"PDF table row object {row_ref.decode()}", cells

    # The table's child reference array gives FDA's reading order.
    tables = []
    columns = None
    for obj in objects.values():
        if not re.search(rb"/S\s*/Table\b", obj):
            continue
        table = re.search(rb"/K\s*\[([^\]]*)\]", obj)
        if not table:
            continue
        rows = list(table_rows(_PDF_REF.findall(table[1])))
        for _, cells in rows:
            if "STRENGTHRLD" in map(heading, cells) and is_heading(cells[-1], "date"):
                i = next(i for i, cell in enumerate(cells) if heading(cell) == "STRENGTHRLD")
                cells[i:i + 1] = ["STRENGTH", "RLD"]
            found = table_columns(cells)
            if columns is None and {"name", "form", "date"} <= found.keys():
                columns = found
        tables.extend(rows)
    return table_entries(tables, columns=columns)


def parse_entries(data, fmt):
    return {"xlsx": xlsx_entries, "pdf": pdf_entries}[fmt](data)


def form_key(text):
    """Normalize FDA form spellings while keeping release and route qualifiers."""
    tokens = re.findall(r"[A-Z0-9]+", text.upper())
    plurals = {"TABLETS", "CAPSULES", "SOLUTIONS", "SUSPENSIONS", "INJECTIONS",
               "PATCHES", "CREAMS", "OINTMENTS", "FILMS", "PELLETS", "POWDERS"}
    tokens = [("PATCH" if token == "PATCHES" else token[:-1]) if token in plurals else token
              for token in tokens]
    if "ORAL" in tokens and not {"SOLUTION", "SUSPENSION"} & set(tokens):
        if {"TABLET", "CAPSULE"} & set(tokens):
            tokens.remove("ORAL")
    return tuple(sorted(tokens))


def ingredient_names(text):
    parts = re.split(r"\s+(?:AND|WITH)\s+|\s*[/;,]\s*", text.upper())
    return tuple(part.strip() for part in parts if part.strip())


def legacy_key(names):
    return ingredient_key([{"active_ingredients": [{"name": name} for name in names]}])


@dataclass(frozen=True)
class EntityProduct:
    key: str
    ingredient: str
    dosage_form: str
    available_from: date


class EntityMatcher:
    """Use a caller-supplied as-of catalog. Keys can be legacy or FIX2 compositions.

    A resolver maps ingredient names to the catalog's key, e.g.
    `lambda names: registry.composition(names).key` for FIX2. Exact normalized
    name/form aliases also support opaque keys and known formulation variants.
    """
    def __init__(self, products, resolve=legacy_key):
        self.by_alias = defaultdict(dict)
        self.by_form_key = defaultdict(dict)
        self.by_name = defaultdict(dict)
        self.by_key = {}
        self.resolve = resolve
        for item in products:
            form = form_key(item.dosage_form)
            if not item.key or not form:
                continue
            alias = tuple(sorted(ingredient_names(item.ingredient)))
            for group in (self.by_alias[alias, form], self.by_form_key[item.key, form], self.by_name[alias], self.by_key):
                group[item.key] = min(item.available_from, group.get(item.key, item.available_from))

    def candidates(self, entry, cutoff):
        names = ingredient_names(entry.ingredient)
        form = form_key(entry.dosage_form)
        exact = {key for key, when in self.by_alias.get((tuple(sorted(names)), form), {}).items()
                 if when <= cutoff}
        if exact:
            return exact
        key = self.resolve(names)
        when = self.by_form_key.get((key, form), {}).get(key)
        return {key} if when is not None and when <= cutoff else set()

    def match(self, entry, cutoff):
        keys = self.candidates(entry, cutoff)
        return next(iter(keys)) if len(keys) == 1 else None

    def possible_names(self, entry, cutoff):
        """Keep a known ingredient with unresolved dosage-form linkage uncertain."""
        names = ingredient_names(entry.ingredient)
        keys = dict(self.by_name.get(tuple(sorted(names)), {}))
        key = self.resolve(names)
        if key in self.by_key:
            keys[key] = self.by_key[key]
        return {key for key, when in keys.items() if when <= cutoff}


@dataclass(frozen=True)
class Edition:
    version_date: date
    source_url: str
    wayback_timestamp: str
    format: str
    rows: int
    sha256: str
    file: str

    @property
    def captured(self):
        return datetime.strptime(self.wayback_timestamp, "%Y%m%d%H%M%S")


class PIVHistory:
    def __init__(self, manifest, raw_dir, matcher):
        self.raw_dir = Path(raw_dir)
        self.matcher = matcher
        self.editions = []
        for row in json.loads(Path(manifest).read_text(encoding="utf-8"))["editions"]:
            if row["parse_status"] != "PASS" or not row["wayback_timestamp"] or not row["version_date"]:
                continue
            fields = {name: row[name] for name in Edition.__dataclass_fields__ if name != "version_date"}
            edition = Edition(date.fromisoformat(row["version_date"]), **fields)
            if edition.version_date <= edition.captured.date():
                self.editions.append(edition)

    def edition_asof(self, cutoff):
        floor = add_months(cutoff, -6)
        return max((e for e in self.editions
                    if floor <= e.version_date <= cutoff and e.captured.date() <= cutoff),
                   key=lambda e: (e.version_date, e.captured, e.sha256), default=None)

    @lru_cache(maxsize=16)
    def entries(self, edition):
        data = (self.raw_dir / edition.file).read_bytes()
        if sha256(data).hexdigest() != edition.sha256:
            raise ValueError("PIV edition SHA-256 mismatch")
        entries = parse_entries(data, edition.format)
        if len(entries) != edition.rows:
            raise ValueError("PIV edition row count mismatch")
        return entries

    @lru_cache(maxsize=16)
    def _matched(self, edition, cutoff):
        matches = defaultdict(list)
        for entry in self.entries(edition):
            keys = self.matcher.candidates(entry, cutoff)
            for key in keys:
                matches[key].append((entry, len(keys) == 1))
            if not keys:
                for key in self.matcher.possible_names(entry, cutoff):
                    matches[key].append((entry, False))
        return matches

    def challenge_asof(self, key, cutoff):
        """FALSE means absent from the fresh published list under the declared join.

        An ambiguous match, unresolved dosage form, or missing date remains UNKNOWN.
        """
        edition = self.edition_asof(cutoff)
        if edition is None:
            return T3.UNKNOWN
        try:
            matches = self._matched(edition, cutoff).get(key, ())
        except (OSError, ValueError, KeyError, IndexError, BadZipFile, ET.ParseError, zlib.error):
            return T3.UNKNOWN
        if any(unique and entry.first_submission and entry.first_submission <= cutoff
               for entry, unique in matches):
            return T3.TRUE
        return T3.UNKNOWN if matches else T3.FALSE
