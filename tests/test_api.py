"""
Integration Tests สำหรับ API Endpoints
ทดสอบ API ผ่าน FastAPI TestClient
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock


@pytest.fixture
def test_client():
    """สร้าง test client"""
    from app.main import app
    return TestClient(app)


@pytest.fixture
def mock_api_key(monkeypatch):
    """Mock API key สำหรับทดสอบ"""
    monkeypatch.setenv("APP_API_KEY", "test_key_123")
    return "test_key_123"


def test_read_root(test_client):
    """ทดสอบ root endpoint"""
    response = test_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "version" in data


@patch('app.services.chroma_service.get_collection_stats')
def test_health_check(mock_stats, test_client):
    """ทดสอบ health check endpoint"""
    mock_stats.return_value = {
        "collection_name": "easy_idea_kb",
        "total_documents": 10,
        "status": "healthy"
    }
    
    response = test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@patch('app.services.chroma_service.upsert_knowledge')
def test_ingest_endpoint(mock_upsert, test_client, mock_api_key):
    """ทดสอบ ingest endpoint"""
    mock_upsert.return_value = 5
    
    response = test_client.post(
        "/ingest",
        headers={"access_token": mock_api_key},
        json={
            "text": "Test knowledge document",
            "source": "test"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["chunks"] == 5


def test_ingest_without_auth(test_client):
    """ทดสอบ ingest โดยไม่มี API key"""
    response = test_client.post(
        "/ingest",
        json={
            "text": "Test knowledge",
            "source": "test"
        }
    )
    
    assert response.status_code == 403


@patch('app.services.gemini_service.generate_with_rag')
@patch('app.services.gdocs_service.create_doc')
def test_generate_endpoint(mock_create_doc, mock_generate, test_client, mock_api_key):
    """ทดสอบ generate endpoint"""
    mock_generate.return_value = {
        "answer": "Generated content",
        "references": ["doc1", "doc2"],
        "context_used": True
    }
    mock_create_doc.return_value = "https://docs.google.com/document/d/123/edit"
    
    response = test_client.post(
        "/generate",
        headers={"access_token": mock_api_key},
        json={
            "topic": "AI trends",
            "use_google_search": True,
            "save_to_docs": True
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "ai_response" in data
    assert "references" in data
    assert data["google_docs_url"] is not None
