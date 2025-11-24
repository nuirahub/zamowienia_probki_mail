"""
Zarządzanie konfiguracją aplikacji.
Ładuje zmienne środowiskowe z pliku .env używając pathlib.
"""
from pathlib import Path
from dotenv import load_dotenv
import os

# Ustal ścieżkę do katalogu głównego (gdzie jest .env)
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

class Config:
    """Klasa konfiguracyjna zawierająca wszystkie zmienne środowiskowe."""
    
    # Baza Danych MSSQL
    DB_SERVER = os.getenv("DB_SERVER")
    DB_NAME = os.getenv("DB_NAME")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    
    # Connection string dla MSSQL
    @property
    def DB_STRING(self) -> str:
        """Tworzy connection string dla MSSQL."""
        if not all([self.DB_SERVER, self.DB_NAME, self.DB_USER, self.DB_PASSWORD]):
            raise ValueError("Brak wymaganych zmiennych środowiskowych dla bazy danych")
        return (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={self.DB_SERVER};"
            f"DATABASE={self.DB_NAME};"
            f"UID={self.DB_USER};"
            f"PWD={self.DB_PASSWORD}"
        )
    
    # Konfiguracja Mail
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.office365.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USER = os.getenv("MAIL_USER")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "True").lower() == "true"
    
    # Logowanie
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = BASE_DIR / "app.log"
    
    # Ścieżki do katalogów
    TEMPLATE_DIR = BASE_DIR / "templates"
    DATA_DIR = BASE_DIR / "data"
    MOCK_DIR = DATA_DIR / "mocks" if DATA_DIR.exists() else None
    
    # Tryb danych (CSV dla prototypu/testów, SQL dla produkcji)
    USE_MOCK_DATA = True
    MOCK_DIR = DATA_DIR / "mocks" if DATA_DIR.exists() else None
    
    # Konfiguracja LLM (wybór dostawcy)
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")  # "gemini", "openai", "qwen"
    
    # Konfiguracja Gemini AI
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    GEMINI_TEMPERATURE = float(os.getenv("GEMINI_TEMPERATURE", "0.3"))
    
    # Konfiguracja OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.3"))
    
    # Konfiguracja Qwen (Alibaba Cloud)
    QWEN_API_KEY = os.getenv("QWEN_API_KEY")
    QWEN_API_URL = os.getenv("QWEN_API_URL")  # URL do API Qwen
    QWEN_MODEL = os.getenv("QWEN_MODEL", "qwen-turbo")
    QWEN_TEMPERATURE = float(os.getenv("QWEN_TEMPERATURE", "0.3"))
    
    # Konfiguracja wysyłania emaili
