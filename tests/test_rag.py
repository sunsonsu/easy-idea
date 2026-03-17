"""
Tests สำหรับ RAG Module
"""

import pytest
from app.rag.embeddings import GeminiEmbeddingFunction
from app.rag.chunking import split_text
from app.rag.prompts import RAGPromptTemplate


def test_split_text():
    """ทดสอบการแบ่งข้อความ"""
    text = "This is a test. " * 100  # สร้างข้อความยาว
    chunks = split_text(text, chunk_size=100, chunk_overlap=20)
    
    assert len(chunks) > 1
    assert all(len(chunk) <= 120 for chunk in chunks)  # รวม overlap


def test_rag_prompt_template():
    """ทดสอบ prompt template"""
    prompt = RAGPromptTemplate.content_generation(
        topic="Test topic",
        context="Test context"
    )
    
    assert "Test topic" in prompt
    assert "Test context" in prompt
    assert "ฐานความรู้ส่วนตัว" in prompt


def test_system_instruction():
    """ทดสอบ system instruction"""
    instruction = RAGPromptTemplate.get_system_instruction("professional")
    assert len(instruction) > 0
    
    instruction_casual = RAGPromptTemplate.get_system_instruction("casual")
    assert instruction != instruction_casual


# Mock tests สำหรับ embeddings (ต้องการ API key)
def test_gemini_embedding_function(request, monkeypatch):
    """ทดสอบ embedding function (integration test)"""
    if not request.config.getoption("--run-integration"):
        pytest.skip("Skip integration tests by default")

    # ต้องการ GEMINI_API_KEY จริงๆ
    pass
