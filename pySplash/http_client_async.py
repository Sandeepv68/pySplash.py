"""Asynchronous HTTP client with retry support using httpx."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from .config import DEFAULT_HEADERS, DEFAULT_RETRIES, DEFAULT_RETRY_DELAY, DEFAULT_TIMEOUT
from .errors import PySplashError

logger = logging.getLogger("pySplash.py")


class AsyncHttpResponse:
    """Wrapper around httpx.Response to provide a uniform interface."""

    def __init__(self, response: httpx.Response) -> None:
        self.status: int = response.status_code
        self.statusText: str = response.reason_phrase or ""
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


class AsyncHttpClient:
    """Async HTTP client with connection pooling, retry logic, and error handling."""

    def __init__(
        self,
        headers: dict[str, str] | None = None,
        timeout: int = DEFAULT_TIMEOUT,
        retries: int = DEFAULT_RETRIES,
        retry_delay: float = DEFAULT_RETRY_DELAY,
    ) -> None:
        self._headers = headers or DEFAULT_HEADERS
        self.timeout = timeout
        self.retries = retries
        self.retry_delay = retry_delay
        self._client: httpx.AsyncClient | None = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                headers=self._headers,
                timeout=self.timeout,
                max_redirects=5,
            )
        return self._client

    async def close(self) -> None:
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> AsyncHttpClient:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def make_request(
        self,
        url: str,
        method: str,
        query_parameters: dict[str, Any] | None = None,
        body: Any | None = None,
    ) -> AsyncHttpResponse:
        if not url:
            raise ValueError("URL required")

        last_error: Exception | None = None

        for attempt in range(self.retries + 1):
            try:
                logger.debug("%s %s (attempt %d/%d)", method, url, attempt + 1, self.retries + 1)
                client = self._get_client()
                response = await client.request(
                    method=method or "get",
                    url=url,
                    params=query_parameters or {},
                    json=body,
                )
                result = AsyncHttpResponse(response)
                if result.status >= 400:
                    result.raise_for_status()
                return result
            except PySplashError:
                raise
            except Exception as exc:
                last_error = exc
                logger.warning("Request failed (attempt %d/%d): %s", attempt + 1, self.retries + 1, exc)
                if attempt < self.retries and self.retry_delay > 0:
                    await asyncio.sleep(self.retry_delay)

        raise last_error  # type: ignore[misc]
