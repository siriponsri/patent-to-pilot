"""Runtime-only S3 worker. Standard library, no evaluator imports."""

import argparse
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
from itertools import combinations
import json
from math import log1p
from pathlib import Path
import re
from time import perf_counter_ns, process_time_ns
import unicodedata


ARMS = ("static", "rerank", "complete_first", "coverage", "scope")
ACTIONS = 4
IDENTITY = ("unit_id", "source_id", "version", "sha256", "locator", "char_start",
            "char_end", "unit_sha256", "text")


def stamp():
    return datetime.now(timezone.utc).isoformat()


def digest(raw):
    return sha256(raw).hexdigest()


def ordered_hash(ids):
    return digest(json.dumps(ids, separators=(",", ":")).encode())


def normalize(text):
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())


def trigrams(text):
    text = normalize(text)
    return Counter(text[i:i + 3] for i in range(len(text) - 2))


THAI_DIGITS = str.maketrans("๐๑๒๓๔๕๖๗๘๙", "0123456789")
MONTHS = "มกราคม กุมภาพันธ์ มีนาคม เมษายน พฤษภาคม มิถุนายน กรกฎาคม สิงหาคม กันยายน ตุลาคม พฤศจิกายน ธันวาคม".split()
CHANNELS = (r"ไปรษณีย์|พัสดุ", r"ด้วยตนเอง|ส่งเอง|มาส่ง|เคาน์เตอร์")
THAI_PROPERTIES = (
    (r"กี่วัน|ระยะเวลา|ภายในวัน", r"\d+\s*วัน"),
    (r"ป้าย(?:แบบ|ชนิด)", r"ป้าย[^\s.,]+"),
    (r"อัตรา|ค่าซ่อม|ค่าธรรมเนียม|กี่บาท", r"\d+(?:[.,]\d+)?\s*บาท"),
    (r"น้ำหนัก", r"\d+(?:[.,]\d+)?\s*(?:กิโลกรัม|กรัม)"),
    (r"กี่ชั่วโมง|จำนวนชั่วโมง", r"\d+\s*ชั่วโมง"),
    (r"กี่เดือน|จำนวนเดือน", r"\d+\s*เดือน"),
    (r"สี(?:อะไร|ใด)|สีแบบ", r"สี[^\s.,]+"),
)
NUMBER_WORD = r"zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|\d+"
EN_PROPERTIES = (
    (r"how many (?:[\w-]+ ){0,2}([\w-]+)", "count"),
    (r"which ([\w-]+)", "item"),
    (r"what (?:is the )?([\w-]+(?: rating| diameter)?)", "item"),
)


def thai_dates(text):
    months = "|".join(MONTHS)
    return [(int(year), MONTHS.index(month) + 1, int(day)) for day, month, year in
            re.findall(rf"(\d{{1,2}})\s*({months})\s*(\d{{4}})", text.translate(THAI_DIGITS))]


