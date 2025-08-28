#!/usr/bin/env python3
"""
Betty Guardian Hook - Smart protection and monitoring
"""

import json
import sys
import os
import re
from pathlib import Path

class BettyGuardian:
    def __init__(self):
        self.protected_files = [
            "docker-compose.yml",
            ".env",
            "database.db",
            "*.sqlite"
        ]
        
        self.dangerous_commands = [
            r"rm\s+-rf\s+/",
            r"docker\s+volume\s+rm",
            r"DROP\s+DATABASE",
            r"DELETE\s+FROM",
            r"git\s+push\s+--force"
        ]
    
    def check_command(self, command):
        """Check if command is dangerous"""
        for pattern in self.dangerous_commands:
            if re.search(pattern, command, re.IGNORECASE):
                return False, f"Dangerous command pattern detected: {pattern}"
        return True, "Command approved"
    
    def check_file_operation(self, file_path, operation):
        """Check if file operation is safe"""
        path = Path(file_path)
        
        # Check protected files
        for protected in self.protected_files:
            if path.match(protected):
                if operation in ["delete", "overwrite"]:
                    return False, f"Protected file: {protected}"
        
        # Check critical directories
        if "/home/jarvis/projects/Betty" in str(path):
            if path.name == "database.db" and operation == "delete":
                return False, "Cannot delete Betty database"
        
        return True, "File operation approved"
    
    def process_event(self, data):
        """Process Claude Code event"""
        tool_name = data.get("tool_name", "")
        
        if tool_name == "PreToolUse":
            tool_input = data.get("tool_input", {})
            actual_tool = tool_input.get("tool_name", "")
            
            if actual_tool == "Bash":
                command = tool_input.get("tool_input", {}).get("command", "")
                safe, reason = self.check_command(command)
                if not safe:
                    return {
                        "success": False,
                        "action": "block",
                        "reason": reason,
                        "suggestion": "Please review this command for safety"
                    }
            
            elif actual_tool == "Write":
                file_path = tool_input.get("tool_input", {}).get("file_path", "")
                safe, reason = self.check_file_operation(file_path, "overwrite")
                if not safe:
                    return {
                        "success": False,
                        "action": "block",
                        "reason": reason,
                        "suggestion": "This file is protected. Please confirm this action."
                    }
        
        return {"success": True, "action": "continue"}

def main():
    if not sys.stdin.isatty():
        input_data = sys.stdin.read()
        try:
            data = json.loads(input_data)
            guardian = BettyGuardian()
            result = guardian.process_event(data)
            print(json.dumps(result))
        except Exception as e:
            print(json.dumps({
                "success": True,
                "action": "continue",
                "error": str(e)
            }))
    else:
        print(json.dumps({"success": True, "action": "continue"}))

if __name__ == "__main__":
    main()
