from google.genai import Client
from chromadb.api.types import EmbeddingFunction, Documents, Embeddings
from app.core.config import settings

class GeminiEmbeddingFunction(EmbeddingFunction):
    def __init__(self, api_key: str):
        """
        Args:
            api_key: Google Gemini API Key
        """
        
        self.client = Client(api_key=api_key)
        self.model = settings.GEMINI_EMBEDDING_MODEL

    def __call__(self, input: Documents) -> Embeddings:
        """
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
