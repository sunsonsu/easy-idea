"""
Embedding Functions สำหรับ RAG
รองรับการสร้าง embeddings จาก Google Gemini
"""

from google.genai import Client
from chromadb.api.types import EmbeddingFunction, Documents, Embeddings
from app.core.config import settings

class GeminiEmbeddingFunction(EmbeddingFunction):
    """
    Custom Embedding Function สำหรับ ChromaDB
    ใช้ Gemini Embedding API ในการสร้าง vector embeddings
    """
    
    def __init__(self, api_key: str):
        """
        Initialize Gemini Embedding Function
        
        Args:
            api_key: Google Gemini API Key
        """
        
        self.client = Client(api_key=api_key)
        self.model = settings.GEMINI_EMBEDDING_MODEL

    def __call__(self, input: Documents) -> Embeddings:
        """
        สร้าง embeddings จากข้อความ
        
        Args:
            input: รายการของข้อความ (Documents)
            
        Returns:
            รายการของ embedding vectors
        """
        response = self.client.models.embed_content(
            model=self.model,
            contents=input
        )
        return [item.values for item in response.embeddings]
