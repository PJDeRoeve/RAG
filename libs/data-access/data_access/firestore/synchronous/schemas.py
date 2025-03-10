"""Base schemas for the Firestore DAOs."""
import uuid
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class FirestoreObjectCreate(BaseModel):
    """A firestore creation object contains a UUID that is generated by default."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)


class FirestoreObjectUpdate(BaseModel):
    """A firestore update object contains a UUID that is None by default."""

    id: (uuid.UUID | None) = None


class FirestoreObject(BaseModel):
    """A base firestore object, as returned from firestore."""

    id: uuid.UUID


class OpString(StrEnum):
    """Allowed operators for firestore filtering."""

    LESS_THAN = "<"
    LESS_THAN_OR_EQUAL = "<="
    EQUAL = "=="
    NOT_EQUAL = "!="
    GREATER_THAN_OR_EQUAL = ">="
    GREATER_THAN = ">"
    IN = "in"
    NOT_IN = "not-in"
    ARRAY_CONTAINS = "array_contains"
    ARRAY_CONTAINS_ANY = "array_contains_any"


class FirestoreFilter(BaseModel):
    """Filter that can be applied to find firestore documents."""

    field_path: str
    op_string: OpString
    value: Any


class FirestoreOrder(BaseModel):
    """Ordering directive for Firestore."""

    field_path: str
    direction: str
