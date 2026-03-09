"""
RAG (Retrieval-Augmented Generation) Module
ประกอบด้วย:
- embeddings: การสร้าง embeddings จาก Gemini
- chunking: การแบ่งข้อความเป็น chunks
- retrieval: การค้นหาและดึงข้อมูลที่เกี่ยวข้อง
- prompts: Template สำหรับ prompts
"""

from .embeddings import GeminiEmbeddingFunction
from .chunking import get_text_splitter
from .retrieval import retrieve_context
from .prompts import RAGPromptTemplate

__all__ = [
    "GeminiEmbeddingFunction",
    "get_text_splitter",
    "retrieve_context",
    "RAGPromptTemplate"
]
