from typing import List

import aiohttp
import fastapi
from fastapi import UploadFile

from embed.cohere import Cohere
from rag.dependencies import get_cohere_handler, get_firestore_client, get_ner_model
from rag.document.dao import DocumentChunkDB, DocumentDB
from rag.document.dependencies import get_document_chunk_db
from rag.document.error import NotSupportedFileFormatError, DocumentNotYetEmbeddedError
from rag.document.schema import DocumentChunk, DocumentRetrieval
from rag.document.service.handler import DocumentHandler

router = fastapi.APIRouter()


@router.post(
    path="/add",
    response_model=str,
    status_code=fastapi.status.HTTP_201_CREATED,
    description=(
        "Add document to knowledge base and return the document id (document is a .txt file)"
    ),
)
async def add_document(
    document: UploadFile = fastapi.File(...),
    session: aiohttp.ClientSession = fastapi.Depends(get_firestore_client),
    cohere: Cohere = fastapi.Depends(get_cohere_handler),
    ner_model = fastapi.Depends(get_ner_model),
    vector_db: DocumentChunkDB = fastapi.Depends(get_document_chunk_db),
    document_db: DocumentDB = fastapi.Depends(get_document_chunk_db),
) -> str:
    try:
        service = DocumentHandler(
            cohere=cohere,
            session=session,
            vector_db=vector_db,
            document_db=document_db,
            ner_model=ner_model
        )
        filename = await service.add_document(document)
        return filename
    except NotSupportedFileFormatError as e:
        raise fastapi.HTTPException(status_code=400, detail=str(e))

@router.delete(
    path="/delete",
    status_code=fastapi.status.HTTP_200_OK,
    description="Delete document from knowledge base",
)
async def delete_document(
    document_name: str = fastapi.Query(..., description="Name of the document"),
    session: aiohttp.ClientSession = fastapi.Depends(get_firestore_client),
    cohere: Cohere = fastapi.Depends(get_cohere_handler),
    vector_db: DocumentChunkDB = fastapi.Depends(get_document_chunk_db),
) -> None:
    service = DocumentHandler(
        cohere=cohere,
        session=session,
        vector_db=vector_db
    )
    await service.delete_document(filename=document_name)


@router.get(
    path="/retrieve-context",
    response_model=List[DocumentRetrieval],
    status_code=fastapi.status.HTTP_200_OK,
    description="Retrieve context for a given query and document name",
)
async def retrieve_context(
    query: str = fastapi.Query(..., description="Query to search for"),
    document_name: str = fastapi.Query(..., description="Name of the document"),
    num_contexts: int = fastapi.Query(5, description="Number of contexts to retrieve"),
    session: aiohttp.ClientSession = fastapi.Depends(get_firestore_client),
    cohere: Cohere = fastapi.Depends(get_cohere_handler),
    vector_db: DocumentChunkDB = fastapi.Depends(get_document_chunk_db),
) -> List[DocumentChunk]:
    try:
        service = DocumentHandler(
            cohere=cohere,
            session=session,
            vector_db=vector_db
        )
        context = await service.retrieve_context(
            query=query, document_name=document_name, num_contexts=num_contexts
        )
        return context
    except DocumentNotYetEmbeddedError as e:
        raise fastapi.HTTPException(status_code=400, detail=str(e))

