"""Redis 연결 및 Pub/Sub 관리"""
import redis
import json
import logging
from typing import Optional, Generator, Dict, Any
from src.core.config import settings

logger = logging.getLogger(__name__)


class RedisManager:
    """Redis 연결 및 Pub/Sub 관리 클래스"""
    
    def __init__(self, url: Optional[str] = None):
        self.url = url or settings.redis_url
        self._client = None
        self._pubsub = None
        
    @property
    def client(self) -> redis.Redis:
        """Redis 클라이언트 (lazy loading)"""
        if self._client is None:
            self._client = redis.from_url(self.url, decode_responses=True)
        return self._client
        
    def publish(self, channel: str, message: Dict[str, Any]) -> int:
        """채널에 메시지 발행
        
        Args:
            channel: 발행할 채널명
            message: 발행할 메시지 (dict)
            
        Returns:
            구독자 수
        """
        try:
            return self.client.publish(channel, json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
            raise
    
    def subscribe(self, channel: str) -> Generator[Dict[str, Any], None, None]:
        """채널 구독 및 메시지 스트림
        
        Args:
            channel: 구독할 채널명
            
        Yields:
            수신된 메시지 (dict)
        """
        pubsub = self.client.pubsub()
        
        try:
            pubsub.subscribe(channel)
            
            for message in pubsub.listen():
                if message['type'] == 'message':
                    try:
                        data = json.loads(message['data'])
                        yield data
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON received: {message['data']}")
                        yield {'error': 'Invalid JSON', 'raw': message['data']}
                        
        except Exception as e:
            logger.error(f"Subscription error: {e}")
            raise
        finally:
            pubsub.unsubscribe(channel)
            pubsub.close()
    
    def health_check(self) -> bool:
        """Redis 연결 상태 확인"""
        try:
            return self.client.ping()
        except:
            return False
            
    def close(self):
        """연결 종료"""
        if self._client:
            self._client.close()
            self._client = None


# 전역 Redis 매니저 인스턴스
redis_manager = RedisManager()