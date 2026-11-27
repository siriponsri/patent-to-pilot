"""Read-only evaluator for the captured exposed handoff fixture."""
import argparse
import json
from pathlib import Path

from handoff_probe import ARMS, PACKET, ROOT, digest, verified_bytes


def evaluate(capture, keys):
    traces = capture["traces"]
    if traces.keys() != keys.keys() or any(set(arms) != set(ARMS) for arms in traces.values()):
        raise ValueError("incomplete case or arm inventory")
    outcomes = {}
    for case, arms in traces.items():
        allowed = keys[case]["valid"]
        context = keys[case]["patent_context"]
        scores = {}
        for arm, trace in arms.items():
            outgoing = trace["handoffs"]["correspondence"]
            issued = outgoing["status"] == "supported"
            source = outgoing["applicant_source"]
            reads = trace["reads"]
            if len(set(reads)) != len(reads) or len(reads) > trace["read_cap"]:
                raise ValueError("invalid or excessive source opens")
            if issued and (source not in reads or not outgoing["reply_locator"]):
                raise ValueError("outgoing locator has no reading action")
            if not issued and not outgoing["request_binding"]:
                raise ValueError("missing state lacks a scoped request")
            context_correct = outgoing["patent_context"] == context
            valid_reply = source in allowed and outgoing["reply_locator"] == allowed[source]
            correct_reply = issued and valid_reply and context_correct
            correct_abstention = (not issued and not allowed and context_correct
                                  and outgoing["request_binding"] == keys[case]["binding"])
            unread = set(allowed) - set(reads)
            scores[arm] = {
                "correct_reply": correct_reply, "correct_abstention": correct_abstention,
                "unsupported_outgoing": issued and not valid_reply,
                "missed_support": not issued and bool(allowed),
                "harmful_stop": not correct_reply and not issued and bool(unread) and len(reads) < trace["read_cap"],
                "mismatches": trace["handoffs"]["regulatory"]["selected_mismatches"],
                "reads": reads, "metadata_inspections": trace["catalog_descriptors_inspected"],
            }
        outcomes[case] = scores
    return outcomes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("original", type=Path)
    parser.add_argument("capture_sha256", help="SHA-256 pinned before the evaluation key is read")
    args = parser.parse_args()
    capture = json.loads(verified_bytes(args.original, args.capture_sha256))
    lock_bytes = (PACKET / "freeze.json").read_bytes()
    if capture["freeze_sha256"] != digest(lock_bytes):
        raise ValueError("captured run does not bind to the exact fixture freeze")
    name, expected = next(iter(json.loads(lock_bytes)["evaluator_key"].items()))
    keys = json.loads(verified_bytes(ROOT / name, expected))
    print(json.dumps(evaluate(capture, keys), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
