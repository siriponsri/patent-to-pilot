"""Adapter for the pinned NBER Orange Book annual protection tables."""

import hashlib
import re
import struct
from collections import defaultdict
from datetime import date, timedelta
from functools import cache
from pathlib import Path
from zipfile import ZipFile

from .ob_history import Edition, EditionSource, ingredient_key_ob, norm_appl_no

DEFAULT_NBER_DIR = Path(
    "C:/Users/User/Desktop/myProject/_private_artifacts/loe-bench/nber_ob"
)
_EPOCH = date(1960, 1, 1)
_NUMERIC = {65526: ("d", 2**1023), 65527: ("f", 2**127),
            65528: ("i", 2147483621), 65529: ("h", 32741), 65530: ("b", 101)}


def _text(value):
    return value.split(b"\0", 1)[0].decode("utf-8").strip()


def _section(data, name, start, end):
    opening, closing = b"<" + name + b">", b"</" + name + b">"
    if not data.startswith(opening, start) or not data.endswith(closing, start, end):
        raise ValueError(f"Invalid Stata section {name!r}")
    return memoryview(data)[start + len(opening):end - len(closing)]


def read_dta118(data):
    """Read fixed-width rows from Stata 118 using the file's section offsets."""
    header = re.match(
        rb"<stata_dta><header><release>118</release><byteorder>(LSF|MSF)</byteorder>"
        rb"<K>(..)</K><N>(........)</N>", data, re.DOTALL
    )
    if not header:
        raise ValueError("Expected Stata 118 header")
    endian = "<" if header[1] == b"LSF" else ">"
    columns = struct.unpack(endian + "H", header[2])[0]
    row_count = struct.unpack(endian + "Q", header[3])[0]
    map_start = data.index(b"</header><map>", header.end()) + len(b"</header>")
    offsets = struct.unpack_from(endian + "14Q", data, map_start + len(b"<map>"))
    if offsets[1] != map_start or offsets[-1] != len(data) or sorted(offsets) != list(offsets):
        raise ValueError("Invalid Stata section offsets")
    types = struct.unpack(endian + f"{columns}H", _section(data, b"variable_types", *offsets[2:4]))
    names = _section(data, b"varnames", *offsets[3:5])
    if len(names) != columns * 129:
        raise ValueError("Invalid Stata name table")
    names = [_text(bytes(names[i:i + 129])) for i in range(0, len(names), 129)]
    fields, missing = [], []
    for kind in types:
        if 1 <= kind <= 2045:
            fields.append(f"{kind}s")
            missing.append(None)
        elif kind in _NUMERIC:
            fmt, minimum_missing = _NUMERIC[kind]
            fields.append(fmt)
            missing.append(minimum_missing)
        else:
            raise ValueError(f"Unsupported Stata storage type {kind}")
    layout = struct.Struct(endian + "".join(fields))
    rows = _section(data, b"data", *offsets[9:11])
    if len(rows) != row_count * layout.size:
        raise ValueError("Stata row count does not match the data section")
    for row in layout.iter_unpack(rows):
        yield {key: _text(value) if limit is None else value if value < limit else None
               for key, value, limit in zip(names, row, missing, strict=True)}


def _expiry(value):
    if value is None:
        return None
    if int(value) != value:
        raise ValueError("Expected a whole Stata daily-date offset")
    return _EPOCH + timedelta(days=int(value))


def _flag(value):
    return {"0": False, "1": True}.get(value)


def _protection(row, table, locator):
    app_type = {"NDA": "N", "ANDA": "A", "N/A": "", "": ""}[row["application_type"]]
    number = row["application_number"]
    if not re.fullmatch(r"[0-9]{1,6}", number):
        raise ValueError(f"{locator}: invalid application number {number!r}")
    product_no = row["product_number"]
    if product_no.isascii() and product_no.isdigit():
        product_no = product_no.zfill(3)
    product = dict(appl_no=norm_appl_no(number), product_no=product_no, appl_type=app_type,
                   locator=locator)
    if table == "patent":
        product.update(patent_no=row["patent_number"], expiry=_expiry(row["patent_expiration"]),
                       use_code=row["use_code"], drug_substance=_flag(row["DS"]),
                       drug_product=_flag(row["DP"]), delist=_flag(row["delist_requested"]),
                       submission_date=None, has_submission_col=False)
    else:
        product.update(code=row["exclusivity_code"], expiry=_expiry(row["exclusivity_expiration"]))
    return product


def _read_archive(path, manifest, edition_dates):
    with path.open("rb") as stream:
        if hashlib.file_digest(stream, "sha256").hexdigest() != manifest["archive"]["sha256"]:
            raise ValueError(f"SHA-256 mismatch for {path.name}")
    patents, exclusivities = defaultdict(list), defaultdict(list)
    products = defaultdict(dict)
    with ZipFile(path) as archive:
        for table, member in manifest["tables"].items():
            data = archive.read(member["member"])
            if hashlib.sha256(data).hexdigest() != member["sha256"]:
                raise ValueError(f"SHA-256 mismatch for {member['member']}")
            i = 0
            for i, row in enumerate(read_dta118(data), 1):
                year = row["edition"]
                if year not in edition_dates:
                    raise ValueError(f"Unexpected NBER edition year {year}")
                locator = f"{member['member']} observation {i}"
                protection = _protection(row, table, locator)
                (patents if table == "patent" else exclusivities)[year].append(protection)
                if protection["appl_type"] == "A":
                    continue
                name = row["active_ingredient"]
                ingredient = "" if name == "N/A" else name
                trade = row["trade_name"]
                identity = tuple(protection[k] for k in ("appl_no", "product_no", "appl_type"))
                products[year].setdefault((*identity, ingredient, trade), dict(
                    appl_no=identity[0], product_no=identity[1], appl_type=identity[2],
                    ingredient=ingredient, ingredient_key=ingredient_key_ob(ingredient),
                    trade_name=trade, approval_date=None, partial_ingredient=year < 2005,
                    locator=locator,
                ))
            if i != member["rows"]:
                raise ValueError(f"Unexpected observation count for {member['member']}")
    return {year: Edition(day, list(products[year].values()), patents[year], exclusivities[year],
                          protection_only=True)
            for year, day in edition_dates.items()}


def nber_sources(manifest, data_dir=DEFAULT_NBER_DIR):
    """Create annual sources with per-edition availability and a lazy archive reader."""
    files = manifest["archive"]
    annual_dates = {}
    sources = []

    @cache
    def load_archive():
        return _read_archive(Path(data_dir) / files["file"], manifest, annual_dates)

    for entry in manifest["editions"]:
        year = entry["year"]
        publication = entry.get("publication_date")
        edition_date = date.fromisoformat(publication) if publication else date(year, 12, 31)
        annual_dates[year] = edition_date
        available = edition_date if publication else date(year + 1, 1, 1)
        basis = "annual_publication" if publication else "annual_year_end_assumption"
        proof = dict(kind=basis, date=available.isoformat(), **entry)
        identity = {**files, "kind": "nber_annual", "edition_year": year}
        sources.append(EditionSource(edition_date, lambda y=year: load_archive()[y], identity, (proof,)))
    return sources
