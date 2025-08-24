#!/usr/bin/env python3
"""
ABOUTME: Debug hook for testing PostTool execution
ABOUTME: Creates a visible log when triggered to verify hooks work
"""

import json
import sys
from datetime import datetime
from pathlib import Path

def main():
    try:
        # Read hook input
        hook_input = json.loads(sys.stdin.read())
        
        # Create debug log
        debug_file = Path("/home/jarvis/projects/Betty/hook-debug.log")
        with open(debug_file, "a") as f:
            f.write(f"{datetime.now().isoformat()} - Hook triggered: {hook_input.get('tool', 'unknown')}\n")
        
        return {"action": "continue"}
        
    except Exception as e:
        # Log error
        error_file = Path("/home/jarvis/projects/Betty/hook-error.log")
        with open(error_file, "a") as f:
            f.write(f"{datetime.now().isoformat()} - Hook error: {e}\n")
        
        return {"action": "continue"}

if __name__ == "__main__":
    result = main()
    print(json.dumps(result))