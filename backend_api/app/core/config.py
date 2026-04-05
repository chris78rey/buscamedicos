from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    APP_ENV: str = "development"
    DEBUG: bool = True
    
    DATABASE_URL: str = "postgresql+asyncpg://buscamedicos:changeme123@localhost:5432/buscamedicos"
    
    SECRET_KEY: str = "changeme-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    REDIS_URL: Optional[str] = None
    
    FILES_PATH: str = "./files"
    MAX_FILE_SIZE_MB: int = 10
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()