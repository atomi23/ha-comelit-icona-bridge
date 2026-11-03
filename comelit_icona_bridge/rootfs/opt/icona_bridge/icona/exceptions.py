"""Custom exceptions for the ICONA bridge library.

Accepts Home Assistant-style keyword args (translation_key, …) so code adapted
from comelit-man keeps working outside Home Assistant.
"""


class ComelitError(Exception):
    """Base exception for all Comelit errors."""

    def __init__(self, *args, **kwargs) -> None:  # noqa: ANN002, ANN003
        message = ""
        if args:
            message = str(args[0])
        elif kwargs.get("translation_key"):
            message = str(kwargs["translation_key"])
        super().__init__(message)
        self.translation_domain = kwargs.get("translation_domain")
        self.translation_key = kwargs.get("translation_key")
        self.translation_placeholders = kwargs.get("translation_placeholders")


class ConnectionComelitError(ComelitError):
    """Failed to connect to the device."""


class AuthenticationError(ComelitError):
    """Authentication failed (invalid token or credentials)."""


class ProtocolError(ComelitError):
    """Unexpected data in the wire protocol."""


class TokenExtractionError(ComelitError):
    """Failed to extract token from device backup."""


class DoorOpenError(ComelitError):
    """Failed to open a door."""


class VideoCallError(ComelitError):
    """Failed to establish video call."""
