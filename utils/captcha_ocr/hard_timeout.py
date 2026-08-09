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
                "--write-out",
                "\n%{http_code}",
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
    body, separator, status_text = completed.stdout.rpartition(b"\n")
    status = int(status_text) if separator and status_text.isdigit() else 0
    if status >= 400:
        response = requests.Response()
        response.status_code = status
        response._content = body
        raise requests.exceptions.HTTPError(f"OCR HTTP {status}", response=response)
    return json.loads(body if separator else completed.stdout)
