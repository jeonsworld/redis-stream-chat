#!/usr/bin/env python3
"""Celery 모니터링 스크립트"""
import sys
import os
import asyncio

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.monitoring import CeleryMonitor

if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == 'list':
            CeleryMonitor.list_active_tasks()
        else:
            asyncio.run(CeleryMonitor.monitor_task(sys.argv[1]))
    else:
        print("Usage:")
        print("  python monitor_celery.py <task_id>  # Monitor specific task")
        print("  python monitor_celery.py list       # List active tasks")