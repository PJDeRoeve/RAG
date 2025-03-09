from enum import Enum


class EmbeddingProvider(str, Enum):
    openai = "openai"
    cohere = "cohere"
