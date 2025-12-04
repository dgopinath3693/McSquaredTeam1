"""
Configuration settings for FastAPI application
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    database_url: str = "postgresql://mcsq_user:mcsq_pass@localhost:5432/mcsq_db"
    database_host: str = "localhost"
    database_port: int = 5432
    database_name: str = "mcsq_db"
    database_user: str = "mcsq_user"
    database_password: str = "mcsq_pass"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
