"""데이터베이스 설정 및 모델"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import create_engine, Column, String, Text, DateTime, Enum, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.dialects.postgresql import UUID
import uuid
import enum

from src.core.config import settings

# 데이터베이스 URL
DATABASE_URL = settings.database_url or "postgresql://streaming_user:streaming_pass@localhost:5432/streaming_db"

# SQLAlchemy 설정
engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_size=10, max_overflow=20)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class ChatStatus(str, enum.Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class MessageType(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    ERROR = "error"


class MessageStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    STREAMING = "streaming"
    COMPLETED = "completed"
    FAILED = "failed"


class Chat(Base):
    __tablename__ = "chats"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False, default="새 채팅")
    status = Column(Enum(ChatStatus), nullable=False, default=ChatStatus.ACTIVE)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계
    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan")
    
    # 인덱스
    __table_args__ = (
        Index('idx_chat_status', 'status'),
        Index('idx_chat_updated_at', 'updated_at'),
    )


class Message(Base):
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_id = Column(UUID(as_uuid=True), ForeignKey('chats.id', ondelete='CASCADE'), nullable=False)
    task_id = Column(String(255), nullable=False, unique=True, index=True)
    type = Column(Enum(MessageType), nullable=False)
    content = Column(Text, nullable=False, default="")
    status = Column(Enum(MessageStatus), nullable=False, default=MessageStatus.PENDING)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계
    chat = relationship("Chat", back_populates="messages")
    
    # 인덱스
    __table_args__ = (
        Index('idx_message_chat_id', 'chat_id'),
        Index('idx_message_task_id', 'task_id'),
        Index('idx_message_status', 'status'),
    )


def get_db():
    """데이터베이스 세션 생성"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """데이터베이스 초기화"""
    Base.metadata.create_all(bind=engine)


class DatabaseChatStore:
    """PostgreSQL 기반 채팅 저장소"""
    
    def __init__(self):
        self.SessionLocal = SessionLocal
    
    def create_chat(self, title: Optional[str] = None) -> Chat:
        """새 채팅 생성"""
        db = SessionLocal()
        try:
            chat = Chat(title=title or "새 채팅")
            db.add(chat)
            db.commit()
            db.refresh(chat)
            return chat
        finally:
            db.close()
    
    def get_chat(self, chat_id: str) -> Optional[dict]:
        """채팅 조회"""
        db = SessionLocal()
        try:
            chat = db.query(Chat).filter(Chat.id == chat_id).first()
            if not chat:
                return None
            
            # 채팅 정보와 메시지를 미리 로드
            result = {
                "id": str(chat.id),
                "title": chat.title,
                "status": chat.status.value,
                "created_at": chat.created_at,
                "updated_at": chat.updated_at,
                "messages": [
                    {
                        "task_id": msg.task_id,
                        "type": msg.type.value,
                        "content": msg.content,
                        "status": msg.status.value,
                        "created_at": msg.created_at
                    }
                    for msg in chat.messages
                ]
            }
            return result
        finally:
            db.close()
    
    def get_all_chats(self, include_archived: bool = False) -> List[Chat]:
        """모든 채팅 조회"""
        db = SessionLocal()
        try:
            query = db.query(Chat)
            if not include_archived:
                query = query.filter(Chat.status == ChatStatus.ACTIVE)
            chats = query.order_by(Chat.updated_at.desc()).all()
            
            # 채팅 목록을 반환하기 전에 필요한 정보를 미리 로드
            result = []
            for chat in chats:
                chat_dict = {
                    "id": str(chat.id),
                    "title": chat.title,
                    "status": chat.status,
                    "created_at": chat.created_at,
                    "updated_at": chat.updated_at,
                    "message_count": len(chat.messages)  # 세션이 열려있을 때 로드
                }
                result.append(chat_dict)
            return result
        finally:
            db.close()
    
    def get_chat_by_task_id(self, task_id: str) -> Optional[Chat]:
        """태스크 ID로 채팅 조회"""
        db = SessionLocal()
        try:
            message = db.query(Message).filter(Message.task_id == task_id).first()
            if message:
                return message.chat
            return None
        finally:
            db.close()
    
    def add_message(self, chat_id: str, task_id: str, type: MessageType, 
                   content: str = "", status: MessageStatus = MessageStatus.PENDING) -> Message:
        """채팅에 메시지 추가"""
        db = SessionLocal()
        try:
            message = Message(
                chat_id=chat_id,
                task_id=task_id,
                type=type,
                content=content,
                status=status
            )
            db.add(message)
            
            # 채팅 업데이트 시간 갱신
            chat = db.query(Chat).filter(Chat.id == chat_id).first()
            if chat:
                chat.updated_at = datetime.utcnow()
                
                # 첫 사용자 메시지로 제목 설정
                if type == MessageType.USER and chat.title == "새 채팅":
                    chat.title = content[:50] + "..." if len(content) > 50 else content
            
            db.commit()
            db.refresh(message)
            return message
        finally:
            db.close()
    
    def update_message_status(self, task_id: str, status: MessageStatus, 
                            content: Optional[str] = None, error: Optional[str] = None):
        """메시지 상태 업데이트"""
        db = SessionLocal()
        try:
            message = db.query(Message).filter(Message.task_id == task_id).first()
            if message:
                message.status = status
                if content is not None:
                    message.content = content
                if error is not None:
                    message.error = error
                message.updated_at = datetime.utcnow()
                db.commit()
        finally:
            db.close()
    
    def append_message_content(self, task_id: str, content: str):
        """메시지 내용 추가 (스트리밍용)"""
        db = SessionLocal()
        try:
            message = db.query(Message).filter(Message.task_id == task_id).first()
            if message:
                message.content += content
                message.updated_at = datetime.utcnow()
                db.commit()
        finally:
            db.close()
    
    def delete_chat(self, chat_id: str):
        """채팅 삭제"""
        db = SessionLocal()
        try:
            chat = db.query(Chat).filter(Chat.id == chat_id).first()
            if chat:
                db.delete(chat)
                db.commit()
        finally:
            db.close()
    
    def archive_chat(self, chat_id: str):
        """채팅 아카이브"""
        db = SessionLocal()
        try:
            chat = db.query(Chat).filter(Chat.id == chat_id).first()
            if chat:
                chat.status = ChatStatus.ARCHIVED
                chat.updated_at = datetime.utcnow()
                db.commit()
        finally:
            db.close()
    
    def get_active_task(self, chat_id: str) -> Optional[str]:
        """채팅의 활성 작업 ID 반환"""
        db = SessionLocal()
        try:
            message = db.query(Message).filter(
                Message.chat_id == chat_id,
                Message.status.in_([MessageStatus.PENDING, MessageStatus.PROCESSING, MessageStatus.STREAMING])
            ).order_by(Message.created_at.desc()).first()
            
            return message.task_id if message else None
        finally:
            db.close()


# 싱글톤 인스턴스
db_chat_store = DatabaseChatStore()