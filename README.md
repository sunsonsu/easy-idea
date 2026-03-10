# Easy Idea API: Gemini Research and Docs Writer

Easy Idea API คือระบบผู้ช่วยวิจัยอัจฉริยะที่ใช้ Gemini ในการค้นหาข้อมูลจากอินเทอร์เน็ต, สรุปเนื้อหา, และบันทึกผลลัพธ์ลง Google Docs อัตโนมัติภายใต้บัญชีของคุณเอง

This project is an intelligent research assistant that leverages Gemini to browse the web, summarize findings, and automatically generate structured reports in Google Docs using your personal account.

## Features

- RAG workflow with Gemini + Google Search grounding
- ChromaDB vector store for knowledge retrieval
- Gemini Embeddings for semantic search
- Auto-save generated report to Google Docs
- Daily scheduler (07:00) for automatic knowledge updates
- Frontend model selector where options come from backend only

## Project Structure

```text
easy-idea/
├── src/
│   ├── app/
│   │   ├── main.py
│   │   ├── services/
│   │   ├── rag/
│   │   └── templates/
│   └── auth_setup.py
├── requirements.txt
├── docker-compose.yml
└── credentials.json (local only, do not commit)
```

## Setup and Installation (การตั้งค่าระบบ)

### 1. Create `.env`

สร้างไฟล์ `.env` ไว้ที่โฟลเดอร์หลัก
Create a `.env` file in the root directory:

```env
GEMINI_API_KEY=your_gemini_api_key_here
APP_API_KEY=your_access_token_for_api
GOOGLE_DRIVE_FOLDER_ID=your_google_drive_folder_id_here

# ChromaDB (local dev with docker-compose)
CHROMA_HOST=localhost
CHROMA_PORT=8000
CHROMA_COLLECTION_NAME=easy_idea_kb

# Model and app config
GEMINI_MODEL=gemini-2.5-flash-lite
GEMINI_EMBEDDING_MODEL=models/gemini-embedding-001
GEMINI_TEMPERATURE=0.7
HOST=0.0.0.0
PORT=8080
LOG_LEVEL=INFO
```

`GOOGLE_DRIVE_FOLDER_ID` หาได้จาก URL ของโฟลเดอร์ เช่น:
`https://drive.google.com/drive/folders/{GOOGLE_DRIVE_FOLDER_ID}`

### 2. Google Cloud API Setup (OAuth)

1. ไปที่ Google Cloud Console และเลือกโปรเจกต์ที่ต้องการ
2. ไปที่ `APIs & Services` -> `Credentials`
3. กด `+ CREATE CREDENTIALS` -> `OAuth client ID`
4. ถ้าระบบให้ตั้งค่า Consent Screen ให้เลือก `External` แล้วกรอกข้อมูลให้ครบ
5. สร้าง Client ID โดยเลือก `Desktop app`
6. ดาวน์โหลดไฟล์ JSON, เปลี่ยนชื่อเป็น `credentials.json`, วางไว้ที่ root ของโปรเจกต์
7. เพิ่มอีเมลของคุณใน `Test Users`

## How to Use (ขั้นตอนการใช้งาน)

### Step 1: Install dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Generate Google token

รันสคริปต์เพื่อล็อกอินและสร้าง `token.json`:

```bash
python src/auth_setup.py
```

ระบบจะเปิด browser ให้กดอนุญาตสิทธิ์ (Google Docs/Drive) แล้วจะสร้าง `token.json` ที่ root

### Step 3: Run application

```bash
python src/app/main.py
```

- API base URL: `http://localhost:8080`
- Swagger docs: `http://localhost:8080/docs`
- UI chat: `http://localhost:8080/ui/chat`

### Optional: Run with Docker Compose

```bash
docker compose up --build
```

## Daily Scheduler

ระบบมี scheduler ภายในแอปที่รันทุกวันเวลา 07:00 (server local time) เพื่อ:

- สร้างหัวข้อสรุปเทรนด์ประจำวัน
- ใช้ Google Search เพื่อเสริมข้อมูล
- บันทึกผลลง ChromaDB
- สร้างเอกสารใน Google Docs

สามารถทดสอบด้วย manual trigger ได้ที่ `POST /daily-job`

## Deployment (Google Cloud)

สำหรับ Cloud deployment:

1. เก็บ `USER_TOKEN_JSON` ใน Secret Manager โดยนำค่า JSON จาก `token.json` ไปใส่
2. map secret เป็น environment variable `USER_TOKEN_JSON` ใน service
3. ตั้งค่า environment variables ที่จำเป็น เช่น `GEMINI_API_KEY`, `APP_API_KEY`, `GOOGLE_DRIVE_FOLDER_ID`

Important note:

- ถ้าใช้ Cloud Run (stateless/scale-to-zero), scheduler ในตัวแอปอาจไม่ทำงานสม่ำเสมอ
- สำหรับ production แนะนำใช้ `Cloud Scheduler` ยิง `POST /daily-job` วันละครั้ง

## Security Note

- Do not commit `credentials.json` or `token.json` to public repositories
- ควรเก็บ secrets ทั้งหมดใน environment variables หรือ Secret Manager
- ตรวจสอบว่าไฟล์ลับอยู่ใน `.gitignore`