import os
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

SCOPES = [
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/drive'
]

def generate_token():
    creds = None
    # ตรวจสอบว่ามี token.json เดิมไหม
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # ถ้าไม่มี หรือหมดอายุและ refresh ไม่ได้ ให้เริ่ม Login ใหม่
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # บันทึก token.json ลงเครื่อง
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
        print("✅ สร้างไฟล์ token.json สำเร็จแล้ว!")

if __name__ == '__main__':
    generate_token()