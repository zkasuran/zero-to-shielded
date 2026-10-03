"""A token-bucket rate limiter, before the fix.

The bug: refill divides by the count of calls, not the elapsed time, so a burst of
calls hands out far more tokens than a second is worth. The bucket never really
throttles. The after file next to this one is the fix.
"""

import time


class RateLimiter:
    def __init__(self, rate: float, burst: float) -> None:
        self.rate = rate
        self.burst = burst
        self.tokens = burst
        self.calls = 0
        self.updated = time.monotonic()

    def allow(self) -> bool:
        self.calls += 1
        now = time.monotonic()
        # BUG: refill is scaled by the number of calls, not by elapsed time, so a
        # burst refills faster than the clock and the limit does not hold.
        self.tokens = min(self.burst, self.tokens + self.rate / self.calls)
        self.updated = now
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False
