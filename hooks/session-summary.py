#!/usr/bin/env python3
"""Generate session summary"""
import json
import sys
from datetime import datetime
from pathlib import Path

try:
    # Count tool usage
    log_file = Path("/home/jarvis/projects/Betty/tool-usage.log")
    if log_file.exists():
        with open(log_file, "r") as f:
            lines = f.readlines()
        
        summary = f"Session ended at {datetime.now().isoformat()}\n"
        summary += f"Total tool uses: {len(lines)}\n"
        
        summary_file = Path("/home/jarvis/projects/Betty/session-summary.log")
        with open(summary_file, "a") as f:
            f.write(summary + "\n")
    
    print(json.dumps({"action": "continue"}))
except:
    print(json.dumps({"action": "continue"}))