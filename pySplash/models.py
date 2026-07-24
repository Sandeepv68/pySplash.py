"""Typed response models for the Unsplash API."""

from __future__ import annotations

from typing import Any, TypedDict


class UserLinks(TypedDict, total=False):
    self: str
    html: str
    photos: str
    likes: str
    portfolio: str


class UserUrls(TypedDict, total=False):
    raw: str
    full: str
    regular: str
    small: str
    medium: str
    large: str
    profile_image: str


class UserProfileImages(TypedDict, total=False):
    small: str
    medium: str
    large: str


class User(TypedDict, total=False):
    id: str
    username: str
    name: str
    first_name: str
    last_name: str
    instagram_username: str
    total_likes: int
    total_photos: int
    total_collections: int
    followers_count: int
    following_count: int
    downloads: int
    bio: str | None
    location: str | None
    total_promoted_photos: int
    followers: int
    following: int
    profile_image: UserProfileImages
    social: dict[str, Any]
    links: UserLinks
    tags: list[dict[str, Any]]
    photos: list[dict[str, Any]]
    portfolio_url: str | None
    updated_at: str
    badge: dict[str, Any]
    user_links: UserLinks


class UserPortfolio(TypedDict, total=False):
    id: str
    title: str
    url: str
    published_at: str
    updated_at: str
    links: dict[str, str]


class UserStatistics(TypedDict, total=False):
    id: str
    username: str
    downloads: dict[str, Any]
    views: dict[str, Any]
    likes: dict[str, Any]
    historical: dict[str, Any]


class Urls(TypedDict, total=False):
    raw: str
    full: str
    regular: str
    small: str
    thumb: str
    small_s3: str


class PhotoLinks(TypedDict, total=False):
    self: str
    html: str
    download: str
    download_location: str


class Photo(TypedDict, total=False):
    id: str
    slug: str
    created_at: str
    updated_at: str
    promoted_at: str | None
    width: int
    height: int
    color: str
    blur_hash: str
    description: str | None
    alt_description: str | None
    breadcrumbs: list[dict[str, Any]]
    urls: Urls
    links: PhotoLinks
    likes: int
    liked_by_user: bool
    current_user_collections: list[dict[str, Any]]
    user: User
    exif: dict[str, Any]
    location: dict[str, Any]
    views: int
    downloads: int
    related_collections: dict[str, Any]
    tags: list[dict[str, Any]]
    sponsorship: dict[str, Any] | None
    topic_submissions: dict[str, Any]
    user_links: UserLinks


class PhotoStatistics(TypedDict, total=False):
    id: str
    downloads: dict[str, Any]
    views: dict[str, Any]
    likes: dict[str, Any]
    historical: dict[str, Any]


class CollectionLinks(TypedDict, total=False):
    self: str
    html: str
    photos: str
    related: str


class Collection(TypedDict, total=False):
    id: str
    title: str
    description: str | None
    published_at: str
    updated_at: str
    curated: bool
    featured: bool
    total_photos: int
    private: bool
    share_key: str
    tags: list[dict[str, Any]]
    links: CollectionLinks
    user: User
    cover_photo: Photo


class SearchResult(TypedDict, total=False):
    total: int
    total_pages: int
    results: list[dict[str, Any]]


class BearerTokenResponse(TypedDict, total=False):
    access_token: str
    token_type: str
    scope: str
    created_at: int


class DeleteResponse(TypedDict, total=False):
    status: int
    statusText: str
    message: str
