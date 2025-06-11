# Redis Stream Chat

Redis Pub/Sub + Celery + FastAPI + PostgreSQL을 사용한 실시간 스트리밍 아키텍처 구현

## 주요 기능

- **실시간 스트리밍**: OpenAI API 응답을 토큰 단위로 스트리밍
- **비동기 처리**: Celery를 통한 백그라운드 작업 처리
- **확장 가능한 아키텍처**: 여러 워커로 수평 확장 가능
- **영구 저장소**: PostgreSQL로 채팅 이력 및 메시지 저장
- **다중 채팅 세션**: 동시에 여러 대화 관리
- **시스템 모니터링**: 내장된 Redis 및 Celery 모니터링 도구

## 빠른 시작

### Docker Compose 사용 (권장)

```bash
# 저장소 클론
git clone <repository-url>
cd redis-streaming

# 환경 설정
cp .env.example .env
# .env 파일을 편집하여 OPENAI_API_KEY 설정

# 모든 서비스 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 애플리케이션 접속
# 브라우저에서 http://localhost:5000 열기
```

### 수동 설치

#### 1. 사전 요구사항

- Python 3.8+
- Redis
- PostgreSQL
- OpenAI API key

#### 2. 설치

```bash
# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경 설정
cp .env.example .env
# .env 파일을 편집하여 필요한 모든 변수 설정
```

#### 3. 서비스 시작

```bash
# PostgreSQL 시작 (Docker 사용)
docker-compose -f docker-compose.postgres.yml up -d

# 또는 로컬 설치
brew install postgresql redis  # macOS
brew services start postgresql redis

# 데이터베이스 초기화
python scripts/init_db.py
```

#### 4. 애플리케이션 실행

각 서비스별로 별도의 터미널을 열어 실행:

```bash
# 터미널 1: Celery Worker
python scripts/run_worker.py

# 터미널 2: FastAPI Server
python scripts/run_server.py

# 터미널 3: Redis Monitor (선택사항)
python scripts/monitor_redis.py
```

## 프로젝트 구조

```
redis-streaming/
├── src/
│   ├── api/              # API 엔드포인트
│   ├── core/             # 핵심 모듈 (config, database, redis, celery)
│   ├── models/           # 데이터 모델 및 스키마
│   ├── services/         # 비즈니스 로직
│   └── utils/            # 유틸리티
├── scripts/              # 유틸리티 스크립트
│   ├── run_server.py     # FastAPI 서버 시작
│   ├── run_worker.py     # Celery 워커 시작
│   ├── init_db.py        # 데이터베이스 초기화
│   ├── clear_db.py       # 모든 데이터 삭제
│   ├── reset_db.py       # 데이터베이스 스키마 리셋
│   └── monitor_*.py      # 모니터링 도구
├── templates/            # HTML 템플릿
├── docs/                 # 문서
│   └── architecture.md   # 상세 아키텍처
├── docker-compose.yml    # Docker 서비스
└── requirements.txt      # Python 의존성
```

## API 엔드포인트

### 채팅 관리
- `POST /api/chats` - 새 채팅 생성
- `GET /api/chats` - 모든 채팅 목록 조회
- `GET /api/chats/{chat_id}` - 특정 채팅 조회
- `DELETE /api/chats/{chat_id}` - 채팅 삭제

### 메시징
- `POST /api/chats/{chat_id}/messages` - 메시지 전송
- `GET /api/chats/{chat_id}/active-task` - 활성 작업 조회

### 스트리밍
- `GET /api/stream/{task_id}` - 실시간 스트리밍을 위한 SSE 엔드포인트

### 시스템
- `GET /api/health` - 헬스 체크
- `GET /api/task/{task_id}` - 태스크 상태
- `GET /docs` - API 문서 (Swagger UI)

## 설정

### 환경 변수

`.env` 파일 생성:

```env
# OpenAI
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_TOKENS=1000
OPENAI_TEMPERATURE=0.7

# Redis
REDIS_URL=redis://localhost:6379/0

# PostgreSQL
DATABASE_URL=postgresql://streaming_user:streaming_pass@localhost:5432/streaming_db

# Application
DEBUG=true
HOST=0.0.0.0
PORT=5000
```

## 모니터링

### Redis 모니터링
```bash
# 모든 Redis pub/sub 채널 모니터링
python scripts/monitor_redis.py

# 특정 패턴 모니터링
python scripts/monitor_redis.py "chat:*"
```

### Celery 모니터링
```bash
# 모든 태스크 목록
python scripts/monitor_celery.py list

# 특정 태스크 모니터링
python scripts/monitor_celery.py <task_id>
```

## 데이터베이스 관리

### 데이터베이스 초기화
```bash
python scripts/init_db.py
```

### 모든 데이터 삭제
```bash
python scripts/clear_db.py
```

### 데이터베이스 리셋 (테이블 삭제 후 재생성)
```bash
python scripts/reset_db.py
```

## 아키텍처

Microservice 아키텍처를 사용:

- **FastAPI**: API 및 SSE를 위한 비동기 웹 서버
- **Celery**: 비동기 처리를 위한 분산 태스크 큐
- **Redis**: 메시지 브로커 및 실시간 스트리밍을 위한 pub/sub
- **PostgreSQL**: 채팅 및 메시지를 위한 영구 저장소
- **OpenAI API**: 응답 생성을 위한 AI 모델

자세한 아키텍처 문서는 [architecture.md](docs/architecture.md)를 참조.

## 개발

### 테스트 실행
```bash
# 수동 API 테스트
python scripts/testing/test_api.py
python scripts/testing/test_openai.py
```
