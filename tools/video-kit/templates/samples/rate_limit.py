"""A token-bucket rate limiter.

Tokens refill at a fixed rate over wall-clock time and the bucket is capped at a
burst size. One token is spent per allowed call. The refill is scaled by the seconds
that actually elapsed, so the limit holds under a burst.
"""

import time


class RateLimiter:
    def __init__(self, rate: float, burst: float) -> None:
        self.rate = rate
        self.burst = burst
        self.tokens = burst
        self.updated = time.monotonic()

    def allow(self) -> bool:
        now = time.monotonic()
        elapsed = now - self.updated
        # Refill by the time that passed, capped at the burst size.
        self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
        self.updated = now
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False
