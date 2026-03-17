from typing import List, Dict, Any, Optional
import chromadb
from app.core.config import settings


def retrieve_context(
    collection: chromadb.Collection,
    query_text: str,
    n_results: int = None,
    where: Optional[Dict[str, Any]] = None,
    where_document: Optional[Dict[str, Any]] = None
) -> List[str]:
    """
    ค้นหาและดึงข้อมูลที่เกี่ยวข้องจาก ChromaDB
    
    Args:
        collection: ChromaDB Collection instance
        query_text: ข้อความที่ต้องการค้นหา
        n_results: จำนวนผลลัพธ์ที่ต้องการ
        where: metadata filters (optional)
        where_document: document content filters (optional)
        
    Returns:
        รายการของเอกสารที่เกี่ยวข้อง
    """
    if n_results is None:
        n_results = settings.DEFAULT_N_RESULTS

    results = collection.query(
        query_texts=[query_text],
        n_results=n_results,
        where=where,
        where_document=where_document
    )

    # คืนค่าเฉพาะเนื้อหาข้อความ
    return results['documents'][0] if results['documents'] else []


def format_context(documents: List[str], separator: str = "\n---\n") -> str:
    """
    จัดรูปแบบเอกสารที่ได้จาการค้นหาให้เป็น context string
    
    Args:
        documents: รายการของเอกสาร
        separator: ตัวแบ่งระหว่างเอกสาร
        
    Returns:
        Context string ที่จัดรูปแบบแล้ว
    """
    if not documents:
        return "ไม่พบข้อมูลเพิ่มเติมในฐานความรู้ส่วนตัว"
    
    return separator.join(documents)


def retrieve_with_scores(
    collection: chromadb.Collection,
    query_text: str,
    n_results: int = None
) -> List[Dict[str, Any]]:
    """
    ค้นหาพร้อมคะแนนความเกี่ยวข้อง
    
    Args:
        collection: ChromaDB Collection instance
        query_text: ข้อความที่ต้องการค้นหา
        n_results: จำนวนผลลัพธ์
        
    Returns:
        รายการของ dict ที่มี document, metadata, และ distance score
    """
    if n_results is None:
        n_results = settings.DEFAULT_N_RESULTS

    results = collection.query(
        query_texts=[query_text],
        n_results=n_results,
        include=['documents', 'metadatas', 'distances']
    )
    
    if not results['documents'][0]:
        return []
    
    return [
        {
            "document": doc,
            "metadata": meta,
            "distance": dist
        }
        for doc, meta, dist in zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        )
    ]
