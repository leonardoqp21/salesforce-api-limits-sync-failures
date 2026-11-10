# Diagnose and tune the sync from Claude or ChatGPT (Stacksync MCP)

The [Stacksync MCP server](https://www.stacksync.com/mcp) (`https://mcp.stacksync.com/mcp`) lets an assistant read your syncs, their settings and issues, and propose changes, with exactly your permissions. You sign in with OAuth. **No key goes into the chat.** Setup: [docs.stacksync.com/mcp](https://docs.stacksync.com/mcp).

## Safe order of work

1. **Read-only first.** Sign in with "Make changes" cleared.
2. **Find the sync** and read its settings: Data Sync Frequency, the per-app rate limit, the Bulk API setting, pending changes.
3. **Read the issues** and group them by cause. Use the triage rules in this repo to name each group.
4. **Ask for a proposal**, not a change: "Which setting would you change first, and why?"
5. **Approve one change at a time.** Rate limit, frequency, then Bulk API.
6. **Read it back** after the change, and watch pending changes and issues.

## What the assistant can and cannot do

| It can | It cannot |
|---|---|
| Read the sync's settings and issues | Read Salesforce's own API usage numbers. That lives in Salesforce |
| Change frequency, per-app rate limit and the Bulk API setting after you approve | Decide for you which resolution (retry, revert, ignore) to use for a group of issues |
| Explain the likely cause of an error message | Fix a Salesforce validation rule or automation |

If a tool says you have no access, a workspace owner changes your role.

## Prompts

See [`prompts/prompts.md`](../prompts/prompts.md).

## Product page

[Stacksync two-way sync](https://www.stacksync.com/two-way-sync) and the [HubSpot and Salesforce pair](https://www.stacksync.com/integrations/hubspot-and-salesforce) for a typical Salesforce sync.
