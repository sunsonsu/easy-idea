# NOTE: This module is now Firestore-backed (Google Cloud Firestore vector search),
# not ChromaDB. Filename kept as chroma_service.py so existing callers/imports work.
import os
from typing import Dict, List, Optional, Any

from app.rag.embeddings import embed_texts, embed_query
from app.rag.chunking import split_text
from app.utils.logger import get_logger
from app.core.config import settings

logger = get_logger(__name__)

_firestore_client = None
_collection = None
_init_error = None


def _get_collection():
    """
    Lazily initialize the Firestore client + collection reference.

    Auth uses Application Default Credentials (ADC). If Firestore (or the
    firestore library) is unavailable, we record the error and return None so
    the app keeps booting and callers degrade gracefully (empty results /
    unavailable status) — mirroring the previous Chroma resilience pattern.
    """
    global _firestore_client, _collection, _init_error

    if _collection is not None:
        return _collection
    if _init_error is not None:
        return None

    try:
        # Lazy import so the app boots even if google-cloud-firestore is absent.
        from google.cloud import firestore

        kwargs: Dict[str, Any] = {"database": settings.FIRESTORE_DATABASE}
        if settings.GOOGLE_CLOUD_PROJECT:
            kwargs["project"] = settings.GOOGLE_CLOUD_PROJECT
        _firestore_client = firestore.Client(**kwargs)
        _collection = _firestore_client.collection(settings.FIRESTORE_COLLECTION)
        logger.info("Firestore collection initialized")
        return _collection
    except Exception as e:
        _init_error = e
        logger.error(f"Firestore unavailable during initialization: {str(e)}")
        return None


def upsert_knowledge(
    text: str,
    metadata: Optional[Dict[str, Any]] = None,
    chunk_size: int = None,
    chunk_overlap: int = None
) -> int:
    """
    บันทึกความรู้ใหม่ลง Firestore

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
            raise RuntimeError(f"Firestore unavailable: {_init_error}")

        from google.cloud.firestore_v1.vector import Vector

        if chunk_size is None:
            chunk_size = settings.DEFAULT_CHUNK_SIZE
        if chunk_overlap is None:
            chunk_overlap = settings.DEFAULT_CHUNK_OVERLAP

        logger.info(f"Starting knowledge ingestion, text length: {len(text)}")

        # แบ่งข้อความเป็น chunks โดยใช้ฟังก์ชันจาก RAG module
        chunks = split_text(text, chunk_size, chunk_overlap)

        logger.info(f"Split into {len(chunks)} chunks")

        # สร้าง embedding ของแต่ละ chunk
        embeddings = embed_texts(chunks)

        # เพิ่ม timestamp ใน metadata
        from datetime import datetime
        enriched_metadata = metadata or {}
        ingested_at = datetime.now().isoformat()
        enriched_metadata['ingested_at'] = ingested_at

        # บันทึกลงฐานข้อมูลแบบ batch (Firestore auto-id ต่อ document)
        batch = _firestore_client.batch()
        for chunk, embedding in zip(chunks, embeddings):
            doc_ref = collection.document()  # auto-id
            batch.set(doc_ref, {
                "text": chunk,
                "embedding": Vector(embedding),
                "metadata": enriched_metadata,
                "ingested_at": ingested_at,
            })
        batch.commit()

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
    ค้นหาความรู้ที่เกี่ยวข้องที่สุด (Firestore vector search)

    Args:
        query_text: ข้อความที่ต้องการค้นหา
        n_results: จำนวนผลลัพธ์
        where: metadata filters (ไม่รองรับใน vector path นี้ — log ถ้าส่งมา)

    Returns:
        รายการของเอกสารที่เกี่ยวข้อง
    """
    try:
        collection = _get_collection()
        if collection is None:
            logger.warning("Firestore unavailable, returning empty query results")
            return []

        if where:
            logger.warning(f"query_knowledge received `where` filter, ignoring it: {where}")

        if n_results is None:
            n_results = settings.DEFAULT_N_RESULTS

        from google.cloud.firestore_v1.vector import Vector
        from google.cloud.firestore_v1.base_vector_query import DistanceMeasure

        logger.info(f"Querying knowledge base: '{query_text[:50]}...'")

        query_vector = embed_query(query_text)

        vector_query = collection.find_nearest(
            vector_field="embedding",
            query_vector=Vector(query_vector),
            distance_measure=DistanceMeasure.COSINE,
            limit=n_results,
        )

        documents = [doc.get("text") for doc in vector_query.stream()]
        logger.info(f"Found {len(documents)} relevant documents")

        return documents

    except Exception as e:
        logger.error(f"Error during knowledge query: {str(e)}")
        return []


