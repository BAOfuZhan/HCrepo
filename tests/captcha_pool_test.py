import datetime
import concurrent.futures
import unittest
from unittest.mock import Mock, patch

import requests

from main import (
    _available_preheated_captchas,
    _click_captcha_preheat_slots,
    _get_captcha_preheat_deadline,
    _remaining_captcha_preheat_seconds,
    _reuse_unsubmitted_captcha,
    _shared_captcha_preheat_is_serial,
    _should_wait_for_background_followup,
    _should_wait_for_click_preheat,
    _store_shared_captcha,
)
from utils.reserve import reserve
from utils.captcha_ocr.jfbym import JfbymOCR
from utils.captcha_ocr.hard_timeout import OCRConnectTimeout, _curl_json


class CaptchaPoolTest(unittest.TestCase):
    def test_past_normal_rotate_deadline_starts_no_captcha_request(self):
        session = reserve(enable_rotate=True)
        session._get = Mock()

        self.assertEqual(
            session._resolve_rotate_captcha_with_retry(
                max_attempts=3,
                deadline_dt=datetime.datetime.now() - datetime.timedelta(seconds=1),
            ),
            "",
        )
        session._get.assert_not_called()

    def test_curl_timeout_distinguishes_connect_from_response_wait(self):
        with patch("utils.captcha_ocr.hard_timeout.subprocess.run") as run:
            run.return_value = Mock(
                returncode=28,
                stdout=b"\n__OCR_META__000,0.000000,9.000000",
                stderr=b"",
            )
            with self.assertRaises(OCRConnectTimeout):
                _curl_json("http://ocr", b"{}", "application/json", 34, 9)

            run.return_value.stdout = b"\n__OCR_META__000,0.120000,34.000000"
            with self.assertRaisesRegex(
                requests.exceptions.ReadTimeout, "waited 33.880s after connection"
            ):
                _curl_json("http://ocr", b"{}", "application/json", 34, 9)

    def test_jfbym_rotate_uses_nine_second_connect_timeout(self):
        with patch(
            "utils.captcha_ocr.jfbym.post_json_with_hard_timeout",
            return_value={"code": 10000, "data": 90},
        ) as post:
            self.assertEqual(
                JfbymOCR("token", "411115").recognize_rotate_angle(
                    b"outer", b"inner", timeout_seconds=34
                ),
                90,
            )

        self.assertEqual(post.call_args.kwargs, {"timeout": 34, "connect_timeout": 9})

    def test_rotate_fallback_reports_active_provider_without_changing_preference(self):
        session = reserve(enable_rotate=True, rotate_ocr_provider="tulingcloud")
        response = Mock(content=b"image")
        response.raise_for_status.return_value = None
        session._get = Mock(return_value=response)

        failed = Mock(last_error=requests.exceptions.ConnectTimeout())
        failed.compose_rotate_image.return_value = b"composed"
        failed.recognize_rotate_angle.return_value = None
        jfbym_timeout = Mock(last_error=OCRConnectTimeout())
        jfbym_timeout.recognize_rotate_angle.return_value = None

        with (
            patch("utils.captcha_ocr.TulingCloudOCR", return_value=failed),
            patch("utils.captcha_ocr.GeePassOCR", return_value=failed),
            patch("utils.captcha_ocr.JfbymOCR", return_value=jfbym_timeout),
            patch("utils.captcha_ocr.TulingCloudOCR.rotate_angle_to_x", return_value=50),
            patch("utils.reserve._get_tulingcloud_config", return_value=("u", "p", "m")),
        ):
            self.assertIsNone(
                session._recognize_rotate_x(
                    "shade",
                    "cutout",
                    deadline_dt=datetime.datetime.now() + datetime.timedelta(seconds=1),
                )
            )

        self.assertEqual(jfbym_timeout.recognize_rotate_angle.call_count, 2)
        jfbym_timeout.recognize_rotate_angle.assert_called_with(
            b"image", b"image", timeout_seconds=44
        )
        failed.recognize_rotate_angle.assert_any_call(
            b"composed", timeout_seconds=60
        )
        failed.recognize_rotate_angle.assert_any_call(
            b"image", b"image", timeout_seconds=44
        )
        self.assertEqual(session.rotate_ocr_active_provider, "jfbym")
        self.assertEqual(session.rotate_ocr_provider, "tulingcloud")

    def test_primary_timeout_probes_backups_and_only_submits_selected_platform(self):
        session = reserve(enable_rotate=True, rotate_ocr_provider="geepass")
        response = Mock(content=b"image")
        response.raise_for_status.return_value = None
        session._get = Mock(return_value=response)

        first = Mock(last_error=None)
        first.recognize_rotate_angle.return_value = None
        second = Mock(last_error=None)
        second.compose_rotate_image.return_value = b"composed"
        second.recognize_rotate_angle.return_value = None
        third = Mock(last_error=None)
        third.recognize_rotate_angle.return_value = 72
        second_class = Mock(return_value=second)
        second_class.TULINGCLOUD_API_URL = "http://tuling.example/ocr"
        second_class.rotate_angle_to_x.return_value = 64
        third_class = Mock(return_value=third)
        third_class.API_URL = "http://api.jfbym.com/ocr"

        def probe(url, timeout):
            if "jfbym" in url:
                return 0.2
            raise requests.exceptions.ConnectTimeout()

        wait_calls = 0

        def soft_timeout_once(futures, **kwargs):
            nonlocal wait_calls
            wait_calls += 1
            if wait_calls == 1:
                return set(), set(futures)
            return concurrent.futures.wait(futures, **kwargs)

        with (
            patch("utils.captcha_ocr.GeePassOCR", return_value=first),
            patch("utils.captcha_ocr.TulingCloudOCR", new=second_class),
            patch("utils.captcha_ocr.JfbymOCR", new=third_class),
            patch("utils.reserve._get_tulingcloud_config", return_value=("u", "p", "m")),
            patch("utils.reserve._get_jfbym_config", return_value=("t", "411115")),
            patch(
                "utils.reserve.probe_http_connection",
                side_effect=probe,
            ),
            patch("utils.reserve.wait", side_effect=soft_timeout_once),
        ):
            result = session._recognize_rotate_x("shade", "cutout")

        self.assertEqual(result, {"provider": "JFBYM", "angle": 72, "x": 64})
        first.recognize_rotate_angle.assert_called_once_with(
            b"image", b"image", timeout_seconds=60
        )
        second.recognize_rotate_angle.assert_not_called()
        third.recognize_rotate_angle.assert_called_once_with(
            b"image", b"image", timeout_seconds=44
        )

    def test_simultaneous_reservation_limit_is_terminal(self):
        self.assertTrue(
            reserve._is_terminal_submit_failure("同时预约数量已达上限3次")
        )

    def test_only_serial_followups_wait_for_background_first_captcha(self):
        self.assertFalse(_should_wait_for_background_followup("serial", 1))
        self.assertTrue(_should_wait_for_background_followup("serial", 2))
        self.assertTrue(_should_wait_for_background_followup("serial", 3))
        self.assertFalse(_should_wait_for_background_followup("burst", 2))

    def test_only_multi_slot_shared_pool_uses_serial_preheat(self):
        self.assertFalse(_shared_captcha_preheat_is_serial(1))
        self.assertTrue(_shared_captcha_preheat_is_serial(2))
        self.assertTrue(_shared_captcha_preheat_is_serial(3))

    def test_multi_slot_background_preheat_never_blocks_token(self):
        self.assertTrue(_should_wait_for_click_preheat(1, True))
        self.assertFalse(_should_wait_for_click_preheat(2, True))
        self.assertFalse(_should_wait_for_click_preheat(3, True))
        self.assertFalse(_should_wait_for_click_preheat(1, False))

    def test_single_slot_keeps_one_click_captcha_preheat(self):
        self.assertEqual(_click_captcha_preheat_slots(1), (1,))
        self.assertEqual(_click_captcha_preheat_slots(2), (1, 2, 3))
        self.assertEqual(_click_captcha_preheat_slots(3), (1, 2, 3))

    def test_soft_deadline_stops_with_one_result_but_retries_when_empty(self):
        soft_deadline = datetime.datetime(2026, 7, 15, 19, 59, 58)
        retry_deadline = datetime.datetime(2026, 7, 15, 20, 0, 40)
        now = soft_deadline + datetime.timedelta(milliseconds=1)

        self.assertGreater(
            _remaining_captcha_preheat_seconds(
                now,
                soft_deadline,
                retry_deadline,
                True,
                {1: "", 2: "", 3: ""},
            ),
            0,
        )
        self.assertEqual(
            _remaining_captcha_preheat_seconds(
                now,
                soft_deadline,
                retry_deadline,
                True,
                {1: "captcha-1", 2: "", 3: ""},
            ),
            0,
        )

    def test_multi_slot_deadline_is_two_seconds_before_a_or_c_token_node(self):
        target = datetime.datetime(2026, 7, 15, 20, 0, 0)

        self.assertEqual(
            _get_captcha_preheat_deadline(
                target,
                target - datetime.timedelta(milliseconds=1531),
                3,
                "A",
            ),
            target - datetime.timedelta(milliseconds=3531),
        )
        self.assertEqual(
            _get_captcha_preheat_deadline(
                target,
                target + datetime.timedelta(milliseconds=14),
                2,
                "C",
            ),
            target - datetime.timedelta(milliseconds=1986),
        )
        self.assertEqual(
            _get_captcha_preheat_deadline(
                target,
                target - datetime.timedelta(milliseconds=1531),
                1,
                "A",
            ),
            target,
        )
        self.assertEqual(
            _get_captcha_preheat_deadline(target, target, 3, "B"),
            target,
        )

    def test_unused_captchas_roll_over_in_original_order(self):
        pool = {1: "captcha-1", 2: "captcha-2", 3: "captcha-3"}

        self.assertEqual(
            _available_preheated_captchas(pool, {"captcha-1"}),
            ["captcha-2", "captcha-3"],
        )
        self.assertEqual(
            _available_preheated_captchas(pool, {"captcha-1", "captcha-2"}),
            ["captcha-3"],
        )
        self.assertEqual(
            _available_preheated_captchas(pool, set(pool.values())),
            [],
        )

    def test_zero_shared_pool_stores_onsite_captcha_in_consumed_slot(self):
        pool = {1: "used-1", 2: "used-2", 3: "used-3"}
        consumed = set(pool.values())

        self.assertEqual(_store_shared_captcha(pool, consumed, "onsite-1"), 1)
        self.assertEqual(
            _available_preheated_captchas(pool, consumed),
            ["onsite-1"],
        )
        self.assertEqual(_store_shared_captcha(pool, consumed, "onsite-1"), 1)

    def test_unsubmitted_captcha_is_reused_but_posted_captcha_is_not(self):
        self.assertEqual(
            _reuse_unsubmitted_captcha(False, "captcha-2"),
            "captcha-2",
        )
        self.assertEqual(_reuse_unsubmitted_captcha(True, "captcha-2"), "")


if __name__ == "__main__":
    unittest.main()
