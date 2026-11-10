"""Local authored-ID allocation observation; never loads a corpus or model."""
import hashlib
import json
from pathlib import Path
import sys
import time
import tracemalloc

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'src'))
from patent_to_pilot.research.sacr_factorial import passage_order_digest  # noqa: E402

families = ['authored-family']
passages = [f'authored-passage-{i}' for i in range(100000)]
owner = np.zeros(len(passages), dtype=np.int64)


def legacy():
    rows = [(p, families[int(o)]) for p, o in zip(passages, owner, strict=True)]
    return hashlib.sha256(json.dumps(rows, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


observations = {}
for name, operation in [('legacy', legacy), ('streamed', lambda: passage_order_digest(families, owner, passages))]:
    tracemalloc.start()
    start = time.perf_counter()
    result = operation()
    elapsed = time.perf_counter() - start
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    observations[name] = dict(sha256=result, peak_traced_bytes=peak, wall_seconds=elapsed)
assert observations['legacy']['sha256'] == observations['streamed']['sha256']
print(json.dumps(dict(authored_passages=len(passages), input_allocated_before_tracing=True,
                     observations=observations), indent=2))