def requirements(question, language):
    """Extract only wording-derived conditions, ordered by their text positions."""
    text = normalize(question).rstrip("?")
    if ";" in text:
        return tuple(dict.fromkeys(part.strip() for part in text.split(";") if part.strip()))
    scopes = []
    if language == "th":
        for date in thai_dates(text):
            year, month, day = date
            pos = re.search(rf"\b0?{day}\s*{MONTHS[month - 1]}\s*{year}",
                            text.translate(THAI_DIGITS))
            scopes.append((pos.start() if pos else 0, "date:" + "-".join(map(str, date))))
        for channel in CHANNELS:
            if match := re.search(channel, text):
                scopes.append((match.start(), "phrase:" + channel))
        for trigger, pattern in THAI_PROPERTIES:
            if match := re.search(trigger, text):
                scopes.append((match.start(), "thai_property:" + pattern))
                break
    else:
        for pattern in (
            r"\b(?:clip|drum|lever|hinge|arm|version|embodiment|configuration|variant)\s+([a-z0-9]+)\b(?=,)",
            r"\b(?:the|its|'s)\s+([a-z0-9-]+)\s+(?:clip|drum|lever|hinge|arm)\b",
            r"\b([a-z0-9-]+)\s+(?:clip|drum|lever|hinge|arm)\b(?=\s+(?:use|have|in)|[?.]|$)",
            r"\b(?:for|on|with|in) the ([a-z0-9-]+)\s+(?:[a-z0-9-]+\s+){0,2}(?:spool|variant|configuration|embodiment|version|model)\b",
        ):
            if match := re.search(pattern, text):
                scopes.append((match.start(1), "word:" + match[1]))
                break
        for pattern, kind in EN_PROPERTIES:
            if match := re.search(pattern, text):
                prop = match[1]
                if kind == "count":
                    # Preserve a count noun, including a count followed by a verb clause.
                    prop = re.split(r"\s+(?:guide|are|does|do|can|has|have|is)\b",
                                    match[0][9:].strip())[0].split()[-1]
                scopes.append((match.start(), f"{kind}:{prop}"))
                break
    if not any(value.startswith(("thai_property:", "count:", "item:")) for _, value in scopes):
        scopes.append((len(text), text))
    return tuple(value for _, value in sorted(scopes))


def property_match(text, kind, prop):
    if kind == "thai_property":
        return re.search(prop, text)
    noun = re.escape(prop)
    if kind == "count":
        return re.search(rf"\b({NUMBER_WORD})\s+{noun}\b", text)
    if kind == "item":
        return re.search(rf"\b{noun}\b[^.!?]*?\b(?:is|are|of)\s+"
                         r"(?:an?\s+)?([a-z0-9-]+)(?=\s*(?:[.,;!?]|$))", text)
    return None


def matches(unit, condition):
    text = normalize(unit["text"])
    kind, sep, value = condition.partition(":")
    if kind == "date":
        date = tuple(map(int, value.split("-")))
        dates = thai_dates(text)
        if dates and re.search(r"ตั้งแต่|ระหว่าง|ถึง", text):
            if len(dates) == 1 and (closed := re.search(
                    r"(\d{1,2})\s*(" + "|".join(MONTHS) + r")\s*ถึง", text.translate(THAI_DIGITS))):
                start = (dates[0][0], MONTHS.index(closed[2]) + 1, int(closed[1]))
                return start <= date <= dates[0]
            return dates[0] <= date and (len(dates) == 1 or date <= dates[-1])
        return False
    if kind == "phrase":
        return bool(re.search(value, text))
    if kind == "word":
        return bool(re.search(rf"\b{re.escape(value)}\b", text))
    if sep:
        return bool(property_match(text.translate(THAI_DIGITS), kind, value))
    return bool(condition and condition in text)


def search_text(condition):
    kind, sep, value = condition.partition(":")
    if not sep:
        return condition
    if kind == "date":
        year, month, day = map(int, value.split("-"))
        return f"{day} {MONTHS[month - 1]} {year}"
    if kind == "thai_property":
        return " ".join(re.findall(r"[ก-๙]+", value))
    return value.replace("|", " ")


def decision_from(unit, conditions, language):
    text = normalize(unit["text"]).translate(THAI_DIGITS)
    for condition in conditions:
        kind, _, value = condition.partition(":")
        if match := property_match(text, kind, value):
            return match[0] if kind == "thai_property" else match[1]
    match = re.search(r"(?:value|ค่า)\s*[:=]\s*([^.;]+)", unit["text"], re.I)
    return match[1].strip() if match else None


class Index:
    def __init__(self, units, edges):
        self.units = {unit["unit_id"]: unit for unit in units}
        self.terms = {uid: trigrams(unit["locator"] + " " + unit["text"])
                      for uid, unit in self.units.items()}
        self.length = {uid: sum(counts.values()) for uid, counts in self.terms.items()}
        self.average = sum(self.length.values()) / len(self.units)
        self.frequency = Counter(term for counts in self.terms.values() for term in counts)
        self.outgoing = {edge["from"]: edge["to"] for edge in edges if not edge["inferred"]}

    def bm25(self, uid, query_terms):
        counts = self.terms[uid]
        norm = 1.2 * (0.25 + 0.75 * self.length[uid] / self.average)
        n = len(self.units)
        return sum(
            log1p((n - self.frequency[term] + 0.5) / (self.frequency[term] + 0.5))
            * counts[term] * 2.2 / (counts[term] + norm)
            for term in sorted(query_terms) if term in counts
        )


