# Redis Pub/Sub + Celery Streaming Architecture

## 개요

이 프로젝트는 Redis Pub/Sub, Celery, Server-Sent Events (SSE)를 사용하여 PostgreSQL 영구 저장소와 함께 비동기 AI 기반 채팅 대화를 처리하는 실시간 스트리밍 아키텍처를 구현합니다.

## 시스템 아키텍처

```
┌─────────────┐                          ┌─────────────┐                     ┌─────────────┐
│   Browser   │  1. POST /api/chats/     │   FastAPI   │   2. Save Message   │ PostgreSQL  │
│  (Client)   │     {chat_id}/messages   │   Server    │────────────────────▶│  Database   │
│             │─────────────────────────▶│             │                     │             │
│             │                          │             │                     └─────────────┘
│             │  9. SSE Stream           │             │
│             │◀─────────────────────────│             │
└─────────────┘     (실시간 토큰)           └──────┬──────┘
                                                │ ▲
                                                │ │
                               3. Create Task   │ │ 8. Subscribe & Forward
                                   to Queue     │ │    (chat:{task_id})
                                                ▼ │
                                        ┌────────────────────────────┐
                                        │         Redis              │
                                        │  ┌──────────────────────┐  │
                                        │  │   Celery Broker      │  │
                                        │  │   (Task Queue)       │  │
                                        │  └──────────┬───────────┘  │
                                        │             │ 4. Get Task  │
                                        │             ▼              │
                                        │  ┌──────────────────────┐  │
                                        │  │    Pub/Sub Channel   │  │
                                        │  │   (chat:{task_id})   │  │
                                        │  └──────────▲───────────┘  │
                                        └─────────────┼──────────────┘
                                                      │ 7. Publish Tokens
┌─────────────┐     5. Call API         ┌─────────────┴──────────┐
│   OpenAI    │◀────────────────────────│    Celery Worker       │
│     API     │  (Streaming Mode)       │                        │
│             │────────────────────────▶│                        │
└─────────────┘  6. Stream Response     └────────────────────────┘
                    (Token by Token)
```

## 데이터 흐름

1. **POST Message**: 사용자가 브라우저에서 채팅 메시지를 FastAPI 서버로 전송
2. **Store**: FastAPI가 메시지를 PostgreSQL에 저장
3. **Create Task**: FastAPI가 Celery 태스크를 Redis Broker에 생성
4. **Pick Task**: Celery Worker가 Redis Broker에서 태스크를 가져옴
5. **Call**: Celery Worker가 OpenAI API를 스트리밍 모드로 호출
6. **Stream Tokens**: OpenAI가 응답을 토큰 단위로 스트리밍
7. **Publish**: Celery Worker가 각 토큰을 Redis Pub/Sub 채널(`chat:{task_id}`)에 발행
8. **Subscribe**: FastAPI가 해당 Redis 채널을 구독하여 토큰 수신
9. **SSE Stream**: FastAPI가 Server-Sent Events를 통해 브라우저로 실시간 전송

## 핵심 컴포넌트

### 1. FastAPI Server (`src/main.py`)
- HTTP 요청 및 WebSocket 연결 처리
- 실시간 스트리밍을 위한 SSE 연결 관리
- RESTful API 엔드포인트 제공
- 웹 인터페이스 제공

### 2. Celery Workers (`src/services/tasks.py`)
- 채팅 메시지를 비동기적으로 처리
- OpenAI API와 통합
- 토큰을 Redis 채널에 발행
- PostgreSQL에서 메시지 상태 업데이트

### 3. Redis Pub/Sub (`src/core/redis.py`)
- Celery 태스크를 위한 메시지 브로커
- 스트리밍 토큰을 위한 실시간 pub/sub
- 채널 패턴: `chat:{task_id}`

### 4. PostgreSQL Database (`src/core/database.py`)
- 채팅 및 메시지를 위한 영구 저장소
- SQLAlchemy ORM 모델
- 동시 접근 지원
- 채팅 이력 유지

### 5. Web Interface (`templates/index.html`)
- 채팅 UI
- 다중 동시 채팅 세션
- 실시간 메시지 스트리밍
- 시스템 로그 뷰어
