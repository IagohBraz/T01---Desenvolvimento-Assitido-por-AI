"""Dados para as abas de visualização do Streamlit. Só lê o Chroma local: nenhuma API externa."""

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass
class IndexSnapshot:
    chunks: pd.DataFrame  # uma linha por chunk, ordenada por documento e chunk_index
    vectors: np.ndarray  # (n_chunks, dim), na mesma ordem de `chunks`
    collection_metadata: dict


def load_snapshot(chroma_dir: Path, collection: str) -> IndexSnapshot | None:
    import chromadb

    if not Path(chroma_dir).exists():
        return None
    client = chromadb.PersistentClient(path=str(chroma_dir))
    if collection not in [c.name for c in client.list_collections()]:
        return None
    coll = client.get_collection(collection)
    data = coll.get(include=["embeddings", "documents", "metadatas"])
    if not data["ids"]:
        return None

    df = pd.DataFrame(data["metadatas"])
    df.insert(0, "id", data["ids"])
    df["text"] = data["documents"]
    df["length"] = df["text"].str.len()
    df["row"] = range(len(df))
    df = df.sort_values(["source", "chunk_index"]).reset_index(drop=True)
    vectors = np.asarray(data["embeddings"], dtype=np.float32)[df["row"].to_numpy()]
    df = df.drop(columns="row")
    _add_overlaps(df)
    return IndexSnapshot(df, vectors, coll.metadata or {})


def _add_overlaps(df: pd.DataFrame) -> None:
    """Overlap em caracteres com o chunk anterior e o seguinte do mesmo documento."""
    end = df["start_index"] + df["length"]
    same_prev = df["source"].eq(df["source"].shift(1))
    same_next = df["source"].eq(df["source"].shift(-1))
    df["overlap_prev"] = np.where(same_prev, (end.shift(1) - df["start_index"]).clip(lower=0), 0).astype(int)
    df["overlap_next"] = np.where(same_next, (end - df["start_index"].shift(-1)).clip(lower=0), 0).astype(int)
    df["overlap_count"] = (df["overlap_prev"] > 0).astype(int) + (df["overlap_next"] > 0).astype(int)


def pca_fit(vectors: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Média e 2 componentes principais (SVD do numpy), para projetar outros vetores no mesmo mapa."""
    mean = vectors.mean(axis=0)
    _, _, vt = np.linalg.svd(vectors - mean, full_matrices=False)
    return mean, vt[:2]


def project_2d(vectors: np.ndarray, basis: tuple[np.ndarray, np.ndarray] | None = None) -> np.ndarray:
    """PCA em 2 dimensões, para o mapa dos embeddings."""
    mean, components = basis or pca_fit(vectors)
    return (np.atleast_2d(vectors) - mean) @ components.T


def explained_variance(vectors: np.ndarray, k: int = 2) -> float:
    centered = vectors - vectors.mean(axis=0)
    s = np.linalg.svd(centered, compute_uv=False) ** 2
    return float(s[:k].sum() / s.sum())


def nearest_neighbors(vectors: np.ndarray, index: int, k: int = 5) -> list[tuple[int, float]]:
    """Os k chunks mais parecidos (similaridade de cosseno), sem o próprio chunk."""
    norm = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)
    sims = norm @ norm[index]
    order = [i for i in np.argsort(-sims) if i != index][:k]
    return [(int(i), float(sims[i])) for i in order]
