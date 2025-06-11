#!/usr/bin/env python3
"""데이터베이스 완전 리셋 스크립트 (테이블 재생성)"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.database import Base, engine, init_db
from sqlalchemy import text

def drop_all_tables():
    """모든 테이블 삭제"""
    try:
        # 모든 테이블 삭제
        Base.metadata.drop_all(bind=engine)
        print("✓ 모든 테이블 삭제됨")
        return True
    except Exception as e:
        print(f"✗ 테이블 삭제 실패: {e}")
        return False

def create_all_tables():
    """모든 테이블 재생성"""
    try:
        init_db()
        print("✓ 모든 테이블 재생성됨")
        return True
    except Exception as e:
        print(f"✗ 테이블 생성 실패: {e}")
        return False

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

def confirm_action():
    """사용자 확인"""
    print("\n⚠️  경고: 이 작업은 모든 테이블을 삭제하고 재생성합니다!")
    print("모든 데이터가 영구적으로 삭제됩니다!")
    print("\n정말로 계속하시겠습니까? (yes/no): ", end="")
    
    response = input().strip().lower()
    return response == 'yes'

def main():
    """메인 함수"""
    print("데이터베이스 완전 리셋 스크립트")
    print("=" * 40)
    
    # 데이터베이스 연결 확인
    if not check_database_connection():
        print("\nPostgreSQL이 실행 중인지 확인하세요:")
        print("  docker-compose -f docker-compose.postgres.yml up -d")
        return 1
    
    # 사용자 확인
    if not confirm_action():
        print("\n취소되었습니다.")
        return 0
    
    print("\n데이터베이스 리셋 중...")
    
    # 테이블 삭제
    if not drop_all_tables():
        return 1
    
    # 테이블 재생성
    if not create_all_tables():
        return 1
    
    print("\n✓ 데이터베이스가 완전히 리셋되었습니다!")
    print("  - 모든 테이블이 재생성되었습니다")
    print("  - 모든 데이터가 삭제되었습니다")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())