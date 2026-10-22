"""Onda 3 — Augmented: embedding da pergunta (mesmo modelo dos documentos) e top-k chunks no Chroma.

A similaridade é 1 − distância de cosseno (coleção criada com hnsw:space=cosine).
Sempre devolve até k chunks distintos, sem completar com resultados repetidos ou
inventados. `low_relevance` sinaliza para a onda 4 que nenhum trecho parece responder.
"""

import time
from dataclasses import dataclass, field

from langchain_core.documents import Document

from xperiun_rag.config import Settings

MAX_QUESTION_CHARS = 2000
# Calibrado nos documentos atuais: perguntas sobre o conteúdo ficam em ~0,45–0,65;
# perguntas fora do tema ("receita de bolo") ficam em ~0,20.
LOW_RELEVANCE_THRESHOLD = 0.35


class RetrievalError(Exception):
    """Erro com mensagem segura para mostrar ao usuário."""


@dataclass
class RetrievedChunk:
    rank: int
    similarity: float
    document: Document

    @property
    def citation(self) -> str:
        m = self.document.metadata
        pages = f"pág. {m['page_start']}" + (f"–{m['page_end']}" if m["page_end"] != m["page_start"] else "")
        return f"{m['source']} · {pages} · {m['section']}"


@dataclass
class RetrievalResult:
    question: str
    chunks: list[RetrievedChunk] = field(default_factory=list)
    question_vector: list[float] = field(default_factory=list, repr=False)
    embed_ms: float = 0.0
    search_ms: float = 0.0

    @property
    def best_similarity(self) -> float:
        return max((c.similarity for c in self.chunks), default=0.0)

    @property
    def low_relevance(self) -> bool:
        return self.best_similarity < LOW_RELEVANCE_THRESHOLD


def normalize_question(question: str) -> str:
    question = " ".join((question or "").split())
    if not question:
        raise RetrievalError("Digite uma pergunta.")
    if len(question) > MAX_QUESTION_CHARS:
        raise RetrievalError(f"A pergunta passa de {MAX_QUESTION_CHARS} caracteres. Resuma e tente de novo.")
    return question


def retrieve(question: str, settings: Settings, store=None, k: int | None = None) -> RetrievalResult:
    from xperiun_rag.vectorstore import get_vectorstore

    question = normalize_question(question)
    k = k or settings.top_k
    if store is None:
        if "OPENAI_API_KEY" in settings.missing_keys():
            raise RetrievalError("OPENAI_API_KEY ausente no .env: não é possível gerar o embedding da pergunta.")
        store = get_vectorstore(settings)

    if not store.get(limit=1, include=[])["ids"]:
        raise RetrievalError("A base está vazia. Rode a ingestão (scripts/ingest.py) antes de perguntar.")

    # Falha do provedor ou de rede: mensagem sem detalhes internos nem segredos.
    started = time.perf_counter()
    try:
        vector = store.embeddings.embed_query(question)
    except Exception as exc:
        raise RetrievalError(f"Falha ao gerar o embedding da pergunta ({exc.__class__.__name__}). Tente novamente.") from exc
    embedded = time.perf_counter()
    try:
        hits = store.similarity_search_by_vector_with_relevance_scores(vector, k=k)
    except Exception as exc:
        raise RetrievalError(f"Falha ao consultar o Chroma ({exc.__class__.__name__}).") from exc
    searched = time.perf_counter()

    seen: set = set()
    chunks: list[RetrievedChunk] = []
    for doc, distance in hits:
        key = doc.id or (doc.metadata.get("source"), doc.metadata.get("chunk_index"))
        if key in seen:
            continue
        seen.add(key)
        chunks.append(RetrievedChunk(rank=len(chunks) + 1, similarity=round(1 - distance, 4), document=doc))
    return RetrievalResult(
        question=question,
        chunks=chunks,
        question_vector=list(vector),
        embed_ms=(embedded - started) * 1000,
        search_ms=(searched - embedded) * 1000,
    )
