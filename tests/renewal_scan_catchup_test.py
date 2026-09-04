from datetime import datetime, timezone, timedelta
import unittest

from server_store.renewal_scan import catch_up_day


BEIJING = timezone(timedelta(hours=8))


class RenewalScanCatchUpTest(unittest.TestCase):
    def test_catch_up_before_23_targets_yesterday(self):
        now = datetime(2026, 8, 22, 22, 59, tzinfo=BEIJING)
        self.assertEqual(catch_up_day(now).isoformat(), "2026-08-21")

    def test_catch_up_at_23_targets_today(self):
        now = datetime(2026, 8, 22, 23, 0, tzinfo=BEIJING)
        self.assertEqual(catch_up_day(now).isoformat(), "2026-08-22")


if __name__ == "__main__":
    unittest.main()
