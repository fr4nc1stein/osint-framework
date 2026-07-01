"""Application Configuration"""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # Application
    APP_NAME: str = "OSIF v2.0"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://osif:osif@localhost:5432/osif"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_POOL_SIZE: int = 10
    
    # API Server
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 6000
    API_WORKERS: int = 4
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    # Worker
    WORKER_CONCURRENCY: int = 4
    REQUEST_DELAY_MS: int = 500
    
    # External APIs (from OSIF v1)
    VT_API: str = ""
    SHODAN_API_KEY: str = ""
    ABUSEIPDB_API_KEY: str = ""
    HUNTER_API_KEY: str = ""
    TOMBA_API_KEY: str = ""
    TOMBA_SECRET_KEY: str = ""
    CENSYS_APPID: str = ""
    CENSYS_SECRET: str = ""
    ABUSECH_API_KEY: str = ""
    BITCOINABUSE_API_KEY: str = ""
    WIGLE_API_NAME: str = ""
    WIGLE_API_TOKEN: str = ""
    SECURITY_TRAIL_API: str = ""
    
    # Security (Phase 2)
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7


settings = Settings()
