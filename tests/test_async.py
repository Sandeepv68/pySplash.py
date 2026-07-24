"""Asynchronous pySplash API tests."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pySplash import PySplashApiAsync, PySplashError

BEARER_TOKEN = "test-bearer-token"


@pytest.fixture
def captured_args():
    return {"args": None}


@pytest.fixture
async def api(captured_args):
    with patch("pySplash.api_async.AsyncHttpClient") as MockClient:
        mock_instance = MagicMock()
        MockClient.return_value = mock_instance

        async def capture_make_request(url, method, query_parameters=None, body=None):
            captured_args["args"] = {
                "url": url,
                "method": method,
                "query_parameters": query_parameters or {},
                "body": body,
            }
            mock_resp = MagicMock()
            mock_resp.status = 200
            mock_resp.statusText = "OK"
            mock_resp.data = {
                "url": url,
                "method": method,
                "queryParameters": query_parameters or {},
                "body": body,
            }
            return mock_resp

        mock_instance.make_request = AsyncMock(side_effect=capture_make_request)
        client = PySplashApiAsync()
        client.init(bearer_token=BEARER_TOKEN)
        yield client, captured_args


@pytest.mark.asyncio
class TestPySplashApiAsync:
    async def test_initializes_with_bearer_token(self, api):
        client, _captured = api
        await client.get_current_user_profile()
        assert client._headers["Authorization"] == f"Bearer {BEARER_TOKEN}"

    async def test_throws_for_missing_init_values(self):
        client = PySplashApiAsync()
        with pytest.raises(PySplashError, match="Redirect URI missing!"):
            client.init(access_key="abc", secret_key="def")

    async def test_wraps_request_failures(self, api):
        client, _captured = api
        with patch("pySplash.api_async.AsyncHttpClient") as MockClient:
            mock_instance = MagicMock()
            MockClient.return_value = mock_instance
            mock_instance.make_request = AsyncMock(side_effect=Exception("boom"))
            with pytest.raises(PySplashError):
                await client.get_current_user_profile()

    async def test_get_current_user_profile(self, api):
        client, captured = api
        await client.get_current_user_profile()
        assert captured["args"]["url"] == "https://api.unsplash.com/me"
        assert captured["args"]["method"] == "GET"

    async def test_get_photo(self, api):
        client, captured = api
        await client.get_photo("g3PyXO4A0yc", 120, 180, "0,0,100,200")
        assert captured["args"]["url"] == "https://api.unsplash.com/photos/g3PyXO4A0yc"
        assert captured["args"]["query_parameters"]["rect"] == "0,0,100,200"

    async def test_get_random_photo(self, api):
        client, captured = api
        await client.get_random_photo("123", True, "sandeepv", "nature", 400, 300, "portrait", 2)
        params = captured["args"]["query_parameters"]
        assert params["collections"] == "123"
        assert params["featured"] is True
        assert params["orientation"] == "portrait"

    async def test_create_collection(self, api):
        client, captured = api
        await client.create_collection("Test", "desc", True)
        params = captured["args"]["query_parameters"]
        assert params["title"] == "Test"
        assert params["private"] is True

    async def test_update_current_user_profile(self, api):
        client, captured = api
        await client.update_current_user_profile(
            "mock-user", "Mock", "User", "mock@example.com", "https://example.com", "Earth", "Testing", "mock_insta"
        )
        params = captured["args"]["query_parameters"]
        assert params["username"] == "mock-user"
        assert captured["args"]["method"] == "PUT"

    async def test_get_public_profile(self, api):
        client, captured = api
        await client.get_public_profile("sandeepv", 200, 300)
        assert captured["args"]["query_parameters"] == {"w": 200, "h": 300}

    async def test_get_user_portfolio(self, api):
        client, captured = api
        await client.get_user_portfolio("sandeepv")
        assert "portfolio" in captured["args"]["url"]

    async def test_get_user_photos_defaults(self, api):
        client, captured = api
        await client.get_user_photos("sandeepv")
        params = captured["args"]["query_parameters"]
        assert params["page"] == 1
        assert params["order_by"] == "latest"

    async def test_search(self, api):
        client, captured = api
        await client.search("ocean", 2, 15, "123", "landscape")
        params = captured["args"]["query_parameters"]
        assert params["query"] == "ocean"
        assert params["collections"] == "123"

    async def test_stats_endpoints(self, api):
        client, captured = api
        await client.get_stats_totals()
        assert "stats/total" in captured["args"]["url"]

        await client.get_stats_month()
        assert "stats/month" in captured["args"]["url"]

    async def test_collection_crud(self, api):
        client, captured = api
        await client.create_new_collection("My Collection", "desc", True)
        assert captured["args"]["query_parameters"]["title"] == "My Collection"

        await client.update_existing_collection("cid", "Title", "desc2", False)
        assert captured["args"]["query_parameters"]["title"] == "Title"

        await client.delete_collection("cid")
        assert captured["args"]["method"] == "DELETE"

    async def test_add_remove_photo_from_collection(self, api):
        client, captured = api
        await client.add_photo_to_collection("cid", "pid")
        assert captured["args"]["query_parameters"]["photo_id"] == "pid"
        assert captured["args"]["method"] == "POST"

        await client.remove_photo_from_collection("cid", "pid")
        assert captured["args"]["method"] == "DELETE"

    async def test_empty_username_throws(self, api):
        client, _ = api
        with pytest.raises(PySplashError, match="username is required"):
            await client.get_public_profile("")

    async def test_unsupported_orientation_throws(self, api):
        client, _ = api
        with pytest.raises(PySplashError, match="orientation has an unsupported value"):
            await client.get_random_photo(orientation="invalid")

    async def test_missing_query_throws(self, api):
        client, _ = api
        with pytest.raises(PySplashError, match="query is missing"):
            await client.search(None)

    async def test_async_context_manager_closes_client(self):
        async with PySplashApiAsync() as client:
            client.init(bearer_token=BEARER_TOKEN)
            assert client._client is None
            client._get_client()
            assert client._client is not None
        assert client._client is None

    async def test_403_raises_pysplash_error(self, api):
        client, _ = api
        with patch("pySplash.api_async.AsyncHttpClient") as MockClient:
            mock_instance = MagicMock()
            MockClient.return_value = mock_instance
            mock_response = MagicMock()
            mock_response.status = 403
            mock_response.statusText = "Forbidden"
            mock_response.data = {"errors": ["Rate limit exceeded"]}
            mock_instance.make_request = AsyncMock(return_value=mock_response)
            with pytest.raises(PySplashError, match="HTTP 403"):
                await client.get_current_user_profile()

    async def test_204_returns_delete_message(self, api):
        client, _ = api
        with patch("pySplash.api_async.AsyncHttpClient") as MockClient:
            mock_instance = MagicMock()
            MockClient.return_value = mock_instance
            mock_response = MagicMock()
            mock_response.status = 204
            mock_response.statusText = "No Content"
            mock_response.data = None
            mock_instance.make_request = AsyncMock(return_value=mock_response)
            result = await client.delete_collection("cid")
            assert result["status"] == 204
            assert result["message"] == "Content Deleted"

    async def test_client_reuse(self, api):
        client, _ = api
        c1 = client._get_client()
        c2 = client._get_client()
        assert c1 is c2
