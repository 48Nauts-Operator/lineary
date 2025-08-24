#!/usr/bin/env python3
"""Track tool usage"""
import json
import sys
from datetime import datetime
from pathlib import Path

try:
    hook_input = json.loads(sys.stdin.read())
    tool = hook_input.get("tool", "")
    
    # Log all tool usage
    log_file = Path("/home/jarvis/projects/Betty/tool-usage.log")
    with open(log_file, "a") as f:
        f.write(f"{datetime.now().isoformat()} - Tool: {tool}\n")
    
    print(json.dumps({"action": "continue"}))
except:
    print(json.dumps({"action": "continue"}))