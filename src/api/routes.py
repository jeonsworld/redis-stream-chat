"""API 라우트 정의"""
import json
import uuid
import asyncio
from typing import AsyncGenerator, Optional

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sse_starlette.sse import EventSourceResponse
from celery.result import AsyncResult

from src.core.celery_app import app as celery_app
from src.core.redis import RedisManager
from src.core.config import settings
from src.models.schemas import ChatRequest, ChatResponse, TaskStatus, HealthResponse
from src.services.tasks import process_chat_message
from src.core.database import db_chat_store, MessageType, MessageStatus

# 라우터 생성
router = APIRouter()

# 템플릿 설정
templates = Jinja2Templates(directory=str(settings.templates_dir))


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """메인 페이지"""
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "app_name": settings.app_name}
    )


@router.post("/api/chats/{chat_id}/messages")
async def send_message(chat_id: str, request: ChatRequest):
    """채팅에 메시지 전송"""
    # 채팅 확인 (여기서는 존재 여부만 확인)
    if not db_chat_store.get_chat(chat_id):
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # 태스크 ID 생성
    task_id = str(uuid.uuid4())
    
    # 사용자 메시지 저장
    db_chat_store.add_message(
        chat_id=chat_id,
        task_id=f"user-{task_id}",
        type=MessageType.USER,
        content=request.message,
        status=MessageStatus.COMPLETED
    )
    
    # AI 응답 메시지 준비
    db_chat_store.add_message(
        chat_id=chat_id,
        task_id=task_id,
        type=MessageType.ASSISTANT,
        content="",
        status=MessageStatus.PENDING
    )
    
    # Celery 태스크 실행
    task = process_chat_message.apply_async(
        args=[request.message, task_id, chat_id],
        task_id=task_id
    )
    
    return {
        "task_id": task_id,
        "status": "started",
        "stream_url": f"/api/stream/{task_id}"
    }


@router.get("/api/stream/{task_id}")
async def stream_chat(task_id: str):
    """SSE 스트리밍 엔드포인트"""
    
    async def event_generator() -> AsyncGenerator[dict, None]:
        channel = f"chat:{task_id}"
        
        # 연결 확인 메시지
        yield {
            "event": "message",
            "data": json.dumps({"type": "connected", "task_id": task_id})
        }
        
        # 새 Redis 매니저 인스턴스 생성 (스레드 안전성)
        redis = RedisManager()
        
        try:
            # Redis 메시지 스트리밍
            for message in redis.subscribe(channel):
                yield {
                    "event": "message",
                    "data": json.dumps(message)
                }
                
                # 완료 또는 에러 시 종료
                if message.get('type') in ['complete', 'error']:
                    break
                
                # 이벤트 루프에 제어권 양보
                await asyncio.sleep(0)
                
        except asyncio.CancelledError:
            # 클라이언트 연결 끊김
            raise
        except Exception as e:
            yield {
                "event": "message",
                "data": json.dumps({
                    "type": "error",
                    "error": f"Stream error: {str(e)}"
                })
            }
        finally:
            redis.close()
    
    return EventSourceResponse(event_generator())


@router.get("/api/task/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """태스크 상태 조회"""
    result = AsyncResult(task_id, app=celery_app)
    
    if not result:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return TaskStatus(
        task_id=task_id,
        state=result.state,
        info=result.info
    )


@router.post("/api/chats")
async def create_chat():
    """새 채팅 생성"""
    chat = db_chat_store.create_chat()
    return {
        "chat_id": str(chat.id),
        "title": chat.title,
        "created_at": chat.created_at.isoformat()
    }


@router.get("/api/chats")
async def get_chats():
    """모든 채팅 목록 조회"""
    chats = db_chat_store.get_all_chats()
    return {
        "chats": [
            {
                "chat_id": chat["id"],
                "title": chat["title"],
                "updated_at": chat["updated_at"].isoformat(),
                "message_count": chat["message_count"]
            }
            for chat in chats
        ]
    }


@router.get("/api/chats/{chat_id}")
async def get_chat(chat_id: str):
    """특정 채팅 조회"""
    chat = db_chat_store.get_chat(chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    return {
        "chat_id": chat["id"],
        "title": chat["title"],
        "status": chat["status"],
        "created_at": chat["created_at"].isoformat(),
        "updated_at": chat["updated_at"].isoformat(),
        "messages": [
            {
                "task_id": msg["task_id"],
                "type": msg["type"],
                "content": msg["content"],
                "status": msg["status"],
                "created_at": msg["created_at"].isoformat()
            }
            for msg in chat["messages"]
        ]
    }


@router.delete("/api/chats/{chat_id}")
async def delete_chat(chat_id: str):
    """채팅 삭제"""
    chat = db_chat_store.get_chat(chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    db_chat_store.delete_chat(chat_id)
    return {"status": "deleted"}


@router.get("/api/chats/{chat_id}/active-task")
async def get_active_task(chat_id: str):
    """채팅의 활성 작업 조회"""
    chat = db_chat_store.get_chat(chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    active_task_id = db_chat_store.get_active_task(chat_id)
    if active_task_id:
        # 활성 메시지 찾기
        for message in chat["messages"]:
            if message["task_id"] == active_task_id:
                return {
                    "task_id": active_task_id,
                    "status": message["status"],
                    "content": message["content"]
                }
    
    return {"task_id": None}


@router.get("/api/health", response_model=HealthResponse)
async def health_check():
    """헬스체크"""
    from src.core.redis import redis_manager
    import time
    
    redis_status = "connected" if redis_manager.health_check() else "disconnected"
    
    return HealthResponse(
        status="ok" if redis_status == "connected" else "error",
        redis=redis_status,
        timestamp=time.time()
    )