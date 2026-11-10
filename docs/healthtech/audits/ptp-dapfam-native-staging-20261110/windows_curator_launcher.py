"""Windows-only bounded curator launcher. No retries and no repository writes."""
import argparse
import ctypes as C
from ctypes import wintypes as W
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import time


class BASIC(C.Structure):
    _fields_ = [("PerProcessUserTimeLimit", C.c_longlong), ("PerJobUserTimeLimit", C.c_longlong),
                ("LimitFlags", W.DWORD), ("MinimumWorkingSetSize", C.c_size_t),
                ("MaximumWorkingSetSize", C.c_size_t), ("ActiveProcessLimit", W.DWORD),
                ("Affinity", C.c_size_t), ("PriorityClass", W.DWORD), ("SchedulingClass", W.DWORD)]


class IO(C.Structure):
    _fields_ = [(name, C.c_ulonglong) for name in ("ReadOperationCount", "WriteOperationCount",
                "OtherOperationCount", "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]


class EXTENDED(C.Structure):
    _fields_ = [("BasicLimitInformation", BASIC), ("IoInfo", IO),
                ("ProcessMemoryLimit", C.c_size_t), ("JobMemoryLimit", C.c_size_t),
                ("PeakProcessMemoryUsed", C.c_size_t), ("PeakJobMemoryUsed", C.c_size_t)]


def bind_job(memory_bytes):
    if os.name != "nt":
        raise RuntimeError("Windows required")
    k = C.WinDLL("kernel32", use_last_error=True)
    k.GetCurrentProcess.restype = W.HANDLE
    k.CreateJobObjectW.argtypes = [C.c_void_p, W.LPCWSTR]
    k.CreateJobObjectW.restype = W.HANDLE
    k.SetInformationJobObject.argtypes = [W.HANDLE, C.c_int, C.c_void_p, W.DWORD]
    k.SetInformationJobObject.restype = W.BOOL
    k.AssignProcessToJobObject.argtypes = [W.HANDLE, W.HANDLE]
    k.AssignProcessToJobObject.restype = W.BOOL
    k.GetProcessAffinityMask.argtypes = [W.HANDLE, C.POINTER(C.c_size_t), C.POINTER(C.c_size_t)]
    k.GetProcessAffinityMask.restype = W.BOOL
    k.QueryInformationJobObject.argtypes = [W.HANDLE, C.c_int, C.c_void_p, W.DWORD, C.c_void_p]
    k.QueryInformationJobObject.restype = W.BOOL
    process = k.GetCurrentProcess()
    current, system = C.c_size_t(), C.c_size_t()
    if not k.GetProcessAffinityMask(process, C.byref(current), C.byref(system)):
        raise C.WinError(C.get_last_error())
    bits = [1 << i for i in range(C.sizeof(C.c_size_t) * 8) if current.value & (1 << i)][:8]
    if not bits:
        raise RuntimeError("no allowed processor")
    info = EXTENDED()
    requested_flags = 0x8 | 0x10 | 0x100 | 0x200 | 0x2000
    info.BasicLimitInformation.LimitFlags = requested_flags
    info.BasicLimitInformation.ActiveProcessLimit = 1
    info.BasicLimitInformation.Affinity = sum(bits)
    info.ProcessMemoryLimit = info.JobMemoryLimit = memory_bytes
    job = k.CreateJobObjectW(None, None)
    if not job or not k.SetInformationJobObject(job, 9, C.byref(info), C.sizeof(info)):
        raise C.WinError(C.get_last_error())
    if not k.AssignProcessToJobObject(job, process):
        raise C.WinError(C.get_last_error())
    actual = EXTENDED()
    if not k.QueryInformationJobObject(job, 9, C.byref(actual), C.sizeof(actual), None):
        raise C.WinError(C.get_last_error())
    if (actual.ProcessMemoryLimit != memory_bytes or actual.JobMemoryLimit != memory_bytes or
            actual.BasicLimitInformation.ActiveProcessLimit != 1 or
            actual.BasicLimitInformation.LimitFlags & requested_flags != requested_flags or
            actual.BasicLimitInformation.Affinity != sum(bits)):
        raise RuntimeError("resource limit readback mismatch")
    observed, observed_system = C.c_size_t(), C.c_size_t()
    if not k.GetProcessAffinityMask(process, C.byref(observed), C.byref(observed_system)):
        raise C.WinError(C.get_last_error())
    if (not observed.value or observed.value & ~sum(bits) or observed.value.bit_count() > 8):
        raise RuntimeError("effective process affinity mismatch")
    return k, job, actual


def child(args):
    start = time.monotonic()
    info = {"status": "LIMIT_SETUP_PENDING", "pid": os.getpid()}
    code = 1
    try:
        k, job, limits = bind_job(args.memory_bytes)
        info.update(status="RUNNING", memory_limit_bytes=limits.JobMemoryLimit,
                    affinity_mask=limits.BasicLimitInformation.Affinity,
                    active_process_limit=limits.BasicLimitInformation.ActiveProcessLimit)
        Path(args.run_dir, "child-ready.json").write_text(json.dumps(info))
        sys.argv = [args.script, *args.script_args]
        try:
            runpy.run_path(args.script, run_name="__main__")
            code = 0
        except SystemExit as exc:
            code = exc.code if isinstance(exc.code, int) else (0 if exc.code is None else 1)
        except BaseException as exc:
            info["exception_type"] = type(exc).__name__
            code = 1
        peak = EXTENDED()
        if k.QueryInformationJobObject(job, 9, C.byref(peak), C.sizeof(peak), None):
            info["peak_job_commit_bytes"] = peak.PeakJobMemoryUsed
            info["peak_process_commit_bytes"] = peak.PeakProcessMemoryUsed
        info["status"] = "COMPLETED" if code == 0 else "FAILED"
    except BaseException as exc:
        info.update(status="LIMIT_SETUP_FAILED", exception_type=type(exc).__name__)
    info.update(exit_code=code, wall_seconds=time.monotonic() - start)
    Path(args.run_dir, "child-result.json").write_text(json.dumps(info, indent=2))
    return code


def main(args):
    dest = Path(args.run_dir)
    dest.mkdir(parents=True, exist_ok=False)
    env = os.environ.copy()
    for key in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS", "ARROW_NUM_THREADS"):
        env[key] = "8"
    env.update(CUDA_VISIBLE_DEVICES="", HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", PYTHONDONTWRITEBYTECODE="1")
    command = [sys.executable, __file__, "--child", "--run-dir", str(dest),
               "--memory-bytes", str(args.memory_bytes), "--seconds", str(args.seconds),
               "--script", args.script, "--", *args.script_args]
    started = time.monotonic()
    with (dest / "stdout.txt").open("xb") as out, (dest / "stderr.txt").open("xb") as err:
        proc = subprocess.Popen(command, env=env, stdout=out, stderr=err, creationflags=subprocess.CREATE_NO_WINDOW)
        (dest / "process.json").write_text(json.dumps({"pid": proc.pid, "started_unix": time.time()}))
        timed_out = False
        try:
            code = proc.wait(timeout=args.seconds)
        except subprocess.TimeoutExpired:
            timed_out = True
            proc.kill()
            code = proc.wait(timeout=5)
    result = {"status": "TIMEOUT" if timed_out else "COMPLETED" if code == 0 else "FAILED",
              "pid": proc.pid, "process_exit_code": code, "wall_seconds": time.monotonic() - started,
              "timeout_seconds": args.seconds, "memory_limit_bytes": args.memory_bytes,
              "max_cpu_affinity": 8, "model_calls": 0, "gpu_calls": 0, "automatic_retries": 0}
    (dest / "supervisor-result.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result))
    return 124 if timed_out else code


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--child", action="store_true")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--memory-bytes", type=int, default=31 * 2**30)
    parser.add_argument("--seconds", type=int, default=1800)
    parser.add_argument("--script", required=True)
    parser.add_argument("script_args", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.script_args[:1] == ["--"]:
        args.script_args = args.script_args[1:]
    if not 1 <= args.seconds <= 1800 or not 64 * 2**20 <= args.memory_bytes <= 32 * 2**30:
        raise SystemExit("resource envelope refused")
    raise SystemExit(child(args) if args.child else main(args))
