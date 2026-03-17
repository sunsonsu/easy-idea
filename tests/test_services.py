"""
Tests สำหรับ Services
"""

from unittest.mock import Mock, patch


def test_chroma_service_import():
    """ทดสอบการ import chroma_service"""
    from app.services.chroma_service import upsert_knowledge, query_knowledge
    assert callable(upsert_knowledge)
    assert callable(query_knowledge)


def test_gemini_service_import():
    """ทดสอบการ import gemini_service"""
    from app.services.gemini_service import generate_with_rag
    assert callable(generate_with_rag)


@patch('app.services.chroma_service._get_collection')
def test_upsert_knowledge(mock_get_collection):
    """ทดสอบการบันทึกความรู้"""
    from app.services.chroma_service import upsert_knowledge
    
    mock_collection = Mock()
    mock_collection.upsert = Mock()
    mock_get_collection.return_value = mock_collection
    
    text = "This is test knowledge."
    result = upsert_knowledge(text, metadata={"source": "test"})
    
    assert isinstance(result, int)
    assert result > 0


@patch('app.services.chroma_service._get_collection')
def test_query_knowledge(mock_get_collection):
    """ทดสอบการค้นหาความรู้"""
    from app.services.chroma_service import query_knowledge
    
    mock_collection = Mock()
    mock_collection.query = Mock(return_value={
        'documents': [['Document 1', 'Document 2']]
    })
    mock_get_collection.return_value = mock_collection
    
    results = query_knowledge("test query", n_results=2)
    
    assert len(results) == 2
    assert results[0] == 'Document 1'


@patch('app.services.gemini_service.client')
@patch('app.services.chroma_service._get_collection')
def test_generate_with_rag(mock_get_collection, mock_client):
    """ทดสอบการ generate ด้วย RAG"""
    from app.services.gemini_service import generate_with_rag
    
    # Mock collection query
    mock_collection = Mock()
    mock_collection.query = Mock(return_value={
        'documents': [['Relevant document']]
    })
    mock_get_collection.return_value = mock_collection
    
    # Mock Gemini response
    mock_response = Mock()
    mock_response.text = "Generated content"
    mock_client.models.generate_content = Mock(return_value=mock_response)
    
    result = generate_with_rag("test topic", use_search=False)
    
    assert "answer" in result
    assert "references" in result
    assert isinstance(result["references"], list)
