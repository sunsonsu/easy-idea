import os
import json
import datetime
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai
from google.genai import types

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

load_dotenv()

app = FastAPI(title="Easy Idea API")

SCOPES = [
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/drive' 
]

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
google_search_tool = types.Tool(google_search=types.GoogleSearch())

def get_common_creds():
    """Get User Token from Secret Manager (Environment Variable) or Local File"""
    creds = None
    
    token_json_str = os.getenv("USER_TOKEN_JSON")
    
    if token_json_str:
        token_data = json.loads(token_json_str)
        creds = Credentials.from_authorized_user_info(token_data, SCOPES)
    else:
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # Refresh token if expired
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        
    if not creds:
        raise Exception("Credential NOT FOUND: token.json not found in Local and Secret Manager")
        
    return creds

def get_gdocs_service():
    creds = get_common_creds()
    return build('docs', 'v1', credentials=creds)

def get_drive_service():
    creds = get_common_creds()
    return build('drive', 'v3', credentials=creds)

def create_doc(title, content):

    drive_service = get_drive_service()
    docs_service = get_gdocs_service()
    
    # --- Folder Drive ID ---
    FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
    
    file_metadata = {
        'name': title,
        'mimeType': 'application/vnd.google-apps.document',
        'parents': [FOLDER_ID] 
    }
    
    # create file
    doc_file = drive_service.files().create(body=file_metadata, fields='id').execute()
    doc_id = doc_file.get('id')
    
    # write content
    requests = [{'insertText': {'location': {'index': 1}, 'text': content}}]
    docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()
    
    return f"https://docs.google.com/document/d/{doc_id}/edit"

# --- Models ---
class ContentRequest(BaseModel):
    topic: str
    save_to_docs: bool = True

@app.get("/")
def read_root():
    return {"status": "Easy Idea OK!"}

@app.post("/generate")
async def generate_content(req: ContentRequest):
    try:
        # เรียกใช้ Gemini
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
async def daily_job():
    topic = "สรุปข่าวน่าสนใจประจำวันเกี่ยวกับเทคโนโลยี AI และการตลาด พร้อมแนวโน้มในอนาคต"
    return await generate_content(ContentRequest(topic=topic, save_to_docs=True))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
