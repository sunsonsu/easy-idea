import os
import chromadb
from typing import Dict, List, Optional, Any

from app.rag.embeddings import GeminiEmbeddingFunction
from app.rag.chunking import split_text
from app.utils.logger import get_logger
from app.core.config import settings

logger = get_logger(__name__)

_chroma_client = None
_collection = None
_init_error = None


def _get_collection():
    global _chroma_client, _collection, _init_error

    if _collection is not None:
        return _collection
    if _init_error is not None:
        return None

    try:
        _chroma_client = chromadb.HttpClient(
            host=settings.CHROMA_HOST,
            port=settings.CHROMA_PORT
        )
        google_ef = GeminiEmbeddingFunction(api_key=settings.GEMINI_API_KEY)
        _collection = _chroma_client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION_NAME,
            embedding_function=google_ef
        )
        logger.info("Chroma collection initialized")
        return _collection
    except Exception as e:
        _init_error = e
        logger.error(f"Chroma unavailable during initialization: {str(e)}")
        return None

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
        collection = _get_collection()
        if collection is None:
            raise RuntimeError(f"Chroma unavailable: {_init_error}")

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
        collection = _get_collection()
        if collection is None:
            logger.warning("Chroma unavailable, returning empty query results")
            return []

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
        collection = _get_collection()
        if collection is None:
            return {
                "collection_name": settings.CHROMA_COLLECTION_NAME,
                "total_documents": 0,
                "status": "unavailable",
                "error": str(_init_error) if _init_error else "Chroma not initialized"
            }

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
        collection = _get_collection()
        if collection is None:
            return {"ids": [], "documents": [], "metadatas": []}

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


def list_daily_trends(limit: int = 30) -> List[Dict[str, Any]]:
    """
    ดึงรายการ daily trends ที่ generate ไว้แล้ว
    
    Args:
        limit: จำนวนสูงสุด
        
    Returns:
        รายการ daily trends พร้อม metadata
    """
    try:
        collection = _get_collection()
        if collection is None:
            return []

        # ดึง documents ที่มี type = "daily_trend"
        results = collection.get(
            where={"type": "daily_trend"},
            limit=limit,
            include=["metadatas", "documents"]
        )
        
        if not results or not results.get("metadatas"):
            return []
        
        # Group by date และเก็บเฉพาะข้อมูลที่จำเป็น
        trends_by_date = {}
        for idx, metadata in enumerate(results["metadatas"]):
            date = metadata.get("date", "Unknown")
            if date not in trends_by_date:
                trends_by_date[date] = {
                    "date": date,
                    "topic": metadata.get("topic", "Daily Trend"),
                    "doc_url": metadata.get("doc_url", ""),
                    "source": metadata.get("source", ""),
                    "preview": results["documents"][idx][:200] if idx < len(results["documents"]) else ""
                }
        
        # แปลงเป็น list และเรียงตามวันที่ล่าสุด
        trends = list(trends_by_date.values())
        # เรียงตาม date (ถ้า format เป็น DD Mon YYYY)
        trends.sort(key=lambda x: x["date"], reverse=True)
        
        logger.info(f"Found {len(trends)} daily trends")
        return trends
        
    except Exception as e:
        logger.error(f"Error listing daily trends: {str(e)}")
        return []


def delete_collection() -> bool:
    """
    ลบ collection (ใช้ระมัดระวัง!)
    
    Returns:
        True ถ้าสำเร็จ
    """
    try:
        global _chroma_client, _collection, _init_error
        if _chroma_client is None:
            _ = _get_collection()
        if _chroma_client is None:
            logger.warning("Delete collection requested while Chroma unavailable")
            return False

        _chroma_client.delete_collection(name=settings.CHROMA_COLLECTION_NAME)
        _collection = None
        _init_error = None
        logger.warning("Collection deleted!")
        return True
    except Exception as e:
        logger.error(f"Error deleting collection: {str(e)}")
        return False