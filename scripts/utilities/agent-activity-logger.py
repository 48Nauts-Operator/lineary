#!/usr/bin/env python3
"""
Agent Activity Logger for 137Docs Project
Tracks all agent activities, commands, file changes, and results
"""

import json
import datetime
import os
import hashlib
import subprocess
import requests
from pathlib import Path

class AgentActivityLogger:
    def __init__(self, log_file="/home/jarvis/projects/nautBrain/agent-activity.log"):
        self.log_file = log_file
        self.session_id = None
        self.agent_type = None
        self.start_time = None
        
    def start_session(self, agent_type, task_description, prompt):
        """Start a new agent session"""
        self.session_id = hashlib.md5(f"{datetime.datetime.now().isoformat()}{agent_type}".encode()).hexdigest()[:8]
        self.agent_type = agent_type
        self.start_time = datetime.datetime.now()
        
        session_data = {
            "session_id": self.session_id,
            "agent_type": agent_type,
            "start_time": self.start_time.isoformat(),
            "task_description": task_description,
            "prompt": prompt,
            "commands": [],
            "file_changes": [],
            "environment": self._detect_environment(),
            "status": "STARTED"
        }
        
        self._write_log_entry("SESSION_START", session_data)
        self._send_ntfy(f"🤖 Agent Started: {agent_type}", f"Task: {task_description[:100]}...")
        
    def log_command(self, command, description, result=None, error=None):
        """Log a command executed by the agent"""
        if not self.session_id:
            return
            
        command_data = {
            "session_id": self.session_id,
            "timestamp": datetime.datetime.now().isoformat(),
            "command": command,
            "description": description,
            "result": result,
            "error": error,
            "success": error is None
        }
        
        self._write_log_entry("COMMAND", command_data)
        
        if error:
            self._send_ntfy(f"❌ Command Failed: {self.agent_type}", f"Cmd: {command[:50]}...\nError: {error[:100]}...")
        
    def log_file_change(self, file_path, change_type, before_content=None, after_content=None):
        """Log file modifications made by the agent"""
        if not self.session_id:
            return
            
        file_data = {
            "session_id": self.session_id,
            "timestamp": datetime.datetime.now().isoformat(),
            "file_path": file_path,
            "change_type": change_type,  # CREATE, MODIFY, DELETE
            "before_hash": hashlib.md5(before_content.encode()).hexdigest() if before_content else None,
            "after_hash": hashlib.md5(after_content.encode()).hexdigest() if after_content else None,
            "lines_changed": self._count_line_changes(before_content, after_content) if before_content and after_content else None
        }
        
        self._write_log_entry("FILE_CHANGE", file_data)
        self._send_ntfy(f"📝 File Modified: {self.agent_type}", f"File: {os.path.basename(file_path)}\nType: {change_type}")
        
    def end_session(self, status="COMPLETED", summary=None, errors=None):
        """End the agent session"""
        if not self.session_id:
            return
            
        end_time = datetime.datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        session_end_data = {
            "session_id": self.session_id,
            "agent_type": self.agent_type,
            "end_time": end_time.isoformat(),
            "duration_seconds": duration,
            "status": status,
            "summary": summary,
            "errors": errors
        }
        
        self._write_log_entry("SESSION_END", session_end_data)
        
        emoji = "✅" if status == "COMPLETED" else "❌" if status == "FAILED" else "⚠️"
        self._send_ntfy(f"{emoji} Agent Finished: {self.agent_type}", 
                       f"Status: {status}\nDuration: {duration:.1f}s\nSummary: {summary[:100] if summary else 'No summary'}...")
        
        # Reset session
        self.session_id = None
        self.agent_type = None
        self.start_time = None
        
    def _detect_environment(self):
        """Detect which docker environment is being used"""
        try:
            # Check which docker-compose file is active
            result = subprocess.run(["docker-compose", "ps"], capture_output=True, text=True)
            if result.returncode == 0:
                return "docker-compose.yml (PRODUCTION)"
        except:
            pass
            
        try:
            result = subprocess.run(["docker-compose", "-f", "docker-compose.dev.yml", "ps"], capture_output=True, text=True)
            if result.returncode == 0:
                return "docker-compose.dev.yml (DEV - WRONG!)"
        except:
            pass
            
        return "UNKNOWN"
        
    def _count_line_changes(self, before, after):
        """Count number of lines changed between before and after content"""
        if not before or not after:
            return None
            
        before_lines = set(before.split('\n'))
        after_lines = set(after.split('\n'))
        
        added = len(after_lines - before_lines)
        removed = len(before_lines - after_lines)
        
        return {"added": added, "removed": removed}
        
    def _write_log_entry(self, entry_type, data):
        """Write log entry to file"""
        log_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "type": entry_type,
            "data": data
        }
        
        # Ensure log directory exists
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        
        with open(self.log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
            
    def _send_ntfy(self, title, message):
        """Send NTFY notification"""
        try:
            requests.post("https://ntfy.sh/da-tech-137docs", 
                         json={
                             "title": title,
                             "message": message,
                             "tags": ["robot", "betty", "coordination"],
                             "priority": 3
                         },
                         timeout=5)
        except Exception as e:
            print(f"Failed to send NTFY notification: {e}")

# Global logger instance
logger = AgentActivityLogger()

# Helper functions for easy use
def start_agent_session(agent_type, task_description, prompt):
    logger.start_session(agent_type, task_description, prompt)

def log_agent_command(command, description, result=None, error=None):
    logger.log_command(command, description, result, error)

def log_agent_file_change(file_path, change_type, before_content=None, after_content=None):
    logger.log_file_change(file_path, change_type, before_content, after_content)

def end_agent_session(status="COMPLETED", summary=None, errors=None):
    logger.end_session(status, summary, errors)

if __name__ == "__main__":
    # Test the logger
    start_agent_session("test-agent", "Testing logging system", "This is a test prompt")
    log_agent_command("echo 'test'", "Testing command logging", "test output")
    log_agent_file_change("/tmp/test.txt", "CREATE", None, "test content")
    end_agent_session("COMPLETED", "Successfully tested logging system")