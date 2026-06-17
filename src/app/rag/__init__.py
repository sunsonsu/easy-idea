"""
RAG (Retrieval-Augmented Generation) Module
ประกอบด้วย:
- embeddings: การสร้าง embeddings จาก Gemini
- chunking: การแบ่งข้อความเป็น chunks
- retrieval: การจัดรูปแบบ context ที่เกี่ยวข้อง
- prompts: Template สำหรับ prompts
"""

from .chunking import get_text_splitter
from .retrieval import format_context
from .prompts import RAGPromptTemplate

__all__ = [
    "get_text_splitter",
    "format_context",
    "RAGPromptTemplate"
]
