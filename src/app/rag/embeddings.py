from typing import Optional

from google.genai import Client
from google.genai import types
from app.core.config import settings


def _embed_config() -> types.EmbedContentConfig:
    # Cap output dim to fit Firestore's vector index (<=2048). Same dim must be
    # used for ingest, query, and the index (settings.EMBEDDING_DIMENSION).
    return types.EmbedContentConfig(output_dimensionality=settings.EMBEDDING_DIMENSION)

# Cache one client at module scope. A per-call temporary gets GC'd mid-request,
# closing its httpx client, which breaks tenacity's retry
# ("Cannot send a request, as the client has been closed").
_cached_client: Optional[Client] = None


def _client() -> Client:
    """สร้าง/คืน Gemini Client (singleton) จาก API key ใน settings"""
    global _cached_client
    if _cached_client is None:
        _cached_client = Client(api_key=settings.GEMINI_API_KEY)
    return _cached_client


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    สร้าง embedding vectors สำหรับหลายข้อความ

    Args:
        texts: รายการของข้อความ

    Returns:
        รายการของ embedding vectors (หนึ่ง vector ต่อหนึ่งข้อความ)
    """
    response = _client().models.embed_content(
        model=settings.GEMINI_EMBEDDING_MODEL,
        contents=texts,
        config=_embed_config()
    )
    return [item.values for item in response.embeddings]


def embed_query(text: str) -> list[float]:
    """
    สร้าง embedding vector สำหรับข้อความเดียว (query)

    Args:
        text: ข้อความที่ต้องการ embed

    Returns:
        embedding vector เดียว
    """
    response = _client().models.embed_content(
        model=settings.GEMINI_EMBEDDING_MODEL,
        contents=text,
        config=_embed_config()
    )
    return response.embeddings[0].values
