"""Historical FDA Orange Book editions and leakage-safe as-of features.

Features use the latest edition available by the cutoff. If none exists the
result status is UNKNOWN (never a silent FALSE). Orange Book files carry no paragraph-IV
field; only patent Submission_Date (present from the 2018 editions on) is a challenge-timing
proxy, and it is reported as None when the edition lacks the column.
"""
import json
import os
import re
import zipfile
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Callable, Dict, List, Optional

from loe_bench.common import norm_ingredient

DEFAULT_DIR = "C:/Users/User/Desktop/myProject/_private_artifacts/loe-bench/ob_editions"
FILES = ("products", "patent", "exclusivity")
PRODUCT_COLS_NOTYPE = ["Ingredient", "DF;Route", "Trade_Name", "Applicant", "Strength", "Appl_No",
                       "Product_No", "TE_Code", "Approval_Date", "RLD", "Type", "Applicant_Full_Name"]
PATENT_COLS_NOTYPE = ["Appl_No", "Product_No", "Patent_No", "Patent_Expire_Date_Text",
                      "Drug_Substance_Flag", "Drug_Product_Flag", "Patent_Use_Code", "Delist_Flag"]
EXCL_COLS_NOTYPE = ["Appl_No", "Product_No", "Exclusivity_Code", "Exclusivity_Date"]


def parse_ob_date(s) -> Optional[date]:
    """'Apr 28, 2020' -> date; 'Approved Prior to Jan 1, 1982' or blank -> None."""
    s = (s or "").strip()
    if not s or s.lower().startswith("approved prior"):
        return None
    try:
        return datetime.strptime(s, "%b %d, %Y").date()
    except ValueError:
        return None


def ingredient_key_ob(ingredient: str) -> str:
    """Same format as common.ingredient_key: sorted normalised moieties joined by '|'."""
    parts = [norm_ingredient(p) for p in (ingredient or "").split(";")]
    return "|".join(sorted({p for p in parts if p}))


def norm_appl_no(x) -> str:
    return re.sub(r"\D", "", str(x or "")).zfill(6)


def _read_table(text: str, fallback_cols: List[str]) -> List[Dict[str, str]]:
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if not lines:
        return []
    first = [c.strip() for c in lines[0].split("~")]
    if "Appl_No" in first or "Ingredient" in first:
        cols, body = [c.lower() for c in first], lines[1:]
    else:  # headerless early editions (2009)
        cols, body = [c.lower() for c in fallback_cols], lines
    rows = []
    for ln in body:
        v = ln.split("~")
        v += [""] * (len(cols) - len(v))
        rows.append({c: v[i].strip() for i, c in enumerate(cols)})
    return rows


def parse_products(text: str) -> List[dict]:
    out = []
    for position, r in enumerate(_read_table(text, PRODUCT_COLS_NOTYPE), 1):
        out.append(dict(appl_no=norm_appl_no(r.get("appl_no")), product_no=r.get("product_no", ""),
                        appl_type=r.get("appl_type", ""), ingredient=r.get("ingredient", ""),
                        ingredient_key=ingredient_key_ob(r.get("ingredient", "")),
                        trade_name=r.get("trade_name", ""), rld=r.get("rld", ""), type=r.get("type", ""),
                        approval_date=parse_ob_date(r.get("approval_date")),
                        approval_date_text=r.get("approval_date", ""), form_route=r.get("df;route", ""),
                        strength=r.get("strength", ""), locator=f"products data row {position}"))
    return out


