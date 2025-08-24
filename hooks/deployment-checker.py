#!/usr/bin/env python3
"""Simple deployment checker hook"""
import json
import sys
from datetime import datetime
from pathlib import Path

# Read input from Claude Code
try:
    hook_input = json.loads(sys.stdin.read())
    tool = hook_input.get("tool", "")
    inputs = hook_input.get("inputs", {})
    
    # Log to a file we can check
    log_file = Path("/home/jarvis/projects/Betty/hook-activity.log")
    with open(log_file, "a") as f:
        f.write(f"{datetime.now().isoformat()} - {tool} executed\n")
        
        if tool in ["Write", "Edit", "MultiEdit"]:
            file_path = inputs.get("file_path", "")
            if file_path:
                f.write(f"  File: {file_path}\n")
                
                # Check if deployment needed
                if "/frontend/" in file_path:
                    print("⚠️ FRONTEND CHANGED - Run: docker-compose restart frontend", file=sys.stderr)
                elif "/memory-api/" in file_path:
                    print("⚠️ BACKEND CHANGED - Run: docker-compose restart memory-api", file=sys.stderr)
    
    # Return success
    print(json.dumps({"action": "continue"}))
    
except Exception as e:
    # Log error
    with open("/home/jarvis/projects/Betty/hook-errors.log", "a") as f:
        f.write(f"{datetime.now().isoformat()} - Error: {e}\n")
    print(json.dumps({"action": "continue"}))