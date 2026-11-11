"""Label-free, fixed S/G equivalence controls; no Neo4j or corpus encoding."""
import hashlib
from .mtm_runtime import InputBoundaryError
from .sg_relations_v2 import extract_family_v2


def query_keys(query_id,text,expected_sha256):
    if type(text) is not str or hashlib.sha256(text.encode()).hexdigest()!=expected_sha256:
        raise InputBoundaryError('canonical query text mismatch')
    result=extract_family_v2({'id':query_id,'title':'','abstract':text,'claims':''})
    return sorted({row['alias_key'] for row in result['records']})


def structured_rankings(keys,postings,universe):
    """Return full positive match rankings; S and G use independent traversals."""
    universe=set(universe); keys=set(keys)
    if any(not set(members)<=universe for members in postings.values()):
        raise InputBoundaryError('posting family outside frozen universe')
    # S: accumulate each distinct key posting.
    counts={}
    for key in sorted(keys):
        for fid in postings.get(key,{}):counts[fid]=counts.get(fid,0)+1
    s=sorted(counts,key=lambda fid:(-counts[fid],fid))
    # G: bipartite membership edges, then count distinct neighboring query keys.
    edges={(key,fid) for key,members in postings.items() if key in keys for fid in members}
    neighbors={}
    for key,fid in edges:neighbors.setdefault(fid,set()).add(key)
    g=sorted(neighbors,key=lambda fid:(-len(neighbors[fid]),fid))
    if s!=g or any(counts[fid]!=len(neighbors[fid]) for fid in s):
        raise InputBoundaryError('S/G complete ranking parity failure')
    return {'S':s,'G':g,'matched_key_counts':counts}


def fuse(baseline,structured,universe):
    known=set(universe)
    for ranking in (baseline,structured):
        if len(ranking)!=len(set(ranking)) or not set(ranking)<=known:
            raise InputBoundaryError('duplicate or unknown ranked family')
    if len(baseline)>200:raise InputBoundaryError('B0 top200 input required')
    if not structured:return list(baseline)
    scores={}
    for ranking in (baseline,structured):
        for rank,fid in enumerate(ranking,1):scores[fid]=scores.get(fid,0.0)+1/(60+rank)
    return sorted(scores,key=lambda fid:(-scores[fid],fid))[:200]
