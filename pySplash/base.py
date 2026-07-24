"""Shared utilities for sync and async API clients."""

from __future__ import annotations

import hashlib
import logging
from typing import Any

from .errors import PySplashError

logger = logging.getLogger("pySplash.py")


class PySplashBase:
    """Shared validation, error handling, and URL construction for both sync and async clients."""

    @staticmethod
    def _compute_hash(value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    @staticmethod
    def _validate_required(value: Any, field_name: str) -> None:
        if value is None or value == "":
            if field_name == "id":
                message = "Parameter : id is required!"
            elif field_name == "query":
                message = "Parameter : query is missing!"
            else:
                message = f"Parameter : {field_name} is required and cannot be empty!"
            raise PySplashError(message)

    @staticmethod
    def _validate_supported_value(value: str | None, allowed_values: list, field_name: str) -> None:
        if value is not None and value not in allowed_values:
            raise PySplashError(f"Parameter : {field_name} has an unsupported value!")

    @staticmethod
    def _validate_int(value: Any, field_name: str, minimum: int = 1, maximum: int | None = None) -> None:
        if value is not None:
            if not isinstance(value, int) or isinstance(value, bool):
                raise PySplashError(f"Parameter : {field_name} must be an integer!")
            if value < minimum:
                raise PySplashError(f"Parameter : {field_name} must be >= {minimum}!")
            if maximum is not None and value > maximum:
                raise PySplashError(f"Parameter : {field_name} must be <= {maximum}!")

    @staticmethod
    def _validate_bool(value: Any, field_name: str) -> None:
        if value is not None and not isinstance(value, bool):
            raise PySplashError(f"Parameter : {field_name} must be a boolean or optional!")

    @staticmethod
    def _build_query_parameters(params: dict[str, Any]) -> dict[str, Any]:
        return {k: v for k, v in params.items() if v is not None and v != ""}

    @staticmethod
    def _build_url(base: str, path: str, **replacements: str) -> str:
        url = base + path
        for key, value in replacements.items():
            url = url.replace(f":{key}", value)
        return url

    @staticmethod
    def _handle_response_status(data: Any, status: int, status_text: str) -> Any:
        if status == 204:
            logger.debug("204 No Content - resource deleted")
            return {"status": status, "statusText": status_text, "message": "Content Deleted"}
        if status >= 400:
            logger.warning("%d %s", status, status_text)
            raise PySplashError(
                f"HTTP {status} {status_text}",
                status_code=status,
                status_text=status_text,
            )
        return data

    @staticmethod
    def _create_pysplash_error(error: Exception) -> PySplashError:
        if isinstance(error, PySplashError):
            return error
        status_code = getattr(getattr(error, "response", None), "status_code", None)
        status_text = getattr(
            getattr(error, "response", None),
            "reason",
            getattr(getattr(error, "response", None), "reason_phrase", None),
        )
        return PySplashError(
            str(error),
            status_code=status_code,
            status_text=status_text,
            cause=error,
        )

    @staticmethod
    def _default_headers(bearer_token: str | None = None, access_key: str | None = None) -> dict[str, str]:
        headers: dict[str, str] = {
            "Content-type": "application/json",
            "X-Requested-With": "PySplash.py",
        }
        if bearer_token:
            headers["Authorization"] = f"Bearer {bearer_token}"
            headers["X-PySplash-Header"] = PySplashBase._compute_hash(bearer_token)
        elif access_key:
            headers["Authorization"] = f"Client-ID {access_key}"
            headers["X-PySplash-Header"] = PySplashBase._compute_hash(access_key)
        return headers

    @staticmethod
    def _extract_location_params(location: dict[str, Any] | None) -> dict[str, Any]:
        if not location:
            return {}
        result: dict[str, Any] = {}
        mapping = {
            "latitude": "location[latitude]",
            "longitude": "location[longitude]",
            "name": "location[name]",
            "city": "location[city]",
            "country": "location[country]",
            "confidential": "location[confidential]",
        }
        for key, param_name in mapping.items():
            if key in location and location[key] is not None:
                result[param_name] = location[key]
        return result

    @staticmethod
    def _extract_exif_params(exif: dict[str, Any] | None) -> dict[str, Any]:
        if not exif:
            return {}
        result: dict[str, Any] = {}
        mapping = {
            "make": "exif[make]",
            "model": "exif[model]",
            "exposure_time": "exif[exposure_time]",
            "aperture_value": "exif[aperture_value]",
            "focal_length": "exif[focal_length]",
            "iso_speed_ratings": "exif[iso_speed_ratings]",
        }
        for key, param_name in mapping.items():
            if key in exif and exif[key] is not None:
                result[param_name] = exif[key]
        return result
