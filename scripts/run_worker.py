#!/usr/bin/env python3
"""Celery 워커 실행 스크립트"""
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.celery_app import app

if __name__ == '__main__':
    app.worker_main(['worker', '--loglevel=info'])