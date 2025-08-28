#!/usr/bin/env python3
"""
ABOUTME: Betty PreTool Todo Checker - Checks and organizes todos before tool execution
ABOUTME: Integrates with Claude Code to provide todo context before any task
"""

import json
import os
import sys
import re
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

class BettyPreToolTodoChecker:
    def __init__(self):
        self.todo_base_dir = Path("/home/jarvis/projects/Betty/todos")
        self.betty_api_url = "http://localhost:3034/api/tasks"
        
        # Categories for organization
        self.categories = {
            "priority": [],  # P0-P1: Critical/Urgent
            "general": [],   # P2-P3: Normal workflow
            "backlog": []    # P4-P5: Future enhancements
        }
        
        # Priority keywords
        self.priority_keywords = {
            "high": ["critical", "urgent", "fix", "broken", "error", "security", "crash", "bug", "P0", "P1"],
            "normal": ["implement", "create", "add", "update", "improve", "P2", "P3"],
            "low": ["optimize", "refactor", "enhance", "document", "cleanup", "P4", "P5"]
        }
    
    def check_todos(self, tool_name: str = None, tool_inputs: Dict = None) -> Dict:
        """Main PreTool check"""
        try:
            # Load todos from various sources
            file_todos = self.load_file_todos()
            api_todos = self.load_api_todos()
            
            # Merge and categorize
            all_todos = self.merge_todos(file_todos, api_todos)
            self.categorize_todos(all_todos)
            
            # Find relevant todos
            relevant = self.find_relevant_todos(tool_name, tool_inputs)
            
            # Generate report
            report = self.generate_report(relevant)
            
            # Save organized structure
            self.save_organized_todos()
            
            # Check if we should block or warn
            should_block, reason = self.should_block_execution(tool_name, relevant, tool_inputs)
            
            return {
                "success": True,
                "report": report,
                "relevant_todos": relevant,
                "should_block": should_block,
                "block_reason": reason,
                "stats": {
                    "total": len(all_todos),
                    "priority": len(self.categories["priority"]),
                    "general": len(self.categories["general"]),
                    "backlog": len(self.categories["backlog"])
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def load_file_todos(self) -> List[Dict]:
        """Load todos from markdown files"""
        todos = []
        active_dir = self.todo_base_dir / "active"
        
        if active_dir.exists():
            for md_file in active_dir.glob("*.md"):
                content = md_file.read_text()
                extracted = self.extract_todos_from_markdown(content, md_file.name)
                todos.extend(extracted)
        
        return todos
    
    def extract_todos_from_markdown(self, content: str, filename: str) -> List[Dict]:
        """Extract todo items from markdown"""
        todos = []
        lines = content.split("\n")
        current_priority = self.extract_priority(f"{filename} {content}")
        
        patterns = [
            r"^[-*]\s*\[[\s]\]\s*(.+)",       # - [ ] Task
            r"^[-*]\s*TODO:\s*(.+)",          # - TODO: Task
            r"^\*\*T\d+[^:]*\**:\s*(.+)",     # **T001-AUTH**: Task
        ]
        
        for line in lines:
            for pattern in patterns:
                match = re.match(pattern, line)
                if match:
                    todos.append({
                        "task": match.group(1).strip(),
                        "source": "file",
                        "file": filename,
                        "priority": current_priority,
                        "status": "pending"
                    })
            
            # Update priority from line content
            if "P0" in line or "Critical" in line:
                current_priority = 1
            elif "P1" in line or "High" in line:
                current_priority = 2
            elif "P2" in line or "Normal" in line:
                current_priority = 3
            elif "P3" in line or "Low" in line:
                current_priority = 4
            elif "P4" in line or "Backlog" in line:
                current_priority = 5
        
        return todos
    
    def load_api_todos(self) -> List[Dict]:
        """Load todos from Betty API"""
        try:
            response = requests.get(f"{self.betty_api_url}/list", timeout=2)
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    pending = data.get("by_status", {}).get("pending", [])
                    return [{**todo, "source": "api"} for todo in pending]
        except:
            pass
        return []
    
    def merge_todos(self, file_todos: List[Dict], api_todos: List[Dict]) -> List[Dict]:
        """Merge and deduplicate todos"""
        seen = set()
        merged = []
        
        for todo in file_todos + api_todos:
            key = todo["task"].lower().strip()
            if key not in seen:
                seen.add(key)
                merged.append(todo)
        
        return merged
    
    def categorize_todos(self, todos: List[Dict]):
        """Categorize todos by priority"""
        for todo in todos:
            priority = todo.get("priority", self.extract_priority(todo["task"]))
            
            if priority <= 2:
                self.categories["priority"].append(todo)
            elif priority <= 4:
                self.categories["general"].append(todo)
            else:
                self.categories["backlog"].append(todo)
        
        # Sort within categories
        for category in self.categories.values():
            category.sort(key=lambda x: x.get("priority", 5))
    
    def extract_priority(self, text: str) -> int:
        """Extract priority from text"""
        text_lower = text.lower()
        
        # Explicit priority markers
        if "p0" in text_lower or "critical" in text_lower:
            return 1
        if "p1" in text_lower or "urgent" in text_lower:
            return 2
        if "p2" in text_lower:
            return 3
        if "p3" in text_lower:
            return 4
        if "p4" in text_lower or "backlog" in text_lower:
            return 5
        
        # Keyword-based priority
        for keyword in self.priority_keywords["high"]:
            if keyword in text_lower:
                return 2
        
        for keyword in self.priority_keywords["normal"]:
            if keyword in text_lower:
                return 3
        
        for keyword in self.priority_keywords["low"]:
            if keyword in text_lower:
                return 4
        
        return 3  # Default
    
    def find_relevant_todos(self, tool_name: Optional[str], tool_inputs: Optional[Dict]) -> List[Dict]:
        """Find todos relevant to current tool execution"""
        if not tool_name and not tool_inputs:
            return []
        
        relevant = []
        search_text = f"{tool_name or ''} {str(tool_inputs or '')}".lower()
        
        all_todos = []
        for todos in self.categories.values():
            all_todos.extend(todos)
        
        for todo in all_todos:
            todo_text = todo["task"].lower()
            words = search_text.split()
            
            # Check for matching words
            for word in words:
                if len(word) > 3 and word in todo_text:
                    relevant.append(todo)
                    break
        
        return relevant
    
    def generate_report(self, relevant_todos: List[Dict]) -> str:
        """Generate todo report"""
        lines = []
        
        # Header
        lines.append("=" * 60)
        lines.append("📋 BETTY TODO CHECKER - PRETOOL ANALYSIS")
        lines.append("=" * 60)
        
        # Priority tasks
        if self.categories["priority"]:
            lines.append("\n🔥 PRIORITY TASKS (P0-P1):")
            for todo in self.categories["priority"][:5]:
                lines.append(f"  • {todo['task']}")
            if len(self.categories["priority"]) > 5:
                lines.append(f"  ... and {len(self.categories['priority']) - 5} more")
        
        # General tasks
        if self.categories["general"]:
            lines.append("\n📝 GENERAL TASKS (P2-P3):")
            for todo in self.categories["general"][:3]:
                lines.append(f"  • {todo['task']}")
            if len(self.categories["general"]) > 3:
                lines.append(f"  ... and {len(self.categories['general']) - 3} more")
        
        # Backlog count
        if self.categories["backlog"]:
            lines.append(f"\n📦 BACKLOG (P4-P5): {len(self.categories['backlog'])} items")
        
        # Relevant todos
        if relevant_todos:
            lines.append("\n⚡ RELEVANT TO CURRENT TASK:")
            for todo in relevant_todos:
                priority = todo.get('priority', 3)
                lines.append(f"  • {todo['task']} [P{priority}]")
        
        # Summary
        total = sum(len(cat) for cat in self.categories.values())
        lines.append(f"\n📊 TOTAL: {total} todos")
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def should_block_execution(self, tool_name: str, relevant_todos: List[Dict], tool_inputs: Dict = None) -> Tuple[bool, str]:
        """Check if we should block tool execution"""
        # Only block for EXTREMELY critical situations (P0 only, not P1)
        # And only if the tool is creating new work, not investigating/fixing
        critical_todos = [t for t in self.categories["priority"] if t.get("priority", 3) == 1]
        
        # List of tools that should never be blocked (investigation/fix tools)
        never_block = ["Bash", "Read", "Grep", "LS", "Edit", "MultiEdit", "Write", "Task"]
        
        # Only block if trying to create NEW features with P0 todos pending
        if critical_todos and tool_name not in never_block:
            # Check if this seems like new feature work
            if tool_inputs and any(word in str(tool_inputs).lower() 
                                 for word in ["create new", "add feature", "implement new"]):
                tasks = ", ".join([t["task"] for t in critical_todos[:2]])
                return True, f"⚠️ P0 CRITICAL TODOS: {tasks}"
        
        return False, ""
    
    def save_organized_todos(self):
        """Save organized todos to structured directories"""
        try:
            # Create directories
            for category in ["priority", "general", "backlog"]:
                (self.todo_base_dir / category).mkdir(parents=True, exist_ok=True)
            
            # Save summaries
            for category, todos in self.categories.items():
                self.save_category_markdown(category, todos)
            
            # Save JSON summary
            summary = {
                "timestamp": datetime.now().isoformat(),
                "stats": {
                    "total": sum(len(cat) for cat in self.categories.values()),
                    "priority": len(self.categories["priority"]),
                    "general": len(self.categories["general"]),
                    "backlog": len(self.categories["backlog"])
                },
                "categories": {
                    cat: [{"task": t["task"], "priority": t.get("priority", 3)} for t in todos]
                    for cat, todos in self.categories.items()
                }
            }
            
            (self.todo_base_dir / "todo-summary.json").write_text(
                json.dumps(summary, indent=2)
            )
            
        except Exception as e:
            print(f"Warning: Could not save todos: {e}", file=sys.stderr)
    
    def save_category_markdown(self, category: str, todos: List[Dict]):
        """Save category as markdown"""
        emoji_map = {"priority": "🔥", "general": "📝", "backlog": "📦"}
        
        content = [
            f"# {emoji_map.get(category, '📋')} {category.upper()} TASKS",
            f"\n**Total**: {len(todos)} tasks",
            f"**Updated**: {datetime.now().isoformat()}",
            "\n## Tasks\n"
        ]
        
        for i, todo in enumerate(todos, 1):
            content.append(f"### {i}. {todo['task']}")
            content.append(f"- **Priority**: P{todo.get('priority', 3)}")
            content.append(f"- **Source**: {todo.get('source', 'unknown')}")
            if todo.get("file"):
                content.append(f"- **File**: {todo['file']}")
            content.append("")
        
        (self.todo_base_dir / category / "README.md").write_text("\n".join(content))


def main():
    """Hook entry point for Claude Code"""
    # Read hook input
    hook_input = json.loads(sys.stdin.read())
    
    tool_name = hook_input.get("tool", "")
    tool_inputs = hook_input.get("inputs", {})
    
    # Initialize checker
    checker = BettyPreToolTodoChecker()
    result = checker.check_todos(tool_name, tool_inputs)
    
    # Print report to stderr so it shows in Claude
    if result.get("report"):
        print(result["report"], file=sys.stderr)
    
    # Check if we should block
    if result.get("should_block"):
        print(f"\n❌ BLOCKING: {result['block_reason']}", file=sys.stderr)
        response = {
            "action": "block",
            "message": result["block_reason"]
        }
    else:
        response = {
            "action": "continue",
            "metadata": {
                "todos_checked": True,
                "relevant_count": len(result.get("relevant_todos", [])),
                "priority_count": result.get("stats", {}).get("priority", 0)
            }
        }
    
    # Output response
    print(json.dumps(response))


if __name__ == "__main__":
    main()