import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings:
    """
    Application Settings
    จัดการค่า configuration ทั้งหมดจาก environment variables
    """
    
    # Project Info
    PROJECT_NAME: str = "Easy Idea RAG"
    VERSION: str = "1.0"
    
    # API Keys
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    APP_API_KEY: str = os.getenv("APP_API_KEY", "")
    
    # Google Services
    GOOGLE_DRIVE_FOLDER_ID: Optional[str] = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
    
    # ChromaDB Configuration
    CHROMA_HOST: str = os.getenv("CHROMA_HOST", "chromadb")
    CHROMA_PORT: int = int(os.getenv("CHROMA_PORT", "8000"))
    CHROMA_COLLECTION_NAME: str = os.getenv("CHROMA_COLLECTION_NAME", "easy_idea_kb")

    # Gemini Model Configuration
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
    GEMINI_EMBEDDING_MODEL: str = os.getenv("GEMINI_EMBEDDING_MODEL", "models/gemini-embedding-002")
    GEMINI_TEMPERATURE: float = float(os.getenv("GEMINI_TEMPERATURE", "0.7"))

    # RAG Configuration
    DEFAULT_CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1000"))
    DEFAULT_CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "100"))
    DEFAULT_N_RESULTS: int = int(os.getenv("N_RESULTS", "3"))

    # Server Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8080"))

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    def validate(self) -> bool:
        """
        ตรวจสอบว่า settings สำคัญครบถ้วนหรือไม่
        
        Returns:
            True ถ้า valid
            
        Raises:
            ValueError: ถ้าขาด settings สำคัญ
        """
        if not self.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is required")
        
        if not self.APP_API_KEY:
            raise ValueError("APP_API_KEY is required")
        
        return True
    
    def __repr__(self) -> str:
        """แสดง settings (ซ่อน sensitive data)"""
        return (
            f"Settings("
            f"PROJECT_NAME='{self.PROJECT_NAME}', "
            f"CHROMA_HOST='{self.CHROMA_HOST}', "
            f"CHROMA_PORT={self.CHROMA_PORT}, "
            f"LOG_LEVEL='{self.LOG_LEVEL}'"
            f")"
        )


# สร้าง singleton instance
settings = Settings()

# Validate settings เมื่อ import
try:
    settings.validate()
except ValueError as e:
    print(f"Warning: Configuration validation failed: {e}")