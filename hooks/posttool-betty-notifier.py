#!/usr/bin/env python3
"""
ABOUTME: Betty PostTool Hook - Sends notifications to Betty API
ABOUTME: Tracks file changes and deployment needs through Betty's system
"""

import json
import sys
import subprocess
from datetime import datetime
from pathlib import Path

def send_to_betty(message, priority=3):
    """Send notification to Betty API"""
    try:
        # Send to Betty tasks API
        task_text = f"DEPLOY: {message}"
        subprocess.run([
            "curl", "-X", "POST",
            f"http://localhost:3034/api/tasks/add?task={task_text}&priority={priority}",
            "-H", "Content-Type: application/json"
        ], capture_output=True, timeout=2)
    except:
        pass

def main():
    """Process PostTool hook"""
    try:
        # Read hook input
        hook_input = json.loads(sys.stdin.read())
        
        tool_name = hook_input.get("tool", "")
        tool_inputs = hook_input.get("inputs", {})
        
        # Track deployment needs
        deployment_file = Path.home() / ".betty" / "deployment-tracker.json"
        deployment_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing deployment needs
        if deployment_file.exists():
            with open(deployment_file, "r") as f:
                deployment_needs = json.load(f)
        else:
            deployment_needs = {"frontend": [], "backend": [], "docker": []}
        
        # Check for file modifications
        if tool_name in ["Write", "Edit", "MultiEdit"]:
            file_path = tool_inputs.get("file_path", "")
            
            if "/frontend/" in file_path:
                deployment_needs["frontend"].append({
                    "file": file_path,
                    "time": datetime.now().isoformat(),
                    "tool": tool_name
                })
                send_to_betty(f"Frontend file changed: {file_path.split('/')[-1]}", priority=2)
                
                # Create visible marker file
                marker = Path("/home/jarvis/projects/Betty/.frontend-needs-deploy")
                marker.write_text(f"Last change: {datetime.now().isoformat()}\nFile: {file_path}\n")
                
            elif "/memory-api/" in file_path:
                deployment_needs["backend"].append({
                    "file": file_path,
                    "time": datetime.now().isoformat(),
                    "tool": tool_name
                })
                send_to_betty(f"Backend file changed: {file_path.split('/')[-1]}", priority=2)
                
                # Create visible marker file
                marker = Path("/home/jarvis/projects/Betty/.backend-needs-deploy")
                marker.write_text(f"Last change: {datetime.now().isoformat()}\nFile: {file_path}\n")
            
            elif "docker-compose" in file_path:
                deployment_needs["docker"].append({
                    "file": file_path,
                    "time": datetime.now().isoformat(),
                    "tool": tool_name
                })
                send_to_betty("Docker configuration changed", priority=1)
                
                # Create visible marker file
                marker = Path("/home/jarvis/projects/Betty/.docker-needs-rebuild")
                marker.write_text(f"Last change: {datetime.now().isoformat()}\nFile: {file_path}\n")
        
        # Check for deployment commands
        elif tool_name == "Bash":
            command = tool_inputs.get("command", "")
            
            if "docker-compose" in command and "frontend" in command:
                # Clear frontend deployment needs
                deployment_needs["frontend"] = []
                marker = Path("/home/jarvis/projects/Betty/.frontend-needs-deploy")
                if marker.exists():
                    marker.unlink()
                send_to_betty("Frontend deployed successfully", priority=5)
                
            elif "docker-compose" in command and "memory-api" in command:
                # Clear backend deployment needs
                deployment_needs["backend"] = []
                marker = Path("/home/jarvis/projects/Betty/.backend-needs-deploy")
                if marker.exists():
                    marker.unlink()
                send_to_betty("Backend deployed successfully", priority=5)
                
            elif "docker-compose up" in command:
                # Clear all deployment needs
                deployment_needs = {"frontend": [], "backend": [], "docker": []}
                for marker_name in [".frontend-needs-deploy", ".backend-needs-deploy", ".docker-needs-rebuild"]:
                    marker = Path(f"/home/jarvis/projects/Betty/{marker_name}")
                    if marker.exists():
                        marker.unlink()
                send_to_betty("All services deployed successfully", priority=5)
        
        # Save deployment needs
        with open(deployment_file, "w") as f:
            json.dump(deployment_needs, f, indent=2)
        
        # Generate response with pending deployments
        pending = []
        if deployment_needs["frontend"]:
            pending.append("frontend")
        if deployment_needs["backend"]:
            pending.append("backend")
        if deployment_needs["docker"]:
            pending.append("docker")
        
        if pending:
            return {
                "action": "continue",
                "pending_deployments": pending,
                "message": f"Deployment needed for: {', '.join(pending)}"
            }
        
        return {"action": "continue"}
        
    except Exception as e:
        # Log errors
        error_log = Path.home() / ".betty" / "hook-errors.log"
        error_log.parent.mkdir(parents=True, exist_ok=True)
        with open(error_log, "a") as f:
            f.write(f"{datetime.now().isoformat()} - PostTool error: {e}\n")
        
        return {"action": "continue"}

if __name__ == "__main__":
    result = main()
    print(json.dumps(result))