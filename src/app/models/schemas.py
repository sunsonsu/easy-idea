from pydantic import BaseModel, Field
from typing import Optional

class IngestRequest(BaseModel):
    """ข้อมูลสำหรับเพิ่มเข้าฐานความรู้ (ChromaDB)"""
    text: str = Field(..., description="เนื้อหาความรู้ที่ต้องการให้ AI จดจำ")
    source: Optional[str] = Field("manual_input", description="แหล่งที่มาของข้อมูล เช่น ชื่อไฟล์ หรือ URL")

class ContentRequest(BaseModel):
    """ข้อมูลสำหรับสั่งให้ AI วิจัยและสร้างรายงาน"""
    topic: str = Field(..., description="หัวข้อที่ต้องการให้วิจัย")
    model: Optional[str] = Field(None, description="Gemini model ที่ต้องการใช้ (None = ใช้ค่า default จาก config)")
    use_google_search: bool = Field(True, description="อนุญาตให้ AI ค้นหา Google เพิ่มเติมหรือไม่")
    save_to_docs: bool = Field(True, description="บันทึกลง Google Docs หรือไม่")
    save_to_knowledge: bool = Field(False, description="บันทึกผลลัพธ์กลับเข้าฐานความรู้ ChromaDB หรือไม่")