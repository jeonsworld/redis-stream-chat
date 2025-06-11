#!/usr/bin/env python3
"""Test the /api/chats endpoint directly"""
import requests
import json

# Test the endpoint
url = "http://localhost:5000/api/chats"
print(f"Testing {url}...")

try:
    response = requests.get(url)
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {response.headers}")
    print(f"Content-Type: {response.headers.get('content-type')}")
    print(f"Raw Response: {response.text}")
    
    if response.headers.get('content-type', '').startswith('application/json'):
        print(f"JSON Response: {response.json()}")
    else:
        print("Response is not JSON")
        
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")