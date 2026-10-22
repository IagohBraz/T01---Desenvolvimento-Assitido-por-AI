"""Ingestão: PDFs de docs/ → extração → chunks → embeddings OpenAI → Chroma.

Sincronização idempotente por documento (chave: nome do arquivo + SHA-256):
- documento sem mudança: pulado (não gera novos embeddings);
- documento alterado: chunks antigos apagados e o documento é reindexado;
- documento removido de docs/: chunks apagados do Chroma.
"""

from dataclasses import asdict, dataclass, field
from pathlib import Path

from langchain_core.documents import Document

from xperiun_rag.chunking import chunk_document
from xperiun_rag.config import Settings
from xperiun_rag.extract import ExtractionError, extract_pdf


@dataclass
class DocumentResult:
    source: str
    status: str  # indexado | atualizado | inalterado | erro | simulado
    chunks: int = 0
    pages: int = 0
    classification: str = ""
    warnings: list[str] = field(default_factory=list)
    error: str = ""


@dataclass
class IngestReport:
    documents: list[DocumentResult] = field(default_factory=list)
    removed_sources: list[str] = field(default_factory=list)
    total_chunks_in_store: int | None = None

    @property
    def ok(self) -> bool:
        return not any(d.status == "erro" for d in self.documents)

    def to_dict(self) -> dict:
        return asdict(self) | {"ok": self.ok}


def load_chunks(settings: Settings) -> tuple[list[DocumentResult], dict[str, list[Document]]]:
    """Extrai e quebra todos os PDFs, sem chamar nenhuma API externa."""
    results: list[DocumentResult] = []
    chunks_by_source: dict[str, list[Document]] = {}
    for path in sorted(Path(settings.docs_dir).glob("*.pdf")):
        try:
            doc = extract_pdf(path)
        except ExtractionError as exc:
            results.append(DocumentResult(source=path.name, status="erro", error=str(exc)))
            continue
        chunks = chunk_document(doc, settings.chunk_size, settings.chunk_overlap)
        chunks_by_source[doc.source] = chunks
        results.append(
            DocumentResult(
                source=doc.source,
                status="simulado",
                chunks=len(chunks),
                pages=len(doc.pages),
                classification=doc.classification,
                warnings=doc.warnings,
            )
        )
    return results, chunks_by_source


def ingest(settings: Settings, store=None, rebuild: bool = False) -> IngestReport:
    """Sincroniza o Chroma com docs/. `store` permite injetar um vector store nos testes."""
    from xperiun_rag.vectorstore import get_vectorstore

    results, chunks_by_source = load_chunks(settings)
    report = IngestReport(documents=results)
    if store is None:
        if rebuild:
            _drop_collection(settings)
        store = get_vectorstore(settings)

    existing = store.get(include=["metadatas"])
    indexed: dict[str, tuple[str, list[str]]] = {}
    for chunk_id, meta in zip(existing["ids"], existing["metadatas"]):
        sha, ids = indexed.setdefault(meta["source"], (meta["doc_sha256"], []))
        ids.append(chunk_id)

    for result in results:
        if result.status == "erro":
            continue
        chunks = chunks_by_source[result.source]
        previous = indexed.get(result.source)
        if previous and previous[0] == chunks[0].metadata["doc_sha256"] and len(previous[1]) == len(chunks):
            result.status = "inalterado"
            continue
        if previous:
            store.delete(ids=previous[1])
        store.add_documents(chunks, ids=[c.id for c in chunks])
        result.status = "atualizado" if previous else "indexado"

    # Fonte que sumiu de docs/. Um PDF que falhou na extração mantém a versão anterior indexada.
    current_sources = {r.source for r in results}
    for source, (_, ids) in indexed.items():
        if source not in current_sources:
            store.delete(ids=ids)
            report.removed_sources.append(source)

    report.total_chunks_in_store = len(store.get(include=[])["ids"])
    return report


def _drop_collection(settings: Settings) -> None:
    import chromadb

    client = chromadb.PersistentClient(path=str(settings.chroma_dir))
    if settings.chroma_collection in [c.name for c in client.list_collections()]:
        client.delete_collection(settings.chroma_collection)