def get_collection_stats() -> Dict[str, Any]:
    """
    ดึงสถิติของ collection (ใช้ aggregate count())

    Returns:
        Dict ที่มีข้อมูลสถิติ
    """
    try:
        collection = _get_collection()
        if collection is None:
            return {
                "collection_name": settings.FIRESTORE_COLLECTION,
                "total_documents": 0,
                "status": "unavailable",
                "error": str(_init_error) if _init_error else "Firestore not initialized"
            }

        agg = collection.count().get()
        # aggregate result shape: [[AggregationResult]]
        count = int(agg[0][0].value)
        return {
            "collection_name": settings.FIRESTORE_COLLECTION,
            "total_documents": count,
            "status": "healthy"
        }
    except Exception as e:
        logger.error(f"Error getting collection stats: {str(e)}")
        return {
            "collection_name": settings.FIRESTORE_COLLECTION,
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
        where: metadata filter (ไม่รองรับ — log ถ้าส่งมา)

    Returns:
        Dict ที่มี documents, metadatas, ids
    """
    try:
        collection = _get_collection()
        if collection is None:
            return {"ids": [], "documents": [], "metadatas": []}

        if where:
            logger.warning(f"list_documents received `where` filter, ignoring it: {where}")

        # ponytail: Firestore .offset() bills the skipped reads as if they were
        # returned. Fine for this low-volume KB; revisit with cursor pagination
        # only if document counts grow large.
        query = collection.limit(limit).offset(offset)

        ids: List[str] = []
        documents: List[str] = []
        metadatas: List[Dict[str, Any]] = []
        for doc in query.stream():
            data = doc.to_dict() or {}
            ids.append(doc.id)
            documents.append(data.get("text", ""))
            metadatas.append(data.get("metadata", {}))

        return {
            "ids": ids,
            "documents": documents,
            "metadatas": metadatas,
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

        from google.cloud.firestore_v1.base_query import FieldFilter

        # ดึง documents ที่มี metadata.type == "daily_trend"
        query = collection.where(
            filter=FieldFilter("metadata.type", "==", "daily_trend")
        ).limit(limit)

        # Group by date และเก็บเฉพาะข้อมูลที่จำเป็น
        trends_by_date: Dict[str, Dict[str, Any]] = {}
        for doc in query.stream():
            data = doc.to_dict() or {}
            metadata = data.get("metadata", {}) or {}
            text = data.get("text", "") or ""
            date = metadata.get("date", "Unknown")
            if date not in trends_by_date:
                trends_by_date[date] = {
                    "date": date,
                    "topic": metadata.get("topic", "Daily Trend"),
                    "doc_url": metadata.get("doc_url", ""),
                    "source": metadata.get("source", ""),
                    "preview": text[:200]
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
    ลบเอกสารทั้งหมดใน collection (Firestore ไม่มี server-side drop —
    ต้อง batch-delete ทุก document)

    Returns:
        True ถ้าสำเร็จ
    """
    try:
        global _collection, _init_error
        collection = _get_collection()
        if collection is None:
            logger.warning("Delete collection requested while Firestore unavailable")
            return False

        # ลบเป็นชุด ๆ (Firestore batch limit ~500 ops)
        batch_size = 400
        while True:
            docs = list(collection.limit(batch_size).stream())
            if not docs:
                break
            batch = _firestore_client.batch()
            for doc in docs:
                batch.delete(doc.reference)
            batch.commit()
            if len(docs) < batch_size:
                break

        logger.warning("Collection contents deleted!")
        return True
    except Exception as e:
        logger.error(f"Error deleting collection: {str(e)}")
        return False
