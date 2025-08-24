#!/usr/bin/env python3
"""
NTFY Notification Hook for Betty
Sends notifications to https://ntfy.da-tech.io/Betty
"""

import json
import sys
import requests
from datetime import datetime

NTFY_URL = "https://ntfy.da-tech.io/Betty"

def send_notification(title, message, priority="default", tags=None):
    """Send notification to NTFY server"""
    headers = {
        "Title": title,
        "Priority": priority
    }
    
    if tags:
        headers["Tags"] = ",".join(tags)
    
    try:
        response = requests.post(NTFY_URL, data=message, headers=headers, timeout=5)
        return response.status_code == 200
    except Exception as e:
        print(f"Failed to send notification: {e}", file=sys.stderr)
        return False

def main():
    # Read input from Claude Code
    if not sys.stdin.isatty():
        input_data = sys.stdin.read()
        try:
            data = json.loads(input_data)
        except json.JSONDecodeError:
            return
    else:
        return
    
    tool_name = data.get("tool_name", "")
    
    # Notification triggers
    if tool_name == "Stop":
        # Session completed
        stats = data.get("stats", {})
        duration = stats.get("duration", "unknown")
        send_notification(
            "✅ Betty Session Complete",
            f"Session finished after {duration}",
            "low",
            ["white_check_mark"]
        )
    
    elif tool_name == "PostToolUse":
        tool_input = data.get("tool_input", {})
        actual_tool = tool_input.get("tool_name", "")
        
        # Notify on significant events
        if actual_tool == "Write" and "test" in str(tool_input).lower():
            send_notification(
                "🧪 Tests Created",
                "New test files have been written",
                "default",
                ["test_tube"]
            )
        
        elif actual_tool == "MultiEdit":
            file_count = len(tool_input.get("edits", []))
            if file_count > 5:
                send_notification(
                    "📝 Major Code Changes",
                    f"Modified {file_count} sections",
                    "default",
                    ["memo"]
                )
    
    # Always continue
    print(json.dumps({"success": True, "action": "continue"}))

if __name__ == "__main__":
    main()
