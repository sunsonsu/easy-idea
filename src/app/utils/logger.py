"""
Centralized Logging Configuration
จัดการ logging สำหรับทั้งระบบ
"""

import logging
import sys
from typing import Optional
from datetime import datetime


# สร้าง formatter สำหรับ log messages
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None
) -> None:
    """
    ตั้งค่า logging สำหรับทั้งแอปพลิเคชัน
    
    Args:
        level: ระดับ logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: path ของไฟล์ log (optional)
    """
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # สร้าง handlers
    handlers = [
        logging.StreamHandler(sys.stdout)
    ]
    
    # เพิ่ม file handler ถ้าระบุ log_file
    if log_file:
        handlers.append(
            logging.FileHandler(log_file, encoding='utf-8')
        )
    
    # ตั้งค่า basic config
    logging.basicConfig(
        level=log_level,
        format=LOG_FORMAT,
        datefmt=DATE_FORMAT,
        handlers=handlers
    )
    
    # ปิด logging จาก libraries ที่ verbose เกินไป
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    สร้าง logger instance สำหรับ module
    
    Args:
        name: ชื่อของ logger (ปกติใช้ __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class LoggerMixin:
    """
    Mixin class สำหรับเพิ่ม logging capability
    ใช้กับ class ที่ต้องการ logging
    """
    
    @property
    def logger(self) -> logging.Logger:
        """Get logger instance for this class"""
        return get_logger(self.__class__.__name__)


# สร้าง custom log level สำหรับ RAG operations (optional)
RAG_OPERATION = 25  # ระหว่าง INFO (20) และ WARNING (30)
logging.addLevelName(RAG_OPERATION, "RAG_OP")


def log_rag_operation(logger: logging.Logger, message: str) -> None:
    """
    Log RAG operation พิเศษ
    
    Args:
        logger: Logger instance
        message: ข้อความที่ต้องการ log
    """
    logger.log(RAG_OPERATION, message)
