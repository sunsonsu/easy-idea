"""
Gemini AI Service
จัดการการเรียกใช้ Gemini API พร้อม RAG
"""

import os
from typing import Dict, Any, Optional, List
from google import genai
from google.genai import types

from app.services.chroma_service import query_knowledge
from app.rag.retrieval import format_context
from app.rag.prompts import RAGPromptTemplate
from app.utils.logger import get_logger
from app.core.config import settings

# Initialize logger
logger = get_logger(__name__)

# Initialize Gemini Client
client = genai.Client(api_key=settings.GEMINI_API_KEY)
google_search_tool = types.Tool(google_search=types.GoogleSearch())


def list_models() -> List[Dict[str, str]]:
    """
    ดึงรายการ Gemini models ที่รองรับ generateContent

    Returns:
        รายการ dict ที่มี id และ display_name ของแต่ละ model
    """
    try:
        models = []
        for m in client.models.list():
            # กรองเฉพาะ model ที่รองรับ generateContent
            supported = getattr(m, "supported_actions", None) or []
            if "generateContent" not in supported:
                continue
            model_id = m.name  # เช่น "models/gemini-2.5-flash-lite"
            display = getattr(m, "display_name", None) or model_id
            models.append({"id": model_id, "display_name": display})
        logger.info(f"Found {len(models)} available Gemini models")
        return models
    except Exception as e:
        logger.error(f"Error listing models: {str(e)}")
        # Fallback: คืน default model เดียวเผื่อ API ล่ม
        return [{"id": settings.GEMINI_MODEL, "display_name": settings.GEMINI_MODEL}]

def generate_with_rag(
    topic: str,
    use_search: bool = True,
    n_results: int = None,
    model: str = None
) -> Dict[str, Any]:
    """
    ฟังก์ชันหลักในการดึงความรู้จาก ChromaDB มาให้ Gemini ตอบ
    
    Args:
        topic: หัวข้อที่ต้องการให้วิจัย
        use_search: ใช้ Google Search หรือไม่
        n_results: จำนวนเอกสารที่ต้องการจาก knowledge base
        model: Gemini model ที่ต้องการใช้
        
    Returns:
        Dict ที่มี answer และ references
    """
    try:
        if n_results is None:
            n_results = settings.DEFAULT_N_RESULTS
        if model is None:
            model = settings.GEMINI_MODEL

        logger.info(f"Starting RAG generation for topic: '{topic[:50]}...'")

        # 1. ดึงความรู้ที่เกี่ยวข้องจาก ChromaDB
        relevant_docs = query_knowledge(topic, n_results=n_results)
        
        # 2. จัดรูปแบบ context
        context_text = format_context(relevant_docs)
        
        logger.info(f"Retrieved {len(relevant_docs)} documents from knowledge base")
        
        # 3. สร้าง prompt โดยใช้ RAGPromptTemplate
        prompt = RAGPromptTemplate.content_generation(
            topic=topic,
            context=context_text
        )
        
        # 4. ตั้งค่า tools สำหรับ Gemini
        tools = [google_search_tool] if use_search else []
        
        # 5. เรียก Gemini API
        logger.info(f"Calling Gemini API with model: {model}")
        
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=RAGPromptTemplate.get_system_instruction("professional"),
                tools=tools,
                temperature=settings.GEMINI_TEMPERATURE
            )
        )
        
        answer = response.text
        logger.info(f"Generated response length: {len(answer)} characters")
        
        return {
            "answer": answer,
            "references": relevant_docs,
            "context_used": len(relevant_docs) > 0
        }
        
    except Exception as e:
        logger.error(f"Error during RAG generation: {str(e)}")
        # Fallback: ตอบโดยไม่ใช้ RAG
        return generate_without_rag(topic, use_search, model)


def generate_without_rag(
    topic: str,
    use_search: bool = True,
    model: str = None
) -> Dict[str, Any]:
    """
    สร้างเนื้อหาโดยไม่ใช้ RAG (fallback)
    
    Args:
        topic: หัวข้อที่ต้องการ
        use_search: ใช้ Google Search หรือไม่
        model: Gemini model
        
    Returns:
        Dict ที่มี answer และ references
    """
    try:
        if model is None:
            model = settings.GEMINI_MODEL
        logger.warning("Generating without RAG (fallback mode)")

        tools = [google_search_tool] if use_search else []
        
        response = client.models.generate_content(
            model=model,
            contents=topic,
            config=types.GenerateContentConfig(
                system_instruction="คุณคือผู้เชี่ยวชาญด้านคอนเทนต์มาร์เก็ตติ้ง สรุปข้อมูลให้เป็นระบบและน่าสนใจ",
                tools=tools
            )
        )
        
        return {
            "answer": response.text,
            "references": [],
            "context_used": False
        }
        
    except Exception as e:
        logger.error(f"Error in fallback generation: {str(e)}")
        raise


def summarize_text(text: str, max_words: int = 200) -> str:
    """
    สรุปข้อความ
    
    Args:
        text: ข้อความที่ต้องการสรุป
        max_words: จำนวนคำสูงสุด
        
    Returns:
        ข้อความสรุป
    """
    try:
        prompt = RAGPromptTemplate.summarization(text, max_words)
        
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt
        )
        
        return response.text
        
    except Exception as e:
        logger.error(f"Error during summarization: {str(e)}")
        raise