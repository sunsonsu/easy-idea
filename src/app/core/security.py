"""
Security Module
จัดการ API Key authentication
"""

from fastapi import HTTPException, Security
from fastapi.security.api_key import APIKeyHeader

from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

api_key_header = APIKeyHeader(name="access_token", auto_error=False)


def get_api_key(header_value: str = Security(api_key_header)):
    """
    ตรวจสอบ API Key จาก Header
    
    Args:
        header_value: ค่า API key จาก header
        
    Returns:
        API key ถ้า valid
        
    Raises:
        HTTPException: ถ้า API key ไม่ถูกต้อง
    """
    if not header_value:
        logger.warning("API request without access_token")
        raise HTTPException(
            status_code=403,
            detail="Missing access_token in header"
        )
    
    if header_value == settings.APP_API_KEY:
        return header_value
    
    logger.warning(f"Invalid API key attempt: {header_value[:10]}...")
    raise HTTPException(
        status_code=403,
        detail="Could not validate credentials: รหัสผ่านไม่ถูกต้อง"
    )