import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Brightloop Software — Subscription Management System"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "brightloop-super-secure-jwt-secret-key-2026-odoo-assessment")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 60  # 1 hour
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./brightloop.db")
    
    # Company Default Settings
    COMPANY_NAME: str = "Brightloop Software Inc."
    COMPANY_EMAIL: str = "billing@brightloop.com"
    COMPANY_PHONE: str = "+1 (800) 555-LOOP"
    COMPANY_ADDRESS: str = "100 Innovation Way, Suite 400, Tech City, TC 94016"
    CURRENCY: str = "USD"
    CURRENCY_SYMBOL: str = "$"

    class Config:
        case_sensitive = True

settings = Settings()
