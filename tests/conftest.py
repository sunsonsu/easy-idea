"""
Test Configuration
"""

import pytest


def pytest_addoption(parser):
    """เพิ่ม custom options สำหรับ pytest"""
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Run integration tests that require API keys"
    )


@pytest.fixture
def sample_text():
    """Sample text สำหรับทดสอบ"""
    return """
    AI และ Machine Learning กำลังเปลี่ยนแปลงโลก
    เทคโนโลยีเหล่านี้ช่วยให้เราสามารถสร้างระบบอัตโนมัติ
    และวิเคราะห์ข้อมูลได้อย่างมีประสิทธิภาพ
    """


@pytest.fixture
def sample_metadata():
    """Sample metadata สำหรับทดสอบ"""
    return {
        "source": "test_source",
        "category": "technology",
        "author": "test_user"
    }
