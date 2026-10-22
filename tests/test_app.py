import os
import sys
import unittest
from pathlib import Path
from unittest import mock

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / "app.py")
sys.path.insert(0, str(Path(__file__).resolve().parent))


class AppTestCase(unittest.TestCase):
    def test_app_runs_and_shows_config(self):
        at = AppTest.from_file(APP).run(timeout=30)
        self.assertFalse(at.exception)
        self.assertIn("Xperiun", at.title[0].value)

    def test_missing_keys_warning_lists_names_only(self):
        # Simula .env sem chaves: load_dotenv não sobrescreve variáveis já definidas.
        with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "", "ANTHROPIC_API_KEY": ""}):
            at = AppTest.from_file(APP).run(timeout=30)
        self.assertFalse(at.exception)
        warning = at.warning[0].value
        self.assertIn("OPENAI_API_KEY", warning)
        self.assertIn("ANTHROPIC_API_KEY", warning)

    def test_retrieval_tab_rejects_empty_question_without_calling_api(self):
        at = AppTest.from_file(APP).run(timeout=30)
        at.text_input(key="question_input").input("   ")
        next(b for b in at.button if "Buscar" in b.label).click().run(timeout=30)
        self.assertFalse(at.exception)
        self.assertIn("Digite uma pergunta.", [e.value for e in at.error])

    def test_retrieval_tab_asks_for_openai_key(self):
        with mock.patch.dict(os.environ, {"OPENAI_API_KEY": ""}):
            at = AppTest.from_file(APP).run(timeout=30)
        self.assertTrue(any("OPENAI_API_KEY" in w.value and "pergunta" in w.value for w in at.warning))

    def test_example_question_fills_input(self):
        at = AppTest.from_file(APP).run(timeout=30)
        at.selectbox(key="example_question").select_index(1).run(timeout=30)
        self.assertEqual(at.text_input(key="question_input").value, at.selectbox(key="example_question").value)

    def test_chat_tab_renders_answer_sources_and_payload_without_api(self):
        from test_generator import FakeClient, retrieval

        client = FakeClient(parts=("O vale-refeição é R$ 45,00 [1].",))
        with (
            mock.patch("xperiun_rag.retriever.retrieve", return_value=retrieval()),
            mock.patch("xperiun_rag.generator.anthropic.Anthropic", return_value=client),
            mock.patch.dict(os.environ, {"OPENAI_API_KEY": "sk-fake", "ANTHROPIC_API_KEY": "sk-fake"}),
        ):
            at = AppTest.from_file(APP).run(timeout=30)
            at.chat_input[0].set_value("Qual o valor do vale-refeição?").run(timeout=30)
        self.assertFalse(at.exception)
        assistant = [cm for cm in at.chat_message if cm.name == "assistant"]
        self.assertEqual(len(assistant), 1)
        self.assertIn("R$ 45,00 [1]", assistant[0].markdown[0].value)
        labels = [e.label for e in at.expander]
        self.assertIn("📚 Fontes: 3 trechos recuperados", labels)
        self.assertIn("🔍 O que foi enviado ao Claude", labels)
        self.assertEqual(len(client.calls), 1)

    def test_page_never_renders_secret_values(self):
        fake = {"OPENAI_API_KEY": "sk-fake-openai-123", "ANTHROPIC_API_KEY": "sk-fake-anthropic-456"}
        with mock.patch.dict(os.environ, fake):
            at = AppTest.from_file(APP).run(timeout=30)
        rendered = " ".join(str(el.value) for el in (*at.markdown, *at.success, *at.warning, *at.info, *at.caption))
        rendered += str([t.value for t in at.table])
        for secret in fake.values():
            self.assertNotIn(secret, rendered)


if __name__ == "__main__":
    unittest.main()
