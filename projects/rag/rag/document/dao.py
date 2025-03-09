from data_access.firestore.asynchronous.dao import FirestoreDAO
from rag.document.schema import DocumentChunk, DocumentChunkCreate, Document, DocumentCreate


class DocumentChunkDB(FirestoreDAO[DocumentChunk, DocumentChunkCreate]):
    collection_name = "document_chunks"

class DocumentDB(FirestoreDAO[Document, DocumentCreate]):
    collection_name = "documents"
