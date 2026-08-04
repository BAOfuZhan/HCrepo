"""GitHub OCR HTTP requests with a real wall-clock deadline."""

import json
import subprocess
from urllib.parse import urlencode

import requests


def post_json_with_hard_timeout(url: str, payload: dict, *, timeout: int = 30) -> dict:
    return _curl_json(url, json.dumps(payload).encode(), "application/json", timeout)


def post_form_with_hard_timeout(url: str, payload: dict, *, timeout: int = 30) -> dict:
    return _curl_json(url, urlencode(payload).encode(), "application/x-www-form-urlencoded", timeout)


def _curl_json(url: str, body: bytes, content_type: str, timeout: int) -> dict:
    try:
        completed = subprocess.run(
            [
                "curl",
                "--silent",
                "--show-error",
                "--max-time",
                str(timeout),
                "--request",
                "POST",
                "--header",
                f"Content-Type: {content_type}",
                "--data-binary",
                "@-",
                url,
            ],
            input=body,
            capture_output=True,
            timeout=timeout + 2,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise requests.exceptions.ConnectTimeout(
            f"OCR request exceeded {timeout}s wall-clock limit"
        ) from exc
    if completed.returncode == 28:
        raise requests.exceptions.ConnectTimeout(f"OCR request exceeded {timeout}s wall-clock limit")
    if completed.returncode:
        raise requests.exceptions.ConnectionError(
            completed.stderr.decode("utf-8", errors="replace").strip()
            or f"curl exited with code {completed.returncode}"
        )
    return json.loads(completed.stdout)
