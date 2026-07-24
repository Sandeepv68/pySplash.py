"""Synchronous pySplash.py API client."""

from __future__ import annotations

import logging
from typing import Any

from .base import PySplashBase
from .config import AVAILABLE_ORDERS, AVAILABLE_ORIENTATIONS, URL_CONFIG
from .errors import PySplashError
from .http_client import HttpClient
from .models import (
    BearerTokenResponse,
    Collection,
    DeleteResponse,
    Photo,
    PhotoLinks,
    PhotoStatistics,
    SearchResult,
    User,
    UserPortfolio,
    UserStatistics,
)

logger = logging.getLogger("pySplash.py")

_BASE = URL_CONFIG["API_LOCATION"]
_TOKEN_URL = URL_CONFIG["BEARER_TOKEN_URL"]


class PySplashApi(PySplashBase):
    """Sync wrapper for the Unsplash API.

    Supports context manager protocol for clean resource management::

        with PySplashApi() as api:
            api.init(bearer_token='...')
            result = api.get_photo('id')

    Also supports explicit client reuse::

        api = PySplashApi()
        try:
            api.init(bearer_token='...')
            result = api.get_photo('id')
        finally:
            api.close()
    """

    def __init__(self) -> None:
        self._access_key: str = ""
        self._secret_key: str = ""
        self._redirect_uri: str = ""
        self._code: str = ""
        self._grant_type: str = "authorization_code"
        self._bearer_token: str = ""
        self._timeout: int = 10
        self._retries: int = 2
        self._retry_delay: float = 0.1
        self._headers: dict[str, str] = {}
        self._client: HttpClient | None = None

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None

    def __enter__(self) -> PySplashApi:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def _get_client(self) -> HttpClient:
        if self._client is None:
            self._client = HttpClient(
                headers=self._headers,
                timeout=self._timeout,
                retries=self._retries,
                retry_delay=self._retry_delay,
            )
        return self._client

    def _fetch_url(
        self,
        url: str,
        method: str,
        query_parameters: dict[str, Any] | None = None,
        body: Any | None = None,
    ) -> Any:
        client = self._get_client()
        try:
            res = client.make_request(url, method, self._build_query_parameters(query_parameters or {}), body)
        except Exception as exc:
            raise self._create_pysplash_error(exc) from exc

        return self._handle_response_status(res.data, res.status, res.statusText)

    def init(
        self,
        access_key: str | None = None,
        secret_key: str | None = None,
        redirect_uri: str | None = None,
        code: str | None = None,
        bearer_token: str | None = None,
        timeout: int = 10,
        retries: int = 2,
        retry_delay: float = 0.1,
    ) -> None:
        """Initialize the client with API credentials or a bearer token."""
        if timeout > 0:
            self._timeout = timeout
        if retries >= 0:
            self._retries = retries
        if retry_delay >= 0:
            self._retry_delay = retry_delay

        self._bearer_token = bearer_token or ""
        self._headers = self._default_headers(bearer_token=bearer_token, access_key=access_key)

        if bearer_token:
            return

        if not access_key:
            raise PySplashError("Access Key missing!")
        if not secret_key:
            raise PySplashError("Secret Key missing!")
        if not redirect_uri:
            raise PySplashError("Redirect URI missing!")
        if not code:
            raise PySplashError("Authorization Code missing!")

        self._access_key = access_key
        self._secret_key = secret_key
        self._redirect_uri = redirect_uri
        self._code = code

    # ── Auth ──────────────────────────────────────────────────────────

    def generate_bearer_token(self) -> BearerTokenResponse:
        """Exchange the authorization code for a bearer token."""
        self._validate_required(self._access_key, "access_key")
        self._validate_required(self._secret_key, "secret_key")
        self._validate_required(self._redirect_uri, "redirect_uri")
        self._validate_required(self._code, "code")

        return self._fetch_url(
            _TOKEN_URL,
            "POST",
            {
                "client_id": self._access_key,
                "client_secret": self._secret_key,
                "redirect_uri": self._redirect_uri,
                "code": self._code,
                "grant_type": self._grant_type,
            },
        )

    # ── Current User ──────────────────────────────────────────────────

    def get_current_user_profile(self) -> User:
        """Get the current user's profile."""
        return self._fetch_url(_BASE + URL_CONFIG["CURRENT_USER_PROFILE"], "GET")

    def update_current_user_profile(
        self,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        email: str | None = None,
        url: str | None = None,
        location: str | None = None,
        bio: str | None = None,
        instagram_username: str | None = None,
    ) -> User:
        """Update the current user's profile."""
        return self._fetch_url(
            _BASE + URL_CONFIG["UPDATE_CURRENT_USER_PROFILE"],
            "PUT",
            {
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "url": url,
                "location": location,
                "bio": bio,
                "instagram_username": instagram_username,
            },
        )

    # ── Users ─────────────────────────────────────────────────────────

    def get_public_profile(
        self,
        username: str,
        width: int | None = None,
        height: int | None = None,
    ) -> User:
        """Get a user's public profile."""
        self._validate_required(username, "username")
        self._validate_int(width, "width", minimum=1)
        self._validate_int(height, "height", minimum=1)
        return self._fetch_url(
            _BASE + URL_CONFIG["USERS_PUBLIC_PROFILE"] + username,
            "GET",
            {"w": width, "h": height},
        )

    def get_user_portfolio(self, username: str) -> UserPortfolio:
        """Get a user's portfolio link."""
        self._validate_required(username, "username")
        return self._fetch_url(
            self._build_url(_BASE, URL_CONFIG["USERS_PORTFOLIO"], username=username),
            "GET",
        )

    def get_user_photos(
        self,
        username: str,
        page: int | None = None,
        per_page: int | None = None,
        stats: bool | None = None,
        resolution: str | None = None,
        quantity: int | None = None,
        order_by: str | None = None,
    ) -> list[Photo]:
        """Get a user's photos."""
        self._validate_required(username, "username")
        self._validate_supported_value(order_by, AVAILABLE_ORDERS, "order_by")
        self._validate_bool(stats, "stats")
        self._validate_int(page, "page", minimum=1)
        self._validate_int(per_page, "per_page", minimum=1, maximum=30)
        self._validate_int(quantity, "quantity", minimum=1, maximum=30)
        return self._fetch_url(
            self._build_url(_BASE, URL_CONFIG["USERS_PHOTOS"], username=username),
            "GET",
            {
                "page": page if page is not None else 1,
                "per_page": per_page if per_page is not None else 10,
                "order_by": order_by if order_by is not None else "latest",
                "stats": stats if stats is not None else False,
                "resolution": resolution if resolution is not None else "days",
                "quantity": quantity if quantity is not None else 30,
            },
        )

    def get_user_liked_photos(
        self,
        username: str,
        page: int | None = None,
        per_page: int | None = None,
        order_by: str | None = None,
    ) -> list[Photo]:
        """Get a user's liked photos."""
        self._validate_required(username, "username")
        self._validate_supported_value(order_by, AVAILABLE_ORDERS, "order_by")
        self._validate_int(page, "page", minimum=1)
        self._validate_int(per_page, "per_page", minimum=1, maximum=30)
        return self._fetch_url(
            self._build_url(_BASE, URL_CONFIG["USERS_LIKED_PHOTOS"], username=username),
            "GET",
            {
                "page": page if page is not None else 1,
                "per_page": per_page if per_page is not None else 10,
                "order_by": order_by if order_by is not None else "latest",
            },
        )

    def get_user_collections(
        self,
        username: str,
        page: int | None = None,
        per_page: int | None = None,
    ) -> list[Collection]:
        """Get a user's collections."""
        self._validate_required(username, "username")
        self._validate_int(page, "page", minimum=1)
        self._validate_int(per_page, "per_page", minimum=1, maximum=30)
        return self._fetch_url(
            self._build_url(_BASE, URL_CONFIG["USERS_COLLECTIONS"], username=username),
            "GET",
            {
                "page": page if page is not None else 1,
                "per_page": per_page if per_page is not None else 10,
            },
        )

    def get_user_statistics(
        self,
        username: str,
        resolution: str | None = None,
        quantity: int | None = None,
    ) -> UserStatistics:
        """Get a user's statistics."""
        self._validate_required(username, "username")
        self._validate_int(quantity, "quantity", minimum=1, maximum=30)
        return self._fetch_url(
            self._build_url(_BASE, URL_CONFIG["USERS_STATISTICS"], username=username),
            "GET",
            {
                "resolution": resolution if resolution is not None else "days",
                "quantity": quantity if quantity is not None else 30,
            },
        )

    # ── Photos ────────────────────────────────────────────────────────

    def list_photos(
        self,
        page: int | None = None,
        per_page: int | None = None,
        order_by: str | None = None,
    ) -> list[Photo]:
        """List photos."""
        self._validate_supported_value(order_by, AVAILABLE_ORDERS, "order_by")
        self._validate_int(page, "page", minimum=1)
        self._validate_int(per_page, "per_page", minimum=1, maximum=30)
        return self._fetch_url(
            _BASE + URL_CONFIG["LIST_PHOTOS"],
            "GET",
            {
                "page": page if page is not None else 1,
                "per_page": per_page if per_page is not None else 10,
                "order_by": order_by if order_by is not None else "latest",
            },
        )

    def list_curated_photos(
        self,
        page: int | None = None,
        per_page: int | None = None,
        order_by: str | None = None,
    ) -> list[Photo]:
        """List curated photos."""
        self._validate_supported_value(order_by, AVAILABLE_ORDERS, "order_by")
        self._validate_int(page, "page", minimum=1)
        self._validate_int(per_page, "per_page", minimum=1, maximum=30)
        return self._fetch_url(
            _BASE + URL_CONFIG["LIST_CURATED_PHOTOS"],
            "GET",
            {
                "page": page if page is not None else 1,
                "per_page": per_page if per_page is not None else 10,
                "order_by": order_by if order_by is not None else "latest",
            },
        )

    def get_photo(
        self,
        id: str,
        width: int | None = None,
        height: int | None = None,
        rect: str | None = None,
    ) -> Photo:
        """Get a photo by ID."""
        self._validate_required(id, "id")
        self._validate_int(width, "width", minimum=1)
        self._validate_int(height, "height", minimum=1)
        return self._fetch_url(
            self._build_url(_BASE, URL_CONFIG["GET_A_PHOTO"], id=id),
            "GET",
            {"w": width, "h": height, "rect": rect},
        )

    def get_a_photo(
        self,
        id: str,
        width: int | None = None,
        height: int | None = None,
        rect: str | None = None,
    ) -> Photo:
        """Get a photo by ID (alias for get_photo)."""
        return self.get_photo(id, width, height, rect)

    def get_random_photo(
        self,
        collections: str | int | None = None,
        featured: bool | None = None,
        username: str | None = None,
        query: str | None = None,
        width: int | None = None,
        height: int | None = None,
        orientation: str | None = None,
        count: int | None = None,
    ) -> Photo | list[Photo]:
        """Get a random photo.

        Returns a single Photo unless count is specified, in which case
        a list of Photos is returned.
        """
        self._validate_supported_value(orientation, AVAILABLE_ORIENTATIONS, "orientation")
        self._validate_bool(featured, "featured")
        self._validate_int(width, "width", minimum=1)
        self._validate_int(height, "height", minimum=1)
        self._validate_int(count, "count", minimum=1, maximum=30)
        return self._fetch_url(
            _BASE + URL_CONFIG["GET_A_RANDOM_PHOTO"],
            "GET",
            {
                "collections": str(collections) if collections is not None else None,
                "featured": featured if featured is not None else False,
                "username": username,
                "query": query,
                "width": width,
                "height": height,
                "orientation": orientation if orientation is not None else "landscape",
                "count": count if count is not None else 1,
            },
        )

    def get_a_random_photo(
        self,
        collections: str | int | None = None,
        featured: bool | None = None,
        username: str | None = None,
        query: str | None = None,
        width: int | None = None,
        height: int | None = None,
        orientation: str | None = None,
        count: int | None = None,
    ) -> Photo | list[Photo]:
        """Get a random photo (alias for get_random_photo)."""
        return self.get_random_photo(collections, featured, username, query, width, height, orientation, count)

    def get_photo_statistics(
        self,
        id: str,
        resolution: str | None = None,
        quantity: int | None = None,
    ) -> PhotoStatistics:
        """Get a photo's statistics."""
        self._validate_required(id, "id")
        self._validate_int(quantity, "quantity", minimum=1, maximum=30)
        return self._fetch_url(
            self._build_url(_BASE, URL_CONFIG["GET_A_PHOTO_STATISTICS"], id=id),
            "GET",
            {
                "resolution": resolution if resolution is not None else "days",
                "quantity": quantity if quantity is not None else 30,
            },
        )

    def get_photo_link(self, id: str) -> PhotoLinks:
        """Get a photo's download link."""
        self._validate_required(id, "id")
        return self._fetch_url(
            self._build_url(_BASE, URL_CONFIG["GET_A_PHOTO_DOWNLOAD_LINK"], id=id),
            "GET",
        )

    def update_photo(
        self,
        id: str,
        location: dict[str, Any] | None = None,
        exif: dict[str, Any] | None = None,
    ) -> Photo:
        """Update a photo's location and EXIF data."""
        self._validate_required(id, "id")
        params = {**self._extract_location_params(location), **self._extract_exif_params(exif)}
        return self._fetch_url(
            self._build_url(_BASE, URL_CONFIG["UPDATE_A_PHOTO"], id=id),
            "PUT",
            params,
        )

    def like_photo(self, id: str) -> Photo:
        """Like a photo."""
        self._validate_required(id, "id")
        return self._fetch_url(
            self._build_url(_BASE, URL_CONFIG["LIKE_A_PHOTO"], id=id),
            "POST",
        )

    def unlike_photo(self, id: str) -> Photo:
        """Unlike a photo."""
        self._validate_required(id, "id")
        return self._fetch_url(
            self._build_url(_BASE, URL_CONFIG["UNLIKE_A_PHOTO"], id=id),
            "DELETE",
        )

    # ── Search ────────────────────────────────────────────────────────

    def search(
        self,
        query: str,
        page: int | None = None,
        per_page: int | None = None,
        collections: str | int | None = None,
        orientation: str | None = None,
    ) -> SearchResult:
        """Search photos."""
        self._validate_required(query, "query")
        self._validate_supported_value(orientation, AVAILABLE_ORIENTATIONS, "orientation")
        self._validate_int(page, "page", minimum=1)
        self._validate_int(per_page, "per_page", minimum=1, maximum=30)
        return self._fetch_url(
            _BASE + URL_CONFIG["SEARCH_PHOTOS"],
            "GET",
            {
                "query": query,
                "page": page if page is not None else 1,
                "per_page": per_page if per_page is not None else 10,
                "collections": str(collections) if collections is not None else None,
                "orientation": orientation,
            },
        )

    def search_collections(
        self,
        query: str,
        page: int | None = None,
        per_page: int | None = None,
    ) -> SearchResult:
        """Search collections."""
        self._validate_required(query, "query")
        self._validate_int(page, "page", minimum=1)
        self._validate_int(per_page, "per_page", minimum=1, maximum=30)
        return self._fetch_url(
            _BASE + URL_CONFIG["SEARCH_COLLECTIONS"],
            "GET",
            {
                "query": query,
                "page": page if page is not None else 1,
                "per_page": per_page if per_page is not None else 10,
            },
        )

    def search_users(
        self,
        query: str,
        page: int | None = None,
        per_page: int | None = None,
    ) -> SearchResult:
        """Search users."""
        self._validate_required(query, "query")
        self._validate_int(page, "page", minimum=1)
        self._validate_int(per_page, "per_page", minimum=1, maximum=30)
        return self._fetch_url(
            _BASE + URL_CONFIG["SEARCH_USERS"],
            "GET",
            {
                "query": query,
                "page": page if page is not None else 1,
                "per_page": per_page if per_page is not None else 10,
            },
        )

    # ── Stats ─────────────────────────────────────────────────────────

    def get_stats_totals(self) -> dict[str, Any]:
        """Get Unsplash platform statistics totals."""
        return self._fetch_url(_BASE + URL_CONFIG["STATS_TOTALS"], "GET")

    def get_stats_month(self) -> dict[str, Any]:
        """Get Unsplash platform monthly statistics."""
        return self._fetch_url(_BASE + URL_CONFIG["STATS_MONTH"], "GET")

    # ── Collections ───────────────────────────────────────────────────

    def list_collections(
        self,
        page: int | None = None,
        per_page: int | None = None,
    ) -> list[Collection]:
        """List collections."""
        self._validate_int(page, "page", minimum=1)
        self._validate_int(per_page, "per_page", minimum=1, maximum=30)
        return self._fetch_url(
            _BASE + URL_CONFIG["LIST_COLLECTIONS"],
            "GET",
            {
                "page": page if page is not None else 1,
                "per_page": per_page if per_page is not None else 10,
            },
        )

    def list_featured_collections(
        self,
        page: int | None = None,
        per_page: int | None = None,
    ) -> list[Collection]:
        """List featured collections."""
        self._validate_int(page, "page", minimum=1)
        self._validate_int(per_page, "per_page", minimum=1, maximum=30)
        return self._fetch_url(
            _BASE + URL_CONFIG["LIST_FEATURED_COLLECTIONS"],
            "GET",
            {
                "page": page if page is not None else 1,
                "per_page": per_page if per_page is not None else 10,
            },
        )

    def list_curated_collections(
        self,
        page: int | None = None,
        per_page: int | None = None,
    ) -> list[Collection]:
        """List curated collections."""
        self._validate_int(page, "page", minimum=1)
        self._validate_int(per_page, "per_page", minimum=1, maximum=30)
        return self._fetch_url(
            _BASE + URL_CONFIG["LIST_CURATED_COLLECTIONS"],
            "GET",
            {
                "page": page if page is not None else 1,
                "per_page": per_page if per_page is not None else 10,
            },
        )

    def get_collection(self, id: str) -> Collection:
        """Get a collection by ID."""
        self._validate_required(id, "id")
        return self._fetch_url(
            self._build_url(_BASE, URL_CONFIG["GET_COLLECTION"], id=id),
            "GET",
        )

    def get_curated_collection(self, id: str) -> Collection:
        """Get a curated collection by ID."""
        self._validate_required(id, "id")
        return self._fetch_url(
            self._build_url(_BASE, URL_CONFIG["GET_CURATED_COLLECTION"], id=id),
            "GET",
        )

    def get_collection_photos(
        self,
        id: str,
        page: int | None = None,
        per_page: int | None = None,
    ) -> list[Photo]:
        """Get a collection's photos."""
        self._validate_required(id, "id")
        self._validate_int(page, "page", minimum=1)
        self._validate_int(per_page, "per_page", minimum=1, maximum=30)
        return self._fetch_url(
            self._build_url(_BASE, URL_CONFIG["GET_COLLECTION_PHOTOS"], id=id),
            "GET",
            {
                "page": page if page is not None else 1,
                "per_page": per_page if per_page is not None else 10,
            },
        )

    def get_curated_collection_photos(
        self,
        id: str,
        page: int | None = None,
        per_page: int | None = None,
    ) -> list[Photo]:
        """Get a curated collection's photos."""
        self._validate_required(id, "id")
        self._validate_int(page, "page", minimum=1)
        self._validate_int(per_page, "per_page", minimum=1, maximum=30)
        return self._fetch_url(
            self._build_url(_BASE, URL_CONFIG["GET_CURATED_COLLECTION_PHOTOS"], id=id),
            "GET",
            {
                "page": page if page is not None else 1,
                "per_page": per_page if per_page is not None else 10,
            },
        )

    def list_related_collections(self, id: str) -> list[Collection]:
        """List a collection's related collections."""
        self._validate_required(id, "id")
        return self._fetch_url(
            self._build_url(_BASE, URL_CONFIG["LIST_RELATED_COLLECTION"], id=id),
            "GET",
        )

    def create_collection(
        self,
        title: str,
        description: str | None = None,
        private_collection: bool = False,
    ) -> Collection:
        """Create a new collection."""
        self._validate_required(title, "title")
        return self._fetch_url(
            _BASE + URL_CONFIG["CREATE_NEW_COLLECTION"],
            "POST",
            {
                "title": title,
                "description": description,
                "private": private_collection,
            },
        )

    def create_new_collection(
        self,
        title: str,
        description: str | None = None,
        private_collection: bool = False,
    ) -> Collection:
        """Create a new collection (alias for create_collection)."""
        return self.create_collection(title, description, private_collection)

    def update_collection(
        self,
        id: str,
        title: str,
        description: str | None = None,
        private_collection: bool = False,
    ) -> Collection:
        """Update an existing collection."""
        self._validate_required(id, "id")
        self._validate_required(title, "title")
        return self._fetch_url(
            self._build_url(_BASE, URL_CONFIG["UPDATE_EXISTING_COLLECTION"], id=id),
            "PUT",
            {
                "title": title,
                "description": description,
                "private": private_collection,
            },
        )

    def update_existing_collection(
        self,
        id: str,
        title: str,
        description: str | None = None,
        private_collection: bool = False,
    ) -> Collection:
        """Update an existing collection (alias for update_collection)."""
        return self.update_collection(id, title, description, private_collection)

    def delete_collection(self, id: str) -> DeleteResponse:
        """Delete a collection."""
        self._validate_required(id, "id")
        return self._fetch_url(
            self._build_url(_BASE, URL_CONFIG["DELETE_COLLECTION"], id=id),
            "DELETE",
        )

    def add_photo_to_collection(self, collection_id: str, photo_id: str) -> Collection:
        """Add a photo to a collection."""
        self._validate_required(collection_id, "collection_id")
        self._validate_required(photo_id, "photo_id")
        return self._fetch_url(
            self._build_url(_BASE, URL_CONFIG["ADD_PHOTO_TO_COLLECTION"], collection_id=collection_id),
            "POST",
            {"photo_id": photo_id},
        )

    def remove_photo_from_collection(self, collection_id: str, photo_id: str) -> DeleteResponse:
        """Remove a photo from a collection."""
        self._validate_required(collection_id, "collection_id")
        self._validate_required(photo_id, "photo_id")
        return self._fetch_url(
            self._build_url(_BASE, URL_CONFIG["REMOVE_PHOTO_FROM_COLLECTION"], collection_id=collection_id),
            "DELETE",
            {"photo_id": photo_id},
        )
