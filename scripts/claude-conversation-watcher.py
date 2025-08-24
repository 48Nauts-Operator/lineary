#!/usr/bin/env python3
"""
Claude Conversation Watcher
Monitors Claude Code JSONL files and syncs them to Betty Memory System
"""

import os
import json
import time
import hashlib
import requests
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from typing import Dict, List, Optional
from datetime import datetime

class ClaudeConversationHandler(FileSystemEventHandler):
    """Handles changes to Claude conversation files"""
    
    def __init__(self, betty_api_url: str = "http://localhost:3034", api_key: Optional[str] = None):
        self.betty_api_url = betty_api_url
        self.api_key = api_key or "betty_dev_test_key"
        self.processed_messages = set()  # Track processed message hashes
        self.claude_dir = Path.home() / ".claude" / "projects"
        
    def on_modified(self, event):
        """Handle file modification events"""
        if event.is_directory:
            return
            
        if event.src_path.endswith('.jsonl'):
            print(f"[INFO] Detected change in: {event.src_path}")
            self.process_conversation_file(event.src_path)
    
    def on_created(self, event):
        """Handle new file creation"""
        if not event.is_directory and event.src_path.endswith('.jsonl'):
            print(f"[INFO] New conversation file: {event.src_path}")
            time.sleep(0.5)  # Wait for file to be written
            self.process_conversation_file(event.src_path)
    
    def process_conversation_file(self, filepath: str):
        """Process a Claude conversation JSONL file"""
        try:
            with open(filepath, 'r') as f:
                lines = f.readlines()
                
            for line in lines:
                if not line.strip():
                    continue
                    
                try:
                    data = json.loads(line)
                    self.process_message(data, filepath)
                except json.JSONDecodeError as e:
                    print(f"[ERROR] Failed to parse JSON line: {e}")
                    
        except Exception as e:
            print(f"[ERROR] Failed to process file {filepath}: {e}")
    
    def process_message(self, message: Dict, source_file: str):
        """Process individual message and send to Betty"""
        # Create unique hash for message to avoid duplicates
        message_hash = hashlib.sha256(
            json.dumps(message, sort_keys=True).encode()
        ).hexdigest()
        
        if message_hash in self.processed_messages:
            return  # Skip already processed messages
        
        # Extract relevant fields based on Claude's JSONL structure
        # This structure may need adjustment based on actual format
        betty_payload = {
            "title": f"Claude Conversation - {Path(source_file).stem}",
            "content": json.dumps(message),  # Store full message as JSON
            "knowledge_type": "conversation",
            "tags": ["claude", "conversation", "auto-captured"],
            "metadata": {
                "source_file": source_file,
                "message_hash": message_hash,
                "captured_at": datetime.now().isoformat(),
                "role": message.get("role", "unknown"),
                "timestamp": message.get("timestamp", datetime.now().isoformat())
            }
        }
        
        # Send to Betty API
        try:
            response = requests.post(
                f"{self.betty_api_url}/api/knowledge",
                json=betty_payload,
                headers={
                    "X-API-Key": self.api_key,
                    "Content-Type": "application/json"
                },
                timeout=5
            )
            
            if response.status_code == 201:
                print(f"[SUCCESS] Message synced to Betty: {message_hash[:8]}...")
                self.processed_messages.add(message_hash)
            else:
                print(f"[ERROR] Failed to sync to Betty: {response.status_code} - {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Failed to connect to Betty API: {e}")
    
    def initial_sync(self):
        """Perform initial sync of existing conversation files"""
        print(f"[INFO] Starting initial sync from {self.claude_dir}")
        
        if not self.claude_dir.exists():
            print(f"[WARNING] Claude directory not found: {self.claude_dir}")
            return
            
        jsonl_files = list(self.claude_dir.glob("**/*.jsonl"))
        print(f"[INFO] Found {len(jsonl_files)} conversation files")
        
        for filepath in jsonl_files:
            print(f"[INFO] Syncing: {filepath}")
            self.process_conversation_file(str(filepath))

def main():
    """Main entry point"""
    print("=" * 60)
    print("Claude Conversation Watcher for Betty Memory System")
    print("=" * 60)
    
    # Configuration
    CLAUDE_DIR = Path.home() / ".claude" / "projects"
    BETTY_API_URL = "http://localhost:3034"
    API_KEY = os.getenv("BETTY_API_KEY", "betty_dev_test_key")
    
    # Check if Claude directory exists
    if not CLAUDE_DIR.exists():
        print(f"[ERROR] Claude directory not found: {CLAUDE_DIR}")
        print("[INFO] Creating directory and waiting for Claude conversations...")
        CLAUDE_DIR.mkdir(parents=True, exist_ok=True)
    
    # Initialize handler
    handler = ClaudeConversationHandler(BETTY_API_URL, API_KEY)
    
    # Perform initial sync
    handler.initial_sync()
    
    # Set up file watcher
    observer = Observer()
    observer.schedule(handler, str(CLAUDE_DIR), recursive=True)
    observer.start()
    
    print(f"[INFO] Watching for changes in: {CLAUDE_DIR}")
    print("[INFO] Press Ctrl+C to stop")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\n[INFO] Stopping watcher...")
    
    observer.join()
    print("[INFO] Watcher stopped")

if __name__ == "__main__":
    main()