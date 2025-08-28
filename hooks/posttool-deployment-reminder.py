#!/usr/bin/env python3
"""
ABOUTME: Betty PostTool Deployment Reminder - Checks if Docker deployment is needed
ABOUTME: Reminds Claude to deploy containers after making frontend/backend changes
"""

import json
import sys
import os
import subprocess
from pathlib import Path
from datetime import datetime

class DeploymentReminder:
    def __init__(self):
        self.deployment_log = Path.home() / ".betty" / "deployment-reminders.jsonl"
        self.deployment_log.parent.mkdir(parents=True, exist_ok=True)
        
        # Files that require deployment when modified
        self.deployment_triggers = {
            "frontend": [
                ".tsx", ".ts", ".jsx", ".js",
                "package.json", "tailwind.config",
                "vite.config", "nginx.conf"
            ],
            "backend": [
                ".py", "requirements.txt",
                "Dockerfile", "docker-compose"
            ]
        }
        
        self.pending_deployments = set()
    
    def process_hook_input(self):
        """Process PostTool hook input from Claude Code"""
        try:
            # Read hook input from stdin
            hook_input = json.loads(sys.stdin.read())
            
            tool_name = hook_input.get("tool", "")
            tool_inputs = hook_input.get("inputs", {})
            
            # Check if this was a file modification
            if tool_name in ["Write", "Edit", "MultiEdit"]:
                self.check_deployment_needed(tool_name, tool_inputs)
            
            # Check if building/deploying
            elif tool_name == "Bash":
                command = tool_inputs.get("command", "")
                if any(keyword in command for keyword in ["docker-compose build", "docker build", "docker-compose up"]):
                    self.mark_deployment_done(command)
            
            # Generate reminder if needed
            reminder = self.generate_reminder()
            
            if reminder:
                # Try to send to NTFY for visibility
                try:
                    subprocess.run([
                        "curl", "-X", "POST",
                        "https://ntfy.sh/betty-deployment-reminders",
                        "-H", "Priority: high",
                        "-H", "Tags: warning,rocket",
                        "-d", reminder
                    ], capture_output=True, timeout=2)
                except:
                    pass
                
                self.log_reminder(reminder)
                
                # Return the reminder in the response for visibility
                return {
                    "action": "continue",
                    "message": reminder,
                    "pending_deployments": list(self.pending_deployments)
                }
            
            return {"action": "continue"}
            
        except Exception as e:
            print(f"Deployment reminder error: {e}", file=sys.stderr)
            return {"action": "continue"}
    
    def check_deployment_needed(self, tool_name, tool_inputs):
        """Check if file changes require deployment"""
        file_path = tool_inputs.get("file_path", "")
        
        if not file_path:
            return
        
        # Check if frontend file
        if "/frontend/" in file_path and any(file_path.endswith(ext) for ext in self.deployment_triggers["frontend"]):
            self.pending_deployments.add("frontend")
            
        # Check if backend file  
        elif "/memory-api/" in file_path and any(file_path.endswith(ext) for ext in self.deployment_triggers["backend"]):
            self.pending_deployments.add("backend")
            
        # Check docker-compose changes
        elif "docker-compose" in file_path:
            self.pending_deployments.add("all-services")
    
    def mark_deployment_done(self, command):
        """Mark deployment as completed based on command"""
        if "frontend" in command:
            self.pending_deployments.discard("frontend")
        elif "memory-api" in command or "backend" in command:
            self.pending_deployments.discard("backend")
        elif "docker-compose up" in command and not any(service in command for service in ["frontend", "backend"]):
            self.pending_deployments.clear()
    
    def generate_reminder(self):
        """Generate deployment reminder message"""
        if not self.pending_deployments:
            return None
        
        reminders = []
        
        if "frontend" in self.pending_deployments:
            reminders.append(
                "🚨 DEPLOYMENT REMINDER: Frontend changes detected!\n"
                "   Run: docker-compose build frontend && docker stop betty_frontend && "
                "docker rm betty_frontend && docker-compose up -d frontend"
            )
        
        if "backend" in self.pending_deployments:
            reminders.append(
                "🚨 DEPLOYMENT REMINDER: Backend changes detected!\n"
                "   Run: docker-compose restart memory-api"
            )
        
        if "all-services" in self.pending_deployments:
            reminders.append(
                "🚨 DEPLOYMENT REMINDER: Docker config changed!\n"
                "   Run: docker-compose up -d --force-recreate"
            )
        
        if reminders:
            return "\n".join([
                "=" * 60,
                "⚠️  DEPLOYMENT CHECKLIST - CHANGES NOT YET DEPLOYED",
                "=" * 60
            ] + reminders + [
                "=" * 60,
                "💡 TIP: Always deploy after making code changes!",
                "=" * 60
            ])
        
        return None
    
    def log_reminder(self, reminder):
        """Log reminder to file"""
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "pending": list(self.pending_deployments),
                "reminder": reminder
            }
            
            with open(self.deployment_log, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            print(f"Failed to log reminder: {e}", file=sys.stderr)
    
    def check_container_status(self):
        """Check if containers are running"""
        try:
            result = subprocess.run(
                ["docker", "ps", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            running_containers = result.stdout.strip().split("\n")
            
            # Check critical containers
            required = ["betty_frontend", "betty_memory_api", "betty_postgres"]
            missing = [c for c in required if c not in running_containers]
            
            if missing:
                return f"⚠️ WARNING: Missing containers: {', '.join(missing)}"
            
            return None
            
        except Exception:
            return None

def main():
    """Hook entry point"""
    reminder = DeploymentReminder()
    result = reminder.process_hook_input()
    
    # Also check container status
    status_warning = reminder.check_container_status()
    if status_warning:
        print(status_warning, file=sys.stderr)
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()