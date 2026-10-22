import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

import numpy as np
from langchain_core.embeddings import DeterministicFakeEmbedding

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from xperiun_rag.config import load_settings  # noqa: E402
from xperiun_rag.explorer import load_snapshot, nearest_neighbors, project_2d  # noqa: E402
from xperiun_rag.ingest import ingest  # noqa: E402
from xperiun_rag.vectorstore import get_vectorstore  # noqa: E402


class ExplorerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        settings = replace(load_settings(), chroma_dir=Path(cls.tmp.name) / "chroma", chroma_collection="teste")
        store = get_vectorstore(settings, embeddings=DeterministicFakeEmbedding(size=16))
        cls.report = ingest(settings, store=store)
        cls.snap = load_snapshot(settings.chroma_dir, "teste")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_snapshot_has_all_chunks_in_document_order(self):
        df = self.snap.chunks
        self.assertEqual(len(df), self.report.total_chunks_in_store)
        self.assertEqual(self.snap.vectors.shape, (len(df), 16))
        for _, group in df.groupby("source"):
            self.assertEqual(group["chunk_index"].tolist(), list(range(len(group))))

    def test_vectors_follow_row_order(self):
        # O vetor da linha i tem de ser o embedding do texto da linha i.
        fake = DeterministicFakeEmbedding(size=16)
        row = self.snap.chunks.iloc[7]
        np.testing.assert_allclose(self.snap.vectors[7], fake.embed_query(row["text"]), rtol=1e-5)

    def test_overlaps_match_offsets(self):
        df = self.snap.chunks
        for _, group in df.groupby("source"):
            g = group.reset_index(drop=True)
            self.assertEqual(g.loc[0, "overlap_prev"], 0)
            self.assertEqual(g.loc[len(g) - 1, "overlap_next"], 0)
            for i in range(1, len(g)):
                expected = g.loc[i - 1, "start_index"] + g.loc[i - 1, "length"] - g.loc[i, "start_index"]
                self.assertEqual(g.loc[i, "overlap_prev"], expected)
                self.assertEqual(g.loc[i - 1, "overlap_next"], expected)
                self.assertTrue(1 <= expected <= 52)

    def test_projection_and_neighbors(self):
        coords = project_2d(self.snap.vectors)
        self.assertEqual(coords.shape, (len(self.snap.chunks), 2))
        neighbors = nearest_neighbors(self.snap.vectors, 0, k=5)
        self.assertEqual(len(neighbors), 5)
        self.assertNotIn(0, [i for i, _ in neighbors])
        sims = [s for _, s in neighbors]
        self.assertEqual(sims, sorted(sims, reverse=True))

    def test_missing_collection_returns_none(self):
        self.assertIsNone(load_snapshot(Path(self.tmp.name) / "nao_existe", "teste"))


if __name__ == "__main__":
    unittest.main()
