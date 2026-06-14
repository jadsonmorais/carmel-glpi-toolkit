"""
Singleton do modelo sentence-transformers.
Modelo: paraphrase-multilingual-mpnet-base-v2
  - Suporte nativo a PT-BR
  - ~420MB no primeiro download (cache em ~/.cache/torch/sentence_transformers/)
  - Sem dependências de API externa
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

_MODEL_NAME = "paraphrase-multilingual-mpnet-base-v2"
_model = None


def get_embedder():
    """Carrega o modelo uma vez por processo (singleton)."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError(
                "sentence-transformers não instalado. Execute:\n"
                "  pip install sentence-transformers"
            )
        print(f"[RAG] Carregando modelo {_MODEL_NAME}...")
        _model = SentenceTransformer(_MODEL_NAME)
        print("[RAG] Modelo pronto.")
    return _model


def embed(text: str) -> list[float]:
    """Gera embedding normalizado para um único texto."""
    return get_embedder().encode(text, normalize_embeddings=True).tolist()


def embed_batch(texts: list[str]) -> list[list[float]]:
    """Gera embeddings normalizados em lote (mais eficiente para muitos textos)."""
    return get_embedder().encode(
        texts,
        normalize_embeddings=True,
        batch_size=32,
        show_progress_bar=len(texts) > 20,
    ).tolist()
