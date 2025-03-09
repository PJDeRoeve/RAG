"""Utility functions for data access."""
import uuid
from datetime import datetime, UTC


def create_uuid(name: str) -> uuid.UUID:
    """Create a UUID from a list of strings.

    Args:
        strings: list of strings to create a UUID from.

    Returns:
        A UUID string.
    """
    return uuid.uuid5(uuid.NAMESPACE_OID, name)


def get_current_datetime_utc():
    return datetime.now(UTC)
