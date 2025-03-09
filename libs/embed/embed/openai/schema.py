from enum import Enum


class EmbeddingModel(str, Enum):
    # model recommended by OpenAI
    ada_002 = "text-embedding-ada-002"
    small_3 = "text-embedding-3-small"
    large_3 = "text-embedding-3-large"

    # similarity embeddings
    ada_001 = "text-similarity-ada-001"
    babbage_001 = "text-similarity-babbage-001"
    curie_001 = "text-similarity-curie-001"
    davinci_001 = "text-similarity-davinci-001"

    # text search embeddings
    ada_doc_001 = "text-search-ada-doc-001"
    ada_query_001 = "text-search-ada-query-001"
    babbage_doc_001 = "text-search-babbage-doc-001"
    babbage_query_001 = "text-search-babbage-query-001"
    curie_doc_001 = "text-search-curie-doc-001"
    curie_query_001 = "text-search-curie-query-001"
    davinci_doc_001 = "text-search-davinci-doc-001"
    davincy_query_001 = "text-search-davinci-query-001"

    # code search embeddings
    ada_code_001 = "code-search-ada-code-001"
    ada_text_001 = "code-search-ada-text-001"
    babbage_code_001 = "code-search-babbage-code-001"
    babbage_text_001 = "code-search-babbage-text-001"
