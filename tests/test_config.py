import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from xperiun_rag.config import load_settings  # noqa: E402

ENV_VARS = (
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "EMBEDDING_MODEL",
    "LLM_MODEL",
    "DOCS_DIR",
    "CHROMA_DIR",
    "CHROMA_COLLECTION",
    "CHUNK_SIZE",
    "CHUNK_OVERLAP",
    "TOP_K",
)


class ConfigTest(unittest.TestCase):
    def setUp(self):
        clean = {k: v for k, v in os.environ.items() if k not in ENV_VARS}
        patcher = mock.patch.dict(os.environ, clean, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def _env_file(self, content: str) -> Path:
        path = Path(self.tmp.name) / ".env"
        path.write_text(content, encoding="utf-8")
        return path

    def test_defaults_follow_spec(self):
        settings = load_settings(self._env_file(""))
        self.assertEqual(settings.embedding_model, "text-embedding-3-small")
        self.assertEqual(settings.llm_model, "claude-opus-5-5")
        self.assertEqual(settings.chunk_size, 350)
        self.assertEqual(settings.chunk_overlap, 52)
        self.assertEqual(settings.top_k, 3)

    def test_missing_keys_are_reported_by_name(self):
        settings = load_settings(self._env_file(""))
        self.assertEqual(settings.missing_keys(), ["OPENAI_API_KEY", "ANTHROPIC_API_KEY"])

    def test_keys_present(self):
        settings = load_settings(self._env_file("OPENAI_API_KEY=sk-fake-1\nANTHROPIC_API_KEY=sk-fake-2\n"))
        self.assertEqual(settings.missing_keys(), [])

    def test_repr_does_not_expose_secrets(self):
        settings = load_settings(self._env_file("OPENAI_API_KEY=sk-secret-a\nANTHROPIC_API_KEY=sk-secret-b\n"))
        self.assertNotIn("sk-secret-a", repr(settings))
        self.assertNotIn("sk-secret-b", repr(settings))

    def test_env_example_lists_all_variables_without_values_for_keys(self):
        example = (Path(__file__).resolve().parents[1] / ".env.exemple").read_text(encoding="utf-8")
        lines = example.splitlines()
        # Mensagens de falha nunca incluem o conteúdo do arquivo, que pode ter chaves reais.
        for name in ENV_VARS:
            self.assertTrue(any(line.startswith(f"{name}=") for line in lines), f"{name} ausente")
        for name in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY"):
            self.assertIn(f"{name}=", lines, f"{name} deve estar vazia no .env.exemple (há um valor preenchido)")


if __name__ == "__main__":
    unittest.main()
