import re
from typing import List, Dict

from aiohttp import ClientSession
from fastapi import UploadFile

from data_access.firestore.asynchronous.schemas import OpString, FirestoreFilter
from data_access.utils import create_uuid
from embed.cohere import Cohere
from embed.cohere.schema import InputType
from rag.document.dao import DocumentChunkDB, DocumentDB
from rag.document.error import NotSupportedFileFormatError, DocumentNotYetEmbeddedError
from rag.document.schema import DocumentChunkCreate, DocumentChunk, DocumentRetrieval, Document, DocumentCreate
from rag.document.service.chunker import llm_based_legal_document_chunking


class DocumentHandler:
    def __init__(
        self, cohere: Cohere, session: ClientSession, vector_db: DocumentChunkDB, document_db: DocumentDB, ner_model
    ):
        self.cohere = cohere
        self.session = session
        self.vector_db = vector_db
        self.document_db = document_db
        self.ner_model = ner_model

    async def add_document(self, document: UploadFile) -> DocumentCreate:
        text = await self._verify_document_is_txt_file(document)
        file_name = document.filename
        chunks = await self._split_document_into_chunks(text)
        document_chunks = await self._embed_chunks(file_name, chunks)
        await self._write_to_vector_db(document_chunks)
        fact_sheet = await self._distill_fact_sheet_of_document(text)
        saved_document = await self._write_to_document_db(file_name=file_name, text=text, fact_sheet=fact_sheet)
        return saved_document

    async def delete_document(self, file_name: str):
        filters = [FirestoreFilter(
            field_path="document_name",
            op_string=OpString.EQUAL,
            value=file_name
        )]
        docs = self.vector_db.list(filters=filters)
        async for doc in docs:
            await self.vector_db.delete(doc.id)
        id = create_uuid(file_name)
        if await self.document_db.exists(id):
            await self.document_db.delete(id)

    async def _verify_document_is_txt_file(self, document: UploadFile) -> str:
        file_extension = document.filename.rsplit(".", maxsplit=1)[-1]
        if file_extension != "txt":
            raise NotSupportedFileFormatError("Only .txt files are supported")
        content = await document.read()
        text = content.decode("utf-8")
        return text

    async def _split_document_into_chunks(self, text: str) -> List[str]:
        """
        Chunking strategy is crucial here.
        I would develop a two-step chunking strategy:
        - Detect whether document follows certain legal document template (where you can split by sections, legal keywords, etc.)
        - If not, use more classic chunking strategies like character/token/sentence/paragraph based chunking

        Because this is a take home case, I will skip this and take the lazy route which I would not use in production:
        One-shot LLM prompt begging the model to split it into chunks for me :)
        """
        chunks = await llm_based_legal_document_chunking(document=text)
        return chunks

    async def _embed_chunks(
        self, document_name: str, chunks: List[str]
    ) -> List[DocumentChunkCreate]:
        embeddings = await self.cohere.embed(chunks, input_type=InputType.search_query)
        document_chunks = [
            DocumentChunkCreate(
                embedding=embedding, document_name=document_name, document_chunk=chunk, chunk_index=idx
            )
            for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings))
        ]
        return document_chunks

    async def _write_to_vector_db(self, document_chunks: List[DocumentChunkCreate]):
        await self.vector_db.create_many(document_chunks)

    async def _verify_document_contains_embedded_chunks(self, filters: List[FirestoreFilter]) -> None:
        result_set = self.vector_db.list(filters=filters)
        async for _ in result_set:
            return
        raise DocumentNotYetEmbeddedError(
            "The document has not been added. Please add the document first."
        )

    async def retrieve_context(self, query: str, document_name: str, num_contexts: int) -> List[DocumentRetrieval]:
        query_embedding = await self.cohere.embed([query], input_type=InputType.search_query)
        filters = [FirestoreFilter(
            field_path="document_name",
            op_string=OpString.EQUAL,
            value=document_name
        )]
        await self._verify_document_contains_embedded_chunks(filters= filters)
        result_set = self.vector_db.search(
            embedding=query_embedding[0],
            filters=filters,
            limit=num_contexts
        )
        results =[DocumentRetrieval(**result.model_dump()) async for result in result_set]
        return results

    async def _distill_fact_sheet_of_document(self, text: str) -> str:
        """
        Some facts and aspects of a legal document are crucial to answer almost any question about it, and
        appear in almost all docs (The parties, the date, any addresses, etc.)
        We could use a Named Entity Recognition model to extract these facts and save them somewhere.
        We use an English-only kinda outdated model here (Spacy) to extract these facts.
        Would use something fancier and multi-lingual in production and it's still insanely unsupervised,
        but for now, this will do
        """
        doc = self.ner_model(text)
        labels_of_interest: Dict[str, List[str]] = {"PERSON": [], "ORG": [], "GPE": []}
        for entity in doc.ents:
            if entity.label_ in labels_of_interest:
                chunk_text = entity.text
                for chunk in doc.noun_chunks:
                    if entity.start >= chunk.start and entity.end <= chunk.end:
                        chunk_text = chunk.text
                if chunk_text not in labels_of_interest[entity.label_]:
                    labels_of_interest[entity.label_].append(chunk_text)
        person_context = "The parties of interest are: " + ", ".join(labels_of_interest["PERSON"])
        org_context = "Organizations involved are: " + ", ".join(labels_of_interest["ORG"])
        gpe_context = "Locations mentioned are: " + ", ".join(labels_of_interest["GPE"])
        return f"{person_context}\n{org_context}\n{gpe_context}"

    async def _write_to_document_db(self, file_name: str, text: str, fact_sheet: str):
        document = DocumentCreate(
            document_name=file_name,
            fact_sheet=fact_sheet,
            content=text,
        )
        await self.document_db.create(document)
        return document