class Meter:
    """The sole query-time access point to indexed candidates."""

    def __init__(self, index, question, seed):
        self.start = perf_counter_ns()
        self.cpu = process_time_ns()
        self.start_utc = stamp()
        self.index = index
        self.query_terms = trigrams(question)
        self.events = []
        self.visible = {}
        self.record("seed", seed)

    def record(self, kind, ids, **details):
        at = perf_counter_ns()
        if len(self.events) >= ACTIONS or len(ids) > 6:
            raise ValueError("candidate ceiling")
        for uid in ids:
            self.visible[uid] = (self.index.units[uid], self.index.outgoing.get(uid),
                                 self.index.bm25(uid, self.query_terms))
        self.events.append(dict(action=kind, inspected=list(ids), start_ns=at,
                                end_ns=perf_counter_ns(), utc=stamp(), **details))

    def acquire(self, pool, condition, target):
        # All six eligible candidates are depth-accounted, including repeats.
        ids = sorted(self.index.units)
        terms = trigrams(search_text(condition))
        self.record("acquire", ids, condition=condition, target=target, selected=[])
        available = [uid for uid in ids if uid not in pool]
        if available:
            best = min(available, key=lambda uid: (uid != target,
                       -self.index.bm25(uid, terms), uid))
            self.events[-1]["selected"].append(best)
            self.events[-1]["end_ns"] = perf_counter_ns()
            return [*pool, best]
        return pool

    def rerank(self, pool, conditions, complete_first):
        self.record("rerank", pool)
        ranked = assignments(self, pool, conditions, complete_first)
        head = tuple(pool[:2])
        winner = ranked[0]
        if rank(self, head, conditions, complete_first) == rank(
                self, winner, conditions, complete_first):
            winner = head
        ordered = [*winner, *(uid for uid in pool if uid not in winner)]
        self.events[-1].update(ordered=ordered, chosen=winner, end_ns=perf_counter_ns())
        return ordered, winner


def hits(meter, ids, conditions):
    return {condition for uid in ids for condition in conditions
            if matches(meter.visible[uid][0], condition)}


def relation(meter, ids):
    return len(ids) == 2 and any(meter.visible[uid][1] in set(ids) - {uid} for uid in ids)


def rank(meter, ids, conditions, complete_first=False):
    lexical = sum(meter.visible[uid][2] for uid in sorted(ids))
    match_count = len(hits(meter, ids, conditions))
    if complete_first:
        return match_count, lexical
    return int(relation(meter, ids)), match_count, lexical


def assignments(meter, pool, conditions, complete_first=False):
    candidates = [(uid,) for uid in pool] + list(combinations(pool, 2))
    return sorted(candidates, key=lambda ids: (
        tuple(-value for value in rank(meter, ids, conditions, complete_first)),
        tuple(sorted(ids))))


def supported(meter, ids, conditions):
    return bool(conditions and relation(meter, ids)
                and hits(meter, ids, conditions) == set(conditions))


def missing(meter, pool, conditions):
    matched = hits(meter, pool, conditions)
    return next((cond for cond in conditions if cond not in matched), None)


def scope_lookup(meter, pool, conditions):
    outgoing = [uid for uid in pool if meter.visible[uid][1] not in (None, *pool)]
    outgoing = [uid for uid in outgoing if hits(meter, [uid], conditions)]
    if outgoing:
        anchor = min(outgoing, key=lambda uid: (
            -len(hits(meter, [uid], conditions)), -meter.visible[uid][2], uid))
        return missing(meter, [anchor], conditions) or conditions[0], meter.visible[anchor][1]
    return missing(meter, pool, conditions), None


