"""
Text Chunking Strategies
จัดการการแบ่งข้อความเป็น chunks สำหรับ embedding
"""

from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List
from app.core.config import settings


def get_text_splitter(
    chunk_size: int = None,
    chunk_overlap: int = None,
    separators: List[str] = None
) -> RecursiveCharacterTextSplitter:
    """
    สร้าง text splitter สำหรับแบ่งข้อความ
    
    Args:
        chunk_size: ขนาดของแต่ละ chunk (characters)
        chunk_overlap: ความทับซ้อนระหว่าง chunks
        separators: ตัวแบ่งที่ต้องการใช้ (เรียงลำดับความสำคัญ)
        
    Returns:
        RecursiveCharacterTextSplitter instance
    """
    if chunk_size is None:
        chunk_size = settings.DEFAULT_CHUNK_SIZE
    if chunk_overlap is None:
        chunk_overlap = settings.DEFAULT_CHUNK_OVERLAP
    if separators is None:
        # Default separators เหมาะสำหรับข้อความทั่วไป
        separators = ["\n\n", "\n", ". ", " ", ""]
    
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=separators,
        length_function=len
    )

def split_text(
    text: str,
    chunk_size: int = None,
    chunk_overlap: int = None
) -> List[str]:
    """
    แบ่งข้อความเป็น chunks
    
    Args:
        text: ข้อความที่ต้องการแบ่ง
        chunk_size: ขนาดของแต่ละ chunk
        chunk_overlap: ความทับซ้อนระหว่าง chunks
        
    Returns:
        รายการของ text chunks
    """
    splitter = get_text_splitter(chunk_size, chunk_overlap)
    print(f"Splitting text into chunks with size {chunk_size} and overlap {chunk_overlap}...")
    return splitter.split_text(text)
