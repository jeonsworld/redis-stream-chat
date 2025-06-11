import asyncio
from openai import OpenAI
from src.core.config import settings

# OpenAI 클라이언트
client = OpenAI(api_key=settings.openai_api_key)

def test_openai():
    try:
        print("Testing OpenAI API...")
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say hello in Korean"}
            ],
            stream=False,
            max_tokens=10
        )
        print(f"Response: {response.choices[0].message.content}")
        
        # 스트리밍 테스트
        print("\nTesting streaming...")
        stream = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Count to 3"}
            ],
            stream=True,
            max_tokens=20
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content:
                print(chunk.choices[0].delta.content, end='', flush=True)
        print("\nDone!")
        
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")

if __name__ == "__main__":
    test_openai()