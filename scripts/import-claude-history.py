#!/usr/bin/env python3
"""
Import Claude conversation history into Betty Memory System
"""

import json
import sys
import requests
from pathlib import Path
from datetime import datetime

def import_conversation_file(filepath: str, betty_api_url: str = "http://localhost:3034"):
    """Import a single Claude conversation file into Betty"""
    
    print(f"Importing: {filepath}")
    imported_count = 0
    
    with open(filepath, 'r') as f:
        for line_num, line in enumerate(f, 1):
            if not line.strip():
                continue
                
            try:
                data = json.loads(line)
                
                # Extract message content
                message = data.get('message', {})
                if not message:
                    continue
                
                # Prepare Betty payload
                betty_payload = {
                    "title": f"Claude Conversation - {data.get('sessionId', 'unknown')[:8]}",
                    "content": message.get('content', '') if isinstance(message.get('content'), str) else json.dumps(message.get('content', '')),
                    "knowledge_type": "conversation",
                    "tags": ["claude", "historical", "imported", message.get('role', 'unknown')],
                    "metadata": {
                        "session_id": data.get('sessionId'),
                        "uuid": data.get('uuid'),
                        "parent_uuid": data.get('parentUuid'),
                        "timestamp": data.get('timestamp'),
                        "role": message.get('role'),
                        "cwd": data.get('cwd'),
                        "type": data.get('type'),
                        "source_file": str(filepath)
                    }
                }
                
                # Send to Betty API
                response = requests.post(
                    f"{betty_api_url}/api/knowledge",
                    json=betty_payload,
                    headers={
                        "X-API-Key": "betty_dev_test_key",
                        "Content-Type": "application/json"
                    },
                    timeout=5
                )
                
                if response.status_code == 201:
                    imported_count += 1
                    if imported_count % 10 == 0:
                        print(f"  Imported {imported_count} messages...")
                else:
                    print(f"  Failed line {line_num}: {response.status_code}")
                    
            except Exception as e:
                print(f"  Error on line {line_num}: {e}")
    
    print(f"✓ Imported {imported_count} messages from {filepath}")
    return imported_count

def main():
    """Import all Claude conversations into Betty"""
    
    claude_dir = Path.home() / ".claude" / "projects" / "-home-jarvis-projects-Betty"
    
    if not claude_dir.exists():
        print(f"Error: Directory not found: {claude_dir}")
        sys.exit(1)
    
    # Find the conversation with Van Dike
    target_file = claude_dir / "2112ad62-64b2-41b7-be40-9618c8f229ce.jsonl"
    
    if target_file.exists():
        print(f"Importing conversation with Van Dike...")
        import_conversation_file(str(target_file))
    else:
        print(f"File not found: {target_file}")
    
    print("\nDone! Now search Betty for 'Van Dike':")
    print("curl -X POST http://localhost:3034/api/knowledge/search -H 'Content-Type: application/json' -d '{\"query\": \"Van Dike\"}'")

if __name__ == "__main__":
    main()