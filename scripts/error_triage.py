"""Triage a Salesforce sync error: is it an API limit, record locking, automation, or not a limit at all?

Paste an error message or point it at a log file:

    python scripts/error_triage.py "REQUEST_LIMIT_EXCEEDED: TotalRequests Limit exceeded."
    python scripts/error_triage.py --file samples/errors.txt

The rules are simple pattern matches on the messages Salesforce commonly returns. They are a
starting point, not a diagnosis. Salesforce can change wording, and a vague message may fit
more than one family. Standard library only. Python 3.9 or newer.
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class Rule:
    family: str
    pattern: re.Pattern
    meaning: str
    next_steps: tuple[str, ...]


RULES: list[Rule] = [
    Rule("daily-api-allocation", re.compile(r"TotalRequests", re.I),
         "The org has used its API request allocation for the rolling 24-hour period. It is shared by every integration.",
         ("Check API usage in Salesforce (Setup, Company Information) and what else calls the API",
          "Lower the sync's per-app rate limit and the sync frequency so it spends fewer calls",
          "Stop expensive reads such as full table scans or repeated initial loads",
          "Ask Salesforce about a larger allocation if the baseline is simply too high")),
    Rule("concurrent-requests", re.compile(r"Concurrent(PerOrg)?(LongTxn)?\s*Limit|concurrent.*(request|api)", re.I),
         "Too many long-running requests (20 seconds or more) were in flight at once.",
         ("Lower concurrency and batch sizes",
          "Find slow queries or slow automation triggered by the writes",
          "Spread writes out with a rate limit or a queue")),
    Rule("request-limit-unspecified", re.compile(r"REQUEST_LIMIT_EXCEEDED", re.I),
         "Salesforce refused the request because a request limit was reached. The message does not say which one.",
         ("Check BOTH the 24-hour API usage and the number of long-running concurrent requests",
          "Read the rest of the error text for TotalRequests or a concurrent limit")),
    Rule("record-locking", re.compile(r"UNABLE_TO_LOCK_ROW|unable to obtain exclusive access|ENTITY_IS_LOCKED", re.I),
         "Two writes tried to change the same record, or records with the same parent, at the same time.",
         ("Reduce parallel writes to related records",
          "Group or sort writes by parent record, and lower concurrency",
          "Use serial processing only as a last resort, because it is slower",
          "Retry with backoff. This failure is usually temporary")),
    Rule("automation-governor-limit", re.compile(r"Too many (SOQL queries|DML statements|query rows)|Apex CPU time|heap size|Too many future|CPU time limit", re.I),
         "Salesforce automation (triggers, flows, Apex) fired by the write ran out of its own per-transaction limits. This is not an API limit.",
         ("Look at the triggers, flows and processes that run when this object is written",
          "Send smaller batches so each transaction does less",
          "Ask your Salesforce admin to bulkify the automation")),
    Rule("storage-limit", re.compile(r"STORAGE_LIMIT_EXCEEDED|data storage", re.I),
         "The org is out of data or file storage. Not an API limit.",
         ("Free or buy storage. Writes will keep failing until then",)),
    Rule("not-a-limit-edition", re.compile(r"REST API is not enabled|API_DISABLED_FOR_ORG|API_CURRENTLY_DISABLED", re.I),
         "The API is not available to this org or user. Not a rate limit.",
         ("Check the Salesforce edition includes the API (Professional needs an add-on)",
          "Check the connected user has API Enabled")),
    Rule("not-a-limit-permissions", re.compile(r"INSUFFICIENT_ACCESS|INVALID_FIELD_FOR_INSERT_UPDATE|FIELD_INTEGRITY_EXCEPTION|no access to field|INVALID_SESSION_ID", re.I),
         "A permission, field-security or session problem. Not a limit.",
         ("Check the connected user's profile, permission sets and field-level security",
          "Reauthorize the connection if the session expired")),
    Rule("not-a-limit-data-rules", re.compile(r"FIELD_CUSTOM_VALIDATION_EXCEPTION|REQUIRED_FIELD_MISSING|DUPLICATES_DETECTED|DUPLICATE_VALUE|STRING_TOO_LONG|INVALID_OR_NULL_FOR_RESTRICTED_PICKLIST", re.I),
         "A validation rule, a required field, a duplicate rule or a value that does not fit. Not a limit.",
         ("Read the failing record's value against the Salesforce rule",
          "Fix the data or the rule. Retrying will not help")),
]
UNKNOWN = Rule("unknown", re.compile(r"."), "No known pattern matched.", ("Read the full error text and the failing record", "Check the sync's issues for the same record"))


def triage(message: str) -> Rule:
    for rule in RULES:
        if rule.pattern.search(message):
            return rule
    return UNKNOWN


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("message", nargs="?")
    parser.add_argument("--file")
    args = parser.parse_args()
    lines = [args.message] if args.message else open(args.file, encoding="utf-8").read().splitlines() if args.file else sys.stdin.read().splitlines()

    counts: dict[str, int] = {}
    for line in filter(str.strip, lines):
        rule = triage(line)
        counts[rule.family] = counts.get(rule.family, 0) + 1
        if len(lines) == 1:
            print(f"{rule.family}: {rule.meaning}")
            for step in rule.next_steps:
                print(f"  - {step}")
    if len(lines) > 1:
        for family, n in sorted(counts.items(), key=lambda x: -x[1]):
            rule = next((r for r in RULES + [UNKNOWN] if r.family == family))
            print(f"{n:4}  {family}: {rule.meaning}")


if __name__ == "__main__":
    main()
