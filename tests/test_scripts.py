import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import api_budget as ab  # noqa: E402
from error_triage import triage  # noqa: E402
from write_pacer import paced, unpaced  # noqa: E402


class TriageTests(unittest.TestCase):
    CASES = {
        "REQUEST_LIMIT_EXCEEDED: TotalRequests Limit exceeded.": "daily-api-allocation",
        "REQUEST_LIMIT_EXCEEDED: ConcurrentPerOrgLongTxn Limit exceeded.": "concurrent-requests",
        "REQUEST_LIMIT_EXCEEDED": "request-limit-unspecified",
        "UNABLE_TO_LOCK_ROW: unable to obtain exclusive access to this record": "record-locking",
        "System.LimitException: Too many SOQL queries: 101": "automation-governor-limit",
        "Apex CPU time limit exceeded": "automation-governor-limit",
        "STORAGE_LIMIT_EXCEEDED: storage limit exceeded": "storage-limit",
        "The REST API is not enabled for this Organization": "not-a-limit-edition",
        "INSUFFICIENT_ACCESS_OR_READONLY: insufficient access rights": "not-a-limit-permissions",
        "FIELD_CUSTOM_VALIDATION_EXCEPTION: Close date cannot be in the past": "not-a-limit-data-rules",
        "REQUIRED_FIELD_MISSING: Required fields are missing: [LastName]": "not-a-limit-data-rules",
        "no idea what this is": "unknown",
    }

    def test_known_messages(self):
        for message, family in self.CASES.items():
            with self.subTest(message=message):
                self.assertEqual(triage(message).family, family)

    def test_every_rule_has_steps(self):
        for message in self.CASES:
            self.assertTrue(triage(message).next_steps)

    def test_sample_log_file_is_classified(self):
        lines = (ROOT / "samples" / "errors.txt").read_text().splitlines()
        families = {triage(l).family for l in lines if l.strip()}
        self.assertLessEqual({"daily-api-allocation", "record-locking", "unknown", "not-a-limit-data-rules"}, families)


class BudgetTests(unittest.TestCase):
    def test_allocation_formula(self):
        self.assertEqual(ab.allocation(100_000, 15, 1_000), 115_000)
        self.assertEqual(ab.allocation(100_000, 15, 1_000, extra=5_000), 120_000)

    def test_calls_for_changes(self):
        self.assertEqual(ab.calls_for_changes(20_000, 1), 20_000)
        self.assertEqual(ab.calls_for_changes(20_000, 200), 100)
        self.assertEqual(ab.calls_for_changes(201, 200), 2)

    def test_polling_costs_calls_even_when_nothing_changes(self):
        self.assertEqual(ab.calls_for_polling(1440, 2), 2880)

    def test_full_scans(self):
        self.assertEqual(ab.calls_for_scans(50_000, 2_000, 1), 25)
        self.assertEqual(ab.calls_for_scans(50_000, 2_000, 24), 600)

    def test_sustainable_rate_and_ceiling(self):
        self.assertAlmostEqual(ab.sustainable_rate(86_400), 1.0)
        self.assertAlmostEqual(ab.sustainable_rate(86_400, 0.5), 0.5)
        self.assertEqual(ab.daily_ceiling(5, 1), 432_000)
        self.assertEqual(ab.daily_ceiling(1000, 3600), 24_000)

    def test_a_generous_rate_limit_is_not_a_guard(self):
        r = ab.plan(base=100_000, licenses=15, per_license=1_000, changes_per_day=20_000, other_share=0.3, rate=5, frequency=1)
        self.assertFalse(r["rate_limit_is_a_real_guard"])
        r = ab.plan(base=100_000, licenses=15, per_license=1_000, changes_per_day=20_000, other_share=0.3, rate=1, frequency=60)
        self.assertTrue(r["rate_limit_is_a_real_guard"])

    def test_plan_fits_or_not(self):
        small = ab.plan(base=100_000, licenses=15, per_license=1_000, changes_per_day=20_000, polls_per_day=1440, calls_per_poll=2)
        self.assertTrue(small["fits"])
        big = ab.plan(base=100_000, licenses=15, per_license=1_000, changes_per_day=200_000, other_share=0.3)
        self.assertFalse(big["fits"])

    def test_drain_time(self):
        self.assertEqual(ab.drain_seconds(10_000, 10), 1_000)
        self.assertEqual(ab.drain_seconds(1, 0), float("inf"))


class PacerTests(unittest.TestCase):
    BURST = {0: 5000}

    def test_unpaced_burst_is_one_huge_second(self):
        self.assertEqual(unpaced(self.BURST, 1).peak_calls_per_second, 5000)

    def test_pacing_bounds_the_rate_and_loses_nothing(self):
        r = paced(self.BURST, 10, 1)
        self.assertEqual(r.peak_calls_per_second, 10)
        self.assertEqual(r.total_calls, 5000)
        self.assertEqual(r.seconds_to_finish, 500)

    def test_batching_cuts_calls_and_time(self):
        r = paced(self.BURST, 10, 200)
        self.assertEqual(r.total_calls, 25)
        self.assertLess(r.seconds_to_finish, 10)
        self.assertLessEqual(r.peak_calls_per_second, 10)

    def test_longest_wait_matches_the_backlog(self):
        self.assertEqual(paced({0: 100}, 10, 1).longest_wait_seconds, 9)

    def test_invalid_settings(self):
        with self.assertRaises(ValueError):
            paced(self.BURST, 0, 1)


class HygieneTests(unittest.TestCase):
    def test_no_em_dashes(self):
        for path in ROOT.rglob("*.md"):
            self.assertNotIn(chr(0x2014), path.read_text(encoding="utf-8"), str(path))


if __name__ == "__main__":
    unittest.main()
