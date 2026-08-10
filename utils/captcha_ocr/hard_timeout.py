"""GitHub OCR HTTP requests with a real wall-clock deadline."""

import json
import logging
import socket
import ssl
import subprocess
import time
from urllib.parse import urlencode
from urllib.parse import urlparse

import requests


class OCRConnectTimeout(requests.exceptions.ConnectTimeout):
    """DNS/TCP connection was not established before the connect deadline."""


def probe_http_connection(url: str, timeout: int = 9) -> float:
    """Probe DNS/TCP/TLS reachability without sending an HTTP request body."""
    parsed = urlparse(url)
    host = parsed.hostname
    if not host:
        raise ValueError(f"OCR probe URL has no host: {url}")
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    started_at = time.monotonic()
    with socket.create_connection((host, port), timeout=timeout) as connection:
        if parsed.scheme == "https":
            context = ssl.create_default_context()
            with context.wrap_socket(connection, server_hostname=host):
                pass
    return time.monotonic() - started_at


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
                "\n__OCR_META__%{http_code},%{time_connect},%{time_total}",
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
    meta_parts = meta.split(b",") if separator else []
    status_text = meta_parts[0] if meta_parts else b""
    connect_time_text = meta_parts[1] if len(meta_parts) > 1 else b""
    total_time_text = meta_parts[2] if len(meta_parts) > 2 else b""
    try:
        connect_elapsed = float(connect_time_text)
        connected = connect_elapsed > 0
    except ValueError:
        connect_elapsed = 0.0
        connected = False
    try:
        total_elapsed = float(total_time_text)
    except ValueError:
        total_elapsed = 0.0
    if completed.returncode in {6, 7} or (completed.returncode == 28 and not connected):
        raise OCRConnectTimeout(
            f"OCR DNS/TCP connection exceeded {connect_timeout or timeout}s limit"
        )
    if completed.returncode == 28:
        raise requests.exceptions.ReadTimeout(
            f"OCR response exceeded {timeout}s wall-clock limit after connection"
            + (
                f"; waited {max(0.0, total_elapsed - connect_elapsed):.3f}s after connection"
                if total_elapsed
                else ""
            )
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
    logging.info(
        "OCR HTTP 响应完成：建连耗时=%.3f秒，连接后等待完整响应=%.3f秒",
        connect_elapsed,
        max(0.0, total_elapsed - connect_elapsed),
    )
    return json.loads(body if separator else completed.stdout)
