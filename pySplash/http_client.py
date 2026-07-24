"""Synchronous HTTP client with retry support using requests."""

from __future__ import annotations

import logging
import time
from typing import Any

import requests

from .config import DEFAULT_HEADERS, DEFAULT_RETRIES, DEFAULT_RETRY_DELAY, DEFAULT_TIMEOUT
from .errors import PySplashError

logger = logging.getLogger("pySplash.py")


class HttpResponse:
    """Wrapper around requests.Response to provide a uniform interface."""

    def __init__(self, response: requests.Response) -> None:
        self.status: int = response.status_code
        self.statusText: str = response.reason or ""
        try:
            self.data: Any = response.json() if response.content else None
        except ValueError:
            self.data = response.text or None

    def raise_for_status(self) -> None:
        if self.status >= 400:
            raise PySplashError(
                f"HTTP {self.status} {self.statusText}",
                status_code=self.status,
                status_text=self.statusText,
            )


class HttpClient:
    """Sync HTTP client with session reuse, retry logic, and error handling."""

    def __init__(
        self,
        headers: dict[str, str] | None = None,
        timeout: int = DEFAULT_TIMEOUT,
        retries: int = DEFAULT_RETRIES,
        retry_delay: float = DEFAULT_RETRY_DELAY,
    ) -> None:
        self._session = requests.Session()
        self._session.headers.update(headers or DEFAULT_HEADERS)
        self.timeout = timeout
        self.retries = retries
        self.retry_delay = retry_delay

    def close(self) -> None:
        self._session.close()

    def __enter__(self) -> HttpClient:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def make_request(
        self,
        url: str,
        method: str,
        query_parameters: dict[str, Any] | None = None,
        body: Any | None = None,
    ) -> HttpResponse:
        if not url:
            raise ValueError("URL required")

        last_error: Exception | None = None

        for attempt in range(self.retries + 1):
            try:
                logger.debug("%s %s (attempt %d/%d)", method, url, attempt + 1, self.retries + 1)
                response = self._session.request(
                    method=method or "get",
                    url=url,
                    params=query_parameters or {},
                    json=body,
                    timeout=self.timeout,
                    allow_redirects=True,
                )
                result = HttpResponse(response)
                if result.status >= 400:
                    result.raise_for_status()
                return result
            except PySplashError:
                raise
            except Exception as exc:
                last_error = exc
                logger.warning("Request failed (attempt %d/%d): %s", attempt + 1, self.retries + 1, exc)
                if attempt < self.retries and self.retry_delay > 0:
                    time.sleep(self.retry_delay)

        raise last_error  # type: ignore[misc]
