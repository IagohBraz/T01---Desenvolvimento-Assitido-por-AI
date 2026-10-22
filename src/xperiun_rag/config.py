"""Configuração lida do .env. Nunca expõe o valor das chaves, apenas se estão presentes."""

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]

REQUIRED_KEYS = ("OPENAI_API_KEY", "ANTHROPIC_API_KEY")


@dataclass(frozen=True)
class Settings:
    openai_api_key: str = field(repr=False)
    anthropic_api_key: str = field(repr=False)
    embedding_model: str
    llm_model: str
    docs_dir: Path
    chroma_dir: Path
    chroma_collection: str
    chunk_size: int
    chunk_overlap: int
    top_k: int

    def missing_keys(self) -> list[str]:
        """Nomes das chaves obrigatórias ausentes (sem valores)."""
        values = {
            "OPENAI_API_KEY": self.openai_api_key,
            "ANTHROPIC_API_KEY": self.anthropic_api_key,
        }
        return [name for name in REQUIRED_KEYS if not values[name].strip()]


def _path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else PROJECT_ROOT / path


def load_settings(env_file: Path | None = None) -> Settings:
    load_dotenv(env_file or PROJECT_ROOT / ".env", override=False)
    get = os.getenv
    return Settings(
        openai_api_key=get("OPENAI_API_KEY", ""),
        anthropic_api_key=get("ANTHROPIC_API_KEY", ""),
        embedding_model=get("EMBEDDING_MODEL", "text-embedding-3-small"),
        llm_model=get("LLM_MODEL", "claude-opus-5-5"),
        docs_dir=_path(get("DOCS_DIR", "docs")),
        chroma_dir=_path(get("CHROMA_DIR", "data/chroma")),
        chroma_collection=get("CHROMA_COLLECTION", "xperiun_docs"),
        chunk_size=int(get("CHUNK_SIZE", "350")),
        chunk_overlap=int(get("CHUNK_OVERLAP", "52")),
        top_k=int(get("TOP_K", "3")),
    )
