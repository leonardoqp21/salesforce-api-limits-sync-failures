# Triage runbook: a Salesforce sync is failing or stalled

Read before you write. Nothing below changes anything until step 5, and only after you decide.

## 1. What is the symptom?

| Symptom | Go to |
|---|---|
| It failed from the very first call | **Connection and access** below |
| Records are late, and the pending count grows | **Pace** below |
| Errors say `REQUEST_LIMIT_EXCEEDED` | **Which limit** below |
| Errors say `UNABLE_TO_LOCK_ROW` | [Concurrency and locking](concurrency-and-locking.md) |
| Errors mention triggers, SOQL, CPU or heap | [Automation limits](concurrency-and-locking.md#automation-governor-limits) |
| The same record fails every time | **Not a limit** below |
| The sync is paused | **Paused** below |

## 2. Read the issues

Read the issues for the sync and group them by cause. Use `python scripts/error_triage.py --file errors.txt` to classify a list of messages. Choose the resolution for each group yourself: retry re-reads the current source values, revert changes data in the other app, ignore leaves it.

## 3. Connection and access

- Is the Salesforce edition one that includes the API? (Professional needs an add-on. Group and Essentials cannot connect.) The error "The REST API is not enabled for this Organization" means it does not.
- Does the connected user have **API Enabled**?
- Is the Stacksync connected app installed in the org?
- Did the session expire? Reauthorize the connection.

## 4. Which limit?

1. Open Salesforce API usage for the last 24 hours. Is it near the allocation? See [the daily allocation](daily-api-allocation.md).
2. If it is high, find **who** is spending. Another integration, a report or your sync?
3. If it is not high, look for **concurrency**: large batches, slow automation, many parallel writers.

## 5. Pace

Pending changes keep growing when changes arrive faster than the pace you set. Look at the Data Sync Frequency and the per-app rate limit. A limit that is too low makes changes wait, which is safe but slow. See [pace and rate limits](sync-pace.md).

## 6. Not a limit

Look at the failing record: a validation rule, a required field, field-level security on a custom field, a duplicate rule, a value that does not fit. Fix the data or the rule. A retry will not help.

## 7. Paused

A sync paused temporarily was stopped by errors from the app. Fix the cause, then switch it on. Paused changes wait and sync when it starts again.

## 8. Apply the fix, then confirm

- Change one setting at a time.
- Watch pending changes and issues for a full cycle.
- Write down what you changed and why.

## What not to do

- **Do not delete and recreate the sync** to "reset" it. A new sync does not know which records the old one linked, and duplicates every record.
- **Do not retry in a tight loop.** It spends calls and delays recovery.
- **Do not copy a sync** on the same two apps.
- **Do not raise the rate limit** because of a limit error. That is the opposite of the fix.

[Stacksync docs for the Salesforce connector](https://docs.stacksync.com/two-way-sync/connectors/salesforce).
