# Queues and batching: when a rate limit is not enough

A sync's per-app rate limit paces the sync's own calls. But your **workflows** that write to Salesforce are a different source of calls. Ten workflows reacting to events can all call at once.

## The problem

```text
many producers (workflows, sync triggers)  ->  Salesforce, all at the same moment
```

A wait step in each workflow does not help. Each run waits on its own, and 20 runs still call together. Retrying on "too many requests" inside a step spends more calls on failures and still bursts.

## The fix: a queue in front of the writer

```text
producers  ->  queue  ->  one consumer, in batches  ->  Salesforce
```

Records wait in the queue while the writer paces itself. They are not lost.

| Queue setting | What it controls |
|---|---|
| **Flushes per time window** | The call pace (the documented default is 10 per second) |
| **Batch size** | Records per consumer run (default 1,000, up to 10,000) |
| **Maximum age** | The longest a record waits before a flush (default 60 seconds) |
| **Order** | Oldest first, or urgent first |

Derive them from the app's limit: batch size is what the app accepts per call or run, and flushes per window stay under its call limit.

## Rules for the consumer

- **Write the whole batch with one bulk-capable call** where Salesforce offers one, instead of one call per record. Verify the batch limits for the endpoint you use in Salesforce's REST API guide.
- **Upsert by key**, so a repeated batch is harmless.
- **Make it safe to repeat.** A failed consumer run is not retried automatically. Replay it.
- **Keep queue, producers and consumer in the same region.**
- **Pause the consumer, not the trigger,** to hold work during a fix.
- **Ask before clearing a queue,** and read how many records are waiting.

## When the producer is a sync

A sync that changes thousands of records in bursts can hand its changes to a queue, so a workflow processes them in batches rather than one run per record. Use this when changes arrive in the hundreds or thousands, or when the receiving app accepts records in bulk.

## Trade-offs

- One more resource to watch. Records pile up if the consumer stops.
- A delay up to the maximum age before records are written.

See the pacing model in [`scripts/write_pacer.py`](../scripts/write_pacer.py): 5,000 records in one second, written at 10 calls per second, take 500 seconds one by one, and 3 seconds in batches of 200.

[Stacksync workflow automation](https://www.stacksync.com/workflow-automation) · [event queues](https://www.stacksync.com/event-queues)
