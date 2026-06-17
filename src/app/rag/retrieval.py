from typing import List


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
