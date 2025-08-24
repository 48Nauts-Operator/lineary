#!/usr/bin/env python3
"""
ABOUTME: Lineary Task Manager - Direct task management without TodoWrite
ABOUTME: Provides fast, reliable task operations via Lineary's native API
"""

import requests
import json
import sys
from typing import List, Dict, Optional
from datetime import datetime
import argparse

class LinearyTaskManager:
    def __init__(self):
        self.api_url = "http://localhost:3034/api/tasks"
        self.headers = {"Content-Type": "application/json"}
    
    def add_task(self, task: str, priority: int = 3, category: str = "general") -> Optional[Dict]:
        """Add a task directly to Lineary"""
        try:
            response = requests.post(
                f"{self.api_url}/add",
                params={
                    "task": task,
                    "priority": priority,
                    "category": category
                },
                timeout=5  # Fast timeout
            )
            return response.json()
        except Exception as e:
            print(f"Error adding task: {e}")
            return None
    
    def list_tasks(self, status: str = None, category: str = None) -> Dict:
        """List tasks with optional filtering"""
        params = {}
        if status:
            params["status"] = status
        if category:
            params["category"] = category
        
        try:
            response = requests.get(
                f"{self.api_url}/list",
                params=params,
                timeout=5
            )
            return response.json()
        except Exception as e:
            print(f"Error listing tasks: {e}")
            return {"tasks": []}
    
    def update_task(self, task_id: str, status: str) -> Optional[Dict]:
        """Update task status"""
        try:
            response = requests.put(
                f"{self.api_url}/{task_id}/status",
                params={"status": status},
                timeout=5
            )
            return response.json()
        except Exception as e:
            print(f"Error updating task: {e}")
            return None
    
    def organize_tasks(self) -> Dict[str, List]:
        """Organize tasks into priority, general, and backlog"""
        all_tasks = self.list_tasks(status="pending")
        
        organized = {
            "priority": [],
            "general": [],
            "backlog": []
        }
        
        for task in all_tasks.get("tasks", []):
            priority = task.get("priority", 3)
            if priority >= 4:
                organized["priority"].append(task)
            elif priority >= 2:
                organized["general"].append(task)
            else:
                organized["backlog"].append(task)
        
        return organized
    
    def print_dashboard(self):
        """Print organized task dashboard"""
        organized = self.organize_tasks()
        
        total_tasks = sum(len(tasks) for tasks in organized.values())
        
        print("\n" + "=" * 60)
        print(f"📊 LINEARY TASK DASHBOARD - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"Total Tasks: {total_tasks}")
        print("=" * 60)
        
        if organized["priority"]:
            print("\n🔴 PRIORITY TASKS (High Impact)")
            print("-" * 50)
            for i, task in enumerate(organized["priority"], 1):
                status_icon = "⚡" if task.get("status") == "pending" else "✓"
                print(f"{status_icon} {i}. [{task['id'][:8]}] {task['task']}")
                if task.get("created"):
                    created = datetime.fromisoformat(task['created'].replace('Z', '+00:00'))
                    age = (datetime.now() - created.replace(tzinfo=None)).days
                    if age > 0:
                        print(f"     📅 {age} days old")
        
        if organized["general"]:
            print("\n🟡 GENERAL TASKS (Normal Priority)")
            print("-" * 50)
            for i, task in enumerate(organized["general"], 1):
                status_icon = "📝" if task.get("status") == "pending" else "✓"
                print(f"{status_icon} {i}. [{task['id'][:8]}] {task['task']}")
        
        if organized["backlog"]:
            print("\n🟢 BACKLOG (Low Priority)")
            print("-" * 50)
            for i, task in enumerate(organized["backlog"], 1):
                status_icon = "💤" if task.get("status") == "pending" else "✓"
                print(f"{status_icon} {i}. [{task['id'][:8]}] {task['task']}")
        
        print("\n" + "=" * 60)
        print("Commands: lineary-tasks add|list|complete|priority")
        print("=" * 60 + "\n")
    
    def set_priority(self, task_id: str, priority: int) -> Optional[Dict]:
        """Update task priority"""
        try:
            response = requests.put(
                f"{self.api_url}/{task_id}/priority",
                params={"priority": priority},
                timeout=5
            )
            return response.json()
        except Exception as e:
            print(f"Error updating priority: {e}")
            return None

def main():
    parser = argparse.ArgumentParser(description="Lineary Task Manager")
    parser.add_argument("command", nargs="?", default="list",
                        choices=["add", "list", "complete", "priority"],
                        help="Command to execute")
    parser.add_argument("args", nargs="*", help="Command arguments")
    parser.add_argument("-p", "--priority", type=int, default=3,
                        help="Task priority (1-5, higher is more important)")
    parser.add_argument("-c", "--category", default="general",
                        help="Task category (priority/general/backlog)")
    
    args = parser.parse_args()
    manager = LinearyTaskManager()
    
    if args.command == "add":
        if args.args:
            task = " ".join(args.args)
            result = manager.add_task(task, args.priority, args.category)
            if result and result.get("success"):
                print(f"✅ Task added: {task}")
                print(f"   ID: {result.get('task', {}).get('id', 'unknown')[:8]}")
            else:
                print(f"❌ Failed to add task")
    
    elif args.command == "list":
        manager.print_dashboard()
    
    elif args.command == "complete":
        if args.args:
            task_id = args.args[0]
            # Handle short IDs (first 8 chars)
            if len(task_id) == 8:
                # Find full ID from list
                all_tasks = manager.list_tasks()
                for task in all_tasks.get("tasks", []):
                    if task["id"].startswith(task_id):
                        task_id = task["id"]
                        break
            
            result = manager.update_task(task_id, "completed")
            if result and result.get("success"):
                print(f"✅ Task completed!")
            else:
                print(f"❌ Failed to complete task")
    
    elif args.command == "priority":
        if len(args.args) >= 2:
            task_id = args.args[0]
            priority = int(args.args[1])
            
            # Handle short IDs
            if len(task_id) == 8:
                all_tasks = manager.list_tasks()
                for task in all_tasks.get("tasks", []):
                    if task["id"].startswith(task_id):
                        task_id = task["id"]
                        break
            
            result = manager.set_priority(task_id, priority)
            if result and result.get("success"):
                print(f"✅ Priority updated to {priority}")
            else:
                print(f"❌ Failed to update priority")
        else:
            print("Usage: lineary-tasks priority <task_id> <priority>")

if __name__ == "__main__":
    main()