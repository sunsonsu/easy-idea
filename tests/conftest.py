"""
Test Configuration
"""

import pathlib
import sys

import pytest

# Make `app` package importable when running tests from repository root.
_ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
_SRC_DIR = _ROOT_DIR / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))


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
