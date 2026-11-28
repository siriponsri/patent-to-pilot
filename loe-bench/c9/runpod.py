"""Run the paired C9 workflow on one already-approved RunPod SSH endpoint."""

import argparse
import math
import re
import shlex
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from time import monotonic
from uuid import uuid4

from .inputs import (APPROVED_GPUS, ROOT, file_digest, load_projection, select_training, specification,
                     strict_json, track_rows, write_json)

RUNTIME_FILES = ("__init__.py", "c9.py", "common.py", "l1e_prompt.py", "llm_arm.py",
                 "metrics.py", "review_metrics.py")
CONFIG_FILES = ("C9_SPEC.json", "L1E_FROZEN_CONFIG.json", "S0_INPUT_MANIFEST.json")
ARMS = ("sft", "grpo")
HOST = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.-]*@[A-Za-z0-9][A-Za-z0-9.-]*")


def timestamp(value):
    parsed = datetime.fromisoformat(value)
    if parsed.utcoffset() is None:
        raise ValueError("admission times must identify their UTC offset")
    return parsed.timestamp()


def allowances(approval, spec, now):
    budget = spec["budget"]
    if approval["gpu"] not in APPROVED_GPUS or approval["gpu_count"] != 1:
        raise ValueError("the approved placement must be one NVIDIA A10 or NVIDIA L4")
    if not all(isinstance(approval[key], str) and approval[key].strip() for key in (
        "owner_approval_ref", "cprime_pass_ref", "live_quote_ref", "pod_id", "data_center",
    )):
        raise ValueError("record the live quote, C′ pass, approved placement and owner approval")
    rate, non_gpu, disk = [approval[key] for key in
                           ("gpu_usd_per_hour", "non_gpu_total_usd", "ephemeral_storage_gib")]
    if (any(type(x) not in (float, int) or not math.isfinite(x) for x in (rate, non_gpu, disk))
            or not 0 < rate <= budget["max_gpu_rate_usd_per_hour"]
            or not 0 <= non_gpu <= budget["max_non_gpu_usd_combined"]
            or not 0 < disk <= budget["max_ephemeral_storage_gib"]):
        raise ValueError("quote exceeds the frozen C9 rate, non-GPU or disk cap")
    billed = timestamp(approval["billing_started_utc"])
    freeze = timestamp(approval["core_freeze_utc"])
    external_deadline = timestamp(spec["prediction"]["external_timestamp_deadline_utc"])
    if not timestamp("2026-12-01T00:00:00+07:00") <= billed <= now < freeze <= external_deadline:
        raise ValueError("pod billing or core freeze falls outside the admitted window")
    phases = [approval[key] for key in ("setup_seconds", "arm_seconds", "pull_seconds", "teardown_seconds")]
    if any(type(seconds) is not int or seconds < 1 for seconds in phases):
        raise ValueError("phase reservations must be positive whole seconds")
    setup, arm, pull, teardown = phases
    elapsed = now - billed
    per_arm = arm + (elapsed + setup + pull + teardown) / 2
    charge = per_arm * rate / 3600
    if (per_arm > budget["max_gpu_hours_per_arm"] * 3600 or charge > budget["max_gpu_usd_per_arm"]
            or charge + non_gpu / 2 > budget["max_all_in_usd_per_arm"]
            or 2 * charge + non_gpu > budget["all_in_usd"]
            or now + setup + 2 * arm + pull + teardown >= freeze):
        raise ValueError("reservation exceeds a paired budget or core freeze deadline")
    return phases


def remaining(deadline):
    seconds = math.floor(deadline - monotonic())
    if seconds < 1:
        raise TimeoutError("reserved phase time exhausted")
    return seconds


def stage_bundle(bundle, args):
    (bundle / "loe_bench").mkdir(parents=True)
    (bundle / "data").mkdir()
    (bundle / "c9").mkdir()
    for name in RUNTIME_FILES:
        shutil.copyfile(ROOT / "loe_bench" / name, bundle / "loe_bench" / name)
    for name in CONFIG_FILES:
        shutil.copyfile(ROOT / "data" / name, bundle / "data" / name)
    for path in sorted((ROOT / "c9").glob("*.py")):
        shutil.copyfile(path, bundle / "c9" / path.name)
    shutil.copyfile(ROOT / "c9/requirements.txt", bundle / "c9/requirements.txt")
    for source, name, expected in (
        (args.projection, "training.json", args.projection_sha256),
        (args.track_a_roster, "track-a.json", args.track_a_sha256),
    ):
        copied = bundle / name
        shutil.copyfile(source, copied)
        if file_digest(copied) != expected:
            raise ValueError("projection changed between admission and staging")
    lines = [f"{file_digest(path)}  {path.relative_to(bundle).as_posix()}"
             for path in sorted(bundle.rglob("*")) if path.is_file()]
    (bundle / "inputs.sha256").write_bytes(("\n".join(lines) + "\n").encode("ascii"))


