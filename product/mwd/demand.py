"""Descriptive Medicaid baseline from C4's pinned, retrospective inputs."""

from functools import lru_cache

from .contract import BENCH, read_json
from .inputs import verify


class Demand:
    def __init__(self, root, linker, keys):
        from loe_bench import c4

        self.c4 = c4
        self.root = root / "medicaid_sdud"
        self.files = read_json(BENCH / "C4_INPUTS.json")["files"]
        self.mapping = self.files["openfda-ndc-2026-11-27"]
        path = self.root / self.mapping["file"]
        verify(path, self.mapping["sha256"])
        crosswalk = c4.load_crosswalk(path, self.mapping["member"], self.mapping["vintage"])
        ingredients = {name for package in crosswalk.values() for name in package.ingredients}
        self.names = {}
        for name in ingredients:
            composition = linker.registry.composition([name])
            key = linker.canonical(composition.key)
            if key in keys and not composition.low_confidence:
                self.names[name] = key
        self.packages = {ndc: package for ndc, package in crosswalk.items()
                         if any(name in self.names for name in package.ingredients)}

    @lru_cache(maxsize=4)
    def baseline(self, year):
        file = self.files[f"sdud-{year}"]
        path = self.root / file["file"]
        verify(path, file["sha256"])
        period = self.c4.quarter(year, 2)
        quarters = self.c4.read_sdud(path, year)
        values = self.c4.aggregate(period, {ndc: row for ndc, row in quarters[period].items()
                                           if ndc in self.packages}, self.packages)
        return values.counts

    def add_claim(self, report, cutoff, key):
        year = int(cutoff[:4]) - 1
        file = self.files[f"sdud-{year}"]
        selected = sorted(name for name, linked in self.names.items() if linked == key)
        counts = self.baseline(year) if selected else {}
        names = [name for name in selected if counts.get(name) is not None]
        loc = f"Year={year}; Quarter=2; State=XX; FFSU and MCOU; "
        loc += "linked ingredient(s): " + (", ".join(selected) or key)
        sdud = report.source("sdud", "U.S. CMS", file["title"], file["download_last_modified"],
                             file["catalog_modified_utc"][:10], loc, file["url"], file["sha256"],
                             file["retrieved_utc"])
        ndc = report.source("sdud-ndc", "U.S. FDA", "National Drug Code directory",
                            self.mapping["vintage"], self.mapping["vintage"], self.mapping["locator"],
                            self.mapping["url"], self.mapping["sha256"], self.mapping["retrieved_utc"])
        if names:
            # Exact ingredient subsets can overlap via combination products.
            value = "; ".join(f"{name} {counts[name]:,}" for name in names)
            th = (f"ข้อมูล Medicaid ย้อนหลัง ไตรมาส 2 ปี {year} · จำนวนใบสั่งยาในชุดรหัสบรรจุภัณฑ์"
                  f"ที่เชื่อมโยงได้และข้อมูลครบ {value} ตัวเลขนี้ครอบคลุมเฉพาะชุดที่เชื่อมโยงได้")
            en = (f"Retrospective, vintage-uncontrolled Medicaid {year} Q2 prescription claims in "
                  f"complete linked-package subsets: {value}. National market demand remains unknown.")
        else:
            th = (f"ยังไม่ทราบความต้องการย้อนหลังจาก Medicaid ไตรมาส 2 ปี {year} "
                  "เพราะไม่พบกลุ่มรหัสบรรจุภัณฑ์ที่เชื่อมโยงได้และมีจำนวนใบสั่งยาครบ")
            en = (f"Retrospective Medicaid {year} Q2 baseline is unknown. No exact linked package "
                  "subset has complete prescription counts in the available vintage.")
        report.claim("demand", "market", th, en, [sdud, ndc], "known" if names else "unknown",
                     time_basis="retrospective_demand")
