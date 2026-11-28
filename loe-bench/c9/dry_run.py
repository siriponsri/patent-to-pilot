"""Run the two-update CPU smoke through rendering, fitting and prediction."""

import argparse
from pathlib import Path

from loe_bench import l1e_prompt

from .inputs import digest, file_digest, specification, write_json


def synthetic_rows(size=16, *, training=True):
    cutoff = "2014-01-01" if training else "2026-11-27"
    proof = {"source_id": "synthetic", "version": "1", "sha256": digest(b"c9 synthetic fixture"),
             "locator": "synthetic evidence", "record_date": "2013-01-01", "available_on": "2013-01-01"}
    for i in range(size):
        evidence = {field: 0 for field in l1e_prompt.CROSSWALK}
        evidence.update(age_years=i + 1, nce_remaining_years_missing=1, challenge_missing=1,
                        latest_patent_expiry=None, latest_exclusivity_expiry=None, challenge_witnesses=[])
        row = {"drug_key": f"synthetic-{i:03d}", "forecast": {
            "entity": f"Synthetic ingredient {i}", "t0": cutoff,
            "horizon_months": 24, "as_of_evidence": evidence,
        }, "provenance": {"as_of": [proof.copy()]}}
        if training:
            row.update(original_nda="2013-01-01", type1="2013-01-01",
                       covered_through="2016-01-01", resolved_linkage=True,
                       first_final_anda="2015-07-01" if i % 2 else None)
            row["provenance"]["outcome"] = [dict(proof, locator="synthetic closed-window coverage",
                                                  record_date="2016-01-01", available_on="2016-01-01")]
        yield row


def fixture(path, *, training):
    write_json(path, {"schema": "c9-development-v1" if training else "c9-track-a-v1",
                     "s0_manifest_lf_sha256": specification()["s0"]["manifest_lf_sha256"],
                     "rows": list(synthetic_rows(16, training=training))})
    return file_digest(path)


def main():
    from .predict import predict
    from .train import ARMS, train

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True)
    training = args.output / "synthetic-training.json"
    track = args.output / "synthetic-track.json"
    training_sha = fixture(training, training=True)
    track_sha = fixture(track, training=False)
    trained = args.output / "trained"
    train(args.checkpoint, training, training_sha, trained, dry=True)
    for arm in ARMS:
        report = predict(args.checkpoint, track, track_sha, trained, arm,
                         args.output / f"{arm}-predictions", dry=True)
        print(f"{arm} captured {report['rows']} completions, malformed={report['malformed']}", flush=True)


if __name__ == "__main__":
    main()
