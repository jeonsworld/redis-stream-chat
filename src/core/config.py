"""애플리케이션 설정"""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# 프로젝트 루트 디렉토리
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# .env 파일 로드
load_dotenv(BASE_DIR / ".env")


class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # 기본 설정
    app_name: str = "Redis Streaming Demo"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 5000
    
    # Redis 설정
    redis_url: str = "redis://localhost:6379/0"
    
    # OpenAI 설정
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"
    openai_max_tokens: int = 5120
    openai_temperature: float = 0.7
    
    # Celery 설정
    celery_broker_url: Optional[str] = None
    celery_result_backend: Optional[str] = None
    
    # 데이터베이스 설정
    database_url: Optional[str] = None
    
    # 경로 설정
    templates_dir: Path = BASE_DIR / "templates"
    
    class Config:
        env_file = ".env"
        
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Celery URL이 설정되지 않은 경우 Redis URL 사용
        if not self.celery_broker_url:
            self.celery_broker_url = self.redis_url
        if not self.celery_result_backend:
            self.celery_result_backend = self.redis_url


# 싱글톤 설정 인스턴스
settings = Settings()