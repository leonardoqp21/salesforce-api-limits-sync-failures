# Contributing

- **A Salesforce limit or message changed:** update the doc and name the official page and date you checked.
- **A new error pattern:** add a rule to `scripts/error_triage.py` and a test case in `tests/test_scripts.py`.
- **A Stacksync setting changed:** update `docs/sync-pace.md` with the docs page you checked.
- Do not state Salesforce numbers you cannot source. Point to the official limits documentation.
- Describe behavior, not outcomes. No performance claims.
- Use synthetic data only. Never include real org ids, tokens or customer data.
