"""jfbym 图标点选与双圈旋转打码平台接口。"""

import base64
import logging
import os
import re
import time
from typing import Optional

import requests

from .hard_timeout import post_json_with_hard_timeout


class JfbymOCR:
    """www.jfbym.com customApi client."""

    API_URL = "http://api.jfbym.com/api/YmServer/customApi"

    def __init__(self, token: str, type_id: str):
        self.token = str(token or "").strip()
        self.type_id = str(type_id or "").strip()
        self.last_error = None
        self.last_failure_can_fallback = False
        self.headers = {"Content-Type": "application/json"}

    @staticmethod
    def _normalize_base64(base64_str: str) -> str:
        """jfbym 只接受纯 base64 字符，不要 data:image 前缀、空格或换行。"""
        raw = str(base64_str or "").strip()
        if "," in raw and raw.lower().startswith("data:"):
            raw = raw.split(",", 1)[1]
        return re.sub(r"\s+", "", raw)

    @staticmethod
    def _parse_positions_from_text(text: str) -> list[dict]:
        positions = []
        for x, y in re.findall(r"(-?\d+(?:\.\d+)?)\s*[,，]\s*(-?\d+(?:\.\d+)?)", str(text or "")):
            try:
                positions.append({"x": int(float(x)), "y": int(float(y))})
            except ValueError:
                continue
        return positions

    @classmethod
    def _parse_positions(cls, payload) -> Optional[list[dict]]:
        """尽量兼容 jfbym customApi 常见返回形态。"""
        if payload is None:
            return None

        if isinstance(payload, list):
            positions = []
            for item in payload:
                if not isinstance(item, dict):
                    continue
                x = item.get("x") or item.get("X") or item.get("X坐标值")
                y = item.get("y") or item.get("Y") or item.get("Y坐标值")
                try:
                    positions.append({"x": int(float(x)), "y": int(float(y))})
                except (TypeError, ValueError):
                    continue
            return positions or None

        if isinstance(payload, dict):
            for key in ("data", "result", "res", "points", "position", "positions"):
                if key in payload:
                    parsed = cls._parse_positions(payload.get(key))
                    if parsed:
                        return parsed
            x = payload.get("x") or payload.get("X") or payload.get("X坐标值")
            y = payload.get("y") or payload.get("Y") or payload.get("Y坐标值")
            try:
                return [{"x": int(float(x)), "y": int(float(y))}]
            except (TypeError, ValueError):
                return None

        return cls._parse_positions_from_text(str(payload)) or None

    def recognize_iconclick(self, img_data: bytes) -> Optional[list[dict]]:
        self.last_error = None
        b64_data = self._normalize_base64(base64.b64encode(img_data).decode("ascii"))
        data = {
            "token": self.token,
            "type": self.type_id,
            "image": b64_data,
        }
        request_started = time.monotonic()
        logging.info("jfbym 图标点选请求已开始，type=%s", self.type_id)
        try:
            if os.getenv("ROTATE_OCR_FALLBACK_URL"):
                result = post_json_with_hard_timeout(self.API_URL, data)
            else:
                response = requests.request(
                    "POST", self.API_URL, headers=self.headers, json=data, timeout=30
                )
                result = response.json()
        except Exception as e:
            self.last_error = e
            logging.warning(
                "jfbym 图标点选请求失败，耗时 %.3f 秒：%s",
                time.monotonic() - request_started,
                e,
            )
            return None

        logging.info(
            "jfbym 图标点选请求耗时 %.3f 秒",
            time.monotonic() - request_started,
        )
        logging.debug("jfbym iconclick response: %s", result)

        code = result.get("code") if isinstance(result, dict) else None
        message = str(
            (result.get("msg") or result.get("message") or result.get("data") or "")
            if isinstance(result, dict)
            else result
        )
        if "服务繁忙" in message or "图片" in message or "base64" in message.lower():
            logging.warning(
                "jfbym 返回疑似图片/base64问题：%s；请确认上传的是纯 base64 字符，"
                "不要包含 data:image/...;base64, 前缀、空格或换行",
                message,
            )
        if code not in (None, 0, 1, 10000, "0", "1", "10000"):
            logging.debug("jfbym 图标点选识别失败：%s", result)
            return None

        positions = self._parse_positions(result)
        if not positions:
            logging.debug("jfbym 图标点选未返回可用坐标：%s", result)
            return None
        return positions

    @classmethod
    def _parse_rotate_angle(cls, payload) -> Optional[float]:
        if isinstance(payload, dict):
            if "rotate_angle" in payload:
                return cls._parse_rotate_angle(payload["rotate_angle"])
            return cls._parse_rotate_angle(payload.get("data"))
        if isinstance(payload, list):
            for item in payload:
                angle = cls._parse_rotate_angle(item)
                if angle is not None:
                    return angle
            return None
        try:
            return float(payload)
        except (TypeError, ValueError):
            return None

    def recognize_rotate_angle(
        self,
        out_ring_image: bytes,
        inner_circle_image: bytes,
        *,
        timeout_seconds: int = 9,
    ) -> Optional[float]:
        """原图提交 411115，返回内圈顺时针旋转角度。"""
        self.last_error = None
        self.last_failure_can_fallback = False
        data = {
            "out_ring_image": base64.b64encode(out_ring_image).decode("ascii"),
            "inner_circle_image": base64.b64encode(inner_circle_image).decode("ascii"),
            "token": self.token,
            "type": self.type_id,
        }
        started_at = time.monotonic()
        logging.info("jfbym 双圈旋转请求已开始，type=%s", self.type_id)
        try:
            result = post_json_with_hard_timeout(
                self.API_URL, data, timeout=timeout_seconds
            )
        except Exception as e:
            self.last_error = e
            self.last_failure_can_fallback = getattr(
                getattr(e, "response", None), "status_code", None
            ) in {401, 403}
            logging.warning(
                "jfbym 双圈旋转请求失败，耗时 %.3f 秒：%s",
                time.monotonic() - started_at,
                e,
            )
            return None

        if not isinstance(result, dict) or str(result.get("code")) != "10000":
            code = str(result.get("code", "")) if isinstance(result, dict) else ""
            message = str(result.get("msg") or result.get("message") or "") if isinstance(result, dict) else ""
            self.last_failure_can_fallback = code in {"10002", "10003"} or any(
                word in message.lower() for word in ("余额", "token", "权限", "balance", "unauthorized")
            )
            logging.warning("jfbym 双圈旋转识别失败：%s", result)
            return None
        angle = self._parse_rotate_angle(result.get("data"))
        if angle is None:
            logging.warning("jfbym 双圈旋转未返回角度：%s", result)
            return None
        logging.info(
            "jfbym 双圈旋转识别成功：角度=%s，耗时=%.3f秒",
            angle,
            time.monotonic() - started_at,
        )
        return angle
