"""
Tests สำหรับ Utils Module
"""

import pytest
from datetime import datetime
from app.utils.validators import (
    validate_text_length,
    validate_api_key,
    validate_n_results,
    sanitize_filename
)
from app.utils.formatters import (
    format_timestamp,
    truncate_text,
    format_document_title
)
from fastapi import HTTPException


def test_validate_text_length_valid():
    """ทดสอบ validation ข้อความที่ valid"""
    text = "This is valid text"
    result = validate_text_length(text, min_length=5, max_length=100)
    assert result == text


def test_validate_text_length_too_short():
    """ทดสอบ validation ข้อความสั้นเกินไป"""
    with pytest.raises(HTTPException) as exc_info:
        validate_text_length("Hi", min_length=5)
    assert exc_info.value.status_code == 400


def test_validate_text_length_too_long():
    """ทดสอบ validation ข้อความยาวเกินไป"""
    long_text = "x" * 1000
    with pytest.raises(HTTPException):
        validate_text_length(long_text, max_length=100)


def test_validate_api_key():
    """ทดสอบ validation API key"""
    assert validate_api_key("valid_key_123") == True
    assert validate_api_key("") == False
    assert validate_api_key(None) == False
    assert validate_api_key("short") == False


def test_sanitize_filename():
    """ทดสอบการทำความสะอาดชื่อไฟล์"""
    result = sanitize_filename("test<>file:name?.txt")
    assert "<" not in result
    assert ">" not in result
    assert ":" not in result
    assert "?" not in result


def test_format_timestamp():
    """ทดสอบการ format timestamp"""
    dt = datetime(2026, 2, 24, 15, 30, 0)
    result = format_timestamp(dt, "%Y%m%d_%H%M%S")
    assert result == "20260224_153000"


def test_truncate_text():
    """ทดสอบการตัดข้อความ"""
    text = "This is a long text that needs to be truncated"
    result = truncate_text(text, max_length=20, suffix="...")
    assert len(result) <= 20
    assert result.endswith("...")


def test_format_document_title():
    """ทดสอบการสร้างชื่อเอกสาร"""
    title = format_document_title(
        prefix="TEST",
        topic="Sample topic",
        include_timestamp=False
    )
    assert "TEST" in title
    assert "Sample" in title or "topic" in title


def test_validate_n_results_valid():
    """ทดสอบ validation n_results"""
    result = validate_n_results(5, max_results=10)
    assert result == 5


def test_validate_n_results_too_high():
    """ทดสอบ n_results เกินขีดจำกัด"""
    with pytest.raises(HTTPException):
        validate_n_results(20, max_results=10)


def test_validate_n_results_zero():
    """ทดสอบ n_results เป็น 0"""
    with pytest.raises(HTTPException):
        validate_n_results(0)
