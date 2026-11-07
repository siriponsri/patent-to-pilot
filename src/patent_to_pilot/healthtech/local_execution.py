"""Local GPU execution boundary. No paid-provider or budget dependencies.

The lock is cooperative, scoped to the existing project model directory and
shared by embedding and generation launchers. Host/resource checks still
belong to the launcher; possession of this lock is not an allocation from an
operator.
"""
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import os


APPROVED_GPU_UUID = "GPU-277ccc57-c3e5-0731-cd49-f4f8695f7089"
# Owner extension 7 Nov 2026: through 2026-11-30 23:59 Asia/Bangkok (was 15 Nov).
AUTHORIZATION_END_UTC = datetime(2026, 11, 30, 16, 59, tzinfo=timezone.utc)


def check_local_window(*, now=None, visible=None):
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None or now >= AUTHORIZATION_END_UTC:
        raise RuntimeError("local GPU authorization window has ended or time is invalid")
    visible = os.environ.get("CUDA_VISIBLE_DEVICES") if visible is None else visible
    if visible != APPROVED_GPU_UUID:
        raise RuntimeError("CUDA_VISIBLE_DEVICES must name the exact approved GPU UUID")


@contextmanager
def local_gpu_slot(model_root: Path):
    """Acquire a nonblocking OS lock; never unlink another writer's marker."""
    path = model_root.resolve().parent / f".{APPROVED_GPU_UUID}.lock"
    # The model directory must already exist; do not create an alternative root.
    with path.open("a+b") as handle:
        if os.name == "nt":
            import msvcrt

            if path.stat().st_size == 0:
                handle.write(b"\0")
                handle.flush()
            handle.seek(0)
            try:
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as exc:
                raise RuntimeError("approved local GPU slot is already in use") from exc
            try:
                yield path
            finally:
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise RuntimeError("approved local GPU slot is already in use") from exc
            try:
                yield path
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
