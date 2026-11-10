# Why a Salesforce sync fails "because of limits"

"API limit" is used for at least five different problems. They have different causes and different fixes. Name the right one first.

## The six families

| # | Family | What it means | Typical message | Is it an API limit? |
|---|---|---|---|---|
| 1 | **Daily API allocation** | The org used its API requests for the rolling 24-hour period. Shared by every integration | `REQUEST_LIMIT_EXCEEDED: TotalRequests Limit exceeded.` | Yes |
| 2 | **Concurrent requests** | Too many long-running requests (20 seconds or more) at once | `REQUEST_LIMIT_EXCEEDED: ConcurrentPerOrgLongTxn Limit exceeded.` | Yes |
| 3 | **Record locking** | Parallel writes hit the same record, or records under the same parent | `UNABLE_TO_LOCK_ROW: unable to obtain exclusive access to this record` | No, but it looks like one under load |
| 4 | **Automation governor limits** | A trigger, flow or Apex fired by the write ran out of its own per-transaction limits | `Too many SOQL queries: 101`, `Apex CPU time limit exceeded` | No. These are Salesforce's own limits |
| 5 | **Storage limits** | The org is out of data or file storage | `STORAGE_LIMIT_EXCEEDED` | No |
| 6 | **Not a limit at all** | A validation rule, a required field, field security, a duplicate rule or a bad value | `FIELD_CUSTOM_VALIDATION_EXCEPTION`, `REQUIRED_FIELD_MISSING`, `INSUFFICIENT_ACCESS` | No |

Wording can change. Use the messages as a guide, not a contract.

## The same words, two meanings

`REQUEST_LIMIT_EXCEEDED` appears for both the daily allocation and the concurrent limit. Read the rest of the message. If it does not say which one, check both: the last 24 hours of API usage **and** whether long-running requests piled up.

## How to tell them apart

| You see | Think |
|---|---|
| Everything fails after a busy day, and recovers by itself later | Daily allocation (a rolling window) |
| Failures come in bursts when large batches run | Concurrency, or record locking |
| Failures involve the same parent record (many contacts of one account) | Record locking |
| Failures are on writes to one object with heavy automation | Automation governor limits |
| The same record fails every time, whatever the pace | Not a limit. Look at the data and the rules |
| It failed from the first call | Edition, permissions or API access. See [triage](triage-runbook.md) |

## Why a sync is a heavy API user

A sync is always running, and its cost has several parts:

- **Writes** to keep the other side current.
- **Reading** what changed, which costs calls on every poll even when nothing changed.
- **The first run**, which copies every record already in the sending app.
- **Full table scans** for fields that do not mark themselves as changed, such as formula fields.
- **Schema changes**: adding a field can re-read the whole table.

Every one of them draws from the same allocation as your other integrations, reports and tools.

## Run the triage tool

```bash
python scripts/error_triage.py "REQUEST_LIMIT_EXCEEDED: TotalRequests Limit exceeded."
python scripts/error_triage.py --file samples/errors.txt
```

Next: [the daily allocation](daily-api-allocation.md), [concurrency and locking](concurrency-and-locking.md), [pace and rate limits](sync-pace.md).
