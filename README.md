# Salesforce API limits and sync failures: why your sync fails and how to fix it

Your sync to Salesforce fails, stalls or shows `REQUEST_LIMIT_EXCEEDED`, and "API limits" is all anyone says. This repo tells you **which limit** you hit, why a sync is such a heavy API user, how to **set the pace** so it stops, and when a **queue** is the real fix. It includes tested tools that triage error messages, estimate your daily API spend and simulate pacing.

It uses [Stacksync's Salesforce connector](https://www.stacksync.com/connectors/salesforce) and its [two-way sync](https://www.stacksync.com/two-way-sync) settings. The diagnosis applies to any integration.

> **Short answer:** "API limit" covers at least five different problems. The **daily API allocation** is org-wide, rolling over 24 hours and shared by every integration. The **concurrent request limit** caps long-running requests at the same moment. **Record locking** comes from parallel writes to the same record or parent. **Automation limits** (triggers, flows, Apex) are Salesforce's own per-transaction limits. And many "limit" errors are **not limits** at all (validation rules, required fields, permissions). Name the right one, then fix volume (daily), concurrency (bursts) or the data (not a limit). A per-second rate limit stops bursts but does **not** cap the daily total.

## Which one is it?

| You see | It is | Fix |
|---|---|---|
| `REQUEST_LIMIT_EXCEEDED: TotalRequests...` | Daily API allocation | Spend fewer calls. Check who else uses the API |
| `REQUEST_LIMIT_EXCEEDED: Concurrent...` | Concurrent long-running requests | Smaller batches, lower concurrency |
| `UNABLE_TO_LOCK_ROW` | Record locking | Fewer parallel writes to related records |
| `Too many SOQL queries`, `Apex CPU time limit` | Automation governor limits | Smaller batches, bulkify the automation |
| `STORAGE_LIMIT_EXCEEDED` | Storage | Free or buy storage |
| `FIELD_CUSTOM_VALIDATION_EXCEPTION`, `REQUIRED_FIELD_MISSING` | **Not a limit** | Fix the data or the rule |
| `The REST API is not enabled for this Organization` | **Not a limit** (edition) | Check the edition has the API |

```bash
python scripts/error_triage.py "REQUEST_LIMIT_EXCEEDED: TotalRequests Limit exceeded."
python scripts/error_triage.py --file samples/errors.txt
```

## Questions this guide answers

### Why does my sync to Salesforce fail with REQUEST_LIMIT_EXCEEDED?
Because a request limit was reached. The message does not always say which one. Most often it is the **daily API allocation** (a rolling 24-hour count for the whole org) or the **concurrent request limit** (too many long-running requests at once). Read the rest of the message and check both. See [docs/why-it-fails.md](docs/why-it-fails.md).

### How many API calls does Salesforce allow per day?
It depends on the edition and the licenses. For an Enterprise Edition org, Salesforce describes a base amount plus an amount per license, plus add-ons. Its worked example is 100,000 plus 15 licenses at 1,000, which is 115,000. The limit is per org, rolling over 24 hours, and shared by every integration. Check Salesforce's current limits cheat sheet for your numbers. See [docs/daily-api-allocation.md](docs/daily-api-allocation.md).

### What is the Salesforce concurrent API request limit?
A cap on API requests that run **20 seconds or longer** at the same time. Salesforce documents 25 for production orgs and sandboxes, and a lower figure for developer and trial orgs. Shorter requests are not counted. See [docs/concurrency-and-locking.md](docs/concurrency-and-locking.md).

### How do I check my Salesforce API usage?
In Setup (company information and system overview show the last 24 hours), through the `Sforce-Limit-Info` response header, or through the Limits resource. Look at who is spending, not only how much.

### Why is a sync such a heavy API user?
It never stops. It writes changes, reads what changed on every poll (even when nothing did), copies every existing record on its first run, re-reads tables when a field is added and runs full table scans for formula fields. See [docs/why-it-fails.md](docs/why-it-fails.md).

### Is a per-second rate limit enough to stay under the daily limit?
No. 5 calls per second is 432,000 calls per day, far above a 115,000 allocation. A per-second limit protects against **bursts**. For the **daily total** you need lower volume (slower frequency, fewer scans, batching) or a per-hour or per-day limit, at the cost of changes waiting for the window to reset. See [docs/daily-api-allocation.md](docs/daily-api-allocation.md).

### What happens to changes when the rate limit is reached?
In Stacksync, changes **wait and sync once calls are available again. They do not fail.** A changed limit takes up to a minute to apply. Prefer a limit per second or per minute. See [docs/sync-pace.md](docs/sync-pace.md).

### How do I reduce the API calls my sync makes?
Use the slowest Data Sync Frequency the business accepts, map only the tables and fields you need, avoid full table scans where you can, turn on bulk access for large loads, run the first load off-peak, and make sure two syncs are not doing the same job. Estimate it with [`scripts/api_budget.py`](scripts/api_budget.py).

### What is UNABLE_TO_LOCK_ROW and how do I fix it in an integration?
Two writes tried to change the same record, or records with the same parent, at the same time. Group or sort writes by parent, lower concurrency, retry with backoff, and use serial processing only as a last resort because it is slow. See [docs/concurrency-and-locking.md](docs/concurrency-and-locking.md).

### Why do I get "Too many SOQL queries" or "Apex CPU time limit exceeded" during a sync?
That is Salesforce automation (a trigger, flow or Apex) fired by the write running out of its own per-transaction limits. It is not an API limit. Send smaller batches and ask your admin to bulkify the automation. A faster sync will not help.

### Should I use a queue to write to Salesforce?
Yes when workflows or sync triggers write in bursts. A queue in front of the writer paces calls and packs records into batches. Records wait. They are not lost. See [docs/queues-and-batching.md](docs/queues-and-batching.md) and the simulation in [`scripts/write_pacer.py`](scripts/write_pacer.py).

### Is it really a limit, or something else?
Many "limit" errors are validation rules, required fields, field-level security or duplicate rules. If the same record fails every time regardless of pace, it is not a limit. See [docs/triage-runbook.md](docs/triage-runbook.md).

### What should I do when the daily allocation is exhausted?
Do not retry in a tight loop. Requests recover as old calls leave the 24-hour window. Find who is spending, lower the sync's volume, and with a rate limit set the sync keeps changes waiting instead of failing.

### Should I delete and recreate the sync to reset it?
No. A new sync does not know which records the old one linked, so it duplicates every record and makes the call problem worse. Edit the existing sync.

## Tools

```bash
# Is it a limit, and which one?
python scripts/error_triage.py --file samples/errors.txt

# How many calls does my sync spend, and is my rate limit a real guard?
python scripts/api_budget.py --base 100000 --licenses 15 --per-license 1000 \
  --changes-per-day 20000 --polls-per-day 1440 --calls-per-poll 2 \
  --scan-records 50000 --scans-per-day 1 --other-share 0.3 --rate 5 --frequency 1

# What do a rate limit and a queue do to a burst? (a teaching model)
python scripts/write_pacer.py

python -m unittest discover -s tests -v
```

Python 3.9 or newer, standard library only. The Salesforce numbers are yours to supply. The triage rules are simple pattern matches, so Salesforce wording changes can make them miss.

## What is in this repo

| Path | What it is |
|---|---|
| [`docs/why-it-fails.md`](docs/why-it-fails.md) | The six families and how to tell them apart |
| [`docs/daily-api-allocation.md`](docs/daily-api-allocation.md) | How the daily limit works, and why a per-second limit does not cap it |
| [`docs/concurrency-and-locking.md`](docs/concurrency-and-locking.md) | Concurrent requests, record locking and automation limits |
| [`docs/sync-pace.md`](docs/sync-pace.md) | Rate limit, frequency, bulk and full scans |
| [`docs/queues-and-batching.md`](docs/queues-and-batching.md) | When a queue is the fix |
| [`docs/triage-runbook.md`](docs/triage-runbook.md) | From symptom to fix |
| [`docs/monitoring.md`](docs/monitoring.md) | See the limit coming |
| [`docs/build-with-mcp.md`](docs/build-with-mcp.md) | Diagnose from Claude or ChatGPT |
| [`prompts/prompts.md`](prompts/prompts.md) | 6 prompts |
| [`scripts/`](scripts) | `error_triage.py`, `api_budget.py`, `write_pacer.py` |

## About Stacksync

[Stacksync](https://www.stacksync.com) keeps CRMs, ERPs and databases in sync. Connector notes: [Salesforce](https://docs.stacksync.com/two-way-sync/connectors/salesforce). Workflows and queues: [workflow automation](https://www.stacksync.com/workflow-automation) and [event queues](https://www.stacksync.com/event-queues). With the [Stacksync MCP server](https://www.stacksync.com/mcp), Claude or ChatGPT can read a sync's settings and issues and propose the smallest fix.

Salesforce limits, error messages and Stacksync settings change. Check the current documentation and test on a sandbox. This repo makes no performance or compliance claims.

## Contributing

Corrections are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE)
