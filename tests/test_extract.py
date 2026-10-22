import sys
import tempfile
import unittest
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from xperiun_rag.extract import ExtractionError, extract_pdf  # noqa: E402

DOCS = ROOT / "docs"


class ExtractRealDocsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs = {p.name: extract_pdf(p) for p in sorted(DOCS.glob("*.pdf"))}

    def text(self, name: str) -> str:
        return "\n\n".join(p.text for p in self.docs[name].pages)

    def test_all_docs_extracted_with_two_pages(self):
        self.assertEqual(len(self.docs), 3)
        for doc in self.docs.values():
            self.assertEqual(len(doc.pages), 2, doc.source)
            self.assertEqual(doc.warnings, [], doc.source)

    def test_aditivo_is_not_garbled(self):
        # pdftotext embaralhava este PDF; o PyMuPDF deve trazer as cláusulas íntegras.
        text = self.text("Aditivo Fornecedores Xperiun.pdf")
        self.assertIn("1.1. Período de Congelamento: O valor de face mensal", text)
        self.assertIn("Uptime) mensal de operação de 99,98%", text)
        self.assertIn('regime de pagamento "Net-30". Isto significa que todos os pagamentos', text)
        self.assertIn("no prazo máximo e improrrogável de 24 (vinte e quatro) horas", text)

    def test_commission_table_keeps_decimal_commas_and_headers(self):
        text = self.text("Política de Vendas Xperiun.pdf")
        self.assertIn(
            "Produto / Linha de Serviço: Xperiun Cloud Pro; "
            "Taxa Base de Comissão (Até 100% da Cota): 12,0% sobre o ARR do 1º ano; "
            "Acelerador (Acima de 100% da Cota): 15,0% sobre o excedente.",
            text,
        )
        self.assertIn("Xperiun Lite; Taxa Base de Comissão (Até 100% da Cota): 7,5%", text)
        self.assertIn("Serviços de Setup (One-off)", text)
        self.assertNotIn("120%", text)

    def test_sla_table_only_has_rows_present_in_source(self):
        # O PDF original só mostra 1 linha da tabela de SLA (está cortada no rodapé da pág. 1).
        text = self.text("Aditivo Fornecedores Xperiun.pdf")
        rows = [line for line in text.splitlines() if line.startswith("Tabela (pág. 1)")]
        self.assertEqual(len(rows), 1)
        self.assertIn("Até 8 minutos e 38 segundos", rows[0])
        self.assertIn("0% (Sem penalidade - SLA cumprido)", rows[0])

    def test_footer_removed(self):
        for name in self.docs:
            self.assertNotRegex(self.text(name), r"Página \d+ de \d+", name)

    def test_classification_metadata(self):
        self.assertEqual(self.docs["Política de Vendas Xperiun.pdf"].classification, "Interno / Confidencial")
        self.assertEqual(self.docs["Contrato de Trabalho Xperiun.pdf"].classification, "Não informada")

    def test_hyphenated_line_breaks_are_kept_as_one_word(self):
        self.assertIn("auxílio-custeio", self.text("Contrato de Trabalho Xperiun.pdf"))


class ExtractBadFilesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)

    def test_empty_file(self):
        path = self.dir / "vazio.pdf"
        path.write_bytes(b"")
        with self.assertRaisesRegex(ExtractionError, "vazio"):
            extract_pdf(path)

    def test_corrupted_file(self):
        path = self.dir / "corrompido.pdf"
        path.write_bytes(b"isto nao e um pdf")
        with self.assertRaisesRegex(ExtractionError, "ilegível"):
            extract_pdf(path)

    def test_pdf_without_text_suggests_ocr(self):
        path = self.dir / "escaneado.pdf"
        doc = pymupdf.open()
        doc.new_page()
        doc.save(path)
        doc.close()
        with self.assertRaisesRegex(ExtractionError, "OCR"):
            extract_pdf(path)

    def test_blank_page_generates_warning(self):
        path = self.dir / "uma_pagina_em_branco.pdf"
        doc = pymupdf.open()
        doc.new_page().insert_text((72, 72), "Cláusula de teste com texto suficiente para extrair.")
        doc.new_page()
        doc.save(path)
        doc.close()
        result = extract_pdf(path)
        self.assertEqual(result.warnings, ["página 2 sem texto extraível"])


if __name__ == "__main__":
    unittest.main()