def parse_patents(text: str) -> List[dict]:
    out = []
    for position, r in enumerate(_read_table(text, PATENT_COLS_NOTYPE), 1):
        has_sub = "submission_date" in r
        out.append(dict(appl_no=norm_appl_no(r.get("appl_no")), product_no=r.get("product_no", ""),
                        patent_no=r.get("patent_no", ""),
                        appl_type=r.get("appl_type", ""),
                        expiry=parse_ob_date(r.get("patent_expire_date_text")),
                        drug_substance=r.get("drug_substance_flag", "") == "Y",
                        drug_product=r.get("drug_product_flag", "") == "Y",
                        use_code=r.get("patent_use_code", ""), delist=r.get("delist_flag", "") == "Y",
                        submission_date=parse_ob_date(r.get("submission_date")) if has_sub else None,
                        has_submission_col=has_sub, locator=f"patent data row {position}",
                        has_scope_flags=all(r.get(field) in {"", "Y", "N"} for field in
                                            ("drug_substance_flag", "drug_product_flag"))))
    return out


def parse_exclusivity(text: str) -> List[dict]:
    out = []
    for position, r in enumerate(_read_table(text, EXCL_COLS_NOTYPE), 1):
        out.append(dict(appl_no=norm_appl_no(r.get("appl_no")), product_no=r.get("product_no", ""),
                        appl_type=r.get("appl_type", ""),
                        code=r.get("exclusivity_code", ""), expiry=parse_ob_date(r.get("exclusivity_date")),
                        locator=f"exclusivity data row {position}"))
    return out


def read_zip_tables(path: str) -> Dict[str, str]:
    """Return {'products','patent','exclusivity'} text from a (case-insensitive) OB ZIP."""
    out = {}
    with zipfile.ZipFile(path) as z:
        for info in z.infolist():
            stem = os.path.splitext(os.path.basename(info.filename))[0].lower()
            if stem in FILES:
                out[stem] = z.read(info).decode("latin-1")
    missing = [f for f in FILES if f not in out]
    if missing:
        raise ValueError(f"{path}: missing members {missing}")
    return out


@dataclass
class Edition:
    edition_date: date
    products: List[dict]
    patents: List[dict]
    exclusivity: List[dict]
    by_appl: Dict[str, List[dict]] = field(default_factory=dict)
    by_ingr: Dict[str, List[dict]] = field(default_factory=dict)
    protection_only: bool = False

    def __post_init__(self):
        for p in self.products:
            self.by_appl.setdefault(p["appl_no"], []).append(p)
            self.by_ingr.setdefault(p["ingredient_key"], []).append(p)


def load_edition(path: str, edition_date: date) -> Edition:
    t = read_zip_tables(path)
    return Edition(edition_date, parse_products(t["products"]), parse_patents(t["patent"]),
                   parse_exclusivity(t["exclusivity"]))


_NONE_FIELDS = dict(listed=None, patents=None, exclusivities=None, n_patents=None, n_unexpired_patents=None,
                    max_patent_expiry=None, max_exclusivity_expiry=None, exclusivity_codes=None,
                    earliest_patent_submission=None, submission_date_available=None)


def _iso(d):
    return d.isoformat() if d else None


@dataclass(frozen=True, eq=False)
class EditionSource:
    edition_date: date
    loader: Callable[[], Edition]
    identity: Optional[dict] = None
    availability: tuple = ()


def _availability_proofs(entry, audit):
    sha = entry["sha256"]
    proofs = []
    for capture in (entry, *audit.get("additional_captures", {}).get(sha, ())):
        timestamp = capture.get("wayback_ts")
        if not timestamp or not re.fullmatch(r"[0-9]{14}", timestamp):
            continue
        captured = datetime.strptime(timestamp, "%Y%m%d%H%M%S").date()
        proofs.append(dict(kind="wayback", date=captured.isoformat(), wayback_ts=timestamp,
                           url=capture.get("wayback_url"), edition_sha256=sha))
    for record in audit.get("fda_publication_records", ()):
        # A listing at a shared download URL cannot identify the exact ZIP bytes.
        if record.get("edition_sha256") != sha:
            continue
        published = date.fromisoformat(record["publication_date"])
        proofs.append(dict(kind="fda_publication", date=published.isoformat(), url=record["source_url"],
                           html_sha256=record["html_sha256"], locator=record["locator"],
                           edition_sha256=sha))
    return tuple(sorted(proofs, key=lambda proof: proof["date"]))


