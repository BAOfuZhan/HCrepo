"""GitHub OCR HTTP requests with a real wall-clock deadline."""

import json
import subprocess
from urllib.parse import urlencode

import requests


class OCRConnectTimeout(requests.exceptions.ConnectTimeout):
    """DNS/TCP connection was not established before the connect deadline."""


def post_json_with_hard_timeout(
    url: str, payload: dict, *, timeout: int = 30, connect_timeout: int | None = None
) -> dict:
    return _curl_json(
        url, json.dumps(payload).encode(), "application/json", timeout, connect_timeout
    )


def post_form_with_hard_timeout(url: str, payload: dict, *, timeout: int = 30) -> dict:
    return _curl_json(url, urlencode(payload).encode(), "application/x-www-form-urlencoded", timeout)


def _curl_json(
    url: str,
    body: bytes,
    content_type: str,
    timeout: int,
    connect_timeout: int | None = None,
) -> dict:
    connect_timeout_args = (
        ["--connect-timeout", str(connect_timeout)] if connect_timeout is not None else []
    )
    try:
        completed = subprocess.run(
            [
                "curl",
                "--silent",
                "--show-error",
                "--max-time",
                str(timeout),
                *connect_timeout_args,
                "--request",
                "POST",
                "--header",
                f"Content-Type: {content_type}",
                "--write-out",
                "\n__OCR_META__%{http_code},%{time_connect}",
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
    body, separator, meta = completed.stdout.rpartition(b"\n__OCR_META__")
    status_text, _, connect_time_text = meta.partition(b",") if separator else (b"", b"", b"")
    try:
        connected = float(connect_time_text) > 0
    except ValueError:
        connected = False
    if completed.returncode in {6, 7} or (completed.returncode == 28 and not connected):
        raise OCRConnectTimeout(
            f"OCR DNS/TCP connection exceeded {connect_timeout or timeout}s limit"
        )
    if completed.returncode == 28:
        raise requests.exceptions.ReadTimeout(
            f"OCR response exceeded {timeout}s wall-clock limit after connection"
        )
    if completed.returncode:
        raise requests.exceptions.ConnectionError(
            completed.stderr.decode("utf-8", errors="replace").strip()
            or f"curl exited with code {completed.returncode}"
        )
    status = int(status_text) if separator and status_text.isdigit() else 0
    if status >= 400:
        response = requests.Response()
        response.status_code = status
        response._content = body
        raise requests.exceptions.HTTPError(f"OCR HTTP {status}", response=response)
    return json.loads(body if separator else completed.stdout)
