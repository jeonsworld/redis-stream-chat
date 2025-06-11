"""Celery 태스크 정의"""
import logging
import time
from typing import Dict, Any
from celery import Task
from openai import OpenAI

from src.core.celery_app import app
from src.core.redis import redis_manager
from src.core.config import settings
from src.models.schemas import StreamMessage
from src.core.database import db_chat_store, MessageStatus

logger = logging.getLogger(__name__)

# OpenAI 클라이언트
openai_client = OpenAI(api_key=settings.openai_api_key)


class ChatTask(Task):
    """채팅 태스크 기본 클래스"""
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """태스크 실패 시 처리"""
        channel = f"chat:{kwargs.get('task_id', task_id)}"
        error_msg = StreamMessage(
            type="error",
            error=str(exc)
        )
        redis_manager.publish(channel, error_msg.model_dump())
        
        # 채팅 저장소 업데이트
        if len(args) >= 2:
            db_chat_store.update_message_status(args[1], MessageStatus.FAILED, error=f"Error: {str(exc)}")
        

@app.task(base=ChatTask, bind=True, name='chat.process_message')
def process_chat_message(self, user_message: str, task_id: str, chat_id: str) -> Dict[str, Any]:
    """사용자 메시지를 처리하고 LLM 응답을 스트리밍
    
    Args:
        user_message: 사용자 입력 메시지
        task_id: 고유 태스크 ID
        chat_id: 채팅 ID
        
    Returns:
        처리 결과 딕셔너리
    """
    channel = f"chat:{task_id}"
    
    try:
        logger.info(f"Starting task {task_id} for chat {chat_id}")
        
        # 상태 업데이트: PROCESSING
        db_chat_store.update_message_status(task_id, MessageStatus.PROCESSING)
        logger.info(f"Updated status to processing for task {task_id}")
        
        # 시작 메시지
        start_msg = StreamMessage(
            type="start",
            content="처리를 시작합니다..."
        )
        redis_manager.publish(channel, start_msg.model_dump())
        logger.info(f"Published start message to channel {channel}")
        
        # 진행 상태 업데이트
        self.update_state(
            state='PROCESSING',
            meta={'status': '모델 호출 중...', 'progress': 10}
        )
        
        progress_msg = StreamMessage(
            type="progress",
            content="OpenAI 모델에 요청을 보내는 중...",
            progress=10
        )
        redis_manager.publish(channel, progress_msg.model_dump())
        
        # 상태 업데이트: STREAMING
        db_chat_store.update_message_status(task_id, MessageStatus.STREAMING)
        logger.info(f"Updated status to streaming for task {task_id}")
        
        # OpenAI 스트리밍 호출
        logger.info(f"Calling OpenAI API with model {settings.openai_model}")
        stream = openai_client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": "당신은 도움이 되는 AI 어시스턴트입니다."},
                {"role": "user", "content": user_message}
            ],
            stream=True,
            temperature=settings.openai_temperature,
            max_tokens=settings.openai_max_tokens
        )
        logger.info("OpenAI stream created successfully")
        
        # 스트리밍 응답 처리
        full_response = ""
        token_count = 0
        
        for chunk in stream:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_response += content
                token_count += 1
                
                # 토큰 발행
                token_msg = StreamMessage(
                    type="token",
                    content=content,
                    token_count=token_count
                )
                redis_manager.publish(channel, token_msg.model_dump())
                
                # 응답 내용 저장
                db_chat_store.append_message_content(task_id, content)
                
                # 진행률 업데이트 (10토큰마다)
                if token_count % 10 == 0:
                    progress = min(10 + (token_count / 10), 90)
                    self.update_state(
                        state='PROCESSING',
                        meta={
                            'status': f'토큰 생성 중... ({token_count}개)',
                            'progress': progress
                        }
                    )
        
        # 상태 업데이트: COMPLETED
        db_chat_store.update_message_status(task_id, MessageStatus.COMPLETED)
        
        # 완료 메시지
        complete_msg = StreamMessage(
            type="complete",
            content=full_response,
            token_count=token_count
        )
        redis_manager.publish(channel, complete_msg.model_dump())
        
        # 최종 결과 반환
        return {
            'status': 'completed',
            'response': full_response,
            'token_count': token_count,
            'task_id': task_id,
            'duration': time.time() - start_msg.timestamp
        }
        
    except Exception as e:
        logger.error(f"Task failed: {e}", exc_info=True)
        # on_failure에서 에러 메시지 발행
        raise