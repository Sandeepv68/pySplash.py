"""Custom exception class for pySplash.py errors."""

from __future__ import annotations

from typing import Any


class PySplashError(Exception):
    """Exception raised by pySplash.py for API and validation errors."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        status_text: str | None = None,
        cause: Any | None = None,
    ) -> None:
        super().__init__(message)
        self.name = "PySplashError"
        self.status_code = status_code
        self.statusText = status_text
        self.cause = cause

    def __repr__(self) -> str:
        parts = [f"PySplashError({self.args[0]!r}"]
        if self.status_code is not None:
            parts.append(f"status_code={self.status_code}")
        if self.statusText is not None:
            parts.append(f"status_text={self.statusText!r}")
        return ", ".join(parts) + ")"
