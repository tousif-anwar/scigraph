"""Local vector-style index over publication text.

The preferred production backends are Chroma or FAISS when they are installed.
For this course project environment, the command stays runnable by falling back
to a persisted scikit-learn TF-IDF nearest-neighbor index.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import pickle
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
from scipy.sparse import save_npz
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors

from scigraph.utils.config import load_config, resolve_project_path


def backend_available(module_name: str) -> bool:
    """Return whether an optional vector backend can be imported."""
    return importlib.util.find_spec(module_name) is not None


def choose_backend(requested_backend: str) -> str:
    """Choose a backend, preferring installed FAISS/Chroma when requested or automatic."""
    normalized = requested_backend.lower().strip()
    if normalized not in {"auto", "chroma", "faiss", "sklearn_tfidf_fallback"}:
        raise ValueError(f"Unsupported vector backend: {requested_backend}")
    if normalized in {"auto", "chroma"} and backend_available("chromadb"):
        return "chroma"
    if normalized in {"auto", "faiss"} and backend_available("faiss"):
        return "faiss"
    if normalized in {"chroma", "faiss"}:
        return "sklearn_tfidf_fallback"
    return "sklearn_tfidf_fallback"


def normalize_query(text: str) -> str:
    """Normalize whitespace in a query before searching the saved index."""
    return " ".join(text.split())


def _path(config: dict[str, Any], key: str) -> Path:
    return resolve_project_path(config, config["paths"][key])


def load_documents(config: dict[str, Any]) -> pd.DataFrame:
    """Load text documents from the Gold text-document Parquet output."""
    max_documents = int(config["spark"].get("vector_index", {}).get("max_documents", 5000))
    columns = ["paper_id", "title", "publication_year", "language", "document_text"]
    frame = pd.read_parquet(_path(config, "text_documents"), columns=columns)
    frame = frame.dropna(subset=["document_text"])
    frame["document_text"] = frame["document_text"].astype(str)
    frame = frame[frame["document_text"].str.strip() != ""]
    return frame.head(max_documents).reset_index(drop=True)


def write_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    """Write vector-index JSON and Markdown reports."""
    json_path = _path(config, "vector_index_report_json")
    markdown_path = _path(config, "vector_index_report_md")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    lines = [
        "# Vector Index",
        "",
        f"Generated on {date.today().isoformat()}.",
        "",
        "## Summary",
        "",
        f"- Status: {payload.get('status')}",
        f"- Backend used: {payload.get('backend')}",
        f"- Documents indexed: {payload.get('document_count')}",
        f"- Vocabulary size: {payload.get('vocabulary_size')}",
        f"- Neighbors stored per query: {payload.get('n_neighbors')}",
        "",
        "## Output Artifacts",
        "",
    ]
    for name, path in payload.get("artifacts", {}).items():
        lines.append(f"- {name}: `{path}`")
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "The project now has a persisted nearest-neighbor index over paper title and abstract text. If Chroma or FAISS is installed later, the backend selector can be extended without changing downstream report paths; this run used the portable scikit-learn fallback available in the current environment.",
        ]
    )
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_vector_index(config: dict[str, Any]) -> dict[str, Any]:
    """Build and persist the configured vector-style text index."""
    index_dir = _path(config, "vector_index_dir")
    index_dir.mkdir(parents=True, exist_ok=True)
    settings = config["spark"].get("vector_index", {})
    backend = choose_backend(str(settings.get("backend", "auto")))
    max_features = int(settings.get("max_features", 20000))
    n_neighbors = int(settings.get("n_neighbors", 10))

    documents = load_documents(config)
    if documents.empty:
        payload = {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": "empty",
            "backend": backend,
            "document_count": 0,
            "vocabulary_size": 0,
            "n_neighbors": n_neighbors,
            "artifacts": {},
        }
        write_report(config, payload)
        return payload

    texts = (documents["title"].fillna("") + "\n" + documents["document_text"].fillna("")).tolist()
    vectorizer = TfidfVectorizer(max_features=max_features, stop_words="english", norm="l2")
    matrix = vectorizer.fit_transform(texts)
    neighbors = NearestNeighbors(n_neighbors=min(n_neighbors, len(documents)), metric="cosine")
    neighbors.fit(matrix)

    matrix_path = index_dir / "tfidf_matrix.npz"
    vectorizer_path = index_dir / "tfidf_vectorizer.pkl"
    neighbors_path = index_dir / "nearest_neighbors.pkl"
    documents_path = index_dir / "documents.jsonl"
    metadata_path = index_dir / "metadata.json"

    save_npz(matrix_path, matrix)
    vectorizer_path.write_bytes(pickle.dumps(vectorizer))
    neighbors_path.write_bytes(pickle.dumps(neighbors))
    documents[["paper_id", "title", "publication_year", "language"]].to_json(
        documents_path, orient="records", lines=True
    )

    metadata = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "backend": backend,
        "document_count": int(len(documents)),
        "vocabulary_size": int(len(vectorizer.vocabulary_)),
        "max_features": max_features,
        "n_neighbors": int(min(n_neighbors, len(documents))),
    }
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")

    payload = {
        **metadata,
        "status": "success",
        "artifacts": {
            "matrix": str(matrix_path),
            "vectorizer": str(vectorizer_path),
            "neighbors": str(neighbors_path),
            "documents": str(documents_path),
            "metadata": str(metadata_path),
        },
    }
    write_report(config, payload)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/dev.yaml")
    args = parser.parse_args()
    payload = build_vector_index(load_config(Path(args.config)))
    print(
        json.dumps(
            {
                "status": payload["status"],
                "backend": payload.get("backend"),
                "document_count": payload.get("document_count"),
                "vocabulary_size": payload.get("vocabulary_size"),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
