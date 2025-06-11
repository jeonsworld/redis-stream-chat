"""API 요청/응답 스키마"""
from pydantic import BaseModel, Field
from typing import Optional, Literal, Dict, Any
from datetime import datetime


class ChatRequest(BaseModel):
    """채팅 요청 모델"""
    message: str = Field(..., min_length=1, max_length=1000, description="사용자 메시지")


class ChatResponse(BaseModel):
    """채팅 응답 모델"""
    task_id: str = Field(..., description="태스크 ID")
    status: str = Field(..., description="태스크 상태")
    stream_url: str = Field(..., description="SSE 스트림 URL")


class TaskStatus(BaseModel):
    """태스크 상태 모델"""
    task_id: str
    state: str
    info: Optional[Dict[str, Any]] = None


class StreamMessage(BaseModel):
    """스트림 메시지 모델"""
    type: Literal["start", "progress", "token", "complete", "error"]
    content: Optional[str] = None
    token_count: Optional[int] = None
    progress: Optional[int] = None
    error: Optional[str] = None
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp())
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "type": "token",
                    "content": "Hello",
                    "token_count": 1,
                    "timestamp": 1234567890.123
                },
                {
                    "type": "progress",
                    "progress": 50,
                    "timestamp": 1234567890.123
                },
                {
                    "type": "error",
                    "error": "Connection failed",
                    "timestamp": 1234567890.123
                }
            ]
        }


class HealthResponse(BaseModel):
    """헬스체크 응답 모델"""
    status: Literal["ok", "error"]
    redis: Literal["connected", "disconnected"]
    timestamp: float