"""Async class to get embeddings from the Cohere /embed endpoint."""
from asyncio import gather
from typing import Generator, Iterable, List, Optional

from aiohttp import ClientSession

from embed.base import BaseEmbeddingClass
from embed.errors import CohereError
from embed.cohere.schema import EmbeddingModel, InputType


class Cohere(BaseEmbeddingClass):
    URL: str = "https://api.cohere.ai/v1/embed"
    SUPPORTED_MODELS: List[str] = [e.value for e in EmbeddingModel]
    SUPPORTED_MODELS_V3: List[str] = [
        e.value for e in EmbeddingModel if e.value.split("-")[-1] == "v3.0"
    ]
    INPUT_TYPES: List[str] = [i.value for i in InputType]

    def __init__(
        self,
        session: ClientSession,
        key: str,
        model: EmbeddingModel = EmbeddingModel.embed_multilingual_v3,
    ):
        """
        Initialize the Cohere object.

        Args:
            session: ClientSession: The aiohttp ClientSession object.
            key: str: The Cohere API key.
            model: EmbeddingModel: The Cohere embedding model to use.
        """
        if model not in Cohere.SUPPORTED_MODELS:
            raise TypeError(
                f"'model' should be one of {Cohere.SUPPORTED_MODELS}; got {model}"
            )

        super().__init__(session=session, key=key)
        self.model: EmbeddingModel = model

    async def embed(
        self, docs: Iterable[str], input_type: Optional[InputType] = None
    ) -> List[List[float]]:
        """Collect embeddings for each string in 'docs'"""
        if self.model in Cohere.SUPPORTED_MODELS_V3 and not input_type:
            raise ValueError(
                f"'input_type' is required from v3 onwards; should be one of {Cohere.INPUT_TYPES}"
            )

        self._validate_docs(docs)
        partitions: Generator[List[str], None, None] = self._partition_docs(
            docs=docs, limit=90
        )
        tasks = [self._embed_partition(p, input_type) for p in partitions]
        embeddings: List[List[List[float]]] = await gather(*tasks)
        return [e for p in embeddings for e in p]

    async def _embed_partition(
        self, partition: List[str], input_type: Optional[InputType]
    ) -> List[List[float]]:
        """Send request to /embed endpoint and return embeddings"""
        body: dict = {
            "texts": partition,
            "truncate": "END",
            "model": self.model,
        }
        if input_type:
            body["input_type"] = input_type

        resp_json: dict = await self._post_json(
            url=Cohere.URL, body=body, headers=self.headers, error=CohereError
        )
        return [e for e in resp_json.get("embeddings", [])]
