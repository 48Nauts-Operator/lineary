#!/usr/bin/env python3
"""
ABOUTME: Betty PostTool Visible Notifier - Makes hook notifications visible
ABOUTME: Writes notifications to a monitored file for real-time visibility
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime

def main():
    """Process PostTool hook and make notifications visible"""
    try:
        # Read hook input
        hook_input = json.loads(sys.stdin.read())
        
        tool_name = hook_input.get("tool", "")
        tool_inputs = hook_input.get("inputs", {})
        
        # Create visible notification file
        notification_file = Path("/home/jarvis/projects/Betty/ACTIVE_NOTIFICATIONS.txt")
        
        # Track file modifications
        if tool_name in ["Write", "Edit", "MultiEdit"]:
            file_path = tool_inputs.get("file_path", "")
            
            # Generate notification based on file type
            notification = None
            
            if "/frontend/" in file_path and any(file_path.endswith(ext) for ext in [".tsx", ".ts", ".jsx", ".js"]):
                notification = f"""
╔══════════════════════════════════════════════════════════╗
║  🚨 FRONTEND CHANGED - DEPLOYMENT NEEDED!               ║
╠══════════════════════════════════════════════════════════╣
║  Time: {datetime.now().strftime('%H:%M:%S')}                                      ║
║  File: {file_path.split('/')[-1][:40]:<40} ║
║                                                          ║
║  To deploy changes, run:                                ║
║  docker-compose restart frontend                        ║
╚══════════════════════════════════════════════════════════╝
"""
            
            elif "/memory-api/" in file_path and file_path.endswith(".py"):
                notification = f"""
╔══════════════════════════════════════════════════════════╗
║  🚨 BACKEND CHANGED - RESTART NEEDED!                   ║
╠══════════════════════════════════════════════════════════╣
║  Time: {datetime.now().strftime('%H:%M:%S')}                                      ║
║  File: {file_path.split('/')[-1][:40]:<40} ║
║                                                          ║
║  To apply changes, run:                                 ║
║  docker-compose restart memory-api                      ║
╚══════════════════════════════════════════════════════════╝
"""
            
            if notification:
                # Write to visible file
                with open(notification_file, "a") as f:
                    f.write(notification + "\n")
                
                # Also append to a running log
                log_file = Path("/home/jarvis/projects/Betty/deployment-needed.log")
                with open(log_file, "a") as f:
                    f.write(f"{datetime.now().isoformat()} - {tool_name} on {file_path}\n")
                
                # Return notification in response
                return {
                    "action": "continue",
                    "notification": notification.strip(),
                    "file_modified": file_path
                }
        
        # Check for Docker commands
        elif tool_name == "Bash":
            command = tool_inputs.get("command", "")
            if "docker-compose restart" in command:
                service = command.split()[-1] if len(command.split()) > 2 else "services"
                
                # Clear notifications for this service
                if notification_file.exists():
                    content = notification_file.read_text()
                    if service.lower() in content.lower():
                        # Clear the file or remove relevant notifications
                        notification_file.write_text(f"✅ {service} restarted at {datetime.now().strftime('%H:%M:%S')}\n")
                
                return {
                    "action": "continue",
                    "notification": f"✅ {service} restarted successfully"
                }
        
        return {"action": "continue"}
        
    except Exception as e:
        # Log errors to a visible file
        error_file = Path("/home/jarvis/projects/Betty/hook-errors.log")
        with open(error_file, "a") as f:
            f.write(f"{datetime.now().isoformat()} - Error: {e}\n")
        
        return {"action": "continue"}

if __name__ == "__main__":
    result = main()
    print(json.dumps(result))