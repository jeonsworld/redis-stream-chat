#!/usr/bin/env python3
"""API 테스트 스크립트"""
import requests

# 서버 URL
BASE_URL = "http://localhost:5000"

# 세션 생성
session = requests.Session()

print("1. 헬스 체크...")
response = session.get(f"{BASE_URL}/api/health")
print(f"   상태: {response.status_code}")
print(f"   응답: {response.json()}")

print("\n2. 메인 페이지 접속 (세션 ID 획득)...")
response = session.get(f"{BASE_URL}/")
print(f"   상태: {response.status_code}")
print(f"   쿠키: {session.cookies.get_dict()}")

print("\n3. 채팅 메시지 전송...")
message = "안녕하세요, 테스트 메시지입니다."
response = session.post(
    f"{BASE_URL}/api/chat",
    json={"message": message},
    headers={"Content-Type": "application/json"}
)

if response.status_code == 200:
    data = response.json()
    print(f"   상태: {response.status_code}")
    print(f"   응답: {data}")
    task_id = data.get("task_id")
    
    if task_id:
        print(f"\n4. SSE 스트림 연결 테스트...")
        print(f"   Task ID: {task_id}")
        print(f"   Stream URL: {BASE_URL}{data.get('stream_url')}")
        
        # SSE 연결은 별도 스크립트나 브라우저에서 테스트
        print("\n   브라우저에서 다음 URL로 테스트:")
        print(f"   {BASE_URL}{data.get('stream_url')}")
else:
    print(f"   오류: {response.status_code}")
    print(f"   응답: {response.text}")