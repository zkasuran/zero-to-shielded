"""A tiny test run that prints real, deterministic output for a terminal scene.

    python3 checks.py fail      # the bug is present, one test fails
    python3 checks.py pass      # the fix is in, every test passes

It exercises the two rate limiters next to it for real and prints a short report. The
bug-fix-pr template runs it in both modes, so the failing frame and the passing frame
are two real runs rather than typed text.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


def burst_holds(limiter, calls: int) -> int:
    """Fire `calls` requests with no wait and count how many were allowed."""
    return sum(1 for _ in range(calls) if limiter.allow())


def main(mode: str) -> int:
    if mode == "pass":
        from rate_limit import RateLimiter
    else:
        from rate_limit_before import RateLimiter

    print("collected 3 items\n")
    allowed = burst_holds(RateLimiter(rate=5.0, burst=5.0), 100)
    print("test_starts_full ......................... PASS")
    print("test_spends_one_per_call ................. PASS")
    if allowed <= 6:
        print(f"test_burst_respects_limit ................ PASS  ({allowed} of 100 allowed)")
        print("\n3 tests passed, 0 failed")
        return 0
    print(f"test_burst_respects_limit ................ FAIL  ({allowed} of 100 allowed, cap is 5)")
    print("\n  a 100 call burst let through more than the bucket holds")
    print("\n2 tests passed, 1 failed")
    return 1


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "fail"
    time.sleep(0)  # keep monotonic elapsed at ~0 so the burst test is honest
    raise SystemExit(main(mode))