def verify_transfer(results):
    hashes = {}
    for line in (results / "files.sha256").read_text(encoding="ascii").splitlines():
        sha, name = line.split("  ", 1)
        path = (results / name).resolve()
        if not path.is_relative_to(results.resolve()) or path == results.resolve() or name in hashes:
            raise ValueError("unexpected path in remote digest inventory")
        if file_digest(path) != sha:
            raise ValueError(f"retrieved artifact hash mismatch: {name}")
        hashes[name] = sha
    paths = {p.relative_to(results).as_posix() for p in results.rglob("*") if p.is_file()}
    if paths != hashes.keys() | {"files.sha256"}:
        raise ValueError("retrieved file inventory is incomplete")
    return hashes


def verify_pair(results, args, hashes, spec):
    training = strict_json((results / "trained/training-roster.json").read_bytes())
    reports = []
    for arm in ARMS:
        predict_dir = results / f"{arm}-predictions"
        report = strict_json((predict_dir / "prediction.json").read_bytes())
        run = strict_json((results / "trained" / arm / "run.json").read_bytes())
        if (report["status"] != "COMPLETE" or report["dry_run"] or report["arm"] != arm
                or report["track_a_roster_sha256"] != args.track_a_sha256
                or report["predictions_sha256"] != hashes[f"{arm}-predictions/predictions.jsonl"]
                or report["adapter_run_sha256"] != hashes[f"trained/{arm}/run.json"]
                or run["status"] != "COMPLETE" or run["dry_run"] or run["arm"] != arm
                or report["runtime"] != training["runtime"] or run["runtime"] != training["runtime"]
                or run["training_roster_sha256"] != hashes["trained/training-roster.json"]
                or run["initial_sha256"] != hashes["trained/initial.safetensors"]
                or run["updates"] != spec["training"]["optimizer_updates_per_arm"]
                or any(hashes[f"trained/{arm}/{name}"] != sha for name, sha in run["files"].items())):
            raise ValueError("a retrieved arm did not satisfy its adapter or prediction manifest")
        reports.append(report)
    if any(reports[0][key] != reports[1][key] for key in
           ("keys_sha256", "messages_sha256", "prompt_token_ids_sha256", "rows")):
        raise ValueError("Track A arms disagree on roster or prompt bytes")


