#!/usr/bin/env python3
"""
Test single file import to debug 422 errors
"""

import json
import requests

# Test with minimal valid payload
api_url = "http://localhost:3034/api/knowledge"

payload = {
    'title': 'Test Claude Conversation',
    'content': 'Test conversation content from Claude Code',
    'knowledge_type': 'conversation',
    'source_type': 'import',
    'tags': ['test', 'claude-code'],
    'confidence': 'high'
}

print("Testing Betty Memory API with payload:")
print(json.dumps(payload, indent=2))

try:
    response = requests.post(
        api_url,
        json=payload,
        headers={'Content-Type': 'application/json'},
        timeout=5
    )
    
    print(f"\nResponse Status: {response.status_code}")
    
    if response.status_code in [200, 201]:
        print("✅ Success!")
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"❌ Exception: {e}")