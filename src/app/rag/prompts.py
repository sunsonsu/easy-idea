"""
RAG Prompt Templates
เก็บ prompt templates สำหรับระบบ RAG
"""

from typing import Optional


class RAGPromptTemplate:
    """จัดการ Prompt Templates สำหรับ RAG"""
    
    @staticmethod
    def content_generation(
        topic: str,
        context: str,
        system_role: Optional[str] = None
    ) -> str:
        """
        Prompt สำหรับการสร้างคอนเทนต์โดยใช้ RAG
        
        Args:
            topic: หัวข้อที่ต้องการให้วิจัย
            context: ข้อมูลอ้างอิงจากฐานความรู้
            system_role: คำอธิบายบทบาทของ AI (optional)
            
        Returns:
            Formatted prompt string
        """
        if system_role is None:
            system_role = "คุณคือผู้เชี่ยวชาญด้านคอนเทนต์มาร์เก็ตติ้งและนักวิจัยข้อมูล"
        
        return f"""
{system_role}

ข้อมูลอ้างอิงจากฐานความรู้ส่วนตัว (Private Knowledge):
{context}

คำถามหรือหัวข้อที่ต้องการให้ทำ:
{topic}

คำแนะนำการตอบ:
1. หากข้อมูลใน 'ฐานความรู้ส่วนตัว' มีเนื้อหาที่เกี่ยวข้อง ให้ลำดับความสำคัญของข้อมูลนี้ก่อน
2. หากข้อมูลส่วนตัวไม่เพียงพอ สามารถใช้ความรู้ทั่วไปของคุณหรือ Google Search ร่วมด้วยได้
3. สรุปเนื้อหาให้เป็นระบบ น่าสนใจ และสามารถนำไปวางใน Google Docs ได้ทันที
4. อ้างอิงแหล่งข้อมูลให้ชัดเจนเมื่อใช้ข้อมูลจากฐานความรู้
"""
    
    @staticmethod
    def summarization(text: str, max_words: int = 200) -> str:
        """
        Prompt สำหรับการสรุปข้อความ
        
        Args:
            text: ข้อความที่ต้องการสรุป
            max_words: จำนวนคำสูงสุดของสรุป
            
        Returns:
            Formatted prompt string
        """
        return f"""
กรุณาสรุปข้อความต่อไปนี้ให้กระชับและได้ใจความครบถ้วน ไม่เกิน {max_words} คำ:

{text}

สรุป:
"""
    
    @staticmethod
    def question_answering(question: str, context: str) -> str:
        """
        Prompt สำหรับการตอบคำถามจาก context
        
        Args:
            question: คำถาม
            context: ข้อมูลอ้างอิง
            
        Returns:
            Formatted prompt string
        """
        return f"""
จากข้อมูลต่อไปนี้:

{context}

คำถาม: {question}

กรุณาตอบคำถามโดยอ้างอิงจากข้อมูลที่ให้มาเท่านั้น หากข้อมูลไม่เพียงพอ ให้บอกว่า "ไม่พบข้อมูลเพียงพอในการตอบคำถาม"

คำตอบ:
"""
    
    @staticmethod
    def get_system_instruction(
        style: str = "professional"
    ) -> str:
        """
        System instruction สำหรับ Gemini
        
        Args:
            style: สไตล์การตอบ (professional, casual, technical)
            
        Returns:
            System instruction string
        """
        styles = {
            "professional": "สรุปข้อมูลอย่างเป็นมืออาชีพ อ้างอิงแหล่งข้อมูลให้ชัดเจน",
            "casual": "ตอบแบบเป็นกันเองและเข้าใจง่าย แต่ยังคงความถูกต้อง",
            "technical": "ตอบแบบเทคนิคและละเอียด เหมาะสำหรับผู้เชี่ยวชาญ"
        }
        
        return styles.get(style, styles["professional"])
