"""
Easy Idea RAG API
FastAPI application สำหรับระบบ RAG (Retrieval-Augmented Generation)
"""

import sys
import pathlib
# เพิ่ม src/ เข้า sys.path เมื่อรันตรงจาก root (python src/app/main.py)
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

# Import configurations และ security
from app.core.config import settings
from app.core.security import get_api_key

# Import schemas
from app.models.schemas import ContentRequest, IngestRequest

# Import services
from app.services.gemini_service import generate_with_rag, list_models
from app.services.chroma_service import upsert_knowledge, get_collection_stats, list_documents
from app.services.gdocs_service import create_doc

# Import utilities
from app.utils.logger import setup_logging, get_logger
from app.utils.formatters import format_document_title
from app.utils.validators import validate_text_length

# Setup logging
setup_logging(level=settings.LOG_LEVEL)
logger = get_logger(__name__)

# Scheduler
_scheduler = AsyncIOScheduler()

# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API สำหรับสร้างคอนเทนต์ด้วย AI และระบบ RAG พร้อมบันทึกลง Google Docs",
    version=settings.VERSION
)

# Jinja2 Templates
_template_dir = pathlib.Path(__file__).resolve().parent / "templates"
templates = Jinja2Templates(directory=str(_template_dir))
templates.env.globals["version"] = settings.VERSION


# ─────────────────────────────────────────────
# UI Pages (Jinja2 HTML)
# ─────────────────────────────────────────────

@app.get("/ui", response_class=HTMLResponse)
async def ui_home(request: Request):
    """Redirect to chat page"""
    return templates.TemplateResponse("chat.html", {"request": request})


@app.get("/ui/docs-list", response_class=HTMLResponse)
async def ui_docs_list(request: Request):
    """หน้าแสดงรายการเอกสารใน Knowledge Base"""
    return templates.TemplateResponse("docs_list.html", {"request": request})


@app.get("/ui/chat", response_class=HTMLResponse)
async def ui_chat(request: Request):
    """หน้า Chat สำหรับค้นหาและสร้างไอเดีย"""
    return templates.TemplateResponse("chat.html", {"request": request})


# ─────────────────────────────────────────────
# API for frontend
# ─────────────────────────────────────────────

@app.get("/api/knowledge/list")
async def api_knowledge_list(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    auth: str = Depends(get_api_key)
):
    """ดึงรายการเอกสารทั้งหมดจาก ChromaDB"""
    return list_documents(limit=limit, offset=offset)


@app.get("/api/models")
async def api_list_models(auth: str = Depends(get_api_key)):
    """ดึงรายการ Gemini models ที่รองรับ generateContent"""
    models = list_models()
    return {"models": models, "default": settings.GEMINI_MODEL}
    return list_documents(limit=limit, offset=offset)


@app.on_event("startup")
async def startup_event():
    """เรียกเมื่อ application เริ่มทำงาน"""
    logger.info(f"Starting {settings.PROJECT_NAME}")
    logger.info("Checking ChromaDB connection...")
    stats = get_collection_stats()
    logger.info(f"ChromaDB Status: {stats}")

    # เริ่ม scheduler — รัน daily job ทุกวันตอน 07:00
    _scheduler.add_job(
        run_daily_job,
        trigger=CronTrigger(hour=7, minute=0),
        id="daily_content_trend",
        replace_existing=True
    )
    _scheduler.start()
    logger.info("Scheduler started — daily job scheduled at 07:00 every day")


@app.on_event("shutdown")
async def shutdown_event():
    """เรียกเมื่อ application ปิดทำงาน"""
    _scheduler.shutdown(wait=False)
    logger.info(f"Shutting down {settings.PROJECT_NAME}")


@app.get("/")
def read_root():
    """Health check endpoint"""
    return {
        "status": "Easy Idea RAG OK!", 
        "version": settings.VERSION,
        "auth": "API Key Required",
        "project": settings.PROJECT_NAME
    }


@app.get("/health")
async def health_check():
    """
    ตรวจสอบสถานะของระบบ
    """
    try:
        stats = get_collection_stats()
        return {
            "status": "healthy",
            "chroma_db": stats,
            "timestamp": datetime.datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )


