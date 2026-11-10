"""Estimate how many Salesforce API calls a sync spends per day, and what rate limit is safe.

Every number here is YOURS. This tool has no Salesforce numbers of its own, except the
formula shape: an org's daily API request allocation is a base plus a per-license amount.
Check the current official table for your edition and license types.

    python scripts/api_budget.py --base 100000 --licenses 15 --per-license 1000 \
        --changes-per-day 20000 --records-per-call 1 --polls-per-day 1440 --calls-per-poll 2 \
        --scan-records 50000 --scans-per-day 1 --page-size 2000 \
        --other-share 0.3 --rate 5 --frequency 1

The page size and records-per-call are assumptions you must check for the API you use.
Standard library only. Python 3.9 or newer.
"""
from __future__ import annotations

import argparse
import math

SECONDS_PER_DAY = 86_400


def allocation(base: int, licenses: int, per_license: int, extra: int = 0) -> int:
    """Daily API requests: a base, plus an amount per license, plus purchased add-ons."""
    return base + licenses * per_license + extra


def calls_for_changes(changes: int, records_per_call: int) -> int:
    """Writes. One call per record for single-record REST. Fewer when batching or using bulk."""
    return math.ceil(changes / max(1, records_per_call))


def calls_for_polling(polls_per_day: int, calls_per_poll: int) -> int:
    """Reading what changed. Every poll costs calls even when nothing changed."""
    return polls_per_day * calls_per_poll


def calls_for_scans(records: int, page_size: int, scans_per_day: float) -> int:
    """A full table scan reads every record. Cost = pages x scans."""
    return math.ceil(math.ceil(records / max(1, page_size)) * scans_per_day)


def sustainable_rate(total_allocation: int, share: float = 1.0) -> float:
    """Calls per second you can spend all day on, using `share` of the allocation."""
    return total_allocation * share / SECONDS_PER_DAY


def daily_ceiling(rate: float, frequency_seconds: int) -> int:
    """The most calls a per-app rate limit lets through in a day: rate calls per frequency seconds."""
    return int(rate * SECONDS_PER_DAY / frequency_seconds)


def drain_seconds(backlog_calls: int, rate_per_second: float) -> float:
    return backlog_calls / rate_per_second if rate_per_second > 0 else math.inf


def plan(*, base, licenses, per_license, extra=0, changes_per_day, records_per_call=1, polls_per_day=0,
         calls_per_poll=1, scan_records=0, page_size=2000, scans_per_day=0, other_share=0.0, rate=None, frequency=1) -> dict:
    total = allocation(base, licenses, per_license, extra)
    parts = {
        "writes": calls_for_changes(changes_per_day, records_per_call),
        "polling": calls_for_polling(polls_per_day, calls_per_poll),
        "full_scans": calls_for_scans(scan_records, page_size, scans_per_day),
    }
    used = sum(parts.values())
    mine = total * (1 - other_share)
    result = {
        "allocation": total,
        "parts": parts,
        "estimated_daily_calls": used,
        "share_of_allocation": used / total if total else math.inf,
        "budget_for_this_sync": int(mine),
        "fits": used <= mine,
        "sustainable_rate_per_second": sustainable_rate(total, 1 - other_share),
    }
    if rate is not None:
        ceiling = daily_ceiling(rate, frequency)
        result["rate_limit_daily_ceiling"] = ceiling
        result["rate_limit_is_a_real_guard"] = ceiling <= mine
    return result


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--base", type=int, required=True)
    p.add_argument("--licenses", type=int, required=True)
    p.add_argument("--per-license", type=int, required=True)
    p.add_argument("--extra", type=int, default=0)
    p.add_argument("--changes-per-day", type=int, required=True)
    p.add_argument("--records-per-call", type=int, default=1)
    p.add_argument("--polls-per-day", type=int, default=0)
    p.add_argument("--calls-per-poll", type=int, default=1)
    p.add_argument("--scan-records", type=int, default=0)
    p.add_argument("--scans-per-day", type=float, default=0)
    p.add_argument("--page-size", type=int, default=2000)
    p.add_argument("--other-share", type=float, default=0.0, help="share of the allocation used by everything else, 0 to 1")
    p.add_argument("--rate", type=float, help="your per-app rate limit: calls per --frequency seconds")
    p.add_argument("--frequency", type=int, default=1, choices=[1, 60, 3600, 86400])
    a = p.parse_args()

    r = plan(base=a.base, licenses=a.licenses, per_license=a.per_license, extra=a.extra, changes_per_day=a.changes_per_day,
             records_per_call=a.records_per_call, polls_per_day=a.polls_per_day, calls_per_poll=a.calls_per_poll,
             scan_records=a.scan_records, page_size=a.page_size, scans_per_day=a.scans_per_day,
             other_share=a.other_share, rate=a.rate, frequency=a.frequency)
    print(f"Daily allocation:            {r['allocation']:,}")
    for k, v in r["parts"].items():
        print(f"  {k:<26} {v:,}")
    print(f"Estimated daily calls:       {r['estimated_daily_calls']:,} ({r['share_of_allocation']:.0%} of the allocation)")
    print(f"Left for this sync:          {r['budget_for_this_sync']:,}  ->  {'fits' if r['fits'] else 'DOES NOT FIT'}")
    print(f"Sustainable all-day rate:    {r['sustainable_rate_per_second']:.2f} calls per second")
    if "rate_limit_daily_ceiling" in r:
        ok = "a real guard" if r["rate_limit_is_a_real_guard"] else "too high to protect you: it would let the sync use more than its budget"
        print(f"Your rate limit allows up to {r['rate_limit_daily_ceiling']:,} calls a day: {ok}")


if __name__ == "__main__":
    main()