class OBHistory:
    """Store edition sources or legacy (edition_date, loader) pairs without publication proof."""

    def __init__(self, editions):
        editions = list(editions)
        self._legacy = all(not isinstance(item, EditionSource) for item in editions)
        sources = (item if isinstance(item, EditionSource) else EditionSource(*item) for item in editions)
        self._ed = sorted(sources, key=lambda source: (
            source.edition_date, (source.identity or {}).get("kind") != "nber_annual"
        ))
        self._has_annual = any((s.identity or {}).get("kind") == "nber_annual" for s in self._ed)
        self._cache = {}
        self._feature_indexes = {}
        self.data_dir = None

    @classmethod
    def from_manifest(cls, manifest_path: str, data_dir: str = DEFAULT_DIR, **annual):
        with open(manifest_path, encoding="utf-8") as f:
            m = json.load(f)
        return cls.from_records(m, data_dir, **annual)

    @classmethod
    def from_records(cls, manifest, data_dir: str = DEFAULT_DIR, *, nber_manifest=None, nber_dir=None):
        sources = []
        for entry in manifest["editions"]:
            d = date.fromisoformat(entry["edition_date"])
            path = os.path.join(data_dir, entry["file"])
            identity = {name: entry[name] for name in ("file", "sha256", "source_url")}
            identity["kind"] = "fda_zip"
            sources.append(EditionSource(d, lambda p=path, d=d: load_edition(p, d), identity,
                                         _availability_proofs(entry, manifest.get("e2b", {}))))
        if nber_manifest is not None:
            from .nber_ob import DEFAULT_NBER_DIR, nber_sources
            sources.extend(nber_sources(nber_manifest, nber_dir or DEFAULT_NBER_DIR))
        history = cls(sources)
        history.data_dir = data_dir
        return history

    def edition_dates(self) -> List[date]:
        return [source.edition_date for source in self._ed]

    def available_source_asof(self, cutoff: date):
        """Find the latest source admitted by its recorded availability basis."""
        cutoff_iso = cutoff.isoformat()
        for source in reversed(self._ed):
            if source.edition_date <= cutoff:
                for proof in source.availability:
                    if proof["date"] <= cutoff_iso:
                        return source, proof
        return None, None

    def load_source(self, source: EditionSource) -> Edition:
        if source not in self._cache:
            self._cache[source] = source.loader()
        return self._cache[source]

    def _dated_source_asof(self, cutoff):
        for source in reversed(self._ed):
            if source.edition_date <= cutoff:
                return source
        return None

    def edition_asof(self, cutoff: date) -> Optional[Edition]:
        """Select an admitted mixed-source edition, or a date-only edition for legacy audits."""
        source = self.available_source_asof(cutoff)[0] if self._has_annual else self._dated_source_asof(cutoff)
        return self.load_source(source) if source else None

    def features_asof(self, key: str, cutoff: date, *, linker=None) -> dict:
        """key: Appl_No (digits only, e.g. '020571') or an ingredient key ('A|B', 'A;B' or raw name)."""
        source, proof = self.available_source_asof(cutoff)
        if source is None and self._legacy:
            source = self._dated_source_asof(cutoff)
        res = dict(status="UNKNOWN", reason="no edition available by cutoff",
                   cutoff=cutoff.isoformat(), edition_date=None, source=None,
                   availability_proof=None, **_NONE_FIELDS)
        if source is None:
            return res
        ed = self.load_source(source)
        res.update(edition_date=ed.edition_date.isoformat(), source=source.identity,
                   availability_proof=proof)
        k = (key or "").strip()
        if k.isdigit():
            prods = ed.by_appl.get(norm_appl_no(k), [])
            if ed.protection_only:
                prods = [p for p in prods if (
                    linker.application_type(p) if linker else p["appl_type"]
                ) == "N"]
            pk = {(p["appl_no"], p["product_no"]) for p in prods}
        elif linker is not None:
            from .t2_features import _EditionIndex
            cache_key = source, linker
            if cache_key not in self._feature_indexes:
                self._feature_indexes[cache_key] = _EditionIndex(ed, linker=linker)
            pk = self._feature_indexes[cache_key].by_key.get(linker.canonical(k), ())
        elif ed.protection_only:
            res.update(reason="annual moiety lookup requires the FIX2c identity crosswalk")
            return res
        else:
            ik = "|".join(sorted({norm_ingredient(p) for p in re.split(r"[;|]", k) if norm_ingredient(p)}))
            pk = {(p["appl_no"], p["product_no"]) for p in ed.by_ingr.get(ik, [])}
        if not pk:
            if ed.protection_only:
                res.update(reason="key absent from the annual patent and exclusivity tables")
                return res
            res.update(status="NOT_LISTED", reason="key absent from selected edition", listed=False,
                       patents=[], exclusivities=[], n_patents=0, n_unexpired_patents=0,
                       exclusivity_codes=[])
            return res
        pats = [p for p in ed.patents if (p["appl_no"], p["product_no"]) in pk]
        exs = [x for x in ed.exclusivity if (x["appl_no"], x["product_no"]) in pk]
        if ed.protection_only:
            pats = [p for p in pats if p["appl_type"] != "A"]
            exs = [x for x in exs if x["appl_type"] != "A"]
        pe = [p["expiry"] for p in pats if p["expiry"]]
        xe = [x["expiry"] for x in exs if x["expiry"]]
        subs = [p["submission_date"] for p in pats if p["submission_date"]]
        res.update(
            status="OK", reason="", listed=True, n_patents=len({p["patent_no"] for p in pats}),
            n_unexpired_patents=len({p["patent_no"] for p in pats if p["expiry"] and p["expiry"] > cutoff}),
            max_patent_expiry=_iso(max(pe)) if pe else None,
            max_exclusivity_expiry=_iso(max(xe)) if xe else None,
            exclusivity_codes=sorted({x["code"] for x in exs if x["code"]}),
            earliest_patent_submission=_iso(min(subs)) if subs else None,
            submission_date_available=any(p["has_submission_col"] for p in pats) if pats else None,
            patents=[dict(patent_no=p["patent_no"], expiry=_iso(p["expiry"]), use_code=p["use_code"],
                          drug_substance=p["drug_substance"], drug_product=p["drug_product"],
                          delist=p["delist"], submission_date=_iso(p["submission_date"])) for p in pats],
            exclusivities=[dict(code=x["code"], expiry=_iso(x["expiry"])) for x in exs])
        return res


