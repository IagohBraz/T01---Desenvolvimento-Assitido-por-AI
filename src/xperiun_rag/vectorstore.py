"""Acesso ao Chroma persistente com embeddings OpenAI (compartilhado pelas ondas 2 e 3)."""

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

from xperiun_rag.config import Settings


class EmbeddingModelMismatch(Exception):
    """A coleção foi indexada com outro modelo de embeddings."""


def get_embeddings(settings: Settings) -> OpenAIEmbeddings:
    return OpenAIEmbeddings(model=settings.embedding_model, api_key=settings.openai_api_key, max_retries=3)


def get_vectorstore(settings: Settings, embeddings=None) -> Chroma:
    store = Chroma(
        collection_name=settings.chroma_collection,
        embedding_function=embeddings or get_embeddings(settings),
        persist_directory=str(settings.chroma_dir),
        collection_metadata={"hnsw:space": "cosine", "embedding_model": settings.embedding_model},
    )
    indexed_with = (store._collection.metadata or {}).get("embedding_model")
    if indexed_with and indexed_with != settings.embedding_model:
        raise EmbeddingModelMismatch(
            f"Coleção '{settings.chroma_collection}' indexada com '{indexed_with}', "
            f"mas a configuração usa '{settings.embedding_model}'. Reindexe com --rebuild."
        )
    return store
