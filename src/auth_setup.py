import os
import pathlib
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

SCOPES = [
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/drive'
]

# Root directory ของ project (หนึ่งระดับเหนือ src/)
ROOT_DIR = pathlib.Path(__file__).parent.parent
CREDENTIALS_FILE = ROOT_DIR / 'credentials.json'
TOKEN_FILE = ROOT_DIR / 'token.json'

def generate_token():
    creds = None
    # ตรวจสอบว่ามี token.json เดิมไหม
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    
    # ถ้าไม่มี หรือหมดอายุและ refresh ไม่ได้ ให้เริ่ม Login ใหม่
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        
        # บันทึก token.json ลงเครื่อง
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
        print("สร้างไฟล์ token.json สำเร็จแล้ว!")

if __name__ == '__main__':
    generate_token()