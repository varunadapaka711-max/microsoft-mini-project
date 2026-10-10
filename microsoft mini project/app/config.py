import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Bulk Certificate Generator API"
    VERSION: str = "1.0.0"
    DATABASE_URL: str = "sqlite:///./certificates_db.sqlite"
    STORAGE_DIR: str = os.path.join(os.getcwd(), "storage", "certificates")
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()

os.makedirs(settings.STORAGE_DIR, exist_ok=True)
