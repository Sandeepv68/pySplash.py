"""pySplash.py - A Python wrapper for the Unsplash API."""

from .api import PySplashApi
from .api_async import PySplashApiAsync
from .base import PySplashBase
from .errors import PySplashError
from .models import (
    BearerTokenResponse,
    Collection,
    DeleteResponse,
    Photo,
    PhotoLinks,
    PhotoStatistics,
    SearchResult,
    User,
    UserLinks,
    UserPortfolio,
    UserStatistics,
)

__version__ = "1.0.0"
__all__ = [
    "BearerTokenResponse",
    "Collection",
    "DeleteResponse",
    "Photo",
    "PhotoLinks",
    "PhotoStatistics",
    "PySplashApi",
    "PySplashApiAsync",
    "PySplashBase",
    "PySplashError",
    "SearchResult",
    "User",
    "UserLinks",
    "UserPortfolio",
    "UserStatistics",
]
