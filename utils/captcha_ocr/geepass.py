"""GeePass 40200 双圈旋转接口。"""

import base64
import io
import logging
from typing import Optional

from PIL import Image

from .hard_timeout import post_json_with_hard_timeout


class GeePassOCR:
    API_URL = "https://api.geepass.cn/api/recognize/captcha"
    TYPE_ID = 40200

    def __init__(self, token: str):
        self.token = str(token or "").strip()
        self.last_error = None
        self.last_failure_can_fallback = False

    @staticmethod
    def _image_b64(image_bytes: bytes) -> str:
        with Image.open(io.BytesIO(image_bytes)) as image:
            output = io.BytesIO()
            image.convert("RGBA" if "transparency" in image.info else "RGB").save(
                output, format="PNG"
            )
        return base64.b64encode(output.getvalue()).decode("ascii")

    def recognize_rotate_angle(
        self, out_ring_image: bytes, inner_circle_image: bytes, *, timeout_seconds: int = 9
    ) -> Optional[float]:
        self.last_error = None
        self.last_failure_can_fallback = False
        try:
            result = post_json_with_hard_timeout(
                self.API_URL,
                {
                    "token": self.token,
                    "type": self.TYPE_ID,
                    "r_image": self._image_b64(inner_circle_image),
                    "bg_image": self._image_b64(out_ring_image),
                },
                timeout=timeout_seconds,
                connect_timeout=9,
            )
        except Exception as exc:
            self.last_error = exc
            self.last_failure_can_fallback = getattr(
                getattr(exc, "response", None), "status_code", None
            ) in {401, 403}
            logging.warning("GeePass 旋转接口连接失败：%s", exc)
            return None

        code = str(result.get("code", "")) if isinstance(result, dict) else ""
        message = str(result.get("msg") or result.get("message") or "") if isinstance(result, dict) else ""
        if code != "10000":
            self.last_failure_can_fallback = code in {"10002", "10003"} or any(
                word in message.lower() for word in ("余额", "token", "权限", "balance", "unauthorized")
            )
            logging.warning("GeePass 旋转识别失败：%s", result)
            return None
        try:
            return float(result["data"]["data"]["angle"])
        except (KeyError, TypeError, ValueError):
            logging.warning("GeePass 响应缺少有效角度：%s", result)
            return None
