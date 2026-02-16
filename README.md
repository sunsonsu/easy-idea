🤖 Easy Idea API: Gemini Research & Docs Writer
Easy Idea API คือระบบผู้ช่วยวิจัยอัจฉริยะที่ใช้พลังของ Gemini 2.5 Flash-lite ในการค้นหาข้อมูลจากอินเทอร์เน็ต (Google Search Grounding) สรุปเนื้อหา และบันทึกผลการค้นหาลงใน Google Docs โดยอัตโนมัติภายใต้บัญชีของคุณเอง

This project is an intelligent research assistant that leverages Gemini 2.5 Flash-lite to browse the web, summarize findings, and automatically generate structured reports in Google Docs using your personal account.

🛠️ Setup & Installation (การตั้งค่าระบบ)
1. Environment Variables
สร้างไฟล์ .env ไว้ที่โฟลเดอร์หลัก และใส่ค่าดังนี้:
Create a .env file in the root directory with the following values:

ข้อมูลโค้ด
GEMINI_API_KEY=your_gemini_api_key_here
GOOGLE_DRIVE_FOLDER_ID=your_google_drive_folder_id_here

GOOLGLE_DRIVE_FOLDER_ID หาได้จาก URL ของ Folder นั้น ๆ เช่น
https://drive.google.com/drive/folders/{GOOLGLE_DRIVE_FOLDER_ID }

2. Google Cloud API Setup (การตั้งค่า Google Cloud)
ไปที่ Google Cloud Console: API Credentials
(Go to Google Cloud Console and ensure your project is selected.)

กด [+ CREATE CREDENTIALS] -> เลือก OAuth client ID
(Click Create Credentials and select OAuth client ID.)

หากระบบให้ตั้งค่า Configure Consent Screen:

เลือก External กรอกข้อมูลพื้นฐานให้ครบแล้วกด Save
(If prompted, configure the Consent Screen as 'External' and fill in the required info.)

สร้าง Client ID โดยเลือก Application type เป็น Desktop app
(Create Client ID with 'Desktop app' as the application type.)

ดาวน์โหลดไฟล์ JSON และเปลี่ยนชื่อเป็น credentials.json วางไว้ในโฟลเดอร์โปรเจกต์
(Download the JSON file, rename it to credentials.json, and place it in the project folder.)

อย่าลืมเพิ่มอีเมลตัวเองในส่วน Test Users
(Don't forget to add your email in Test Users section)

🚀 How to Use (ขั้นตอนการใช้งาน)
Step 1: Install Dependencies
Bash
pip install -r requirements.txt
Step 2: Generate Access Token
รันสคริปต์เพื่อล็อกอินและขอสิทธิ์เข้าถึง Google Drive/Docs:
Run the authentication script to generate your token.json:

Bash
python auth_setup.py
จะมีหน้าต่างเบราว์เซอร์เด้งขึ้นมา ให้กดอนุญาต (Allow) จนเสร็จสิ้น
(A browser window will open. Grant the necessary permissions.)

Step 3: Run the Application
เริ่มต้นการทำงานของ FastAPI Server:
Start the FastAPI server:

Bash
python app.py
แอปพลิเคชันจะรันที่ http://localhost:8080 คุณสามารถเข้าชม API Documentation ได้ที่ /docs
(The app will run at http://localhost:8080. Access the interactive API docs at /docs.)

☁️ Deployment (การติดตั้งบน Cloud)
สำหรับ Google Cloud Run, ให้ทำตามขั้นตอนนี้:
For Google Cloud Run, follow these steps:

นำเนื้อหาในไฟล์ token.json ไปใส่ใน Secret Manager ชื่อ USER_TOKEN_JSON
(Add the content of token.json to Google Cloud Secret Manager as USER_TOKEN_JSON.)

ตั้งค่า Environment Variable ใน Cloud Run ให้ Map เข้ากับ Secret ดังกล่าว
(Map the Secret to an environment variable in your Cloud Run settings.)

ตรวจสอบให้แน่ใจว่าได้ใส่ GEMINI_API_KEY ในหน้า Configuration
(Ensure GEMINI_API_KEY is added to the Cloud Run environment variables.)

⚠️ Security Note (หมายเหตุความปลอดภัย)
DO NOT commit credentials.json or token.json to public repositories.

ห้าม นำไฟล์ credentials.json หรือ token.json ขึ้น GitHub ที่เป็นสาธารณะโดยเด็ดขาด (ควรใส่ไว้ใน .gitignore)