"""Avalia a recuperação (onda 3) com as perguntas de referência, usando os embeddings reais da OpenAI.

Uso: .venv\\Scripts\\python scripts\\eval_retrieval.py
Acerto = o trecho esperado do documento esperado aparece em algum dos top-k chunks.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from xperiun_rag.config import load_settings  # noqa: E402
from xperiun_rag.reference_questions import REFERENCE_QUESTIONS  # noqa: E402
from xperiun_rag.retriever import RetrievalError, retrieve  # noqa: E402
from xperiun_rag.vectorstore import get_vectorstore  # noqa: E402


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    settings = load_settings()
    try:
        store = get_vectorstore(settings)
    except Exception as exc:
        print(f"ERRO: {exc}")
        return 1

    hits = 0
    for question, source, expected in REFERENCE_QUESTIONS:
        try:
            result = retrieve(question, settings, store=store)
        except RetrievalError as exc:
            print(f"ERRO: {exc}")
            return 1
        rank = next(
            (c.rank for c in result.chunks if c.document.metadata["source"] == source and expected in c.document.page_content),
            None,
        )
        hits += rank is not None
        sims = " ".join(f"{c.similarity:.2f}" for c in result.chunks)
        print(f"  [{'ok' if rank else 'FALHOU'}] posição {rank or '-'} | sim {sims} | {question}")

    total = len(REFERENCE_QUESTIONS)
    print(f"Acertos no top-{settings.top_k}: {hits}/{total} ({hits / total:.0%})")
    return 0 if hits == total else 1


if __name__ == "__main__":
    sys.exit(main())
