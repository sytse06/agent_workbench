"""EmbeddingService — lazy-loaded SentenceTransformer wrapper."""

import logging

import numpy as np

logger = logging.getLogger(__name__)

_MODEL_NAME = "all-MiniLM-L6-v2"


class EmbeddingService:
    """Wraps SentenceTransformer with lazy init and cosine similarity helper.

    The model (~80MB) is downloaded on first use. Pass model_name to swap to
    a different model (e.g. paraphrase-multilingual-MiniLM-L12-v2 for Dutch).
    """

    def __init__(self, model_name: str = _MODEL_NAME) -> None:
        self._model_name = model_name
        self._model = None  # lazy — loads on first embed() call

    def _ensure_init(self) -> None:
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self._model_name)
            logger.info("EmbeddingService loaded: %s", self._model_name)

    def embed(self, text: str) -> list[float]:
        self._ensure_init()
        return self._model.encode(text, convert_to_numpy=True).tolist()  # type: ignore[attr-defined]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        self._ensure_init()
        return self._model.encode(texts, convert_to_numpy=True).tolist()  # type: ignore[attr-defined]

    def cosine_similarity(
        self, query_vec: list[float], chunk_vecs: list[list[float]]
    ) -> list[float]:
        q = np.array(query_vec)
        c = np.array(chunk_vecs)
        q_norm = q / (np.linalg.norm(q) + 1e-10)
        c_norm = c / (np.linalg.norm(c, axis=1, keepdims=True) + 1e-10)
        return (c_norm @ q_norm).tolist()
