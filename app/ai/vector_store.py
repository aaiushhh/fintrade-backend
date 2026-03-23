"""In-memory vector store — fallback when Milvus is not available."""

from typing import List, Tuple

import numpy as np

from app.utils.logger import get_logger

logger = get_logger(__name__)


class InMemoryVectorStore:
    """Simple in-memory vector similarity search using cosine similarity."""

    def __init__(self):
        self._documents: List[dict] = []  # {"id", "text", "embedding", "metadata"}
        self._embeddings: List[np.ndarray] = []

    def add_documents(self, documents: List[dict]) -> None:
        """Add documents with pre-computed embeddings."""
        for doc in documents:
            embedding = np.array(doc["embedding"], dtype=np.float32)
            self._documents.append({
                "id": doc.get("id", len(self._documents)),
                "text": doc["text"],
                "metadata": doc.get("metadata", {}),
            })
            self._embeddings.append(embedding)
        logger.info("documents_added", count=len(documents), total=len(self._documents))

    def search(self, query_embedding: List[float], top_k: int = 5) -> List[Tuple[dict, float]]:
        """Find the top_k most similar documents using cosine similarity."""
        if not self._embeddings:
            return []

        query_vec = np.array(query_embedding, dtype=np.float32)
        query_norm = np.linalg.norm(query_vec)
        if query_norm == 0:
            return []
        query_vec = query_vec / query_norm

        similarities = []
        for i, emb in enumerate(self._embeddings):
            emb_norm = np.linalg.norm(emb)
            if emb_norm == 0:
                similarities.append(0.0)
            else:
                cos_sim = float(np.dot(query_vec, emb / emb_norm))
                similarities.append(cos_sim)

        # Sort by similarity descending
        ranked = sorted(enumerate(similarities), key=lambda x: x[1], reverse=True)
        results = []
        for idx, score in ranked[:top_k]:
            results.append((self._documents[idx], score))
        return results

    @property
    def count(self) -> int:
        return len(self._documents)

    def clear(self) -> None:
        self._documents.clear()
        self._embeddings.clear()


# Global singleton
vector_store = InMemoryVectorStore()
