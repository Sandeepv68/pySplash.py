"""Synchronous pySplash API tests."""

from unittest.mock import MagicMock, patch

import pytest

from pySplash import PySplashApi, PySplashError

BEARER_TOKEN = "test-bearer-token"


@pytest.fixture
def captured_args():
    """Capture arguments passed to HttpClient.make_request."""
    return {"args": None}


@pytest.fixture
def api(captured_args):
    """Create a PySplashApi instance with a mocked HTTP client."""
    with patch("pySplash.api.HttpClient") as MockClient:
        mock_instance = MagicMock()
        MockClient.return_value = mock_instance

        def capture_make_request(url, method, query_parameters=None, body=None):
            captured_args["args"] = {
                "url": url,
                "method": method,
                "query_parameters": query_parameters or {},
                "body": body,
            }
            return MagicMock(
                status=200,
                statusText="OK",
                data={
                    "url": url,
                    "method": method,
                    "queryParameters": query_parameters or {},
                    "body": body,
                },
            )

        mock_instance.make_request.side_effect = capture_make_request
        client = PySplashApi()
        client.init(bearer_token=BEARER_TOKEN)
        yield client, captured_args


class TestPySplashApi:
    def test_initializes_with_bearer_token_and_sets_headers(self, api):
        client, captured = api
        client.get_current_user_profile()
        captured["args"]
        assert "Authorization" in client._headers
        assert client._headers["Authorization"] == f"Bearer {BEARER_TOKEN}"

    def test_throws_for_missing_init_values(self):
        client = PySplashApi()
        with pytest.raises(PySplashError, match="Redirect URI missing!"):
            client.init(access_key="abc", secret_key="def")

    def test_wraps_request_failures_in_pysplash_error(self, api):
        client, _captured = api
        with patch("pySplash.api.HttpClient") as MockClient:
            mock_instance = MagicMock()
            MockClient.return_value = mock_instance
            mock_instance.make_request.side_effect = Exception("boom")
            with pytest.raises(PySplashError):
                client.get_current_user_profile()

    def test_get_current_user_profile_requests_me_endpoint(self, api):
        client, captured = api
        response = client.get_current_user_profile()
        assert captured["args"]["url"] == "https://api.unsplash.com/me"
        assert captured["args"]["method"] == "GET"
        assert response["url"] == "https://api.unsplash.com/me"

    def test_get_photo_aliases_photo_lookup(self, api):
        client, captured = api
        client.get_photo("g3PyXO4A0yc", 120, 180, "0,0,100,200")
        assert captured["args"]["url"] == "https://api.unsplash.com/photos/g3PyXO4A0yc"
        assert captured["args"]["query_parameters"]["rect"] == "0,0,100,200"

    def test_get_random_photo_includes_all_params(self, api):
        client, captured = api
        client.get_random_photo("123", True, "sandeepv", "nature", 400, 300, "portrait", 2)
        params = captured["args"]["query_parameters"]
        assert params["collections"] == "123"
        assert params["featured"] is True
        assert params["username"] == "sandeepv"
        assert params["query"] == "nature"
        assert params["orientation"] == "portrait"
        assert params["count"] == 2

    def test_create_collection_sends_correct_payload(self, api):
        client, captured = api
        client.create_collection("Test collection", "A test", True)
        params = captured["args"]["query_parameters"]
        assert params["title"] == "Test collection"
        assert params["private"] is True

    def test_update_current_user_profile_sends_put(self, api):
        client, captured = api
        client.update_current_user_profile(
            "mock-user", "Mock", "User", "mock@example.com", "https://example.com", "Earth", "Testing", "mock_insta"
        )
        params = captured["args"]["query_parameters"]
        assert params["username"] == "mock-user"
        assert params["email"] == "mock@example.com"
        assert captured["args"]["method"] == "PUT"

    def test_get_public_profile_uses_width_height(self, api):
        client, captured = api
        client.get_public_profile("sandeepv", 200, 300)
        assert captured["args"]["query_parameters"] == {"w": 200, "h": 300}

    def test_get_user_portfolio_requests_correct_endpoint(self, api):
        client, captured = api
        client.get_user_portfolio("sandeepv")
        assert captured["args"]["url"] == "https://api.unsplash.com/users/sandeepv/portfolio"

    def test_get_user_photos_sends_defaults(self, api):
        client, captured = api
        client.get_user_photos("sandeepv")
        params = captured["args"]["query_parameters"]
        assert params["page"] == 1
        assert params["per_page"] == 10
        assert params["order_by"] == "latest"
        assert params["stats"] is False

    def test_get_user_liked_photos_custom_order(self, api):
        client, captured = api
        client.get_user_liked_photos("sandeepv", 2, 5, "popular")
        params = captured["args"]["query_parameters"]
        assert params["page"] == 2
        assert params["per_page"] == 5
        assert params["order_by"] == "popular"

    def test_get_user_collections_defaults(self, api):
        client, captured = api
        client.get_user_collections("sandeepv")
        assert captured["args"]["query_parameters"] == {"page": 1, "per_page": 10}

    def test_get_user_statistics_defaults(self, api):
        client, captured = api
        client.get_user_statistics("sandeepv")
        params = captured["args"]["query_parameters"]
        assert params["resolution"] == "days"
        assert params["quantity"] == 30

    def test_get_photo_builds_rect_params(self, api):
        client, captured = api
        client.get_photo("g3PyXO4A0yc", 100, 200, "0,0,100,200")
        params = captured["args"]["query_parameters"]
        assert params["w"] == 100
        assert params["h"] == 200
        assert params["rect"] == "0,0,100,200"

    def test_get_photo_statistics_correct_request(self, api):
        client, captured = api
        client.get_photo_statistics("g3PyXO4A0yc", "weeks", 10)
        params = captured["args"]["query_parameters"]
        assert params["resolution"] == "weeks"
        assert params["quantity"] == 10

    def test_get_photo_link_requests_download_endpoint(self, api):
        client, captured = api
        client.get_photo_link("g3PyXO4A0yc")
        assert "/download" in captured["args"]["url"]

    def test_update_photo_sends_location_exif(self, api):
        client, captured = api
        location = {"latitude": 10.1, "longitude": 20.2, "name": "Test"}
        exif = {"make": "Canon", "model": "EOS", "iso_speed_ratings": 100}
        client.update_photo("g3PyXO4A0yc", location, exif)
        params = captured["args"]["query_parameters"]
        assert params["location[latitude]"] == 10.1
        assert params["location[name]"] == "Test"
        assert params["exif[make]"] == "Canon"
        assert params["exif[iso_speed_ratings]"] == 100

    def test_like_and_unlike_photo(self, api):
        client, captured = api
        client.like_photo("g3PyXO4A0yc")
        assert captured["args"]["method"] == "POST"
        assert "/like" in captured["args"]["url"]

        client.unlike_photo("g3PyXO4A0yc")
        assert captured["args"]["method"] == "DELETE"

    def test_search_and_search_collections_and_users(self, api):
        client, captured = api
        client.search("ocean", 2, 15, "123", "landscape")
        params = captured["args"]["query_parameters"]
        assert params["query"] == "ocean"
        assert params["page"] == 2
        assert params["collections"] == "123"

        client.search_collections("travel", 3, 20)
        assert captured["args"]["query_parameters"]["page"] == 3

        client.search_users("john", 4, 5)
        assert captured["args"]["query_parameters"]["per_page"] == 5

    def test_stats_and_collection_endpoints(self, api):
        client, captured = api

        client.get_stats_totals()
        assert "stats/total" in captured["args"]["url"]

        client.get_stats_month()
        assert "stats/month" in captured["args"]["url"]

        client.list_collections()
        assert captured["args"]["query_parameters"] == {"page": 1, "per_page": 10}

        client.list_featured_collections(2, 8)
        params = captured["args"]["query_parameters"]
        assert params["page"] == 2
        assert params["per_page"] == 8

        client.list_curated_collections(3, 9)
        params = captured["args"]["query_parameters"]
        assert params["page"] == 3
        assert params["per_page"] == 9

    def test_collection_detail_endpoints(self, api):
        client, captured = api

        client.get_collection("cid")
        assert captured["args"]["url"] == "https://api.unsplash.com/collections/cid"

        client.get_curated_collection("cid")
        assert "curated/cid" in captured["args"]["url"]

        client.get_collection_photos("cid", 4, 12)
        params = captured["args"]["query_parameters"]
        assert params["page"] == 4
        assert params["per_page"] == 12

        client.get_curated_collection_photos("cid", 5, 13)
        params = captured["args"]["query_parameters"]
        assert params["page"] == 5
        assert params["per_page"] == 13

        client.list_related_collections("cid")
        assert "related" in captured["args"]["url"]

    def test_collection_crud_and_photo_ops(self, api):
        client, captured = api

        client.create_new_collection("My Collection", "desc", True)
        params = captured["args"]["query_parameters"]
        assert params["title"] == "My Collection"
        assert params["private"] is True

        client.update_existing_collection("cid", "Title", "desc2", False)
        params = captured["args"]["query_parameters"]
        assert params["title"] == "Title"
        assert params["private"] is False

        client.delete_collection("cid")
        assert captured["args"]["method"] == "DELETE"

        client.add_photo_to_collection("cid", "pid")
        params = captured["args"]["query_parameters"]
        assert params["photo_id"] == "pid"
        assert captured["args"]["method"] == "POST"

        client.remove_photo_from_collection("cid", "pid")
        assert captured["args"]["method"] == "DELETE"

    def test_generate_bearer_token(self):
        with patch("pySplash.api.HttpClient") as MockClient:
            mock_instance = MagicMock()
            MockClient.return_value = mock_instance

            def capture_make_request(url, method, query_parameters=None, body=None):
                return MagicMock(
                    status=200,
                    statusText="OK",
                    data={"url": url, "method": method, "queryParameters": query_parameters or {}, "body": body},
                )

            mock_instance.make_request.side_effect = capture_make_request

            client = PySplashApi()
            client.init(
                access_key="access-key",
                secret_key="secret-key",
                redirect_uri="https://example.com/callback",
                code="authorization-code",
            )
            client.generate_bearer_token()
            assert mock_instance.make_request.called
            args = mock_instance.make_request.call_args
            assert args[0][0] == "https://unsplash.com/oauth/token"
            assert args[0][1] == "POST"

    def test_empty_username_throws(self, api):
        client, _ = api
        with pytest.raises(PySplashError, match="username is required"):
            client.get_public_profile("")

    def test_unsupported_order_by_throws(self, api):
        client, _ = api
        with pytest.raises(PySplashError, match="order_by has an unsupported value"):
            client.get_user_photos("user", order_by="invalid_order")

    def test_unsupported_order_by_liked_throws(self, api):
        client, _ = api
        with pytest.raises(PySplashError, match="order_by has an unsupported value"):
            client.get_user_liked_photos("user", order_by="bad_order")

    def test_empty_id_throws(self, api):
        client, _ = api
        with pytest.raises(PySplashError, match="id is required"):
            client.get_photo("")

    def test_unsupported_orientation_throws(self, api):
        client, _ = api
        with pytest.raises(PySplashError, match="orientation has an unsupported value"):
            client.get_random_photo(orientation="invalid_orientation")

    def test_missing_query_throws(self, api):
        client, _ = api
        with pytest.raises(PySplashError, match="query is missing"):
            client.search(None)

    def test_context_manager_closes_client(self):
        with PySplashApi() as client:
            client.init(bearer_token=BEARER_TOKEN)
            assert client._client is None
            client._get_client()
            assert client._client is not None
        assert client._client is None

    def test_close_without_init(self):
        client = PySplashApi()
        client.close()
        assert client._client is None

    def test_403_raises_pysplash_error(self, api):
        client, _ = api
        with patch("pySplash.api.HttpClient") as MockClient:
            mock_instance = MagicMock()
            MockClient.return_value = mock_instance
            mock_response = MagicMock()
            mock_response.status = 403
            mock_response.statusText = "Forbidden"
            mock_response.data = {"errors": ["Rate limit exceeded"]}
            mock_instance.make_request.return_value = mock_response
            with pytest.raises(PySplashError, match="HTTP 403"):
                client.get_current_user_profile()

    def test_404_raises_pysplash_error(self, api):
        client, _ = api
        with patch("pySplash.api.HttpClient") as MockClient:
            mock_instance = MagicMock()
            MockClient.return_value = mock_instance
            mock_response = MagicMock()
            mock_response.status = 404
            mock_response.statusText = "Not Found"
            mock_response.data = {"errors": ["Not Found"]}
            mock_instance.make_request.return_value = mock_response
            with pytest.raises(PySplashError, match="HTTP 404"):
                client.get_photo("nonexistent")

    def test_204_returns_delete_message(self, api):
        client, _ = api
        with patch("pySplash.api.HttpClient") as MockClient:
            mock_instance = MagicMock()
            MockClient.return_value = mock_instance
            mock_response = MagicMock()
            mock_response.status = 204
            mock_response.statusText = "No Content"
            mock_response.data = None
            mock_instance.make_request.return_value = mock_response
            result = client.delete_collection("cid")
            assert result["status"] == 204
            assert result["message"] == "Content Deleted"

    def test_shared_base_methods(self):
        from pySplash.base import PySplashBase

        assert PySplashApi._compute_hash("test") == PySplashBase._compute_hash("test")
        assert PySplashApi._build_query_parameters({"a": 1, "b": None, "c": ""}) == {"a": 1}

    def test_client_reuse(self, api):
        client, _ = api
        c1 = client._get_client()
        c2 = client._get_client()
        assert c1 is c2

    def test_error_repr(self):
        err = PySplashError("test", status_code=404, status_text="Not Found")
        assert "404" in repr(err)
        assert "Not Found" in repr(err)
