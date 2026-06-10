from __future__ import annotations

import time
from typing import Mapping

import requests as std_requests

try:
    from curl_cffi import requests as curl_requests
except Exception:  # pragma: no cover - optional dependency fallback
    curl_requests = None


DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/json;q=0.8,*/*;q=0.7",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,ja;q=0.7",
}


def fetch_text(
    url: str,
    *,
    timeout: int = 30,
    retries: int = 2,
    sleep_seconds: float = 0.25,
    headers: Mapping[str, str] | None = None,
) -> str:
    """Fetch text with Chrome TLS impersonation first, then normal requests.

    Several public store fronts close vanilla OpenSSL handshakes in this
    environment. curl_cffi keeps the crawler lightweight while covering those
    sites without needing Selenium.
    """

    request_headers = dict(DEFAULT_HEADERS)
    if headers:
        request_headers.update(headers)

    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            if curl_requests is not None:
                response = curl_requests.get(
                    url,
                    headers=request_headers,
                    timeout=timeout,
                    impersonate="chrome",
                )
                response.raise_for_status()
                return response.text
        except Exception as exc:  # pragma: no cover - network dependent
            last_error = exc

        try:
            response = std_requests.get(url, headers=request_headers, timeout=timeout)
            response.raise_for_status()
            response.encoding = response.encoding or "utf-8"
            return response.text
        except Exception as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(sleep_seconds * (attempt + 1))

    raise RuntimeError(f"failed to fetch {url}: {last_error}")

