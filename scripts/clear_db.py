#!/usr/bin/env python3
"""데이터베이스 데이터 초기화 스크립트"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.database import SessionLocal, Chat, Message, engine
from sqlalchemy import text

def clear_all_data():
    """모든 데이터 삭제"""
    db = SessionLocal()
    try:
        # 모든 메시지 삭제 (외래 키 제약 때문에 먼저 삭제)
        deleted_messages = db.query(Message).delete()
        print(f"✓ {deleted_messages}개의 메시지 삭제됨")
        
        # 모든 채팅 삭제
        deleted_chats = db.query(Chat).delete()
        print(f"✓ {deleted_chats}개의 채팅 삭제됨")
        
        # 변경사항 커밋
        db.commit()
        print("✓ 데이터베이스 초기화 완료")
        
    except Exception as e:
        db.rollback()
        print(f"✗ 오류 발생: {e}")
        return False
    finally:
        db.close()
    
    return True

def reset_sequences():
    """시퀀스 리셋 (PostgreSQL)"""
    try:
        with engine.connect() as conn:
            # PostgreSQL의 경우 시퀀스 리셋은 필요없음 (UUID 사용)
            # 하지만 통계 정보는 업데이트
            conn.execute(text("ANALYZE"))
            conn.commit()
            print("✓ 데이터베이스 통계 업데이트됨")
    except Exception as e:
        print(f"⚠ 통계 업데이트 실패 (무시 가능): {e}")

def confirm_action():
    """사용자 확인"""
    print("\n⚠️  경고: 이 작업은 모든 채팅과 메시지를 삭제합니다!")
    print("계속하시겠습니까? (yes/no): ", end="")
    
    response = input().strip().lower()
    return response == 'yes'

def main():
    """메인 함수"""
    print("데이터베이스 초기화 스크립트")
    print("=" * 40)
    
    if not confirm_action():
        print("\n취소되었습니다.")
        return 0
    
    print("\n데이터 삭제 중...")
    
    if clear_all_data():
        reset_sequences()
        print("\n✓ 모든 작업이 완료되었습니다!")
        return 0
    else:
        print("\n✗ 초기화 실패")
        return 1

if __name__ == "__main__":
    sys.exit(main())