def zip_edition_date(path: str) -> date:
    with zipfile.ZipFile(path) as z:
        return max(date(*i.date_time[:3]) for i in z.infolist())


def build_manifest(data_dir: str, provenance: List[dict], out_path: str, extra: Optional[dict] = None):
    """Write OB_EDITIONS.json. provenance: dicts with file, source_url, wayback_ts, sha256, ..."""
    import hashlib
    eds = []
    for pv in provenance:
        p = os.path.join(data_dir, pv["file"])
        with open(p, "rb") as f:
            sha = hashlib.sha256(f.read()).hexdigest()
        if sha != pv["sha256"]:
            raise ValueError(f"sha256 mismatch for {pv['file']}")
        t = read_zip_tables(p)
        pt, pa, ex = parse_products(t["products"]), parse_patents(t["patent"]), parse_exclusivity(t["exclusivity"])
        e = dict(pv)
        e.update(edition_date=zip_edition_date(p).isoformat(),
                 edition_date_basis="max ZIP member modification date",
                 rows=dict(products=len(pt), patent=len(pa), exclusivity=len(ex)),
                 has_submission_date=any(x["has_submission_col"] for x in pa))
        eds.append(e)
    eds.sort(key=lambda e: e["edition_date"])
    m = dict(editions=eds)
    m.update(extra or {})
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(m, f, indent=1)
    return m
