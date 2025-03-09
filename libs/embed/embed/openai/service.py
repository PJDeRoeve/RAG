"""Async class to get embeddings from the OpenAI /embeddings endpoint."""
from asyncio import create_task, gather
from typing import Generator, Iterable, List

from aiohttp import ClientSession

from embed.base import BaseEmbeddingClass
from embed.errors import OpenAIError
from embed.openai.schema import EmbeddingModel


class OpenAI(BaseEmbeddingClass):
    URL: str = "https://api.openai.com/v1/embeddings"
    def __init__(
        self,
        session: ClientSession,
        key: str,
        model: EmbeddingModel = EmbeddingModel.ada_002
    ):
        """
        Initialize the OpenAI object.

        Args:
            session: ClientSession: The aiohttp ClientSession object.
            key: str: The OpenAI API key.
            model: EmbeddingModel: The OpenAI embedding model to use.
        """
        if model not in (m := [e.value for e in EmbeddingModel]):
            raise TypeError(
                f"'model' should be one of {m}; got {model}"
            )

        super().__init__(session=session, key=key)
        self.model: EmbeddingModel = model

    async def embed(self, docs: Iterable[str]) -> List[List[float]]:
        """Collect embeddings for each string in 'docs'"""
        self._validate_docs(docs)
        partitions: Generator[List[str], None, None] = self._partition_docs(docs, limit=150)
        tasks = [create_task(self._embed_partition(p)) for p in partitions]
        embeddings: List[List[List[float]]] = await gather(*tasks)
        return [e for p in embeddings for e in p]

    async def _embed_partition(self, partition: List[str]) -> List[List[float]]:
        """Send request to /embeddings endpoint and return embeddings"""
        body: dict = {"input": partition, "model": self.model}
        resp_json: dict = await self._post_json(
            url=OpenAI.URL, body=body, headers=self.headers, error=OpenAIError
        )
        return [e.get("embedding", []) for e in resp_json.get("data", [])]
