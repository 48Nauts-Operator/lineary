#!/usr/bin/env python3
"""
Import Claude Code conversation history from local storage into Betty Memory System
"""

import os
import json
import glob
import asyncio
from datetime import datetime
from pathlib import Path
import hashlib
import uuid
import asyncpg
import sys

# Claude storage location
CLAUDE_PROJECTS_DIR = "/home/jarvis/.claude/projects"
BETTY_DB_URL = "postgresql://betty:betty_memory_2024@localhost:5434/betty_memory"

async def get_db_connection():
    """Create database connection"""
    return await asyncpg.connect(BETTY_DB_URL)

async def import_conversation(conn, file_path):
    """Import a single conversation file"""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Extract metadata from file path
        file_name = os.path.basename(file_path)
        project_path = os.path.dirname(file_path)
        
        # Create knowledge item
        item_id = str(uuid.uuid4())
        title = f"Claude Conversation - {file_name}"
        content = json.dumps(data)
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        
        # Check if already imported (by hash)
        existing = await conn.fetchval(
            "SELECT id FROM knowledge_items WHERE content_hash = $1",
            content_hash
        )
        
        if existing:
            print(f"  ⚠️  Already imported: {file_name}")
            return False
        
        # Insert into database
        await conn.execute("""
            INSERT INTO knowledge_items (
                id, title, content, knowledge_type, quality_score, complexity_level,
                user_id, project_id, content_hash, metadata, created_at, updated_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            )
        """, 
            item_id, title, content, 'conversation', 0.8, 'medium',
            '95fd614f-7da8-4650-bf23-ed53acba34c2',  # Default system user
            'c5d0c92a-d609-4a9d-bb59-473b7dc12d3a',  # Betty project
            content_hash,
            json.dumps({
                'source': 'claude_local_import',
                'file_path': str(file_path),
                'import_date': datetime.now().isoformat()
            })
        )
        
        print(f"  ✅ Imported: {file_name}")
        return True
        
    except json.JSONDecodeError:
        print(f"  ❌ Invalid JSON: {file_path}")
        return False
    except Exception as e:
        print(f"  ❌ Error importing {file_path}: {e}")
        return False

async def main():
    """Main import function"""
    print("=== Claude History Import Tool ===\n")
    
    # Find all JSON files in Claude projects
    pattern = os.path.join(CLAUDE_PROJECTS_DIR, "**/*.json")
    files = glob.glob(pattern, recursive=True)
    
    print(f"Found {len(files)} JSON files in {CLAUDE_PROJECTS_DIR}")
    
    if not files:
        print("No files to import.")
        return
    
    # Connect to database
    conn = await get_db_connection()
    
    imported = 0
    skipped = 0
    failed = 0
    
    try:
        for file_path in files:
            result = await import_conversation(conn, file_path)
            if result:
                imported += 1
            elif result is False:
                skipped += 1
            else:
                failed += 1
                
    finally:
        await conn.close()
    
    print(f"\n=== Import Complete ===")
    print(f"✅ Imported: {imported}")
    print(f"⚠️  Skipped (duplicates): {skipped}")
    print(f"❌ Failed: {failed}")
    print(f"Total processed: {len(files)}")

if __name__ == "__main__":
    asyncio.run(main())