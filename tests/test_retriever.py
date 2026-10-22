"""Recuperação com Chroma real em diretório temporário e embeddings falsos (sem API externa)."""

import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from langchain_core.documents import Document
from langchain_core.embeddings import DeterministicFakeEmbedding

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from xperiun_rag.config import load_settings  # noqa: E402
from xperiun_rag.ingest import ingest  # noqa: E402
from xperiun_rag.retriever import MAX_QUESTION_CHARS, RetrievalError, retrieve  # noqa: E402
from xperiun_rag.vectorstore import get_vectorstore  # noqa: E402


class CountingEmbedding(DeterministicFakeEmbedding):
    """Conta as chamadas para provar que a pergunta passa pela mesma função de embedding da coleção."""

    queries: list = []

    def embed_query(self, text: str) -> list[float]:
        self.queries.append(text)
        return super().embed_query(text)


class FailingEmbedding(DeterministicFakeEmbedding):
    def embed_query(self, text: str) -> list[float]:
        raise ConnectionError("sk-segredo-que-nao-pode-vazar")


class RetrieverTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(self.tmp.cleanup)
        self.settings = replace(
            load_settings(), chroma_dir=Path(self.tmp.name) / "chroma", chroma_collection="teste", top_k=3
        )
        self.embeddings = CountingEmbedding(size=32, queries=[])

    def store(self, embeddings=None):
        return get_vectorstore(self.settings, embeddings=embeddings or self.embeddings)

    def indexed_store(self):
        store = self.store()
        ingest(self.settings, store=store)
        return store

    def test_returns_three_distinct_chunks_sorted_by_similarity(self):
        result = retrieve("Qual a comissão do Xperiun Cloud Pro?", self.settings, store=self.indexed_store())
        self.assertEqual(len(result.chunks), 3)
        self.assertEqual([c.rank for c in result.chunks], [1, 2, 3])
        self.assertEqual(len({c.document.id for c in result.chunks}), 3)
        sims = [c.similarity for c in result.chunks]
        self.assertEqual(sims, sorted(sims, reverse=True))

    def test_question_is_embedded_once_with_the_collection_embedding(self):
        store = self.indexed_store()
        result = retrieve("  Qual o   prazo Net-30? ", self.settings, store=store)
        self.assertEqual(self.embeddings.queries, ["Qual o prazo Net-30?"])
        self.assertEqual(result.question_vector, self.embeddings.embed_query("Qual o prazo Net-30?"))

    def test_exact_chunk_text_is_ranked_first(self):
        store = self.indexed_store()
        target = store.get(limit=1, offset=10, include=["documents"])
        text, target_id = target["documents"][0], target["ids"][0]
        result = retrieve(text, self.settings, store=store)
        self.assertEqual(result.chunks[0].document.id, target_id)
        self.assertAlmostEqual(result.chunks[0].similarity, 1.0, places=3)

    def test_source_metadata_is_preserved(self):
        result = retrieve("cláusula", self.settings, store=self.indexed_store())
        for chunk in result.chunks:
            for key in ("source", "page_start", "page_end", "section", "classification", "chunk_index"):
                self.assertIn(key, chunk.document.metadata)
            self.assertIn(" · pág. ", chunk.citation)

    def test_fewer_chunks_than_k_are_not_padded(self):
        store = self.store()
        store.add_documents(
            [
                Document(id="a", page_content="texto A", metadata={"source": "x.pdf", "chunk_index": 0}),
                Document(id="b", page_content="texto B", metadata={"source": "x.pdf", "chunk_index": 1}),
            ]
        )
        result = retrieve("texto", self.settings, store=store)
        self.assertEqual(sorted(c.document.id for c in result.chunks), ["a", "b"])

    def test_empty_question(self):
        for question in ("", "   ", None):
            with self.assertRaisesRegex(RetrievalError, "Digite uma pergunta"):
                retrieve(question, self.settings, store=self.store())

    def test_question_too_long(self):
        with self.assertRaisesRegex(RetrievalError, "passa de"):
            retrieve("a" * (MAX_QUESTION_CHARS + 1), self.settings, store=self.store())

    def test_empty_base(self):
        with self.assertRaisesRegex(RetrievalError, "base está vazia"):
            retrieve("qualquer coisa", self.settings, store=self.store())

    def test_provider_failure_message_has_no_details(self):
        store = self.indexed_store()
        failing = get_vectorstore(self.settings, embeddings=FailingEmbedding(size=32))
        with self.assertRaises(RetrievalError) as ctx:
            retrieve("pergunta", self.settings, store=failing)
        self.assertIn("ConnectionError", str(ctx.exception))
        self.assertNotIn("sk-segredo", str(ctx.exception))
        self.assertTrue(store.get(limit=1)["ids"])

    def test_missing_openai_key(self):
        settings = replace(self.settings, openai_api_key="")
        with self.assertRaisesRegex(RetrievalError, "OPENAI_API_KEY"):
            retrieve("pergunta", settings)


if __name__ == "__main__":
    unittest.main()
