# Prompts for Claude or ChatGPT with the Stacksync MCP server

Connect the Stacksync MCP server first (`https://mcp.stacksync.com/mcp`, OAuth, no key in the chat). For diagnosis, sign in with "Make changes" cleared. Every prompt asks the assistant to wait for your approval before changing anything.

## 1. Find the sync and read its pace

```text
Find my Salesforce syncs. For each one, read its settings and tell me: the Data Sync Frequency, the rate limit for each app, whether the Bulk API setting is on, and the pending changes. Do not change anything.
```

## 2. Group the failures

```text
Read the current issues on my Salesforce sync and group them by cause. For each group, tell me whether it looks like the daily API allocation, concurrent requests, record locking, automation limits, storage, or not a limit at all (a validation rule, a required field, permissions). Show the affected mappings and record ids. Do not retry, revert or ignore anything.
```

## 3. Propose the smallest fix

```text
Based on those groups, tell me the one setting you would change first and why: the Data Sync Frequency, the per-app rate limit, or the Bulk API setting. Explain what would happen to the pending changes. Do not change anything until I approve.
```

## 4. Change the rate limit

```text
Change the rate limit for the Salesforce side of <SYNC NAME> to <RATE> calls per <1, 60, 3600 or 86400> seconds. Tell me what it does to the daily ceiling of calls. Read the setting back afterwards and tell me when the change takes effect.
```

## 5. Estimate before a big job

```text
I am about to <import N records / add a field to a table with N records / run the first load>. Using what you know about how this sync works, tell me what costs API calls (the first copy, re-reading a table for a new field, full table scans for formula fields) and what I should do beforehand: a sandbox test, an off-peak window, a lower rate limit. Do not change anything.
```

## 6. Check for duplicate causes

```text
Records are failing and I want to retry. Before I do, tell me what retry does in this product and what I must not do. I do not want to delete and recreate the sync.
```