def launch(args):
    start = monotonic()
    spec = specification()
    approval = strict_json(args.approval.read_bytes())
    setup, arm_seconds, pull_seconds, _ = allowances(approval, spec, datetime.now(timezone.utc).timestamp())
    if not HOST.fullmatch(approval["ssh_host"]) or type(approval["ssh_port"]) is not int or not (
        1 <= approval["ssh_port"] <= 65535
    ):
        raise ValueError("expected an approved direct SSH user@host and port")
    select_training(load_projection(args.projection, args.projection_sha256, training=True))
    track_rows(load_projection(args.track_a_roster, args.track_a_sha256, training=False))
    args.output.mkdir(parents=True)
    prefix = ["-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes", "-i", str(args.identity)]
    port = str(approval["ssh_port"])
    host = approval["ssh_host"]
    work = f"c9-{uuid4().hex}"
    ssh = ["ssh", *prefix, "-p", port, host]
    scp = ["scp", *prefix, "-P", port, "-r"]
    events = []
    status = "NOT_RUN"
    hashes = {}

    def call(argv, deadline, name):
        t = monotonic()
        exit_code = None
        try:
            with (args.output / f"{name}.log").open("xb") as log:
                result = subprocess.run(argv, timeout=remaining(deadline), check=True,
                                        stdout=log, stderr=subprocess.STDOUT)
                exit_code = result.returncode
        except subprocess.CalledProcessError as exc:
            exit_code = exc.returncode
            raise
        finally:
            events.append({"phase": name, "seconds": monotonic() - t,
                           "exit_code": exit_code})

    def remote(script, deadline, name):
        # GNU timeout also bounds the owned remote subprocess if SSH drops.
        bound = max(1, remaining(deadline) - 6)
        call([*ssh, f"timeout -k 3s {bound}s bash -euc {shlex.quote(script)}"], deadline, name)

    try:
        remote(
            f"""test "$RUNPOD_POD_ID" = {shlex.quote(approval["pod_id"])}
gpu=$(nvidia-smi --query-gpu=name --format=csv,noheader)
test "$gpu" = {shlex.quote(approval["gpu"])}
printf '%s\\n' "$gpu"
""", start + setup, "placement")
        with tempfile.TemporaryDirectory(prefix="c9-") as temporary:
            bundle = Path(temporary) / work
            stage_bundle(bundle, args)
            call([*scp, str(bundle), f"{host}:{work}"], start + setup, "upload")
        remote(
            f"""cd {work}
sha256sum --strict -c inputs.sha256
python -m venv --system-site-packages .venv
.venv/bin/python -m pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cu128 -r c9/requirements.txt
.venv/bin/python -m c9.checkpoint checkpoint
export CUDA_VISIBLE_DEVICES=0 PYTHONDONTWRITEBYTECODE=1
.venv/bin/python -c 'from pathlib import Path; from c9.inputs import specification; from c9.predict import prepare_track; prepare_track(Path("checkpoint"), Path("track-a.json"), "{args.track_a_sha256}", specification())'
mkdir results
cp inputs.sha256 results/staged-inputs.sha256
.venv/bin/python -m pip list --format=json > results/runtime-packages.json
""", start + setup, "setup")
        for arm in ARMS:
            deadline = monotonic() + arm_seconds
            remote(
                f"""cd {work}
export CUDA_VISIBLE_DEVICES=0 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1
.venv/bin/python -m c9.train --arm {arm} --checkpoint checkpoint --projection training.json --projection-sha256 {args.projection_sha256} --output results/trained
.venv/bin/python -m c9.predict --arm {arm} --checkpoint checkpoint --trained results/trained --track-a-roster track-a.json --track-a-sha256 {args.track_a_sha256} --output results/{arm}-predictions
""", deadline, arm)
        deadline = monotonic() + pull_seconds
        remote(f"cd {work}/results; find . -type f ! -name files.sha256 -printf '%P\\0' | sort -z | xargs -0 sha256sum > files.sha256",
               deadline, "remote-hashes")
        call([*scp, f"{host}:{work}/results", str(args.output)], deadline, "pull")
        hashes = verify_transfer(args.output / "results")
        verify_pair(args.output / "results", args, hashes, spec)
        remaining(deadline)
        status = "ARTIFACTS_VERIFIED_PENDING_TEARDOWN_AND_TIMESTAMP"
    finally:
        elapsed = datetime.now(timezone.utc).timestamp() - timestamp(approval["billing_started_utc"])
        write_json(args.output / "launch.json", {
            "status": status, "pod_id": approval["pod_id"], "data_center": approval["data_center"],
            "approval_sha256": file_digest(args.approval), "approval_ref": approval["owner_approval_ref"],
            "approved_gpu": approval["gpu"],
            "gpu_usd_per_hour": approval["gpu_usd_per_hour"], "phases": events,
            "pod_billed_seconds_to_launch_exit_estimate": elapsed,
            "gpu_usd_to_launch_exit_estimate": elapsed * approval["gpu_usd_per_hour"] / 3600,
            "quoted_non_gpu_usd": approval["non_gpu_total_usd"], "artifact_sha256": hashes,
        })


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("approval", "identity", "projection", "track-a-roster", "output"):
        parser.add_argument(f"--{name}", required=True, type=Path)
    parser.add_argument("--projection-sha256", required=True)
    parser.add_argument("--track-a-sha256", required=True)
    args = parser.parse_args()
    try:
        launch(args)
    finally:
        print("Teardown checklist", flush=True)
        print("1. Confirm artifact verification or record NOT_RUN and preserve logs.", flush=True)
        print("2. Terminate the approved pod immediately. Verify pod and ephemeral storage removal.", flush=True)
        print("3. Record termination time, final billing and budget by arm.", flush=True)
        print("4. On complete pair only, hash/tag outputs and timestamp on OSF before core freeze.", flush=True)


if __name__ == "__main__":
    main()
