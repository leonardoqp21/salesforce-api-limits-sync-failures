# Concurrency and record locking

These two look like "limits" because they appear under load. They are caused by writing too much **at the same time**, not too much in total.

## Concurrent long-running requests

Salesforce caps the number of API requests that run for **20 seconds or longer** at the same moment. Salesforce documents 25 for production orgs and sandboxes, and a lower number for developer and trial orgs. Requests shorter than that are not capped by this limit. Past the cap the API returns `REQUEST_LIMIT_EXCEEDED`. Check the current figures in Salesforce's limits documentation.

**What makes requests slow:**
- Large batches or large queries.
- Heavy automation (triggers, flows, Apex) that runs on every write.
- Other integrations that are also running long requests.

**Fixes:** smaller batches, lower concurrency, fewer slow triggers, and spreading writes over time.

## Record locking (`UNABLE_TO_LOCK_ROW`)

While a transaction writes a record, Salesforce locks it. A second transaction that waits too long for the lock fails.

**Common triggers in integrations:**
- Parallel writes to many child records of the **same parent**. Each write also locks the parent.
- Two integrations updating the same record at the same time.
- Bulk jobs that split a file into batches and run them in parallel.

**Fixes:**
- Group or sort writes by parent record.
- Lower concurrency for related records.
- Retry with backoff. These failures are usually temporary.
- Process in serial as a **last resort**. It avoids the contention and is much slower.

## Automation governor limits

When a write fires a trigger, flow or Apex code, that code has its own per-transaction limits (queries, DML statements, CPU time). Errors such as `Too many SOQL queries: 101` or `Apex CPU time limit exceeded` mean the **automation** ran out, not the API.

**Fixes:** send smaller batches so each transaction does less, and ask your Salesforce admin to bulkify the automation. A faster sync does not help.

## What to change on the sync

| Symptom | Setting |
|---|---|
| Bursts cause failures | A per-app rate limit per second or per minute, so calls are spaced out |
| Bulk loads cause failures | Check the Bulk API setting for the sync. It needs the right permission on the connected user |
| Locking on related records | Lower throughput, and review automation on the parent object |

See [pace and rate limits](sync-pace.md).
