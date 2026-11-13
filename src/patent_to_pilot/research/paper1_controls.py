"""Paper 1 amendment A1 controls (owner-approved 2026-11-13, before any FA/GR DAPFAM output).

Lessons from the owner's earlier GEPA papers (A-D): exact-zero deltas there suggest rewritten text never
reached the encoder; a scrambled prompt beat the designed one; query/corpus family overlap existed.
These controls are DESCRIPTIVE: they do not change H1-H3, delta, margins or the gatekeeping order.
"""
import hashlib
import random
import re
from .mtm_runtime import InputBoundaryError

IDENTITY_STOP_SHARE = 0.95  # arm identical to B0 on >95% of non-fallback queries -> engineering fault, stop before evaluation


def shuffled_query(query_id, text):
    """F-shuffle control input: the original TA words in a deterministic per-query random order (no LLM)."""
    if type(text) is not str or not text.strip():
        raise InputBoundaryError('nonempty query text required')
    words = re.findall(r'\S+', text)
    rng = random.Random(int(hashlib.sha256(('paper1-f-shuffle-v1|' + query_id).encode()).hexdigest()[:16], 16))
    rng.shuffle(words)
    return ' '.join(words)


def manipulation_check(b0, arm, used, depth=200):
    """b0/arm: {qid: [family ids]}; used: set of qids where the arm text was used (not fallback).

    Returns descriptive movement statistics and an ENGINEERING_FAULT verdict when the arm is (almost)
    identical to B0 on the queries where it should differ.
    """
    if set(arm) != set(b0) or not set(used) <= set(b0):
        raise InputBoundaryError('arm must rank exactly the B0 queries')
    identical, jaccard = 0, []
    for q in used:
        a, b = arm[q][:depth], b0[q][:depth]
        identical += a == b
        sa, sb = set(a), set(b)
        jaccard.append(len(sa & sb) / len(sa | sb) if sa | sb else 1.0)
    n = len(used)
    share = identical / n if n else None
    return {'used_queries': n, 'identical_top_k_share': share,
            'mean_top_k_jaccard': sum(jaccard) / n if n else None, 'depth': depth,
            'verdict': 'ENGINEERING_FAULT_ARM_DID_NOT_REACH_RETRIEVAL' if n and share > IDENTITY_STOP_SHARE else 'MOVEMENT_PRESENT'}


def truncation_share(token_counts, max_length):
    """Share of encoded arm texts whose token count exceeds the encoder max length (truncated)."""
    values = list(token_counts)
    if not values or type(max_length) is not int or max_length < 1:
        raise InputBoundaryError('token counts and max length required')
    return {'texts': len(values), 'truncated': sum(v > max_length for v in values),
            'share': sum(v > max_length for v in values) / len(values), 'max_length': max_length}


def family_overlap(query_ids, corpus_ids, qrels):
    """Query families that also occur in the corpus, and those that are their own positives."""
    corpus = set(corpus_ids)
    in_corpus = sorted(q for q in query_ids if q in corpus)
    self_positive = sorted(q for q in query_ids if q in set(qrels.get(q, ())))
    return {'queries': len(query_ids), 'query_families_in_corpus': len(in_corpus),
            'self_positive_queries': len(self_positive),
            'excluded_for_sensitivity': sorted(set(in_corpus) | set(self_positive))}
