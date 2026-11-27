"""Canonicalize compatible full-product keys and retain conflicting proposals."""
from collections import defaultdict
from dataclasses import dataclass


@dataclass(frozen=True)
class MoietyLinkage:
    canonical: dict[str, str]
    conflicts: tuple[dict, ...]

    def key(self, key: str) -> str:
        return self.canonical.get(key, key)


def _identified(key):
    return frozenset(part for part in key.split("|") if part.startswith(("U:", "E:")))


def _unresolved(key):
    return len(key.split("|")) - len(_identified(key))


def _compatible(keys):
    identifiers = {key: _identified(key) for key in keys}
    electrolytes = {frozenset(part for part in ids if part.startswith("E:"))
                    for ids in identifiers.values()}
    if len(electrolytes) != 1:
        return False
    complete = {ids for key, ids in identifiers.items() if not _unresolved(key)}
    if complete:
        if len(complete) != 1:
            return False
        target, = complete
        return all(ids <= target for ids in identifiers.values())
    return len({ids for ids in identifiers.values() if ids}) <= 1


def link_compositions(compositions):
    """Join equal full sets, then check exact-name links as entire components.

    Equal UNII sets already have equal keys. Electrolytes are identity
    constraints too. A partial key may gain an identifier for a missing
    ingredient, but cannot replace an identifier it already carries.
    """
    by_names = defaultdict(set)
    for composition in compositions:
        if composition.names and composition.key:
            by_names[tuple(sorted(composition.names))].add(composition.key)

    parents = {}

    def find(key):
        parents.setdefault(key, key)
        while parents[key] != key:
            parents[key] = parents[parents[key]]
            key = parents[key]
        return key

    # Build the proposed components first so an unresolved bridge cannot
    # join two different complete UNII sets in either traversal order.
    proposals = {names: sorted(keys) for names, keys in by_names.items() if len(keys) > 1}
    for keys in proposals.values():
        root = find(keys[0])
        for key in keys[1:]:
            parents[find(key)] = root
    components = defaultdict(list)
    for key in parents:
        components[find(key)].append(key)
    signatures = defaultdict(list)
    for names, keys in sorted(proposals.items()):
        signatures[find(keys[0])].append(names)

    canonical, conflicts = {}, []
    for root, keys in sorted(components.items(), key=lambda item: min(item[1])):
        if _compatible(keys):
            representative = min(keys, key=lambda key: (_unresolved(key), key))
            canonical.update({key: representative for key in keys if key != representative})
        else:
            conflicts.append(dict(
                names=signatures[root],
                keys=sorted(keys),
                identifiers={key: sorted(_identified(key)) for key in sorted(keys)},
            ))
    return MoietyLinkage(canonical, tuple(conflicts))
