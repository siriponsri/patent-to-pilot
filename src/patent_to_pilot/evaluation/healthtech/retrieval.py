"""HT-T1 known-link recovery; unjudged pairs are never inferred negatives."""
from __future__ import annotations

from collections import defaultdict
from typing import Literal

from patent_to_pilot.healthtech.contracts import canonical_patent_id, content_hash


def evaluate_known_links(*, expected_query_ids: list[str], references: dict[str, list[str]],
                         predictions: dict[str, list[str]], universe: list[str], k: int = 20,
                         statuses: dict[str, Literal["completed", "failed"]] | None = None) -> dict:
    if type(k) is not int or k < 1:
        raise ValueError("k must be a positive integer")
    expected = set(expected_query_ids)
    if not expected or len(expected) != len(expected_query_ids):
        raise ValueError("expected queries must be nonempty and unique")
    for mapping in (references, predictions, statuses or {}):
        if not set(mapping) <= expected:
            raise ValueError("unexpected query ID")
    corpus = {canonical_patent_id(p) for p in universe}
    if len(corpus) != len(universe):
        raise ValueError("universe contains duplicate canonical IDs")
    gold = {q:{canonical_patent_id(p) for p in references.get(q,[])} for q in expected_query_ids}
    if any(not links <= corpus for links in gold.values()):
        raise ValueError("reference ID absent from declared corpus")
    eligible = sorted(q for q in expected if gold[q])
    excluded = sorted(expected - set(eligible))
    if not eligible:
        raise ValueError("no queries with reference links; known recall is undefined")
    rows=[]
    for q in eligible:
        status=(statuses or {}).get(q, "completed" if q in predictions else "failed")
        if status not in {"completed", "failed"}:
            raise ValueError("unknown query status")
        if q not in predictions:
            status="failed"
        ranking=[]
        seen=set()
        for raw in predictions.get(q,[]):
            try:
                pid=canonical_patent_id(raw)
            except ValueError:
                pid=f"UNKNOWN:{raw}"
            if pid not in seen:
                ranking.append(pid);seen.add(pid)
        at_k=ranking[:k]
        hits=len(set(at_k)&gold[q]) if status=="completed" else 0
        rows.append({"query_id":q,"status":status,"known_links":len(gold[q]),"hits":hits,
                     "known_recall":hits/len(gold[q]),"unique_returned":len(ranking),
                     "unknown_ids_at_k":[p for p in at_k if p not in corpus]})
    return {"task_id":"HT-T1","metric":"macro_known_link_recall","k":k,
        "macro_known_link_recall":sum(r["known_recall"] for r in rows)/len(rows),
        "micro_known_link_recall":sum(r["hits"] for r in rows)/sum(r["known_links"] for r in rows),
        "eligible_query_ids":eligible,"eligible_query_ids_hash":content_hash(eligible),
        "excluded_unjudged_query_ids":excluded,"failed_query_ids":[r["query_id"] for r in rows if r["status"]=="failed"],
        "failure_rule":"missing or failed queries score zero; attempts/costs remain counted",
        "interpretation":"Recovery of declared known links only; neither exhaustive recall nor its established lower bound",
        "per_query":rows}


def shared_reference_groups(references: dict[str,list[str]], *, families: dict[str,str] | None = None) -> list[list[str]]:
    """Connected components for evaluator split preparation, never controller state.

    Family mappings must be independently sourced; absent mappings do not imply
    family independence. No fold count or significance claim is chosen here.
    """
    parent={q:q for q in references}
    def find(q):
        while parent[q]!=q:
            parent[q]=parent[parent[q]];q=parent[q]
        return q
    owners={}
    family_map={canonical_patent_id(k):v for k,v in (families or {}).items()}
    for q, links in references.items():
        for raw in links:
            pid=canonical_patent_id(raw)
            keys=[("patent",pid)]
            if pid in family_map:
                keys.append(("family",family_map[pid]))
            for key in keys:
                if key in owners:
                    parent[find(q)]=find(owners[key])
                else:
                    owners[key]=q
    groups=defaultdict(list)
    for q in sorted(parent):
        groups[find(q)].append(q)
    return sorted(groups.values(),key=lambda group:group[0])
