import uuid
from datetime import datetime, UTC
from typing import List

from pydantic import BaseModel, Field, computed_field

from data_access.firestore.asynchronous.schemas import (
    FirestoreObject,
    FirestoreObjectCreate,
)
from data_access.utils import create_uuid

class Document(FirestoreObject):
    document_name: str
    created_at: datetime
    fact_sheet: str

class DocumentCreate(FirestoreObject):
    document_name: str
    fact_sheet: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class DocumentRetrieval(BaseModel):
    document_name: str
    document_chunk: str
    chunk_index: int

class DocumentChunk(DocumentRetrieval, FirestoreObject):
    created_at: datetime
    embedding: List[float]
    id: uuid.UUID

class DocumentChunkCreate(DocumentRetrieval, FirestoreObjectCreate):
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    embedding: List[float]

    @computed_field
    @property
    def id(self) -> uuid.UUID:
        return create_uuid(self.document_chunk)
