# Monitoring: see the limit coming

## What to watch

| Signal | Why | Alert when |
|---|---|---|
| **API usage, last 24 hours** | The daily allocation is rolling and shared | It passes a share you choose (say 70 percent) |
| **Pending changes** on the sync | Changes are arriving faster than the pace | It keeps growing for more than a cycle |
| **Issues** on the sync | Failed records | New groups appear |
| **Long-running request** errors | Concurrency | Any |
| **Record locking** errors | Parallel writes | A rising count |
| **Sync status** | An app error can pause it | It is paused |
| **Other integrations' volume** | They share the allocation | A new one starts, or one doubles |

## A simple routine

- **Daily:** look at API usage and the sync status.
- **Weekly:** group issues by cause with `scripts/error_triage.py` and look at what is growing.
- **When anything changes:** a new integration, a new field, a big import, a new automation on a synced object. Re-estimate with [`scripts/api_budget.py`](../scripts/api_budget.py).

## Plan big events

Big imports, mass updates, a new field added to a large table, and the first run of a new sync all spend a lot of calls in a short time. Schedule them off-peak and warn the teams that use the same org.

## Keep an inventory of API consumers

List every integration that uses the org's API, its owner and its rough daily call count. When the allocation is tight, this list is the fastest way to find what to turn down.

## With the Stacksync MCP server

An assistant connected through the [Stacksync MCP server](https://www.stacksync.com/mcp) can read the sync's settings, pending changes and issues, group the failures by cause and propose the smallest fix. See [build with MCP](build-with-mcp.md).
