"""Unit tests for EmbeddingService."""

from unittest.mock import MagicMock, patch

from agent_workbench.services.embedding_service import EmbeddingService


def _make_service() -> EmbeddingService:
    return EmbeddingService()


# --- lazy init ---


def test_embedding_service_does_not_load_model_on_init():
    svc = _make_service()
    assert svc._model is None


def test_embedding_service_loads_model_on_first_embed():
    svc = _make_service()
    mock_model = MagicMock()
    mock_model.encode.return_value = MagicMock(tolist=lambda: [0.1] * 384)
    # SentenceTransformer is lazily imported inside _ensure_init — patch it there
    with patch("sentence_transformers.SentenceTransformer", return_value=mock_model):
        svc.embed("hello")
    assert svc._model is mock_model


# --- embed ---


def test_embed_returns_list_of_floats():
    svc = _make_service()
    mock_model = MagicMock()
    import numpy as np

    mock_model.encode.return_value = np.array([0.1] * 384)
    with patch.object(svc, "_ensure_init"):
        svc._model = mock_model
        result = svc.embed("test text")
    assert isinstance(result, list)
    assert len(result) == 384
    assert all(isinstance(v, float) for v in result)


# --- embed_batch ---


def test_embed_batch_returns_n_lists():
    svc = _make_service()
    mock_model = MagicMock()
    import numpy as np

    mock_model.encode.return_value = np.array([[0.1] * 384, [0.2] * 384, [0.3] * 384])
    with patch.object(svc, "_ensure_init"):
        svc._model = mock_model
        result = svc.embed_batch(["a", "b", "c"])
    assert len(result) == 3
    assert all(len(v) == 384 for v in result)


# --- cosine_similarity ---


def test_cosine_similarity_identical_vectors():
    svc = _make_service()
    vec = [1.0, 0.0, 0.0]
    scores = svc.cosine_similarity(vec, [vec])
    assert abs(scores[0] - 1.0) < 1e-6


def test_cosine_similarity_orthogonal_vectors():
    svc = _make_service()
    query = [1.0, 0.0, 0.0]
    chunk = [0.0, 1.0, 0.0]
    scores = svc.cosine_similarity(query, [chunk])
    assert abs(scores[0]) < 1e-6


def test_cosine_similarity_returns_one_score_per_chunk():
    svc = _make_service()
    query = [1.0, 0.0]
    chunks = [[1.0, 0.0], [0.0, 1.0], [0.5, 0.5]]
    scores = svc.cosine_similarity(query, chunks)
    assert len(scores) == 3


def test_cosine_similarity_higher_for_closer_vector():
    svc = _make_service()
    query = [1.0, 0.0]
    close = [0.9, 0.1]
    far = [0.1, 0.9]
    scores = svc.cosine_similarity(query, [close, far])
    assert scores[0] > scores[1]
