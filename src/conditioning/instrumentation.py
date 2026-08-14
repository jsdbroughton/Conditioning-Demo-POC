"""Per-stage timing and peak-memory logging.

Exists because a deployed Automate run that dies gives you a pod exit code
and nothing else — the 2026-08-14 failure had to be diagnosed as "presumably
OOM or presumably runtime" with no way to tell which, and the answer turned
out to matter a lot (it was CPU: one core at 99% for 94 minutes in a single
O(n×m) loop, not memory at all). One line per stage in the run log turns the
next failure into data instead of a guess.

Deliberately stdlib-only and side-effect-free apart from the print — this
runs inside the Automate container, where adding a profiling dependency to
diagnose a production incident is its own problem.
"""

from __future__ import annotations

import sys
import time
from collections.abc import Iterator
from contextlib import contextmanager

try:  # pragma: no cover — resource is POSIX-only, absent on Windows
    import resource
except ImportError:  # pragma: no cover
    resource = None  # type: ignore[assignment]


def peak_rss_mib() -> float | None:
    """Peak resident set size for this process, in MiB, or None if unavailable.

    ru_maxrss units differ by platform and the difference is a factor of
    1024, so getting it wrong makes the number silently meaningless rather
    than obviously wrong: Linux (the Automate container) reports KiB, macOS
    (local dev) reports bytes. This is a high-water mark for the whole
    process — it never goes down, so read it as "peak so far", not "in use
    right now".
    """
    if resource is None:
        return None
    raw = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return raw / (1024 * 1024) if sys.platform == "darwin" else raw / 1024


@contextmanager
def stage(name: str) -> Iterator[None]:
    """Time a block and log its elapsed seconds + peak RSS.

    Logs on the way out even if the block raises, so a stage that dies still
    reports how far it got — that's the case this is actually for.
    """
    started = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - started
        rss = peak_rss_mib()
        rss_note = f", peak RSS {rss:.0f} MiB" if rss is not None else ""
        print(
            f"[ConditioningPOC][timing] {name}: {elapsed:.1f}s{rss_note}",
            flush=True,
        )
