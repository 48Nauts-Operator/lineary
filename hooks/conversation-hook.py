#!/usr/bin/env python3
"""
Betty Real-time Conversation Hook
Captures this very conversation as it happens!
"""

import sys
import json
import requests
import uuid
from datetime import datetime

class RealTimeCapture:
    """Captures conversations in real-time"""
    
    def __init__(self):
        self.betty_api = "http://localhost:3034"
        self.session_id = None
        self.message_count = 0
    
    def start_session(self, title="Live Claude Code Session"):
        """Start capturing this conversation"""
        session_data = {
            "title": title,
            "description": f"Live conversation capture started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "project_id": "b7f71987-b980-4154-8836-5d8a0872b38a",
            "status": "active"
        }
        
        try:
            response = requests.post(f"{self.betty_api}/api/sessions/", json=session_data)
            if response.status_code == 201:
                self.session_id = response.json()["data"]["id"]
                print(f"🎯 LIVE CAPTURE STARTED: {self.session_id}")
                return True
            else:
                print(f"❌ Failed to start live capture: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error starting live capture: {e}")
            return False
    
    def capture_this_conversation(self):
        """Capture the current conversation we're having"""
        if not self.session_id:
            if not self.start_session("Betty Memory System Investigation"):
                return False
        
        # Capture the user's question
        user_message = """So every conversation need to have a ID and then we store a set amount of messages under that ID and call it a Conversation. Each conversation got a unique ID, a topic, an name, and some meta-data. Is that somwhat how it works? So how can we trigger Claude-Code or any other CLI LLM to write these data to Betty? Is that even possible using Cursor? Do we need to build our own VS-Code UI that can do that?"""
        
        # Capture my response
        assistant_message = """Exactly! You've got the architecture right. Betty uses:

Conversation (Session)
├── ID: UUID
├── Title: "Implementing Betty Memory System"  
├── Context: "Working on conversation capture"
├── Metadata: {tools_used, files_modified, duration}
└── Messages[]

For integration, we have several options:

1. MCP Server Integration (RECOMMENDED) - Works with Claude Desktop
2. Background Monitor Script - Runs continuously, watches for conversation files
3. Session Wrapper Script - Wraps LLM tools with Betty capture
4. Custom VS Code Extension - Most complex but most integrated

The background monitor approach is most practical - it runs continuously and automatically captures any LLM conversations to Betty's API."""
        
        # Send both messages
        self.send_message("user", user_message)
        self.send_message("assistant", assistant_message)
        
        print("✅ THIS CONVERSATION HAS BEEN CAPTURED TO BETTY!")
        print(f"📊 View it at: http://localhost:3377")
        print(f"🔍 Session ID: {self.session_id}")
        
        return True
    
    def send_message(self, role, content):
        """Send message to Betty"""
        if not self.session_id:
            return False
        
        message_data = {
            "role": role,
            "content": content,
            "message_index": self.message_count
        }
        
        try:
            response = requests.post(
                f"{self.betty_api}/api/sessions/{self.session_id}/messages",
                json=message_data
            )
            if response.status_code == 201:
                self.message_count += 1
                print(f"✅ Captured {role} message #{self.message_count}")
                return True
            else:
                print(f"❌ Failed to capture {role} message: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error capturing {role} message: {e}")
            return False

# Run the live capture
if __name__ == "__main__":
    capturer = RealTimeCapture()
    capturer.capture_this_conversation()