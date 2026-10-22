"""Verifica se a stack da onda 1 está instalada e se o Chroma funciona localmente.

Não chama nenhuma API externa e não imprime segredos.
Uso: .venv\\Scripts\\python scripts\\check_stack.py
"""

import sys
import tempfile
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

PACKAGES = (
    "streamlit",
    "langchain",
    "langchain-openai",
    "langchain-anthropic",
    "langchain-chroma",
    "chromadb",
    "python-dotenv",
    "pymupdf",
    "langchain-text-splitters",
)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ok = True
    print(f"Python {sys.version.split()[0]} ({sys.executable})")
    if sys.version_info < (3, 11):
        print("ERRO: Python 3.11+ é obrigatório")
        ok = False

    for package in PACKAGES:
        try:
            print(f"  ok  {package} {version(package)}")
        except PackageNotFoundError:
            print(f"  FALTA  {package}")
            ok = False

    import chromadb

    # No Windows o Chroma mantém os arquivos abertos até o fim do processo.
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        client = chromadb.PersistentClient(path=tmp)
        collection = client.get_or_create_collection("smoke_test")
        collection.add(ids=["1"], documents=["teste"], embeddings=[[0.1, 0.2, 0.3]])
        print(f"  ok  Chroma persistente (itens na coleção de teste: {collection.count()})")
        del client

    from xperiun_rag.config import load_settings

    missing = load_settings().missing_keys()
    print("  ok  .env completo" if not missing else f"  aviso  chaves ausentes no .env: {', '.join(missing)}")

    print("STACK OK" if ok else "STACK COM PROBLEMAS")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
