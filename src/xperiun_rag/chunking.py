"""Quebra os documentos extraídos em chunks de até 350 caracteres com overlap de até 52 (DEC-001, DEC-009).

O texto de todas as páginas é concatenado para que um chunk possa atravessar a
virada de página. Cada chunk guarda as páginas que cobre e a cláusula em que começa.
"""

import bisect
import re

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from xperiun_rag.extract import ExtractedDocument

PAGE_SEPARATOR = "\n\n"
SECTION_RE = re.compile(r"CLÁUSULA\s+\d+\s*-\s*[^\n]+")
# Quebra em nível de palavra: com separadores de parágrafo/frase o splitter só aplica
# overlap entre pedaços pequenos mesclados, e na prática o overlap ficava em 0.
# Assim o overlap fica entre ~40 e 52 caracteres, sem cortar palavras ou números.
SEPARATORS = [" ", ""]


def make_splitter(chunk_size: int, chunk_overlap: int) -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=SEPARATORS,
        add_start_index=True,
        strip_whitespace=True,
    )


def chunk_document(doc: ExtractedDocument, chunk_size: int, chunk_overlap: int) -> list[Document]:
    full_text = ""
    page_starts: list[int] = []
    for page in doc.pages:
        if full_text:
            full_text += PAGE_SEPARATOR
        page_starts.append(len(full_text))
        full_text += page.text
    page_numbers = [p.number for p in doc.pages]

    sections = [(m.start(), m.group(0).strip()) for m in SECTION_RE.finditer(full_text)]
    section_starts = [start for start, _ in sections]

    def page_at(offset: int) -> int:
        return page_numbers[bisect.bisect_right(page_starts, offset) - 1]

    def section_at(offset: int) -> str:
        index = bisect.bisect_right(section_starts, offset) - 1
        return sections[index][1] if index >= 0 else "Cabeçalho"

    chunks = make_splitter(chunk_size, chunk_overlap).create_documents([full_text])
    result = []
    for index, chunk in enumerate(chunks):
        start = chunk.metadata["start_index"]
        end = start + len(chunk.page_content) - 1
        result.append(
            Document(
                id=f"{doc.sha256[:16]}-{index:04d}",
                page_content=chunk.page_content,
                metadata={
                    "source": doc.source,
                    "title": doc.title,
                    "classification": doc.classification,
                    "doc_sha256": doc.sha256,
                    "chunk_index": index,
                    "start_index": start,
                    "page_start": page_at(start),
                    "page_end": page_at(end),
                    "section": section_at(start),
                },
            )
        )
    return result