def solve(index, request, arm):
    pool = request["seed_pool"]
    meter = Meter(index, request["question"], pool)
    conditions = requirements(request["question"], request["language"])
    chosen = tuple(pool[:2])
    reason = "static_seed"
    if arm in ("rerank", "complete_first"):
        pool, chosen = meter.rerank(pool, conditions, arm == "complete_first")
        reason = "fixed_pool"
    if arm == "coverage":
        while len(meter.events) < ACTIONS:
            condition = missing(meter, pool, conditions)
            if condition is None:
                pool, chosen = meter.rerank(pool, conditions, False)
                reason = "coverage_complete"
                break
            before = len(hits(meter, pool, conditions))
            new_pool = meter.acquire(pool, condition, None)
            improved = len(hits(meter, new_pool, conditions)) > before
            if new_pool != pool and len(meter.events) < ACTIONS:
                new_pool, chosen = meter.rerank(new_pool, conditions, False)
            pool = new_pool
            complete = missing(meter, pool, conditions) is None
            reason = ("coverage_complete" if complete else
                      "action_cap" if improved else "coverage_no_increase")
            if complete or not improved:
                break
    if arm == "scope":
        reason = "action_cap"
        while True:
            if supported(meter, chosen, conditions):
                reason = "leading_assignment_supported"
                break
            if len(meter.events) == ACTIONS:
                break
            pool_ids = set(pool)
            has_pair = any(
                supported(meter, (uid, target), conditions)
                for uid in pool if (target := meter.visible[uid][1]) in pool_ids
            )
            if has_pair:
                pool, chosen = meter.rerank(pool, conditions, False)
                reason = "compatible_assignment_reranked"
                break
            condition, target = scope_lookup(meter, pool, conditions)
            if condition is None or len(pool) == 6:
                reason = "unresolved_after_actions"
                break
            pool = meter.acquire(pool, condition, target)

    decision = None
    if supported(meter, chosen, conditions):
        target = next(uid for uid in chosen if meter.visible[uid][1] in chosen)
        target = meter.visible[target][1]
        decision = decision_from(meter.visible[target][0], conditions, request["language"])
    evidence = []
    if decision is not None:
        for uid in chosen:
            unit = meter.visible[uid][0]
            evidence.append(dict({key: unit[key] for key in IDENTITY}, role="support"))
    return dict(
        case_id=request["case_id"], arm=arm, initial_pool_hash=ordered_hash(request["seed_pool"]),
        conditions=conditions, events=meter.events, final_pool=pool, chosen=chosen,
        decision=decision if decision is not None else "ABSTAIN", evidence=evidence,
        stop=reason, start_ns=meter.start, end_ns=perf_counter_ns(), start_utc=meter.start_utc,
        cpu_ns=process_time_ns() - meter.cpu,
    )


def read_rows(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("runtime", type=Path)
    args = parser.parse_args()
    began = perf_counter_ns()
    cpu = process_time_ns()
    inputs = {name: read_rows(args.runtime / f"{name}.jsonl")
              for name in ("units", "edges", "requests", "sources")}
    families = {}
    for unit in inputs["units"]:
        families.setdefault(unit["family_id"], []).append(unit)
    indexes = {}
    for family, units in families.items():
        ids = {unit["unit_id"] for unit in units}
        indexes[family] = Index(units, [edge for edge in inputs["edges"] if edge["from"] in ids])
    print(json.dumps(dict(kind="ingestion", elapsed_ns=perf_counter_ns() - began,
                          cpu_ns=process_time_ns() - cpu,
                          bytes=sum((args.runtime / f"{name}.jsonl").stat().st_size for name in inputs))))
    for request in inputs["requests"]:
        for arm in ARMS:
            result = solve(indexes[request["family_id"]], request, arm)
            print(json.dumps(dict(kind="trial", **result), ensure_ascii=True), flush=True)


if __name__ == "__main__":
    main()
