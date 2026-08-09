"""第三方验证码识别接口集中入口。"""

from .chaojiying import ChaojiyingOCR
from .config import (
    DEFAULT_ICONCLICK_OCR_PROVIDER,
    geepass_token,
    jfbym_token,
    jfbym_type_id,
    normalize_iconclick_ocr_provider,
    normalize_rotate_ocr_provider,
    normalize_tulingcloud_captcha_type,
    tulingcloud_model_id,
)
from .geepass import GeePassOCR
from .jfbym import JfbymOCR
from .tulingcloud import TulingCloudOCR

__all__ = [
    "ChaojiyingOCR",
    "DEFAULT_ICONCLICK_OCR_PROVIDER",
    "GeePassOCR",
    "JfbymOCR",
    "TulingCloudOCR",
    "geepass_token",
    "jfbym_token",
    "jfbym_type_id",
    "normalize_iconclick_ocr_provider",
    "normalize_rotate_ocr_provider",
    "normalize_tulingcloud_captcha_type",
    "tulingcloud_model_id",
]
