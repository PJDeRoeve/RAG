import fastapi
from google.cloud import firestore

from rag.dependencies import get_firestore_client
from rag.document.dao import DocumentChunkDB, DocumentDB
from rag.document.schema import DocumentChunk, Document


def get_document_chunk_db(firestore_client: firestore.AsyncClient = fastapi.Depends(get_firestore_client)) -> DocumentChunkDB:
    """Get a DB instance for DocumentChunk"""
    return DocumentChunkDB(schema_definition=DocumentChunk, client=firestore_client)

def get_document_db(firestore_client: firestore.AsyncClient = fastapi.Depends(get_firestore_client)) -> DocumentDB:
    """Get a DB instance for Document"""
    return DocumentDB(schema_definition=Document, client=firestore_client)
