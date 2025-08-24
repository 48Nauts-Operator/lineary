#!/usr/bin/env python3
"""
ABOUTME: PostTool hook that syncs Betty documentation to Obsidian vault
ABOUTME: Automatically copies new/modified docs maintaining directory structure
"""

import os
import sys
import json
import shutil
from pathlib import Path
from datetime import datetime

# Configuration
BETTY_DOCS_BASE = Path("/home/jarvis/projects/Betty/docs")
OBSIDIAN_VAULT_BASE = Path("/home/jarvis/projects/obsidian-vault/betty-vault/Betty/docs")
LOG_FILE = Path("/home/jarvis/projects/Betty/hooks/obsidian-sync.log")

def log_message(message):
    """Log messages with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}\n"
    
    # Write to log file
    with open(LOG_FILE, "a") as f:
        f.write(log_entry)
    
    # Also print for debugging
    print(f"[Obsidian Sync] {message}", file=sys.stderr)

def should_sync_file(file_path):
    """Determine if a file should be synced to Obsidian"""
    path_str = str(file_path).lower()
    
    # File extensions to sync
    doc_extensions = ['.md', '.txt', '.json', '.yaml', '.yml']
    
    # Check if it's a documentation file
    if any(path_str.endswith(ext) for ext in doc_extensions):
        return True
    
    return False

def sync_file_to_obsidian(source_file):
    """Copy a file to Obsidian vault maintaining structure"""
    try:
        # Convert to Path objects
        source_path = Path(source_file)
        
        # Only sync files within Betty docs directory
        if not str(source_path).startswith(str(BETTY_DOCS_BASE)):
            return False
        
        # Calculate relative path from Betty docs base
        relative_path = source_path.relative_to(BETTY_DOCS_BASE)
        
        # Construct destination path in Obsidian vault
        dest_path = OBSIDIAN_VAULT_BASE / relative_path
        
        # Create destination directory if it doesn't exist
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy the file
        shutil.copy2(source_path, dest_path)
        
        log_message(f"Synced: {relative_path} → Obsidian vault")
        return True
        
    except Exception as e:
        log_message(f"Error syncing {source_file}: {str(e)}")
        return False

def process_tool_result(tool_result):
    """Process tool results to find files that need syncing"""
    try:
        tool_name = tool_result.get("tool", "")
        
        # Tools that might create or modify documentation
        doc_tools = ["Write", "Edit", "MultiEdit", "NotebookEdit"]
        
        if tool_name not in doc_tools:
            return
        
        # Extract file path from tool input
        tool_input = tool_result.get("input", {})
        file_path = None
        
        if tool_name == "Write":
            file_path = tool_input.get("file_path")
        elif tool_name in ["Edit", "MultiEdit"]:
            file_path = tool_input.get("file_path")
        elif tool_name == "NotebookEdit":
            file_path = tool_input.get("notebook_path")
        
        if file_path and should_sync_file(file_path):
            # Check if it's in the Betty docs directory
            if str(file_path).startswith(str(BETTY_DOCS_BASE)):
                sync_file_to_obsidian(file_path)
                
                # Send notification about sync
                print(json.dumps({
                    "notification": {
                        "title": "📚 Obsidian Sync",
                        "message": f"Synced {Path(file_path).name} to vault",
                        "type": "info"
                    }
                }))
    
    except Exception as e:
        log_message(f"Error processing tool result: {str(e)}")

def main():
    """Main hook entry point"""
    try:
        # Ensure Obsidian vault directory exists
        OBSIDIAN_VAULT_BASE.mkdir(parents=True, exist_ok=True)
        
        # Read tool result from stdin
        tool_result_json = sys.stdin.read()
        
        if not tool_result_json:
            return
        
        tool_result = json.loads(tool_result_json)
        
        # Process the tool result
        process_tool_result(tool_result)
        
        # Always pass through the original result
        print(tool_result_json, end='')
        
    except json.JSONDecodeError:
        # Not JSON, just pass through
        print(tool_result_json, end='')
    except Exception as e:
        log_message(f"Hook error: {str(e)}")
        # Still pass through the original input
        print(tool_result_json, end='')

if __name__ == "__main__":
    main()