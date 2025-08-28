#!/usr/bin/env python3
"""
Simple Task Tracker for Claude Sessions
Alternative to TodoWrite that won't timeout
"""

import json
import datetime
from pathlib import Path
from typing import List, Dict, Optional
import re

class SimpleTaskTracker:
    """Lightweight task tracker that uses local files instead of API calls"""
    
    def __init__(self, project_path: str = "/home/jarvis/projects/Betty"):
        self.project_path = Path(project_path)
        self.tasks_file = self.project_path / "current-tasks.json"
        self.tasks = self.load_tasks()
        
    def load_tasks(self) -> List[Dict]:
        """Load tasks from file"""
        if self.tasks_file.exists():
            try:
                with open(self.tasks_file) as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def save_tasks(self):
        """Save tasks to file"""
        with open(self.tasks_file, 'w') as f:
            json.dump(self.tasks, f, indent=2)
    
    def add_task(self, content: str, status: str = "pending") -> Dict:
        """Add a new task"""
        task = {
            "id": str(len(self.tasks) + 1),
            "content": content,
            "status": status,
            "created": datetime.datetime.now().isoformat(),
            "updated": datetime.datetime.now().isoformat()
        }
        self.tasks.append(task)
        self.save_tasks()
        return task
    
    def update_task(self, task_id: str, status: Optional[str] = None, content: Optional[str] = None):
        """Update an existing task"""
        for task in self.tasks:
            if task["id"] == task_id:
                if status:
                    task["status"] = status
                if content:
                    task["content"] = content
                task["updated"] = datetime.datetime.now().isoformat()
                self.save_tasks()
                return task
        return None
    
    def get_markdown(self) -> str:
        """Get tasks as markdown"""
        if not self.tasks:
            return "No tasks currently tracked."
        
        lines = ["## Current Tasks\n"]
        
        # Group by status
        pending = [t for t in self.tasks if t["status"] == "pending"]
        in_progress = [t for t in self.tasks if t["status"] == "in_progress"]
        completed = [t for t in self.tasks if t["status"] == "completed"]
        
        if in_progress:
            lines.append("### 🔄 In Progress")
            for task in in_progress:
                lines.append(f"- [{task['id']}] {task['content']}")
            lines.append("")
        
        if pending:
            lines.append("### 📋 Pending")
            for task in pending:
                lines.append(f"- [{task['id']}] {task['content']}")
            lines.append("")
        
        if completed:
            lines.append("### ✅ Completed")
            for task in completed:
                lines.append(f"- [{task['id']}] ~~{task['content']}~~")
            lines.append("")
        
        return "\n".join(lines)
    
    def extract_from_text(self, text: str) -> List[str]:
        """Extract TODO items from text"""
        patterns = [
            r'(?:TODO|TASK|FIXME):\s*(.+?)(?:\n|$)',
            r'- \[ \]\s*(.+?)(?:\n|$)',
            r'\d+\.\s*(.+?)(?:\n|$)'  # Numbered lists
        ]
        
        tasks = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            tasks.extend(matches)
        
        return list(set(tasks))  # Remove duplicates
    
    def clear_completed(self):
        """Remove completed tasks"""
        self.tasks = [t for t in self.tasks if t["status"] != "completed"]
        self.save_tasks()
    
    def get_stats(self) -> Dict:
        """Get task statistics"""
        total = len(self.tasks)
        if total == 0:
            return {"total": 0, "completed": 0, "pending": 0, "in_progress": 0, "completion_rate": 0}
        
        completed = len([t for t in self.tasks if t["status"] == "completed"])
        pending = len([t for t in self.tasks if t["status"] == "pending"])
        in_progress = len([t for t in self.tasks if t["status"] == "in_progress"])
        
        return {
            "total": total,
            "completed": completed,
            "pending": pending,
            "in_progress": in_progress,
            "completion_rate": round((completed / total) * 100, 2) if total > 0 else 0
        }

def main():
    """CLI interface for task tracker"""
    import sys
    
    tracker = SimpleTaskTracker()
    
    if len(sys.argv) < 2:
        print(tracker.get_markdown())
        stats = tracker.get_stats()
        print(f"\n📊 Stats: {stats['completed']}/{stats['total']} completed ({stats['completion_rate']}%)")
        return
    
    command = sys.argv[1].lower()
    
    if command == "add":
        if len(sys.argv) < 3:
            print("Usage: simple-task-tracker.py add 'task description'")
            return
        task = tracker.add_task(" ".join(sys.argv[2:]))
        print(f"✅ Added task [{task['id']}]: {task['content']}")
    
    elif command == "update":
        if len(sys.argv) < 4:
            print("Usage: simple-task-tracker.py update <id> <status>")
            return
        task_id = sys.argv[2]
        status = sys.argv[3]
        task = tracker.update_task(task_id, status=status)
        if task:
            print(f"✅ Updated task [{task['id']}] to {status}")
        else:
            print(f"❌ Task {task_id} not found")
    
    elif command == "clear":
        tracker.clear_completed()
        print("✅ Cleared completed tasks")
    
    elif command == "stats":
        stats = tracker.get_stats()
        print(f"📊 Task Statistics:")
        print(f"  Total: {stats['total']}")
        print(f"  Completed: {stats['completed']}")
        print(f"  In Progress: {stats['in_progress']}")
        print(f"  Pending: {stats['pending']}")
        print(f"  Completion Rate: {stats['completion_rate']}%")
    
    else:
        print(f"Unknown command: {command}")
        print("Available commands: add, update, clear, stats")

if __name__ == "__main__":
    main()