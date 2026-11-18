"""Canonical split and leakage manifest for P1-BridgeRet / P2-CEDS / P3-EG-SHE.

Implements the executable parts of the owner split specification
(owner-note-18112026/01_SPLIT_AND_LEAKAGE_MANIFEST_SPEC.md, SPLIT-SPEC-0.1 PROPOSED)
together with the owner decisions recorded on 2026-11-17
(docs/healthtech/research/plans/owner-decisions-20261117-bridgeret.json):

- TRAIN = filing years 2006-2009 (O1, OWNER_DECISION)
- VAL   = a hash-ordered sample from filing year 2010 (PROPOSED size 2,000)
- 2011  = group-hash 50/50 into P1-DEV (bucket 0) and P2-DEV (bucket 1) (D1, PROPOSED)
- 2012  = reverse sha256('p2-oa-split-v1|' + app_id) order; P1-TEST = last N1 (O2: 10,000),
          P2-TEST = prefix, disjoint (OWNER_DECISION rule); family-aware option A PROPOSED
- 2013  = P3-TEST, untouched

Access boundary. The builder only reads METADATA columns (application id, filing date,
art unit, primary IPC4). Label-derived columns (K(q), cited documents, n_K ...) are refused by
``read_task_metadata``. Gold labels of protected TEST blocks are only reachable through
``ProtectedGoldGate``, which requires an owner approval record bound to the SHA256 of a frozen
manifest. Nothing in this module computes a retrieval score.

Stdlib only so that it runs unchanged on dr-train (python3 -I).
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable, Mapping

MANIFEST_FORMAT = 'ptp-canonical-split-manifest-v1'
SPEC_VERSION = 'SPLIT-SPEC-0.1+owner-decisions-20261117'

# Salts. P2_OA_SALT is OWNER_DECISION (O2 rule, verbatim). The others are PROPOSED constants;
# changing any of them is a logged pre-freeze amendment.
P2_OA_SALT = 'p2-oa-split-v1'
DEV_2011_SALT = 'ptp-2011-dev-split-v1'
VAL_2010_SALT = 'ptp-2010-val-v1'

TRAIN_YEARS = (2006, 2007, 2008, 2009)
VAL_YEAR, DEV_YEAR, TEST12_YEAR, P3_YEAR = 2010, 2011, 2012, 2013
DEFAULT_N1 = 10_000          # O2 OWNER_DECISION
DEFAULT_VAL_N = 2_000        # PROPOSED
DEFAULT_IMBALANCE_TOL = 0.05  # OPEN_DECISION, recommendation +/-5 %

BLOCKS = ('TRAIN', 'VAL', 'P1-DEV', 'P2-DEV', 'P1-TEST', 'P2-TEST', 'P3-TEST')
PROTECTED_BLOCKS = frozenset({'P1-TEST', 'P2-TEST', 'P3-TEST'})

METADATA_COLUMNS = frozenset({'app_id', 'filing_date', 'art_unit', 'ipc4_primary'})
LABEL_COLUMNS = frozenset({'cited', 'basis', 'dom_ipc3', 'dom_ipc4', 'section', 'n_K',
                           'n_K_out3', 'n_foreign_102_103', 'qrels', 'gold', 'relevance'})

FAMILY_PENDING = 'FAMILY_DISJOINTNESS_PENDING'
SPLIT_RULE_CONFLICT = 'SPLIT_RULE_CONFLICT'


class ManifestError(RuntimeError):
    """A spec assertion failed or an input violated the access boundary."""


class ProtectedAccessError(ManifestError):
    """Protected TEST gold was requested without a valid approval bound to a frozen manifest."""


# ---------------------------------------------------------------- hashing utilities

def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def salted_key(salt: str, ident: str) -> str:
    """sha256(salt + '|' + ident) as hex (spec sections 3 and 4)."""
    if not ident or '|' in salt:
        raise ManifestError('empty identifier or invalid salt')
    return sha256_hex(f'{salt}|{ident}')


def canonical_json(obj) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(',', ':'))


def object_sha256(obj) -> str:
    return sha256_hex(canonical_json(obj))


def file_sha256(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(chunk), b''):
            h.update(b)
    return h.hexdigest()


def hashed_id(app_id: str, release_salt: str) -> str:
    """ID hygiene (L-H): released manifests carry salted hashes, never raw IDs."""
    return salted_key(release_salt, app_id)[:24]


# ---------------------------------------------------------------- metadata input

@dataclass(frozen=True)
class TaskMeta:
    app_id: str
    filing_year: int
    art_unit: str = ''
    ipc4_primary: str = ''


_YEAR = re.compile(r'^(19|20)\d\d')


def read_task_metadata(lines: Iterable[str], delimiter: str = '\t') -> list[TaskMeta]:
    """Read only metadata columns from a task table; refuse anything else being requested.

    The task table may physically contain label-derived columns. They are never read into
    memory: we keep only METADATA_COLUMNS from each row and fail if required columns are missing.
    """
    reader = csv.DictReader(lines, delimiter=delimiter)
    header = set(reader.fieldnames or [])
    if not {'app_id', 'filing_date'} <= header:
        raise ManifestError('task table lacks app_id/filing_date')
    out, seen = [], set()
    for row in reader:
        aid = (row.get('app_id') or '').strip()
        fd = (row.get('filing_date') or '').strip()
        if not aid or not _YEAR.match(fd):
            raise ManifestError(f'bad metadata row (app_id={aid!r})')
        if aid in seen:
            raise ManifestError(f'duplicate app_id {aid}')
        seen.add(aid)
        out.append(TaskMeta(aid, int(fd[:4]), (row.get('art_unit') or '').strip(),
                            (row.get('ipc4_primary') or '').strip()))
    return out


def assert_metadata_only(columns: Iterable[str]) -> None:
    """Fail if a caller asks the builder for any column outside the metadata allowlist."""
    bad = sorted(set(columns) - METADATA_COLUMNS)
    if bad:
        raise ProtectedAccessError(f'non-metadata columns requested: {bad}')


# ---------------------------------------------------------------- family grouping

class _UnionFind:
    def __init__(self):
        self.p: dict[str, str] = {}

    def find(self, x: str) -> str:
        self.p.setdefault(x, x)
        root = x
        while self.p[root] != root:
            root = self.p[root]
        while self.p[x] != root:
            self.p[x], x = root, self.p[x]
        return root

    def union(self, a: str, b: str) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            lo, hi = sorted((ra, rb))      # deterministic representative
            self.p[hi] = lo


@dataclass
class Grouping:
    group_of: dict[str, str]
    source: str          # 'family_id' | 'parent_closure' | 'singleton'
    status: str          # 'FAMILY_AWARE' | FAMILY_PENDING
    max_group_size: int


def build_groups(app_ids: Iterable[str],
                 family_ids: Mapping[str, str] | None = None,
                 related_links: Iterable[tuple[str, str]] | None = None) -> Grouping:
    """Spec section 3 precedence: family_id > parent_app_id closure > singleton (PENDING).

    ``related_links`` are (app_id, related_app_id) pairs from continuity tables (continuation,
    divisional, CIP). Linked applications outside ``app_ids`` still join components, because a
    sibling that is not itself a task can bridge two tasks.
    """
    ids = list(app_ids)
    if family_ids:
        missing = [a for a in ids if not family_ids.get(a)]
        if missing:
            raise ManifestError(f'{len(missing)} tasks lack family_id; use closure or singleton')
        g = {a: 'F:' + family_ids[a] for a in ids}
        src, status = 'family_id', 'FAMILY_AWARE'
    elif related_links is not None:
        uf = _UnionFind()
        for a in ids:
            uf.find(a)
        for a, b in related_links:
            if a and b:
                uf.union(a, b)
        g = {a: 'C:' + uf.find(a) for a in ids}
        src, status = 'parent_closure', 'FAMILY_AWARE'
    else:
        g = {a: 'A:' + a for a in ids}
        src, status = 'singleton', FAMILY_PENDING
    sizes: dict[str, int] = {}
    for v in g.values():
        sizes[v] = sizes.get(v, 0) + 1
    return Grouping(g, src, status, max(sizes.values(), default=0))


# ---------------------------------------------------------------- block assignment

def dev_bucket(group_id: str, salt: str = DEV_2011_SALT) -> int:
    """0 -> P1-DEV, 1 -> P2-DEV (spec section 3)."""
    return int(salted_key(salt, group_id), 16) % 2


def order_2012(app_ids: Iterable[str], salt: str = P2_OA_SALT) -> list[str]:
    """Owner rule: sort by sha256(salt|app_id), reverse order (spec section 4)."""
    return sorted(app_ids, key=lambda a: salted_key(salt, a), reverse=True)


def split_2012(eligible: Iterable[str], n1: int = DEFAULT_N1, n_p2: int | None = None,
               salt: str = P2_OA_SALT) -> tuple[list[str], list[str]]:
    ordered = order_2012(eligible, salt)
    if n1 <= 0 or n1 > len(ordered):
        raise ManifestError(f'n1={n1} invalid for {len(ordered)} eligible 2012 tasks')
    cap = len(ordered) - n1
    n_p2 = cap if n_p2 is None else n_p2
    if not 0 <= n_p2 <= cap:
        raise ManifestError(f'n_p2={n_p2} exceeds eligible - n1 = {cap}')
    p1, p2 = ordered[-n1:], ordered[:n_p2]
    if set(p1) & set(p2):
        raise ManifestError('P1-TEST and P2-TEST overlap')
    return p1, p2


def sample_val(app_ids: Iterable[str], n: int = DEFAULT_VAL_N, salt: str = VAL_2010_SALT) -> list[str]:
    ordered = sorted(app_ids, key=lambda a: salted_key(salt, a))
    return ordered[:n]


@dataclass
class SplitConfig:
    n1: int = DEFAULT_N1
    n_p2: int | None = None
    val_n: int = DEFAULT_VAL_N
    imbalance_tolerance: float = DEFAULT_IMBALANCE_TOL
    family_conflict_option: str = 'A'   # spec 4 recommendation; 'B' needs an amendment
    salts: dict = field(default_factory=lambda: {
        'p2_oa': P2_OA_SALT, 'dev_2011': DEV_2011_SALT, 'val_2010': VAL_2010_SALT})

    def as_dict(self) -> dict:
        return {'n1': self.n1, 'n_p2': self.n_p2, 'val_n': self.val_n,
                'imbalance_tolerance': self.imbalance_tolerance,
                'family_conflict_option': self.family_conflict_option, 'salts': dict(self.salts)}


def assign_blocks(tasks: list[TaskMeta], grouping: Grouping, cfg: SplitConfig) -> dict:
    """Return {'blocks': {name: sorted ids}, 'notes': [...], 'stats': {...}}."""
    if cfg.family_conflict_option not in ('A',):
        raise ManifestError('only option A is implemented; option B needs a logged amendment')
    by_year: dict[int, list[str]] = {}
    for t in tasks:
        by_year.setdefault(t.filing_year, []).append(t.app_id)
    blocks = {b: [] for b in BLOCKS}
    notes: list[str] = []
    for y in TRAIN_YEARS:
        blocks['TRAIN'] += by_year.get(y, [])
    blocks['VAL'] = sample_val(by_year.get(VAL_YEAR, []), cfg.val_n, cfg.salts['val_2010'])
    for a in by_year.get(DEV_YEAR, []):
        b = dev_bucket(grouping.group_of[a], cfg.salts['dev_2011'])
        blocks['P1-DEV' if b == 0 else 'P2-DEV'].append(a)
    p1, p2 = split_2012(by_year.get(TEST12_YEAR, []), cfg.n1, cfg.n_p2, cfg.salts['p2_oa'])
    p1_groups = {grouping.group_of[a] for a in p1}
    removed = [a for a in p2 if grouping.group_of[a] in p1_groups]
    if removed:
        notes.append(f'{SPLIT_RULE_CONFLICT}: option A removed {len(removed)} P2-TEST tasks '
                     'whose group intersects P1-TEST')
    blocks['P1-TEST'] = p1
    blocks['P2-TEST'] = [a for a in p2 if a not in set(removed)]
    blocks['P3-TEST'] = list(by_year.get(P3_YEAR, []))
    ignored = sorted(y for y in by_year if y not in (*TRAIN_YEARS, VAL_YEAR, DEV_YEAR, TEST12_YEAR, P3_YEAR))
    if ignored:
        notes.append(f'filing years outside every block (not used): {ignored}')
    if grouping.status == FAMILY_PENDING:
        notes.append(f'{FAMILY_PENDING}: grouping is singleton; the claim "family-disjoint" may not '
                     'be made and the proxy audit (L-C) is mandatory')
    n_dev = len(blocks['P1-DEV']) + len(blocks['P2-DEV'])
    imb = abs(len(blocks['P1-DEV']) - len(blocks['P2-DEV'])) / n_dev if n_dev else 0.0
    stats = {'dev_2011_imbalance': round(imb, 6),
             'dev_2011_imbalance_ok': imb <= cfg.imbalance_tolerance,
             'p2_test_removed_by_family_rule': len(removed),
             'p2_test_cap': len(by_year.get(TEST12_YEAR, [])) - cfg.n1}
    if not stats['dev_2011_imbalance_ok']:
        notes.append('2011 bucket imbalance exceeds tolerance: re-salting only via a logged '
                     'pre-freeze amendment, never by moving groups by hand')
    return {'blocks': {k: sorted(v) for k, v in blocks.items()}, 'notes': notes, 'stats': stats}


# ---------------------------------------------------------------- assertions (spec section 7)

def run_assertions(blocks: Mapping[str, list[str]], grouping: Grouping, n1: int,
                   eligible_2012: int) -> list[dict]:
    S = {k: set(v) for k, v in blocks.items()}
    G = {k: {grouping.group_of[a] for a in v} for k, v in blocks.items()}
    res: list[dict] = []

    def add(aid, desc, ok, detail=None):
        res.append({'id': aid, 'check': desc, 'result': 'PASS' if ok else 'FAIL',
                    **({'detail': detail} if detail is not None else {})})

    pairs = [(a, b) for i, a in enumerate(BLOCKS) for b in BLOCKS[i + 1:]]
    over = {f'{a}&{b}': len(S[a] & S[b]) for a, b in pairs if S[a] & S[b]}
    add('A1-A4', 'app_id disjoint across all blocks', not over, over or None)
    if grouping.status == FAMILY_PENDING:
        res.append({'id': 'L-B', 'check': 'group_id disjoint P1-DEV/P2-DEV and P1-TEST/P2-TEST',
                    'result': 'NOT_ASSESSABLE', 'detail': FAMILY_PENDING})
    else:
        gd = len(G['P1-DEV'] & G['P2-DEV'])
        gt = len(G['P1-TEST'] & G['P2-TEST'])
        add('L-B', 'group_id disjoint P1-DEV/P2-DEV and P1-TEST/P2-TEST', gd == 0 and gt == 0,
            {'dev_shared_groups': gd, 'test_shared_groups': gt})
    add('A3', 'n_p2 <= eligible_2012 - n1 and |P1-TEST| == n1',
        len(S['P2-TEST']) <= eligible_2012 - n1 and len(S['P1-TEST']) == n1,
        {'n_p1': len(S['P1-TEST']), 'n_p2': len(S['P2-TEST']), 'eligible_2012': eligible_2012})
    # cross-year family exposure is reported as a stratum, never deleted (spec 4)
    earlier = G['TRAIN'] | G['VAL'] | G['P1-DEV'] | G['P2-DEV']
    seen = {b: len([a for a in blocks[b] if grouping.group_of[a] in earlier])
            for b in ('P1-TEST', 'P2-TEST', 'P3-TEST')}
    res.append({'id': 'L-B-xyear', 'check': 'TEST tasks whose group also occurs in TRAIN/VAL/DEV',
                'result': 'REPORT', 'detail': seen})
    return res


def assert_all_pass(results: list[dict]) -> None:
    bad = [r for r in results if r['result'] == 'FAIL']
    if bad:
        raise ManifestError(f'assertions failed: {[r["id"] for r in bad]}')


# ---------------------------------------------------------------- leakage audits (interfaces)

def shingles(text: str, k: int = 5) -> set[str]:
    toks = re.findall(r'\w+', text.lower())
    if len(toks) < k:
        return {' '.join(toks)} if toks else set()
    return {' '.join(toks[i:i + k]) for i in range(len(toks) - k + 1)}


def minhash_signature(text: str, num_perm: int = 64, k: int = 5) -> tuple[int, ...]:
    sh = shingles(text, k)
    if not sh:
        return tuple([2 ** 64 - 1] * num_perm)
    sig = []
    for i in range(num_perm):
        sig.append(min(int.from_bytes(hashlib.blake2b(f'{i}|{s}'.encode(), digest_size=8).digest(), 'big')
                       for s in sh))
    return tuple(sig)


def minhash_jaccard(a: tuple[int, ...], b: tuple[int, ...]) -> float:
    if len(a) != len(b) or not a:
        raise ManifestError('signature length mismatch')
    return sum(x == y for x, y in zip(a, b)) / len(a)


def near_duplicate_strata(query_claims: Mapping[str, str], reference_claims: Mapping[str, str],
                          threshold: float = 0.8, num_perm: int = 64) -> dict[str, bool]:
    """L-C: dup=True if claim-1 MinHash Jaccard >= threshold against any reference claim.

    Brute force; adequate for fixtures and DEV-scale audits. A banded LSH index replaces it at
    corpus scale without changing the definition.
    """
    ref = [minhash_signature(t, num_perm) for t in reference_claims.values()]
    return {q: any(minhash_jaccard(minhash_signature(t, num_perm), r) >= threshold for r in ref)
            for q, t in query_claims.items()}


def unseen_document_tags(task_positives: Mapping[str, Iterable[str]],
                         train_positives: Iterable[str], train_query_docs: Iterable[str]) -> dict:
    """L-D: tag each positive seen/unseen in TRAIN and report per-task 'all unseen' strata."""
    seen = set(train_positives) | set(train_query_docs)
    per_task, n_pos, n_seen = {}, 0, 0
    for t, pos in task_positives.items():
        pos = set(pos)
        s = pos & seen
        n_pos += len(pos)
        n_seen += len(s)
        per_task[t] = {'n_pos': len(pos), 'n_seen': len(s), 'unseen_positives': sorted(pos - seen)}
    return {'per_task': per_task,
            'share_positives_seen': (n_seen / n_pos) if n_pos else None,
            'tasks_all_unseen': sum(1 for v in per_task.values() if v['n_seen'] == 0)}


def self_target_violations(queries: Mapping[str, Iterable[str]], query_doc_ids: Mapping[str, str]) -> list[str]:
    """L-E: a task's own application/publication document must never be a target for it."""
    return sorted(q for q, targets in queries.items() if query_doc_ids.get(q) in set(targets))


