"""모니터링 유틸리티"""
import json
import asyncio
from datetime import datetime
from typing import Optional

from src.core.redis import RedisManager
from src.core.celery_app import app as celery_app


class RedisMonitor:
    """Redis Pub/Sub 모니터"""
    
    def __init__(self, channel_pattern: str = "*"):
        self.channel_pattern = channel_pattern
        self.redis = RedisManager()
        
    def monitor(self):
        """채널 모니터링 시작"""
        print(f"Redis Pub/Sub Monitor Started")
        print(f"Channel Pattern: {self.channel_pattern}")
        print("-" * 50)
        
        pubsub = self.redis.client.pubsub()
        pubsub.psubscribe(self.channel_pattern)
        
        try:
            for message in pubsub.listen():
                if message['type'] in ['pmessage', 'message']:
                    timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                    channel = message.get('channel', '').decode('utf-8') if isinstance(message.get('channel'), bytes) else message.get('channel', '')
                    
                    try:
                        data = json.loads(message['data'])
                        print(f"[{timestamp}] {channel}")
                        print(f"  Type: {data.get('type', 'unknown')}")
                        
                        if data.get('type') == 'token':
                            print(f"  Content: {repr(data.get('content', ''))}")
                        elif data.get('type') == 'error':
                            print(f"  Error: {data.get('error', '')}")
                        else:
                            for key, value in data.items():
                                if key != 'type':
                                    print(f"  {key}: {value}")
                    except json.JSONDecodeError:
                        print(f"[{timestamp}] {channel} - RAW: {message['data']}")
                    
                    print()
                    
        except KeyboardInterrupt:
            print("\n모니터링 종료")
        finally:
            pubsub.close()


class CeleryMonitor:
    """Celery 태스크 모니터"""
    
    @staticmethod
    async def monitor_task(task_id: str):
        """특정 태스크 모니터링"""
        from celery.result import AsyncResult
        
        result = AsyncResult(task_id, app=celery_app)
        print(f"Task Monitor: {task_id}")
        print("-" * 50)
        
        last_state = None
        
        try:
            while True:
                current_state = result.state
                
                if current_state != last_state:
                    timestamp = datetime.now().strftime('%H:%M:%S')
                    print(f"[{timestamp}] State: {current_state}")
                    
                    if result.info:
                        print(f"  Info: {result.info}")
                    
                    last_state = current_state
                    
                    if current_state in ['SUCCESS', 'FAILURE']:
                        if current_state == 'SUCCESS':
                            print(f"\n최종 결과: {result.result}")
                        else:
                            print(f"\n실패: {result.info}")
                        break
                
                await asyncio.sleep(0.5)
                
        except KeyboardInterrupt:
            print("\n모니터링 종료")
    
    @staticmethod
    def list_active_tasks():
        """활성 태스크 목록"""
        inspect = celery_app.control.inspect()
        
        print("Active Tasks")
        print("-" * 50)
        
        # 활성 태스크
        active = inspect.active()
        if active:
            for worker, tasks in active.items():
                print(f"\nWorker: {worker}")
                for task in tasks:
                    print(f"  - ID: {task['id']}")
                    print(f"    Name: {task['name']}")
                    print(f"    Args: {task.get('args', [])}")
        else:
            print("No active tasks")
        
        # 예약된 태스크
        scheduled = inspect.scheduled()
        if scheduled:
            print("\nScheduled Tasks:")
            for worker, tasks in scheduled.items():
                print(f"\nWorker: {worker}")
                for task in tasks:
                    print(f"  - {task}")