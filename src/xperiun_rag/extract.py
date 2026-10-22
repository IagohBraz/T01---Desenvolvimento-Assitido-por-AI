"""Extração de texto dos PDFs com PyMuPDF (DEC-003).

- Texto corrido: blocos de `get_text("blocks", sort=True)`, em ordem de leitura.
- Tabelas: `find_tables()` só localiza as células; o texto de cada célula vem de
  `get_text(clip=...)`, porque o texto do próprio `find_tables` perde vírgulas
  e espaços (ex.: "12,0%" vira "120%"). Cada linha vira uma frase autossuficiente
  ("Cabeçalho: valor; ...") para não perder a relação coluna → valor no chunking.
- Rodapé ("... Página N de M") é removido do texto.
"""

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path

import pymupdf

FOOTER_RE = re.compile(r"Página\s+\d+\s+de\s+\d+", re.IGNORECASE)
CLASSIFICATION_RE = re.compile(r"Classificação:\s*([^\n]+)", re.IGNORECASE)
MIN_PAGE_CHARS = 30


@dataclass
class Page:
    number: int
    text: str


@dataclass
class ExtractedDocument:
    source: str
    sha256: str
    title: str
    classification: str
    pages: list[Page]
    warnings: list[str] = field(default_factory=list)

    @property
    def char_count(self) -> int:
        return sum(len(p.text) for p in self.pages)


class ExtractionError(Exception):
    """PDF ilegível ou corrompido."""


def _clean(text: str) -> str:
    """Junta as linhas de um bloco; hífen no fim da linha é mantido sem espaço ("Não-\\nCompetição")."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    out = ""
    for line in lines:
        if not out:
            out = line
        elif out.endswith("-"):
            out += line
        else:
            out += " " + line
    return re.sub(r"\s+", " ", out).strip()


def _inside(rect: pymupdf.Rect, boxes: list[pymupdf.Rect]) -> bool:
    center = pymupdf.Point((rect.x0 + rect.x1) / 2, (rect.y0 + rect.y1) / 2)
    return any(center in box for box in boxes)


def _table_paragraphs(page: pymupdf.Page, table, page_number: int) -> str:
    rows = [
        [_clean(page.get_text("text", clip=cell)) if cell else "" for cell in row.cells]
        for row in table.rows
    ]
    if len(rows) < 2:
        return "\n".join(" | ".join(r) for r in rows)
    header, *body = rows
    lines = []
    for row in body:
        pairs = [f"{h}: {v}" for h, v in zip(header, row) if v]
        lines.append(f"Tabela (pág. {page_number}) — " + "; ".join(pairs) + ".")
    return "\n".join(lines)


def _page_text(page: pymupdf.Page, page_number: int) -> str:
    tables = page.find_tables().tables
    table_boxes = [pymupdf.Rect(t.bbox) for t in tables]

    blocks = [b for b in page.get_text("blocks", sort=True) if b[6] == 0]  # 0 = bloco de texto
    footer_ys = [b[1] for b in blocks if FOOTER_RE.search(b[4])]
    footer_y = min(footer_ys) - 3 if footer_ys else None

    items: list[tuple[float, float, str]] = []
    for x0, y0, x1, y1, text, *_ in blocks:
        if footer_y is not None and y0 >= footer_y:
            continue
        if _inside(pymupdf.Rect(x0, y0, x1, y1), table_boxes):
            continue
        cleaned = _clean(text)
        if cleaned:
            items.append((y0, x0, cleaned))
    for table in tables:
        items.append((table.bbox[1], table.bbox[0], _table_paragraphs(page, table, page_number)))

    items.sort(key=lambda item: (round(item[0]), item[1]))
    return "\n\n".join(_merge_broken_paragraphs([text for _, _, text in items]))


def _merge_broken_paragraphs(paragraphs: list[str]) -> list[str]:
    """O PDF às vezes divide um parágrafo em blocos ("todos os" | "pagamentos a ...").
    Junta quando o próximo bloco começa em minúscula ou o anterior termina em " -"."""
    merged: list[str] = []
    for text in paragraphs:
        if merged and (text[0].islower() or merged[-1].endswith(" -")):
            merged[-1] = f"{merged[-1]} {text}"
        else:
            merged.append(text)
    return merged


def extract_pdf(path: Path) -> ExtractedDocument:
    data = path.read_bytes()
    if not data:
        raise ExtractionError(f"{path.name}: arquivo vazio")
    try:
        doc = pymupdf.open(stream=data, filetype="pdf")
    except Exception as exc:  # PyMuPDF levanta tipos variados para PDFs corrompidos
        raise ExtractionError(f"{path.name}: PDF ilegível ({exc.__class__.__name__})") from exc

    warnings: list[str] = []
    pages: list[Page] = []
    with doc:
        if doc.needs_pass:
            raise ExtractionError(f"{path.name}: PDF protegido por senha")
        for index, page in enumerate(doc, 1):
            text = _page_text(page, index)
            if len(text) < MIN_PAGE_CHARS:
                hint = " (contém imagens: avaliar OCR)" if page.get_images() else ""
                warnings.append(f"página {index} sem texto extraível{hint}")
            pages.append(Page(index, text))

    if not any(p.text for p in pages):
        raise ExtractionError(f"{path.name}: nenhum texto extraível (avaliar OCR)")

    first = pages[0].text
    title = first.split("\n\n", 1)[0][:200]
    match = CLASSIFICATION_RE.search(first)
    classification = match.group(1).strip() if match else "Não informada"

    return ExtractedDocument(
        source=path.name,
        sha256=hashlib.sha256(data).hexdigest(),
        title=title,
        classification=classification,
        pages=pages,
        warnings=warnings,
    )
