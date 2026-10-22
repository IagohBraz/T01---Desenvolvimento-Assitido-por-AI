import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from xperiun_rag.chunking import PAGE_SEPARATOR, chunk_document  # noqa: E402
from xperiun_rag.extract import extract_pdf  # noqa: E402

SIZE, OVERLAP = 350, 52


class ChunkingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs = [extract_pdf(p) for p in sorted((ROOT / "docs").glob("*.pdf"))]
        cls.chunks = {d.source: chunk_document(d, SIZE, OVERLAP) for d in cls.docs}

    def test_chunk_size_limit(self):
        for source, chunks in self.chunks.items():
            for c in chunks:
                self.assertLessEqual(len(c.page_content), SIZE, f"{source} {c.id}")

    def test_overlap_between_consecutive_chunks(self):
        for source, chunks in self.chunks.items():
            for a, b in zip(chunks, chunks[1:]):
                overlap = a.metadata["start_index"] + len(a.page_content) - b.metadata["start_index"]
                self.assertGreater(overlap, 0, f"{source} {b.id}")
                self.assertLessEqual(overlap, OVERLAP, f"{source} {b.id}")

    def test_chunks_are_exact_slices_and_cover_whole_document(self):
        for doc in self.docs:
            full = PAGE_SEPARATOR.join(p.text for p in doc.pages)
            chunks = self.chunks[doc.source]
            for c in chunks:
                start = c.metadata["start_index"]
                self.assertEqual(full[start : start + len(c.page_content)], c.page_content)
            self.assertEqual(chunks[0].metadata["start_index"], 0)
            last = chunks[-1]
            self.assertEqual(last.metadata["start_index"] + len(last.page_content), len(full.rstrip()))

    def test_words_are_not_cut(self):
        for doc in self.docs:
            full = PAGE_SEPARATOR.join(p.text for p in doc.pages)
            for c in self.chunks[doc.source]:
                start, end = c.metadata["start_index"], c.metadata["start_index"] + len(c.page_content)
                self.assertTrue(start == 0 or full[start - 1].isspace(), c.id)
                self.assertTrue(end == len(full) or full[end].isspace(), c.id)

    def test_page_and_section_metadata(self):
        chunks = self.chunks["Política de Vendas Xperiun.pdf"]
        clawback = next(c for c in chunks if "REGRA DE CLAWBACK" in c.page_content)
        self.assertEqual(clawback.metadata["page_start"], 2)
        self.assertTrue(clawback.metadata["section"].startswith("CLÁUSULA 3"))
        first = chunks[0]
        self.assertEqual((first.metadata["page_start"], first.metadata["section"]), (1, "Cabeçalho"))
        for c in chunks:
            self.assertEqual(c.metadata["classification"], "Interno / Confidencial")
            self.assertEqual(c.metadata["source"], "Política de Vendas Xperiun.pdf")

    def test_ids_are_unique_and_deterministic(self):
        ids = [c.id for chunks in self.chunks.values() for c in chunks]
        self.assertEqual(len(ids), len(set(ids)))
        again = chunk_document(self.docs[0], SIZE, OVERLAP)
        self.assertEqual([c.id for c in again], [c.id for c in self.chunks[self.docs[0].source]])


if __name__ == "__main__":
    unittest.main()
