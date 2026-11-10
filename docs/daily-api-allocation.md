# The daily API allocation

## How it works

- It is **per org**, not per user. Every integration, script, app and tool that calls the API draws from the same pool.
- It is counted over a **rolling 24 hours**, not a calendar day.
- Its size depends on the edition and on the number and type of licenses. For an Enterprise Edition org, Salesforce's cheat sheet describes a base amount plus an amount per license, plus any purchased add-ons. Its worked example is 15 licenses at 1,000 each on a base of 100,000, giving 115,000 requests.
- The exact figures vary by edition and license type and change over time. **Check Salesforce's current limits cheat sheet for yours.**

```text
daily allocation  =  base  +  (licenses x per-license amount)  +  add-ons
```

## See what you have used

- In Salesforce Setup, the company information and system overview pages show API requests for the last 24 hours.
- Salesforce returns API usage in a response header (`Sforce-Limit-Info`, with an `api-usage` value) and exposes limits through its Limits resource. Confirm the current names in the REST API reference.
- Look at **who** is spending, not only how much. If a sync is 20 percent of the allocation and reporting tools are 60 percent, the fix is elsewhere.

## Estimate what a sync costs

```bash
python scripts/api_budget.py --base 100000 --licenses 15 --per-license 1000 \
  --changes-per-day 20000 --records-per-call 1 \
  --polls-per-day 1440 --calls-per-poll 2 \
  --scan-records 50000 --scans-per-day 1 --page-size 2000 \
  --other-share 0.3 --rate 5 --frequency 1
```

It adds up writes, polling and full scans, compares them with what is left after everything else, and tells you if your rate limit is a real guard. The numbers are yours. Page size and records per call are assumptions to check for the API you use.

## The insight that surprises people: a per-second limit is not a daily guard

A rate limit of 5 calls per second sounds small. Over a day it allows 5 x 86,400 = **432,000 calls**, far above a 115,000 allocation. The allocation works out to about **1.3 calls per second, all day**.

| Setting | Protects you from |
|---|---|
| A rate limit **per second** | Bursts, and many concurrent calls |
| A rate limit **per hour or per day** | Spending too much over the day. Changes wait until the window resets |
| A lower **Data Sync Frequency** | Wasted polls |
| Fewer **full scans** and **initial loads** | Big one-off spends |

If the daily total is the problem, you need a lower **volume**, not just a lower **burst**.

## Ways to spend fewer calls

| Lever | How it helps |
|---|---|
| **Slower sync frequency** | Fewer polls. Choose the slowest the business accepts |
| **Fewer fields and tables** | Smaller change volume |
| **Batch or bulk writes** | Many records per call |
| **No unnecessary full scans** | A scan reads every record. Choose the longest interval you can accept |
| **One sync per pair of apps** | Never run two syncs doing the same job |
| **Do the initial load off-peak** | The first run copies every record |
| **Stop other waste** | Retired integrations, runaway scripts, hourly reports |
| **A larger allocation** | Ask Salesforce if the baseline is simply too small |

## When the allocation is exhausted

Requests fail until usage falls back under the limit as old calls leave the 24-hour window. Do not retry in a tight loop. It spends calls and delays recovery. With a rate limit set on the sync, changes wait and sync once calls are available instead of failing.
