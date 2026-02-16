import os
import json
import datetime
from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai
from google.genai import types

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

load_dotenv()

app = FastAPI(
    title="Easy Idea API",
    description="API สำหรับวิจัยคอนเทนต์และบันทึกลง Google Docs พร้อมระบบป้องกันด้วย API Key"
)

# --- Security Configuration ---
API_KEY_NAME = "access_token" # ชื่อ Header ที่ต้องใส่ใน Swagger/Request
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

def get_api_key(header_value: str = Security(api_key_header)):
    """ตรวจสอบรหัสผ่านจาก Header"""
    # ดึงรหัสผ่านที่ตั้งไว้จาก Secret Manager / Env
    expected_key = os.getenv("APP_API_KEY") 
    
    if header_value == expected_key:
        return header_value
    
    raise HTTPException(
        status_code=403,
        detail="Could not validate credentials: รหัสผ่านไม่ถูกต้อง หรือไม่ได้ระบุ access_token"
    )

# --- Google API Configuration ---
SCOPES = [
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/drive' 
]

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
google_search_tool = types.Tool(google_search=types.GoogleSearch())

# --- Helper Functions ---

def get_common_creds():
    token_json_str = os.getenv("USER_TOKEN_JSON")
    creds = None
    
    if token_json_str:
        token_data = json.loads(token_json_str)
        creds = Credentials.from_authorized_user_info(token_data, SCOPES)
    else:
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        
    if not creds:
        raise Exception("Credential NOT FOUND: token.json missing")
    return creds

def get_gdocs_service():
    return build('docs', 'v1', credentials=get_common_creds())

def get_drive_service():
    return build('drive', 'v3', credentials=get_common_creds())

def create_doc(title, content):
    drive_service = get_drive_service()
    docs_service = get_gdocs_service()
    
    FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
    
    file_metadata = {
        'name': title,
        'mimeType': 'application/vnd.google-apps.document',
        'parents': [FOLDER_ID] 
    }
    
    doc_file = drive_service.files().create(body=file_metadata, fields='id').execute()
    doc_id = doc_file.get('id')
    
    requests = [{'insertText': {'location': {'index': 1}, 'text': content}}]
    docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()
    
    return f"https://docs.google.com/document/d/{doc_id}/edit"

# --- Models ---
class ContentRequest(BaseModel):
    topic: str
    save_to_docs: bool = True

# --- API Endpoints ---
@app.get("/")
def read_root():
    return {"status": "Easy Idea OK!", "auth_type": "API Key Required"}

@app.post("/generate")
async def generate_content(req: ContentRequest, auth: str = Depends(get_api_key)):
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash-lite',
            contents=req.topic,
            config=types.GenerateContentConfig(
                system_instruction="คุณคือผู้เชี่ยวชาญด้านคอนเทนต์มาร์เก็ตติ้ง สรุปข้อมูลให้เป็นระบบ น่าสนใจและสามารถ copy ไปวางในไฟล์ Google Docs ได้เลย",
                tools=[google_search_tool]
            )
        )
        
        result_text = response.text
        doc_url = None
        
        if req.save_to_docs:
            doc_title = f"AI_Report_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}"
            doc_url = create_doc(doc_title, result_text)
            
        return {
            "topic": req.topic,
            "ai_response": result_text,
            "google_docs_url": doc_url
        }
    except Exception as e:
        return {"error": str(e)}

@app.post("/daily-job")
async def daily_job(auth: str = Depends(get_api_key)):
    topic = "สรุปข่าวน่าสนใจประจำวันเกี่ยวกับเทคโนโลยี AI และการตลาด พร้อมแนวโน้มในอนาคต"
    return await generate_content(ContentRequest(topic=topic, save_to_docs=True), auth)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)