# ---------------------------------------------------------------- protected gold gate

@dataclass(frozen=True)
class GoldApproval:
    manifest_sha256: str
    blocks: tuple[str, ...]
    approved_by: str
    approved_at: str
    purpose: str


def load_approval(path: Path) -> GoldApproval:
    d = json.loads(Path(path).read_text(encoding='utf-8'))
    need = {'manifest_sha256', 'blocks', 'approved_by', 'approved_at', 'purpose'}
    if not need <= set(d):
        raise ProtectedAccessError(f'approval record lacks {sorted(need - set(d))}')
    return GoldApproval(d['manifest_sha256'], tuple(d['blocks']), d['approved_by'],
                        d['approved_at'], d['purpose'])


class ProtectedGoldGate:
    """Single entry point to protected TEST gold.

    Use is allowed only if (1) the manifest is frozen and its SHA256 matches the approval,
    (2) the requested block is in the approval, and (3) the block has not been opened before
    (one look per block, tracked in an append-only open log next to the manifest).
    Non-protected blocks (TRAIN/VAL/DEV) pass without approval.
    """

    def __init__(self, manifest: dict, open_log: Path, approval: GoldApproval | None = None):
        if not manifest.get('frozen'):
            self._frozen_sha = None
        else:
            self._frozen_sha = manifest_sha256(manifest)
        self.manifest, self.open_log, self.approval = manifest, Path(open_log), approval

    def _opened(self) -> set[str]:
        if not self.open_log.exists():
            return set()
        return {json.loads(l)['block'] for l in self.open_log.read_text(encoding='utf-8').splitlines() if l.strip()}

    def open(self, block: str, reader: Callable[[], dict]) -> dict:
        if block not in BLOCKS:
            raise ManifestError(f'unknown block {block}')
        if block in PROTECTED_BLOCKS:
            if self._frozen_sha is None:
                raise ProtectedAccessError('manifest is not frozen')
            a = self.approval
            if a is None or a.manifest_sha256 != self._frozen_sha:
                raise ProtectedAccessError('no approval bound to this frozen manifest')
            if block not in a.blocks:
                raise ProtectedAccessError(f'approval does not cover {block}')
            if block in self._opened():
                raise ProtectedAccessError(f'{block} was already opened once')
            with open(self.open_log, 'a', encoding='utf-8') as f:
                f.write(canonical_json({'block': block, 'manifest_sha256': self._frozen_sha,
                                        'approved_by': a.approved_by, 'purpose': a.purpose}) + '\n')
        return reader()


