"""
Input Validation Utilities
ตรวจสอบความถูกต้องของข้อมูลนำเข้า
"""

import unicodedata
from typing import Optional
from fastapi import HTTPException


def _truncate_preserving_clusters(text: str, max_length: int) -> str:
    """Truncate text without splitting combining marks from their base characters."""
    if len(text) <= max_length:
        return text

    clusters = []
    current_cluster = ""

    for char in text:
        if current_cluster and unicodedata.category(char).startswith("M"):
            current_cluster += char
            continue

        if current_cluster:
            clusters.append(current_cluster)
        current_cluster = char

    if current_cluster:
        clusters.append(current_cluster)

    truncated = []
    current_length = 0
    for cluster in clusters:
        if current_length + len(cluster) > max_length:
            break
        truncated.append(cluster)
        current_length += len(cluster)

    result = "".join(truncated)
    # Defensive cleanup for scripts with combining marks: never end with a mark.
    while result and unicodedata.category(result[-1]).startswith("M"):
        result = result[:-1]

    return result


def validate_text_length(
    text: str,
    min_length: int = 1,
    max_length: int = 50000,
    field_name: str = "text"
) -> str:
    """
    ตรวจสอบความยาวของข้อความ
    
    Args:
        text: ข้อความที่ต้องการตรวจสอบ
        min_length: ความยาวขั้นต่ำ
        max_length: ความยาวสูงสุด
        field_name: ชื่อฟิลด์สำหรับแสดงใน error message
        
    Returns:
        ข้อความที่ผ่านการตรวจสอบ
        
    Raises:
        HTTPException: ถ้าข้อความไม่ผ่านเงื่อนไข
    """
    text = text.strip()
    
    if len(text) < min_length:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} ต้องมีความยาวอย่างน้อย {min_length} ตัวอักษร"
        )
    
    if len(text) > max_length:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} ต้องมีความยาวไม่เกิน {max_length} ตัวอักษร"
        )
    
    return text


def validate_api_key(
    api_key: Optional[str],
    min_length: int = 10
) -> bool:
    """
    ตรวจสอบรูปแบบของ API key
    
    Args:
        api_key: API key ที่ต้องการตรวจสอบ
        min_length: ความยาวขั้นต่ำ
        
    Returns:
        True ถ้า valid, False ถ้าไม่ valid
    """
    if not api_key:
        return False
    
    if len(api_key) < min_length:
        return False
    
    # ตรวจสอบว่าไม่มีตัวอักษรแปลกๆ
    if not all(c.isprintable() for c in api_key):
        return False
    
    return True


def validate_n_results(n_results: int, max_results: int = 10) -> int:
    """
    ตรวจสอบจำนวนผลลัพธ์ที่ต้องการ
    
    Args:
        n_results: จำนวนที่ร้องขอ
        max_results: จำนวนสูงสุดที่อนุญาต
        
    Returns:
        จำนวนที่ผ่านการตรวจสอบ
        
    Raises:
        HTTPException: ถ้าจำนวนไม่อยู่ในช่วงที่อนุญาต
    """
    if n_results < 1:
        raise HTTPException(
            status_code=400,
            detail="n_results ต้องมากกว่า 0"
        )
    
    if n_results > max_results:
        raise HTTPException(
            status_code=400,
            detail=f"n_results ต้องไม่เกิน {max_results}"
        )
    
    return n_results


def sanitize_filename(filename: str) -> str:
    """
    ทำความสะอาดชื่อไฟล์ให้ปลอดภัย
    
    Args:
        filename: ชื่อไฟล์ต้นฉบับ
        
    Returns:
        ชื่อไฟล์ที่ปลอดภัย
    """
    # ลบตัวอักษรที่ไม่อนุญาต
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # จำกัดความยาว
    if len(filename) > 255:
        filename = _truncate_preserving_clusters(filename, 255)
    
    return filename.strip()
