import os
import unittest

from utils.reserve import reserve


class SeatApiFamilyNoFallbackTest(unittest.TestCase):
    def test_token_candidates_never_switch_api_family(self):
        original = os.environ.get("CX_SEAT_API_MODE")
        try:
            for family in ("seat", "seatengine"):
                os.environ["CX_SEAT_API_MODE"] = family
                session = reserve()
                url = session.build_token_url("1", "2026-08-31", "1", "fid")
                self.assertEqual(session._get_select_url_candidates(url), [(family, url)])
                opposite_url = url.replace("/apps/seat/", "/apps/seatengine/")
                opposite_url = opposite_url.replace("/apps/seatengine/", "/apps/seat/") if opposite_url == url else opposite_url
                self.assertEqual(
                    session._get_select_url_candidates(opposite_url),
                    [(family, opposite_url)],
                )
        finally:
            if original is None:
                os.environ.pop("CX_SEAT_API_MODE", None)
            else:
                os.environ["CX_SEAT_API_MODE"] = original


if __name__ == "__main__":
    unittest.main()