@app.post("/ingest")
async def ingest_data(req: IngestRequest, auth: str = Depends(get_api_key)):
    """
    รับข้อมูลความรู้ใหม่ และบันทึกลง ChromaDB
    
    Args:
        req: IngestRequest ที่มี text และ source
        auth: API key authentication
        
    Returns:
        ผลการบันทึกข้อมูล
    """
    try:
        logger.info(f"Ingesting data from source: {req.source}")
        
        # Validate ความยาวของข้อความ
        validate_text_length(req.text, min_length=10, max_length=50000, field_name="text")
        
        # บันทึกลง ChromaDB
        chunks_count = upsert_knowledge(
            text=req.text,
            metadata={"source": req.source}
        )
        
        return {
            "message": f"Successfully ingested {chunks_count} chunks.",
            "status": "success",
            "source": req.source,
            "chunks": chunks_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in ingest endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@app.post("/generate")
async def generate_content(req: ContentRequest, auth: str = Depends(get_api_key)):
    """
    สร้างคอนเทนต์โดยใช้ RAG (ค้นหาความรู้ส่วนตัวก่อนตอบ)
    
    Args:
        req: ContentRequest ที่มี topic, use_google_search, save_to_docs
        auth: API key authentication
        
    Returns:
        ผลลัพธ์การสร้างคอนเทนต์
    """
    try:
        logger.info(f"Generating content for topic: '{req.topic[:50]}...'")
        
        # Validate ความยาวของ topic
        validate_text_length(req.topic, min_length=5, max_length=500, field_name="topic")
        
        # 1. รันกระบวนการ RAG
        result = generate_with_rag(req.topic, use_search=req.use_google_search, model=req.model)
        result_text = result["answer"]
        
        doc_url = None
        
        # 2. บันทึกลง Google Docs หากผู้ใช้ต้องการ
        if req.save_to_docs:
            logger.info("Saving to Google Docs")
            doc_title = format_document_title(
                prefix="RAG_Report",
                topic=req.topic[:30],
                include_timestamp=True
            )
            doc_url = create_doc(doc_title, result_text)
            
            if doc_url:
                logger.info(f"Document saved: {doc_url}")
            else:
                logger.warning("Failed to save document to Google Docs")
        
        # 3. บันทึกผลลัพธ์กลับเข้า ChromaDB หากผู้ใช้ต้องการ
        ingested_chunks = 0
        if req.save_to_knowledge:
            try:
                logger.info("Saving generated content to ChromaDB")
                ingested_chunks = upsert_knowledge(
                    text=result_text,
                    metadata={
                        "source": f"generated:{req.topic[:50]}",
                        "type": "ai_generated"
                    }
                )
                logger.info(f"Ingested {ingested_chunks} chunks back to knowledge base")
            except Exception as e:
                logger.error(f"Failed to ingest generated content: {str(e)}")
        
        return {
            "topic": req.topic,
            "ai_response": result_text,
            "references": result["references"],
            "context_used": result.get("context_used", False),
            "google_docs_url": doc_url,
            "ingested_chunks": ingested_chunks
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in generate endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@app.post("/daily-job")
async def daily_job(auth: str = Depends(get_api_key)):
    """
    Trigger daily job ด้วยตนเอง (สำหรับทดสอบ)
    งานเดียวกับที่ scheduler รันอัตโนมัติทุกวัน 07:00
    """
    logger.info("Manual trigger: running daily job")
    result = await run_daily_job()
    return result


async def run_daily_job() -> dict:
    """
    งานประจำวัน — สรุปเทรนด์คอนเทนต์วันนี้
    บันทึกลง ChromaDB และ Google Docs
    รันอัตโนมัติทุกวัน 07:00 และ trigger ด้วยตนเองผ่าน POST /daily-job ได้
    """
    today = datetime.date.today().strftime("%d %b %Y")
    topic = f"สรุปเทรนด์คอนเทนต์และเทคโนโลยีประจำวันที่ {today} จากแหล่งข่าวและโซเชียลมีเดียล่าสุด"

    logger.info(f"[Daily Job] Starting — topic: {topic}")

    try:
        # 1. สร้างเนื้อหาด้วย RAG + Google Search
        result = generate_with_rag(topic, use_search=True)
        result_text = result["answer"]

        # 2. บันทึกลง ChromaDB
        chunks = upsert_knowledge(
            text=result_text,
            metadata={
                "source": f"daily_job:{today}",
                "type": "daily_trend"
            }
        )
        logger.info(f"[Daily Job] Ingested {chunks} chunks to ChromaDB")

        # 3. บันทึกลง Google Docs
        doc_title = f"Daily_Trend_{today}"
        doc_url = create_doc(doc_title, result_text)
        if doc_url:
            logger.info(f"[Daily Job] Saved to Google Docs: {doc_url}")
        else:
            logger.warning("[Daily Job] Failed to save to Google Docs")

        return {
            "status": "success",
            "date": today,
            "ingested_chunks": chunks,
            "google_docs_url": doc_url,
            "context_used": result.get("context_used", False)
        }

    except Exception as e:
        logger.error(f"[Daily Job] Error: {str(e)}")
        return {"status": "error", "error": str(e)}


if __name__ == "__main__":
    import uvicorn
    # รันผ่านพอร์ตที่กำหนดในเครื่องหรือ Docker
    logger.info("Starting server with uvicorn")
    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT,
        log_level=settings.LOG_LEVEL.lower()
    )
