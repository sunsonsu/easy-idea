"""
Google Docs และ Drive Service
จัดการการสร้างและจัดเก็บเอกสารใน Google Docs
"""

import json
import os
import pathlib
from typing import Optional
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from app.core.config import settings
from app.utils.logger import get_logger
from app.utils.validators import sanitize_filename

# Initialize logger
logger = get_logger(__name__)

# ขอบเขตการเข้าถึง Google API
SCOPES = [
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/drive'
]

# Root directory ของ project (src/app/services/ → src/app/ → src/ → root)
_ROOT_DIR = pathlib.Path(__file__).parent.parent.parent.parent
_TOKEN_FILE = _ROOT_DIR / 'token.json'


def get_common_creds():
    """
    จัดการเรื่อง Authentication และ Refresh Token
    
    Returns:
        Credentials object
        
    Raises:
        Exception: ถ้าไม่พบ credentials
    """
    creds = None
    token_json_str = os.getenv("USER_TOKEN_JSON")
    
    try:
        # 1. ลองดึงจาก Environment Variable (Secret Manager)
        if token_json_str:
            logger.info("Loading credentials from environment variable")
            token_data = json.loads(token_json_str)
            creds = Credentials.from_authorized_user_info(token_data, SCOPES)
        # 2. ถ้าไม่มี ให้หาจากไฟล์โลคอล
        elif _TOKEN_FILE.exists():
            logger.info("Loading credentials from token.json")
            creds = Credentials.from_authorized_user_file(str(_TOKEN_FILE), SCOPES)
        
        # ถ้า Token หมดอายุ ให้ทำการ Refresh
        if creds and creds.expired and creds.refresh_token:
            logger.info("Refreshing expired credentials")
            creds.refresh(Request())
            
        if not creds:
            raise Exception("Credential NOT FOUND: Please run auth_setup.py first")
        
        logger.info("Credentials loaded successfully")
        return creds
        
    except Exception as e:
        logger.error(f"Error loading credentials: {str(e)}")
        raise


def get_gdocs_service():
    """สร้าง Service สำหรับจัดการ Google Docs"""
    creds = get_common_creds()
    return build('docs', 'v1', credentials=creds)


def get_drive_service():
    """สร้าง Service สำหรับจัดการ Google Drive (เพื่อสร้างไฟล์ในโฟลเดอร์)"""
    creds = get_common_creds()
    return build('drive', 'v3', credentials=creds)


def create_doc(title: str, content: str) -> Optional[str]:
    """
    สร้างไฟล์ Google Doc ใหม่ภายในโฟลเดอร์ที่กำหนด และเขียนเนื้อหาลงไป
    
    Args:
        title: ชื่อเอกสาร
        content: เนื้อหาที่ต้องการเขียน
        
    Returns:
        URL ของเอกสาร หรือ None ถ้าเกิด error
    """
    try:
        logger.info(f"Creating Google Doc: '{title}'")
        
        # Sanitize ชื่อไฟล์
        safe_title = sanitize_filename(title)
        
        drive_service = get_drive_service()
        docs_service = get_gdocs_service()
        
        # ดึง Folder ID จาก settings
        FOLDER_ID = settings.GOOGLE_DRIVE_FOLDER_ID
        
        file_metadata = {
            'name': safe_title,
            'mimeType': 'application/vnd.google-apps.document',
            'parents': [FOLDER_ID] if FOLDER_ID else [] 
        }
        
        # 1. สร้างไฟล์ใน Drive
        logger.info("Creating file in Google Drive")
        doc_file = drive_service.files().create(
            body=file_metadata, 
            fields='id,name,webViewLink'
        ).execute()
        
        doc_id = doc_file.get('id')
        logger.info(f"File created with ID: {doc_id}")
        
        # 2. เขียนเนื้อหาลงในไฟล์ที่สร้าง
        logger.info(f"Writing content ({len(content)} characters)")
        requests = [
            {
                'insertText': {
                    'location': {'index': 1},
                    'text': content
                }
            }
        ]
        
        docs_service.documents().batchUpdate(
            documentId=doc_id, 
            body={'requests': requests}
        ).execute()
        
        doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"
        logger.info(f"Document created successfully: {doc_url}")
        
        return doc_url

    except Exception as e:
        logger.error(f"Error creating Google Doc: {str(e)}")
        return None
