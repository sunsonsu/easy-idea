"""
ChromaDB Service
จัดการ Vector Database operations
"""

import os
import chromadb
from typing import Dict, List, Optional, Any

# Import จาก RAG module ที่แยกไว้แล้ว
from app.rag.embeddings import GeminiEmbeddingFunction
from app.rag.chunking import split_text
from app.utils.logger import get_logger
from app.core.config import settings

# Initialize logger
logger = get_logger(__name__)

# Initialize ChromaDB Client
chroma_client = chromadb.HttpClient(
    host=settings.CHROMA_HOST,
    port=settings.CHROMA_PORT
)

# Initialize Embedding Function
google_ef = GeminiEmbeddingFunction(api_key=settings.GEMINI_API_KEY)

# Get or Create Collection
collection = chroma_client.get_or_create_collection(
    name=settings.CHROMA_COLLECTION_NAME,
    embedding_function=google_ef
)

def upsert_knowledge(
    text: str,
    metadata: Optional[Dict[str, Any]] = None,
    chunk_size: int = None,
    chunk_overlap: int = None
) -> int:
    """
    บันทึกความรู้ใหม่ลง ChromaDB
    
    Args:
        text: ข้อความที่ต้องการบันทึก
        metadata: metadata เพิ่มเติม
        chunk_size: ขนาดของแต่ละ chunk
        chunk_overlap: ความทับซ้อนระหว่าง chunks
        
    Returns:
        จำนวน chunks ที่บันทึก
    """
    try:
        if chunk_size is None:
            chunk_size = settings.DEFAULT_CHUNK_SIZE
        if chunk_overlap is None:
            chunk_overlap = settings.DEFAULT_CHUNK_OVERLAP

        logger.info(f"Starting knowledge ingestion, text length: {len(text)}")

        # แบ่งข้อความเป็น chunks โดยใช้ฟังก์ชันจาก RAG module
        chunks = split_text(text, chunk_size, chunk_overlap)
        
        logger.info(f"Split into {len(chunks)} chunks")
        
        # สร้าง IDs ที่ unique
        ids = [f"id_{i}_{os.urandom(4).hex()}" for i in range(len(chunks))]
        
        # เพิ่ม timestamp ใน metadata
        from datetime import datetime
        enriched_metadata = metadata or {}
        enriched_metadata['ingested_at'] = datetime.now().isoformat()
        
        # บันทึกลงฐานข้อมูล
        collection.upsert(
            documents=chunks,
            ids=ids,
            metadatas=[enriched_metadata for _ in chunks]
        )
        
        logger.info(f"Successfully ingested {len(chunks)} chunks")
        return len(chunks)
        
    except Exception as e:
        logger.error(f"Error during knowledge ingestion: {str(e)}")
        raise


def query_knowledge(
    query_text: str,
    n_results: int = None,
    where: Optional[Dict[str, Any]] = None
) -> List[str]:
    """
    ค้นหาความรู้ที่เกี่ยวข้องที่สุด
    
    Args:
        query_text: ข้อความที่ต้องการค้นหา
        n_results: จำนวนผลลัพธ์
        where: metadata filters
        
    Returns:
        รายการของเอกสารที่เกี่ยวข้อง
    """
    try:
        logger.info(f"Querying knowledge base: '{query_text[:50]}...'")
        
        results = collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=where
        )
        
        documents = results['documents'][0] if results['documents'] else []
        logger.info(f"Found {len(documents)} relevant documents")
        
        return documents
        
    except Exception as e:
        logger.error(f"Error during knowledge query: {str(e)}")
        return []


def get_collection_stats() -> Dict[str, Any]:
    """
    ดึงสถิติของ collection
    
    Returns:
        Dict ที่มีข้อมูลสถิติ
    """
    try:
        count = collection.count()
        return {
            "collection_name": collection.name,
            "total_documents": count,
            "status": "healthy"
        }
    except Exception as e:
        logger.error(f"Error getting collection stats: {str(e)}")
        return {
            "collection_name": settings.CHROMA_COLLECTION_NAME,
            "error": str(e),
            "status": "error"
        }


def list_documents(
    limit: int = 50,
    offset: int = 0,
    where: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    ดึงรายการเอกสารจาก collection

    Args:
        limit: จำนวนเอกสารสูงสุด
        offset: ตำแหน่งเริ่มต้น
        where: metadata filter

    Returns:
        Dict ที่มี documents, metadatas, ids
    """
    try:
        kwargs: Dict[str, Any] = {"limit": limit, "offset": offset, "include": ["documents", "metadatas"]}
        if where:
            kwargs["where"] = where
        results = collection.get(**kwargs)
        return {
            "ids": results.get("ids", []),
            "documents": results.get("documents", []),
            "metadatas": results.get("metadatas", []),
        }
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        return {"ids": [], "documents": [], "metadatas": []}


def delete_collection() -> bool:
    """
    ลบ collection (ใช้ระมัดระวัง!)
    
    Returns:
        True ถ้าสำเร็จ
    """
    try:
        chroma_client.delete_collection(name=settings.CHROMA_COLLECTION_NAME)
        logger.warning("Collection deleted!")
        return True
    except Exception as e:
        logger.error(f"Error deleting collection: {str(e)}")
        return False