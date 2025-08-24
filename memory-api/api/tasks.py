# ABOUTME: Task extraction and management API for Betty Memory System
# ABOUTME: Bypasses TodoWrite timeouts by using file-based task storage

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Dict, Optional, Any
from datetime import datetime
import json
import re
import uuid
from pathlib import Path
import asyncio
import structlog

from core.database import DatabaseManager
from core.dependencies import get_db_manager

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/tasks")

class BettyTaskExtractor:
    """
    Manus-inspired task extraction from conversations
    No API calls = No timeouts
    """
    
    def __init__(self):
        self.task_dir = Path.home() / ".betty" / "tasks"
        self.task_dir.mkdir(parents=True, exist_ok=True)
        self.current_tasks = self.task_dir / "current.jsonl"
        self.task_markdown = self.task_dir / "tasks.md"
        
    def extract_tasks_from_text(self, text: str) -> List[Dict]:
        """
        Extract tasks from conversation text using multiple patterns
        """
        tasks = []
        
        # Pattern 1: Explicit TODO markers
        todo_pattern = r'(?:TODO|TASK|FIX|IMPLEMENT|CREATE|ADD|UPDATE):\s*([^\n]+)'
        for match in re.finditer(todo_pattern, text, re.IGNORECASE):
            tasks.append({
                'task': match.group(1).strip(),
                'type': 'explicit',
                'priority': 2
            })
        
        # Pattern 2: Numbered lists that look like tasks
        numbered_pattern = r'^\d+\.\s+([A-Z][^\n]+)$'
        for match in re.finditer(numbered_pattern, text, re.MULTILINE):
            task_text = match.group(1).strip()
            if any(verb in task_text.lower() for verb in ['create', 'implement', 'add', 'fix', 'update', 'build', 'test']):
                tasks.append({
                    'task': task_text,
                    'type': 'numbered',
                    'priority': 1
                })
        
        # Pattern 3: Bullet points with action verbs
        bullet_pattern = r'^[-*]\s+([A-Z][^\n]+)$'
        for match in re.finditer(bullet_pattern, text, re.MULTILINE):
            task_text = match.group(1).strip()
            if any(verb in task_text.lower() for verb in ['need to', 'must', 'should', 'will', 'going to']):
                tasks.append({
                    'task': task_text,
                    'type': 'bullet',
                    'priority': 1
                })
        
        # Pattern 4: "I will/I'll" statements from assistant
        assistant_pattern = r"(?:I will|I'll|Let me|I'm going to)\s+([^\n.]+)"
        for match in re.finditer(assistant_pattern, text):
            tasks.append({
                'task': match.group(1).strip(),
                'type': 'assistant_commitment',
                'priority': 3
            })
        
        return tasks
    
    def save_task(self, task: Dict) -> Dict:
        """
        Save task to file system (instant, no timeout)
        """
        task_entry = {
            'id': str(uuid.uuid4()),
            'task': task['task'],
            'status': task.get('status', 'pending'),
            'priority': task.get('priority', 1),
            'type': task.get('type', 'manual'),
            'created': datetime.now().isoformat(),
            'updated': datetime.now().isoformat(),
            'session_id': task.get('session_id'),
            'extracted_from': task.get('extracted_from', 'conversation')
        }
        
        # Append to JSONL (no API call)
        with open(self.current_tasks, 'a') as f:
            f.write(json.dumps(task_entry) + '\n')
        
        # Update markdown for visibility
        self._update_markdown()
        
        return task_entry
    
    def get_all_tasks(self) -> List[Dict]:
        """
        Get all tasks from file system
        """
        if not self.current_tasks.exists():
            return []
        
        tasks = []
        with open(self.current_tasks, 'r') as f:
            for line in f:
                if line.strip():
                    tasks.append(json.loads(line))
        
        return tasks
    
    def update_task_status(self, task_id: str, status: str) -> bool:
        """
        Update task status without API calls
        """
        tasks = self.get_all_tasks()
        updated = False
        
        for task in tasks:
            if task['id'] == task_id:
                task['status'] = status
                task['updated'] = datetime.now().isoformat()
                if status == 'completed':
                    task['completed_at'] = datetime.now().isoformat()
                updated = True
        
        if updated:
            # Atomic write with temp file
            temp_file = self.current_tasks.with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                for task in tasks:
                    f.write(json.dumps(task) + '\n')
            
            # Atomic replace
            temp_file.replace(self.current_tasks)
            
            # Update markdown
            self._update_markdown()
        
        return updated
    
    def _update_markdown(self):
        """
        Update markdown file for human readability
        """
        tasks = self.get_all_tasks()
        
        content = "# Betty Task Tracker\n\n"
        content += f"*Last updated: {datetime.now().isoformat()}*\n\n"
        
        # Group by status
        pending = [t for t in tasks if t['status'] == 'pending']
        in_progress = [t for t in tasks if t['status'] == 'in_progress']
        completed = [t for t in tasks if t['status'] == 'completed']
        
        if in_progress:
            content += "## 🔄 In Progress\n"
            for task in sorted(in_progress, key=lambda x: x['priority'], reverse=True):
                content += f"- [ ] **[P{task['priority']}]** {task['task']}\n"
        
        if pending:
            content += "\n## 📋 Pending\n"
            for task in sorted(pending, key=lambda x: x['priority'], reverse=True):
                content += f"- [ ] [P{task['priority']}] {task['task']}\n"
        
        if completed:
            content += "\n## ✅ Completed\n"
            for task in completed[-10:]:  # Last 10 completed
                content += f"- [x] ~~{task['task']}~~\n"
        
        # Statistics
        content += f"\n---\n"
        content += f"**Stats**: {len(pending)} pending | {len(in_progress)} in progress | {len(completed)} completed\n"
        
        self.task_markdown.write_text(content)

