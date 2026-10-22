"""Ingestão com Chroma real em diretório temporário e embeddings falsos (sem API externa)."""

import shutil
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from langchain_core.embeddings import DeterministicFakeEmbedding

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from xperiun_rag.config import load_settings  # noqa: E402
from xperiun_rag.ingest import ingest  # noqa: E402
from xperiun_rag.vectorstore import EmbeddingModelMismatch, get_vectorstore  # noqa: E402


class IngestTest(unittest.TestCase):
    def setUp(self):
        # No Windows o Chroma mantém arquivos abertos até o fim do processo.
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(self.tmp.cleanup)
        tmp = Path(self.tmp.name)
        self.docs_dir = tmp / "docs"
        shutil.copytree(ROOT / "docs", self.docs_dir)
        self.settings = replace(
            load_settings(),
            docs_dir=self.docs_dir,
            chroma_dir=tmp / "chroma",
            chroma_collection="teste",
            openai_api_key="",
        )
        self.embeddings = DeterministicFakeEmbedding(size=32)

    def store(self, settings=None):
        return get_vectorstore(settings or self.settings, embeddings=self.embeddings)

    def test_first_ingest_indexes_all_documents(self):
        report = ingest(self.settings, store=self.store())
        self.assertTrue(report.ok)
        self.assertEqual({d.status for d in report.documents}, {"indexado"})
        self.assertEqual(report.total_chunks_in_store, sum(d.chunks for d in report.documents))

    def test_reingest_does_not_duplicate(self):
        first = ingest(self.settings, store=self.store())
        second = ingest(self.settings, store=self.store())
        self.assertEqual({d.status for d in second.documents}, {"inalterado"})
        self.assertEqual(second.total_chunks_in_store, first.total_chunks_in_store)

    def test_persistence_after_reopen_keeps_metadata(self):
        report = ingest(self.settings, store=self.store())
        reopened = self.store()
        data = reopened.get(include=["metadatas", "documents"])
        self.assertEqual(len(data["ids"]), report.total_chunks_in_store)
        meta = data["metadatas"][0]
        for key in ("source", "title", "classification", "doc_sha256", "page_start", "page_end", "section"):
            self.assertIn(key, meta)
        hits = reopened.similarity_search("multiplicador de comissão", k=3)
        self.assertEqual(len(hits), 3)

    def test_removed_document_is_deleted_from_store(self):
        ingest(self.settings, store=self.store())
        (self.docs_dir / "Contrato de Trabalho Xperiun.pdf").unlink()
        report = ingest(self.settings, store=self.store())
        self.assertEqual(report.removed_sources, ["Contrato de Trabalho Xperiun.pdf"])
        sources = {m["source"] for m in self.store().get(include=["metadatas"])["metadatas"]}
        self.assertNotIn("Contrato de Trabalho Xperiun.pdf", sources)

    def test_changed_document_is_replaced(self):
        ingest(self.settings, store=self.store())
        target = self.docs_dir / "Aditivo Fornecedores Xperiun.pdf"
        shutil.copy(self.docs_dir / "Política de Vendas Xperiun.pdf", target)  # mesmo nome, outro conteúdo
        report = ingest(self.settings, store=self.store())
        status = {d.source: d.status for d in report.documents}
        self.assertEqual(status["Aditivo Fornecedores Xperiun.pdf"], "atualizado")
        metas = self.store().get(where={"source": "Aditivo Fornecedores Xperiun.pdf"}, include=["metadatas"])
        self.assertEqual(len({m["doc_sha256"] for m in metas["metadatas"]}), 1)

    def test_corrupted_document_reports_error_and_others_are_indexed(self):
        (self.docs_dir / "quebrado.pdf").write_bytes(b"nao e pdf")
        report = ingest(self.settings, store=self.store())
        self.assertFalse(report.ok)
        status = {d.source: d.status for d in report.documents}
        self.assertEqual(status.pop("quebrado.pdf"), "erro")
        self.assertEqual(set(status.values()), {"indexado"})

    def test_embedding_model_mismatch_is_detected(self):
        ingest(self.settings, store=self.store())
        other = replace(self.settings, embedding_model="text-embedding-3-large")
        with self.assertRaises(EmbeddingModelMismatch):
            self.store(other)


if __name__ == "__main__":
    unittest.main()
