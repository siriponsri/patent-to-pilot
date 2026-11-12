"""Run one local command and append its measured CPU to a JSONL receipt file.

Measurement: Windows GetProcessTimes (user+kernel) on the direct child process
handle after exit, the same basis as the R7 preparation receipts. Grandchild
processes are not included; use only for commands that do not spawn workers.
Usage: python meter_local_cpu.py <receipts.jsonl> -- <command...>
"""
import ctypes
from ctypes import wintypes
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time


def process_cpu_seconds(handle):
    times = [wintypes.FILETIME() for _ in range(4)]
    ok = ctypes.windll.kernel32.GetProcessTimes(wintypes.HANDLE(int(handle)), *[ctypes.byref(t) for t in times])
    if not ok:
        raise OSError('GetProcessTimes failed')
    def ticks(t): return (t.dwHighDateTime << 32) | t.dwLowDateTime
    return (ticks(times[2]) + ticks(times[3])) / 1e7


def main():
    if len(sys.argv) < 4 or sys.argv[2] != '--':
        raise SystemExit('usage: meter_local_cpu.py <receipts.jsonl> -- <command...>')
    target, command = Path(sys.argv[1]), sys.argv[3:]
    hashes = {}
    for arg in command:
        path = Path(arg)
        if path.suffix == '.py' and path.is_file():
            hashes[arg] = hashlib.sha256(path.read_bytes()).hexdigest()
    started = time.monotonic(); started_unix = time.time()
    proc = subprocess.Popen(command)
    code = proc.wait()
    wall = time.monotonic() - started
    cpu = process_cpu_seconds(proc._handle)
    record = {'command': command, 'exit_code': code, 'started_unix': started_unix,
              'wall_seconds': wall, 'cpu_seconds': cpu, 'model_calls': 0,
              'measurement': 'Windows GetProcessTimes user+kernel of direct child; grandchildren excluded',
              'file_sha256': hashes}
    with target.open('a', encoding='utf-8') as handle:
        handle.write(json.dumps(record, sort_keys=True) + '\n')
    print(json.dumps({'exit_code': code, 'cpu_seconds': cpu, 'wall_seconds': round(wall, 3)}))
    raise SystemExit(code)


if __name__ == '__main__':
    main()