def sealed_corpus_union(positive_reader: Callable[[], Iterable[str]], visible_docs: Iterable[str],
                        order_salt: str) -> dict:
    """Challenge-1M builder boundary (resolves the 'corpus must contain TEST positives' vs
    'no protected gold before evaluation' conflict, PROPOSED).

    A restricted process calls this with a reader that yields protected positive doc ids. The
    return value contains only the unlabelled union, sorted by a salted hash so membership order
    carries no label information, plus counts and a digest of the positive set for later audit.
    The positive ids themselves are never returned.
    """
    pos = set(positive_reader())
    union = pos | set(visible_docs)
    return {'corpus_doc_ids': sorted(union, key=lambda d: salted_key(order_salt, d)),
            'n_corpus': len(union), 'n_enriched_positive': len(pos),
            'positive_set_sha256': object_sha256(sorted(pos))}


# ---------------------------------------------------------------- manifest

def manifest_sha256(manifest: dict) -> str:
    body = {k: v for k, v in manifest.items() if k not in ('frozen', 'manifest_sha256')}
    return object_sha256(body)


def build_manifest(tasks: list[TaskMeta], grouping: Grouping, cfg: SplitConfig,
                   inputs: Mapping[str, str], code_sha256: str, synthetic: bool) -> dict:
    """Assemble an UNFROZEN manifest. ``inputs`` maps dataset name -> file sha256."""
    a = assign_blocks(tasks, grouping, cfg)
    eligible_2012 = sum(1 for t in tasks if t.filing_year == TEST12_YEAR)
    results = run_assertions(a['blocks'], grouping, cfg.n1, eligible_2012)
    year_counts: dict[str, int] = {}
    for t in tasks:
        year_counts[str(t.filing_year)] = year_counts.get(str(t.filing_year), 0) + 1
    m = {'format': MANIFEST_FORMAT, 'spec_version': SPEC_VERSION,
         'synthetic': bool(synthetic),
         'config': cfg.as_dict(), 'config_sha256': object_sha256(cfg.as_dict()),
         'inputs': dict(sorted(inputs.items())), 'code_sha256': code_sha256,
         'grouping': {'source': grouping.source, 'status': grouping.status,
                      'max_group_size': grouping.max_group_size},
         'filing_year_counts': dict(sorted(year_counts.items())),
         'block_counts': {k: len(v) for k, v in a['blocks'].items()},
         'blocks': a['blocks'], 'stats': a['stats'], 'notes': a['notes'],
         'assertions': results, 'frozen': False}
    m['manifest_sha256'] = manifest_sha256(m)
    return m


def freeze(manifest: dict) -> dict:
    """Mark frozen after every assertion passed. Freezing never changes the hash."""
    assert_all_pass(manifest['assertions'])
    if manifest.get('synthetic'):
        raise ManifestError('a synthetic manifest cannot be frozen')
    if manifest_sha256(manifest) != manifest['manifest_sha256']:
        raise ManifestError('manifest content changed after hashing')
    out = dict(manifest)
    out['frozen'] = True
    return out


def public_view(manifest: dict, release_salt: str) -> dict:
    """Release form (spec section 9 / L-H): hashed ids only."""
    out = {k: v for k, v in manifest.items() if k != 'blocks'}
    out['blocks_hashed'] = {b: sorted(hashed_id(a, release_salt) for a in ids)
                            for b, ids in manifest['blocks'].items()}
    return out
