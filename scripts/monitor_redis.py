#!/usr/bin/env python3
"""Redis 모니터링 스크립트"""
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.monitoring import RedisMonitor

if __name__ == '__main__':
    channel = sys.argv[1] if len(sys.argv) > 1 else 'chat:*'
    monitor = RedisMonitor(channel)
    monitor.monitor()