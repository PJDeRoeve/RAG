from enum import Enum


class EmbeddingModel(str, Enum):
    english_v2 = "embed-english-v2.0"
    english_light_v2 = "embed-english-light-v2.0"
    embed_multilingual_v2 = "embed-multilingual-v2.0"
    english_v3 = "embed-english-v3.0"
    english_light_v3 = "embed-english-light-v3.0"
    embed_multilingual_v3 = "embed-multilingual-v3.0"
    embed_multilingual_light_v3 = "embed-multilingual-light-v3.0"


class InputType(str, Enum):
    search_document = "search_document"
    search_query = "search_query"
    classification = "classification"
    clustering = "clustering"
