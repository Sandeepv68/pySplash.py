"""Tests for the HTTP client implementations."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pySplash.errors import PySplashError
from pySplash.http_client import HttpClient, HttpResponse
from pySplash.http_client_async import AsyncHttpClient, AsyncHttpResponse


class TestHttpResponse:
    def test_parses_json(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.reason = "OK"
        mock_resp.content = b'{"key": "value"}'
        mock_resp.json.return_value = {"key": "value"}
        result = HttpResponse(mock_resp)
        assert result.status == 200
        assert result.data == {"key": "value"}

    def test_empty_content(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 204
        mock_resp.reason = "No Content"
        mock_resp.content = b""
        result = HttpResponse(mock_resp)
        assert result.data is None

    def test_invalid_json_falls_back_to_text(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.reason = "OK"
        mock_resp.content = b"not json"
        mock_resp.json.side_effect = ValueError("No JSON")
        mock_resp.text = "not json"
        result = HttpResponse(mock_resp)
        assert result.data == "not json"

    def test_raise_for_status_ok(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.reason = "OK"
        mock_resp.content = b"{}"
        mock_resp.json.return_value = {}
        result = HttpResponse(mock_resp)
        result.raise_for_status()

    def test_raise_for_status_error(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.reason = "Server Error"
        mock_resp.content = b'{"error": "fail"}'
        mock_resp.json.return_value = {"error": "fail"}
        result = HttpResponse(mock_resp)
        with pytest.raises(PySplashError, match="HTTP 500"):
            result.raise_for_status()


class TestHttpClient:
    def test_close(self):
        client = HttpClient()
        with patch.object(client._session, "close") as mock_close:
            client.close()
            mock_close.assert_called_once()

    def test_context_manager(self):
        with HttpClient() as client:
            assert isinstance(client, HttpClient)

    def test_empty_url_raises(self):
        client = HttpClient()
        with pytest.raises(ValueError, match="URL required"):
            client.make_request("", "GET")

    def test_successful_request(self):
        client = HttpClient(retries=0)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.reason = "OK"
        mock_response.content = b'{"ok": true}'
        mock_response.json.return_value = {"ok": True}
        with patch.object(client._session, "request", return_value=mock_response) as mock_req:
            result = client.make_request("https://example.com/api", "GET", {"q": "1"})
            mock_req.assert_called_once_with(
                method="GET",
                url="https://example.com/api",
                params={"q": "1"},
                json=None,
                timeout=10,
                allow_redirects=True,
            )
            assert result.status == 200

    def test_retries_on_failure(self):
        client = HttpClient(retries=2, retry_delay=0)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.reason = "OK"
        mock_response.content = b'{"ok": true}'
        mock_response.json.return_value = {"ok": True}
        with patch.object(client._session, "request", side_effect=[ConnectionError("fail"), mock_response]) as mock_req:
            result = client.make_request("https://example.com/api", "POST")
            assert mock_req.call_count == 2
            assert result.status == 200

    def test_raises_after_all_retries_exhausted(self):
        client = HttpClient(retries=1, retry_delay=0)
        with patch.object(client._session, "request", side_effect=ConnectionError("fail")):
            with pytest.raises(ConnectionError):
                client.make_request("https://example.com/api", "GET")

    def test_raises_on_4xx_from_server(self):
        client = HttpClient(retries=0)
        mock_response = MagicMock()
        mock_response.status_code = 503
        mock_response.reason = "Service Unavailable"
        mock_response.content = b"{}"
        mock_response.json.return_value = {}
        with patch.object(client._session, "request", return_value=mock_response):
            with pytest.raises(PySplashError, match="HTTP 503"):
                client.make_request("https://example.com/api", "GET")

    def test_passes_body_and_method(self):
        client = HttpClient(retries=0)
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.reason = "Created"
        mock_response.content = b'{"id": 1}'
        mock_response.json.return_value = {"id": 1}
        with patch.object(client._session, "request", return_value=mock_response) as mock_req:
            client.make_request("https://example.com/api", "POST", body={"name": "test"})
            call_kwargs = mock_req.call_args[1]
            assert call_kwargs["json"] == {"name": "test"}
            assert call_kwargs["method"] == "POST"


class TestAsyncHttpResponse:
    def test_parses_json(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.reason_phrase = "OK"
        mock_resp.content = b'{"key": "value"}'
        mock_resp.json.return_value = {"key": "value"}
        result = AsyncHttpResponse(mock_resp)
        assert result.status == 200
        assert result.data == {"key": "value"}

    def test_empty_content(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 204
        mock_resp.reason_phrase = "No Content"
        mock_resp.content = b""
        result = AsyncHttpResponse(mock_resp)
        assert result.data is None

    def test_raise_for_status_error(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 422
        mock_resp.reason_phrase = "Unprocessable Entity"
        mock_resp.content = b"{}"
        mock_resp.json.return_value = {}
        result = AsyncHttpResponse(mock_resp)
        with pytest.raises(PySplashError, match="HTTP 422"):
            result.raise_for_status()


class TestAsyncHttpClient:
    def test_empty_url_raises(self):
        client = AsyncHttpClient()
        with pytest.raises(ValueError, match="URL required"):
            import asyncio

            asyncio.run(client.make_request("", "GET"))

    async def test_context_manager(self):
        async with AsyncHttpClient() as client:
            assert isinstance(client, AsyncHttpClient)

    async def test_raises_on_5xx(self):
        client = AsyncHttpClient(retries=0)
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.reason_phrase = "Internal Server Error"
        mock_response.content = b"{}"
        mock_response.json.return_value = {}
        with patch("pySplash.http_client_async.httpx.AsyncClient") as MockClient:
            mock_client_instance = MagicMock()
            MockClient.return_value = mock_client_instance
            mock_client_instance.request = AsyncMock(return_value=mock_response)
            with pytest.raises(PySplashError, match="HTTP 500"):
                await client.make_request("https://example.com/api", "GET")
