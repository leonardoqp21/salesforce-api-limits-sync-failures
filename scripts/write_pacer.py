"""See what a rate limit and a queue do to a burst of writes. A teaching simulation.

It models a burst of record changes arriving at once and compares two ways of writing them:
all at once, or paced through a queue that releases a fixed number of calls per second and
packs several records into each call. It is a model of the IDEA, not of any product's internals.

    python scripts/write_pacer.py

Standard library only. Python 3.9 or newer.
"""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class Result:
    peak_calls_per_second: int
    total_calls: int
    seconds_to_finish: int
    longest_wait_seconds: int


def unpaced(arrivals: dict[int, int], records_per_call: int = 1) -> Result:
    """Every arrival is sent immediately. arrivals: {second: records}."""
    per_second = {t: math.ceil(n / records_per_call) for t, n in arrivals.items()}
    return Result(max(per_second.values(), default=0), sum(per_second.values()), max(arrivals, default=0) + 1, 0)


def paced(arrivals: dict[int, int], rate_per_second: int, records_per_call: int = 1) -> Result:
    """Records wait in a queue. Each second at most `rate_per_second` calls leave, each carrying up to `records_per_call` records."""
    if rate_per_second < 1 or records_per_call < 1:
        raise ValueError("rate and batch size must be at least 1")
    waiting: list[int] = []          # arrival second of each waiting record
    peak = total = longest = 0
    t = 0
    last_arrival = max(arrivals, default=-1)
    while t <= last_arrival or waiting:
        waiting.extend([t] * arrivals.get(t, 0))
        calls = min(rate_per_second, math.ceil(len(waiting) / records_per_call))
        sent = waiting[: calls * records_per_call]
        del waiting[: calls * records_per_call]
        for arrived in sent:
            longest = max(longest, t - arrived)
        peak = max(peak, calls)
        total += calls
        t += 1
    return Result(peak, total, t, longest)


def main() -> None:
    burst = {0: 5000}  # 5,000 records change in the same second, for example after an import
    print("A burst of 5,000 record changes in one second\n")
    for label, r in [
        ("unpaced, 1 record per call", unpaced(burst, 1)),
        ("paced 10 calls/s, 1 record per call", paced(burst, 10, 1)),
        ("paced 10 calls/s, 200 records per call", paced(burst, 10, 200)),
    ]:
        print(f"{label:<42} peak {r.peak_calls_per_second:>5} calls/s, {r.total_calls:>5} calls total, "
              f"finished after {r.seconds_to_finish:>4}s, longest wait {r.longest_wait_seconds}s")
    print("\nPacing trades waiting time for a bounded call rate. Batching cuts the number of calls.")
    print("Records wait in the queue. They are not lost.")


if __name__ == "__main__":
    main()