# Initialize global extractor
extractor = BettyTaskExtractor()

@router.post("/extract")
async def extract_tasks_from_session(
    session_id: str,
    db_manager: DatabaseManager = Depends(get_db_manager)
) -> Dict[str, Any]:
    """
    Extract tasks from a conversation session
    No TodoWrite = No timeouts!
    """
    try:
        # Get session messages from database
        async with db_manager.postgres.acquire() as conn:
            messages = await conn.fetch(
                """
                SELECT content, role, created_at 
                FROM messages 
                WHERE session_id = $1 
                ORDER BY created_at
                """,
                session_id
            )
        
        if not messages:
            return {
                "success": False,
                "message": "No messages found in session",
                "tasks": []
            }
        
        # Combine all messages
        full_conversation = "\n".join([
            f"{msg['role']}: {msg['content']}" 
            for msg in messages
        ])
        
        # Extract tasks
        extracted = extractor.extract_tasks_from_text(full_conversation)
        
        # Save each task
        saved_tasks = []
        for task_data in extracted:
            task_data['session_id'] = session_id
            saved_task = extractor.save_task(task_data)
            saved_tasks.append(saved_task)
        
        logger.info(
            "Tasks extracted successfully",
            session_id=session_id,
            task_count=len(saved_tasks)
        )
        
        return {
            "success": True,
            "message": f"Extracted {len(saved_tasks)} tasks",
            "tasks": saved_tasks,
            "file_path": str(extractor.task_markdown)
        }
        
    except Exception as e:
        logger.error(
            "Failed to extract tasks",
            session_id=session_id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list")
async def list_all_tasks() -> Dict[str, Any]:
    """
    List all tasks from file system
    Instant response, no API timeouts
    """
    try:
        tasks = extractor.get_all_tasks()
        
        # Group by status
        by_status = {
            'pending': [],
            'in_progress': [],
            'completed': []
        }
        
        for task in tasks:
            status = task.get('status', 'pending')
            if status in by_status:
                by_status[status].append(task)
        
        return {
            "success": True,
            "total": len(tasks),
            "by_status": by_status,
            "tasks": tasks,
            "markdown_path": str(extractor.task_markdown)
        }
        
    except Exception as e:
        logger.error("Failed to list tasks", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{task_id}/status")
async def update_task_status(
    task_id: str,
    status: str
) -> Dict[str, Any]:
    """
    Update task status
    File-based = No timeout possible
    """
    if status not in ['pending', 'in_progress', 'completed', 'cancelled']:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    try:
        success = extractor.update_task_status(task_id, status)
        
        if not success:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return {
            "success": True,
            "message": f"Task {task_id} updated to {status}",
            "task_id": task_id,
            "status": status
        }
        
    except Exception as e:
        logger.error(
            "Failed to update task",
            task_id=task_id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/add")
async def add_manual_task(
    task: str,
    priority: int = 1,
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Manually add a task
    Direct file write = Instant success
    """
    try:
        task_data = {
            'task': task,
            'priority': priority,
            'type': 'manual',
            'session_id': session_id
        }
        
        saved_task = extractor.save_task(task_data)
        
        return {
            "success": True,
            "message": "Task added successfully",
            "task": saved_task
        }
        
    except Exception as e:
        logger.error("Failed to add task", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_task_statistics() -> Dict[str, Any]:
    """
    Get task statistics
    """
    try:
        tasks = extractor.get_all_tasks()
        
        stats = {
            'total': len(tasks),
            'pending': len([t for t in tasks if t['status'] == 'pending']),
            'in_progress': len([t for t in tasks if t['status'] == 'in_progress']),
            'completed': len([t for t in tasks if t['status'] == 'completed']),
            'by_type': {},
            'by_priority': {}
        }
        
        # Count by type
        for task in tasks:
            task_type = task.get('type', 'unknown')
            stats['by_type'][task_type] = stats['by_type'].get(task_type, 0) + 1
            
            priority = task.get('priority', 0)
            stats['by_priority'][f'P{priority}'] = stats['by_priority'].get(f'P{priority}', 0) + 1
        
        # Completion rate
        if stats['total'] > 0:
            stats['completion_rate'] = round(
                (stats['completed'] / stats['total']) * 100, 2
            )
        else:
            stats['completion_rate'] = 0
        
        return {
            "success": True,
            "statistics": stats
        }
        
    except Exception as e:
        logger.error("Failed to get statistics", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/cleanup")
async def cleanup_old_tasks(days_old: int = 30) -> Dict[str, Any]:
    """
    Archive old completed tasks
    """
    try:
        tasks = extractor.get_all_tasks()
        cutoff = datetime.now().timestamp() - (days_old * 86400)
        
        active_tasks = []
        archived_count = 0
        
        for task in tasks:
            if task['status'] == 'completed':
                created = datetime.fromisoformat(task['created']).timestamp()
                if created < cutoff:
                    archived_count += 1
                    continue
            active_tasks.append(task)
        
        # Write back active tasks
        temp_file = extractor.current_tasks.with_suffix('.tmp')
        with open(temp_file, 'w') as f:
            for task in active_tasks:
                f.write(json.dumps(task) + '\n')
        
        temp_file.replace(extractor.current_tasks)
        extractor._update_markdown()
        
        return {
            "success": True,
            "message": f"Archived {archived_count} old tasks",
            "remaining": len(active_tasks)
        }
        
    except Exception as e:
        logger.error("Failed to cleanup tasks", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))