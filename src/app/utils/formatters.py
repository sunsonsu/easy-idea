"""
Text and Data Formatting Utilities
จัดการการ format ข้อความและข้อมูล
"""

from datetime import datetime
from typing import Optional


def format_timestamp(
    dt: Optional[datetime] = None,
    format_str: str = "%Y%m%d_%H%M%S"
) -> str:
    """
    จัดรูปแบบ timestamp
    
    Args:
        dt: datetime object (ใช้เวลาปัจจุบันถ้าไม่ระบุ)
        format_str: รูปแบบที่ต้องการ
        
    Returns:
        Formatted timestamp string
    """
    if dt is None:
        dt = datetime.now()
    
    return dt.strftime(format_str)


def truncate_text(
    text: str,
    max_length: int = 100,
    suffix: str = "..."
) -> str:
    """
    ตัดข้อความให้สั้นลง
    
    Args:
        text: ข้อความต้นฉบับ
        max_length: ความยาวสูงสุด
        suffix: ข้อความต่อท้าย (เช่น "...")
        
    Returns:
        ข้อความที่ตัดแล้ว
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def format_file_size(size_bytes: int) -> str:
    """
    แปลงขนาดไฟล์เป็น human-readable format
    
    Args:
        size_bytes: ขนาดเป็น bytes
        
    Returns:
        Formatted string (เช่น "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    
    return f"{size_bytes:.1f} PB"


def format_document_title(
    prefix: str,
    topic: Optional[str] = None,
    include_timestamp: bool = True
) -> str:
    """
    สร้างชื่อเอกสารแบบมาตรฐาน
    
    Args:
        prefix: คำนำหน้า (เช่น "RAG_Report")
        topic: หัวข้อ (optional)
        include_timestamp: รวม timestamp หรือไม่
        
    Returns:
        Formatted document title
    """
    parts = [prefix]
    
    if topic:
        # ตัดข้อความยาวๆ และลบตัวอักษรพิเศษ
        clean_topic = truncate_text(topic, max_length=30, suffix="")
        clean_topic = "".join(c if c.isalnum() or c.isspace() else "_" for c in clean_topic)
        parts.append(clean_topic.strip())
    
    if include_timestamp:
        parts.append(format_timestamp())
    
    return "_".join(parts)


def format_context_display(
    documents: list,
    max_docs: int = 3,
    max_length_per_doc: int = 200
) -> str:
    """
    จัดรูปแบบการแสดงผล context documents
    
    Args:
        documents: รายการเอกสาร
        max_docs: จำนวนเอกสารสูงสุดที่จะแสดง
        max_length_per_doc: ความยาวสูงสุดต่อเอกสาร
        
    Returns:
        Formatted context string
    """
    if not documents:
        return "ไม่มีข้อมูลอ้างอิง"
    
    display_docs = documents[:max_docs]
    formatted = []
    
    for i, doc in enumerate(display_docs, 1):
        truncated = truncate_text(doc, max_length_per_doc)
        formatted.append(f"[{i}] {truncated}")
    
    if len(documents) > max_docs:
        formatted.append(f"... และอีก {len(documents) - max_docs} เอกสาร")
    
    return "\n\n".join(formatted)
