# Set the pace: rate limits, frequency and bulk

These are the controls a Stacksync sync gives you, from its documentation. Always check the current docs.

## 1. A rate limit per app

A rate limit is set **per app inside a sync**: the most API calls Stacksync makes to that app per second, minute, hour or day.

- Settings: `rate` calls per `frequency` seconds, where frequency is **1, 60, 3600 or 86400**.
- **When the limit is reached, changes wait and sync once calls are available again. They do not fail.**
- A changed limit takes up to a minute to apply.
- **Prefer per second or per minute**, for example 5 to 10 requests per second. An hourly or daily limit can leave changes waiting until the window resets.

| Window | Protects against | Cost |
|---|---|---|
| Per second | Bursts and concurrency | Does not cap the daily total (see [the daily allocation](daily-api-allocation.md)) |
| Per minute | Short spikes | Same |
| Per hour or day | The daily total | Changes wait for the window to reset |

## 2. Data Sync Frequency

How much wait Stacksync adds between detecting and syncing changes. Documented values: 0 (no added wait), at least once a minute, every 5 minutes, every 15 minutes, every hour, every 6 hours, every 24 hours. **Choose the slowest value the business accepts.** A slower frequency means fewer polls.

## 3. Bulk API access (Salesforce)

A sync setting turns the bulk API on or off. It needs **View All Data** on the connected user's profile. Bulk calls move many records per call, which suits large loads.

## 4. Full table scans (formula fields)

Salesforce formula fields are computed. A change of their inputs does not always count as a change of the formula, so tables with formula fields can use a periodic **full table scan**. Documented intervals run from every hour to every 24 hours, or never. **Each scan reads every record of the table.** Choose the longest interval you accept.

## 5. The first run and new fields

- The first run **copies the records already in the sending app** (both apps, for a two-way pair). On a large table it takes time and many calls. Plan it off-peak.
- Adding a new field to an existing table makes the table **read all its records again**, which costs more calls.

## 6. How to know it is working

- The sync's **pending changes** count. If it keeps growing, changes are arriving faster than the pace you set.
- The **issues** list for failed records.
- A sync **paused temporarily** was stopped by errors from the app. Follow [the triage runbook](triage-runbook.md).

## A starting recipe

1. Estimate daily calls with [`scripts/api_budget.py`](../scripts/api_budget.py).
2. Set the frequency to the slowest the business accepts.
3. Set a per-second rate limit to protect from bursts.
4. If the daily total is tight, add a lower per-hour limit or reduce volume.
5. Run the first load off-peak, on a sandbox first.
6. Watch pending changes and issues for a week. Adjust.

Simulate pacing with [`scripts/write_pacer.py`](../scripts/write_pacer.py).

Official docs: [Salesforce connector](https://docs.stacksync.com/two-way-sync/connectors/salesforce).
