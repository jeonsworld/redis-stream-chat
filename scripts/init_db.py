#!/usr/bin/env python3
"""데이터베이스 초기화 스크립트"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.database import init_db, engine, Base
from sqlalchemy import text

def check_database_connection():
    """데이터베이스 연결 확인"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✓ 데이터베이스 연결 성공")
            return True
    except Exception as e:
        print(f"✗ 데이터베이스 연결 실패: {e}")
        return False

def create_tables():
    """테이블 생성"""
    try:
        init_db()
        print("✓ 테이블 생성 완료")
        return True
    except Exception as e:
        print(f"✗ 테이블 생성 실패: {e}")
        return False

def main():
    """메인 함수"""
    print("데이터베이스 초기화 시작...")
    
    if not check_database_connection():
        print("\nPostgreSQL이 실행 중인지 확인하세요:")
        print("  docker-compose -f docker-compose.postgres.yml up -d")
        return 1
    
    if not create_tables():
        return 1
    
    print("\n✓ 데이터베이스 초기화 완료!")
    return 0

if __name__ == "__main__":
    sys.exit(main())