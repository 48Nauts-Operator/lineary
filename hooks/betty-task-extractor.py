#!/usr/bin/env python3
"""
Betty Task Extractor Hook for Claude Code
Automatically extracts tasks from conversations and saves them to Betty
Completely bypasses TodoWrite to avoid timeouts
"""

import os
import sys
import json
import re
import requests
from pathlib import Path
from datetime import datetime

# Betty API configuration
BETTY_API_URL = os.getenv("BETTY_API_URL", "http://localhost:3034")
BETTY_TASKS_ENDPOINT = f"{BETTY_API_URL}/api/tasks"

class BettyTaskExtractorHook:
    """
    Hook that extracts tasks from Claude's responses
    and saves them to Betty's file-based system
    """
    
    def __init__(self):
        self.enabled = True
        self.last_extraction = None
        self.task_patterns = [
            # Claude's commitment patterns
            r"I(?:'ll| will) (?:now |)([^.]+)",
            r"Let me (?:now |)([^.]+)",
            r"I'm going to ([^.]+)",
            
            # Task markers
            r"(?:TODO|TASK|FIX):\s*([^\\n]+)",
            r"- \[ \] ([^\\n]+)",  # Markdown checkboxes
            
            # Action items
            r"(?:Need to|Must|Should) ([^.]+)",
            r"(?:Creating|Building|Implementing|Fixing) ([^.]+)",
        ]
    
    def should_extract(self, message):
        """
        Determine if we should extract tasks from this message
        """
        # Only extract from assistant messages
        if message.get("role") != "assistant":
            return False
        
        content = message.get("content", "").lower()
        
        # Look for task-related keywords
        task_keywords = [
            "i will", "i'll", "let me", "going to",
            "todo", "task", "implement", "create",
            "fix", "update", "add", "build"
        ]
        
        return any(keyword in content for keyword in task_keywords)
    
    def extract_tasks(self, content):
        """
        Extract tasks from message content
        """
        tasks = []
        
        for pattern in self.task_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                task_text = match.group(1).strip()
                
                # Clean up the task text
                task_text = task_text.strip(".,;")
                
                # Skip very short or very long tasks
                if len(task_text) < 10 or len(task_text) > 200:
                    continue
                
                # Determine priority based on keywords
                priority = self.determine_priority(task_text)
                
                tasks.append({
                    "task": task_text,
                    "priority": priority,
                    "extracted_at": datetime.now().isoformat()
                })
        
        # Deduplicate tasks
        seen = set()
        unique_tasks = []
        for task in tasks:
            task_key = task["task"].lower()
            if task_key not in seen:
                seen.add(task_key)
                unique_tasks.append(task)
        
        return unique_tasks
    
    def determine_priority(self, task_text):
        """
        Determine task priority based on content
        """
        task_lower = task_text.lower()
        
        # High priority keywords
        if any(word in task_lower for word in ["critical", "urgent", "immediately", "asap", "fix", "error", "bug"]):
            return 5
        
        # Medium-high priority
        if any(word in task_lower for word in ["important", "must", "need", "should"]):
            return 4
        
        # Medium priority
        if any(word in task_lower for word in ["implement", "create", "build", "update"]):
            return 3
        
        # Low-medium priority
        if any(word in task_lower for word in ["test", "check", "verify", "document"]):
            return 2
        
        # Low priority (default)
        return 1
    
    def save_to_betty(self, tasks):
        """
        Save tasks to Betty's file-based system
        """
        saved_count = 0
        
        for task in tasks:
            try:
                # Call Betty API to add task
                response = requests.post(
                    f"{BETTY_TASKS_ENDPOINT}/add",
                    params={
                        "task": task["task"],
                        "priority": task["priority"]
                    },
                    timeout=1  # Very short timeout since it's file-based
                )
                
                if response.status_code == 200:
                    saved_count += 1
                    print(f"[Betty] Task saved: {task['task'][:50]}...")
                
            except Exception as e:
                # If API fails, fall back to direct file write
                self.save_to_file_fallback(task)
                saved_count += 1
        
        return saved_count
    
    def save_to_file_fallback(self, task):
        """
        Fallback: Save directly to file if API is unavailable
        """
        betty_dir = Path.home() / ".betty" / "tasks"
        betty_dir.mkdir(parents=True, exist_ok=True)
        
        task_file = betty_dir / "tasks.jsonl"
        
        task_entry = {
            "id": str(datetime.now().timestamp()),
            "task": task["task"],
            "priority": task["priority"],
            "status": "pending",
            "created": datetime.now().isoformat(),
            "source": "claude_hook"
        }
        
        with open(task_file, "a") as f:
            f.write(json.dumps(task_entry) + "\\n")
    
    def process_message(self, message):
        """
        Process a message and extract tasks
        """
        if not self.should_extract(message):
            return {"extracted": 0, "message": "No extraction needed"}
        
        content = message.get("content", "")
        tasks = self.extract_tasks(content)
        
        if not tasks:
            return {"extracted": 0, "message": "No tasks found"}
        
        # Save to Betty
        saved = self.save_to_betty(tasks)
        
        return {
            "extracted": len(tasks),
            "saved": saved,
            "message": f"Extracted {len(tasks)} tasks, saved {saved} to Betty"
        }

def main():
    """
    Main hook entry point for Claude Code
    """
    # Read input from Claude Code
    if not sys.stdin.isatty():
        input_data = sys.stdin.read()
        try:
            data = json.loads(input_data)
        except json.JSONDecodeError:
            print(json.dumps({"error": "Invalid JSON input"}))
            return
    else:
        # Test mode
        data = {
            "tool_name": "PostToolUse",
            "tool_input": {
                "message": {
                    "role": "assistant",
                    "content": "I'll now implement the Manus-inspired file-based context system. Let me create the task extraction API and test it thoroughly. TODO: Add visualization to dashboard."
                }
            }
        }
    
    # Initialize extractor
    extractor = BettyTaskExtractorHook()
    
    # Check if this is a PostToolUse event with a message
    if data.get("tool_name") == "PostToolUse":
        tool_input = data.get("tool_input", {})
        if "message" in tool_input:
            result = extractor.process_message(tool_input["message"])
            
            # Return result to Claude Code
            print(json.dumps({
                "success": True,
                "action": "tasks_extracted",
                "details": result,
                "bypass_todowrite": True,
                "note": "Tasks saved to Betty's file system - no timeouts possible!"
            }))
            return
    
    # Default response
    print(json.dumps({
        "success": True,
        "action": "continue",
        "message": "Betty Task Extractor active"
    }))

if __name__ == "__main__":
    main()