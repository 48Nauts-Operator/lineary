#!/usr/bin/env python3
"""
Comprehensive import tool for Betty Memory System
Imports from multiple sources:
1. Claude local storage (.claude/projects)
2. Betty proxy captures
3. Any JSON conversation files
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
import argparse

class BettyImporter:
    def __init__(self, db_url=None):
        self.db_url = db_url or "postgresql://betty:betty_memory_2024@localhost:5434/betty_memory"
        self.stats = {
            'imported': 0,
            'skipped': 0,
            'failed': 0,
            'total': 0
        }
        
    async def connect(self):
        """Create database connection"""
        self.conn = await asyncpg.connect(self.db_url)
        
    async def close(self):
        """Close database connection"""
        if hasattr(self, 'conn'):
            await self.conn.close()
    
    async def import_json_file(self, file_path, source_type="unknown"):
        """Import a single JSON file"""
        self.stats['total'] += 1
        
        try:
            # Read file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Try to parse as JSON
            try:
                data = json.loads(content)
            except json.JSONDecodeError:
                # Try to extract JSON from text
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group())
                else:
                    raise ValueError("No valid JSON found")
            
            # Generate hash
            content_hash = hashlib.sha256(content.encode()).hexdigest()
            
            # Check if already exists
            existing = await self.conn.fetchval(
                "SELECT id FROM knowledge_items WHERE content_hash = $1",
                content_hash
            )
            
            if existing:
                print(f"  ⚠️  Skip (duplicate): {os.path.basename(file_path)}")
                self.stats['skipped'] += 1
                return
            
            # Determine content type
            knowledge_type = 'conversation'
            if 'messages' in str(data).lower() or 'request' in str(data).lower():
                knowledge_type = 'conversation'
            elif 'code' in file_path.lower():
                knowledge_type = 'code'
            elif 'doc' in file_path.lower():
                knowledge_type = 'document'
            
            # Create knowledge item
            item_id = str(uuid.uuid4())
            title = self._generate_title(data, file_path)
            
            # Insert into database
            await self.conn.execute("""
                INSERT INTO knowledge_items (
                    id, title, content, knowledge_type, quality_score, complexity_level,
                    user_id, project_id, content_hash, metadata, created_at, updated_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                )
            """, 
                item_id, 
                title, 
                json.dumps(data) if isinstance(data, dict) else content,
                knowledge_type,
                0.8,  # quality_score
                'medium',  # complexity_level
                '95fd614f-7da8-4650-bf23-ed53acba34c2',  # Default system user
                'c5d0c92a-d609-4a9d-bb59-473b7dc12d3a',  # Betty project
                content_hash,
                json.dumps({
                    'source': source_type,
                    'file_path': str(file_path),
                    'file_size': os.path.getsize(file_path),
                    'import_date': datetime.now().isoformat()
                })
            )
            
            print(f"  ✅ Imported: {os.path.basename(file_path)[:50]}...")
            self.stats['imported'] += 1
            
        except Exception as e:
            print(f"  ❌ Failed: {os.path.basename(file_path)} - {str(e)[:50]}")
            self.stats['failed'] += 1
    
    def _generate_title(self, data, file_path):
        """Generate a meaningful title"""
        if isinstance(data, dict):
            # Try to extract from data
            if 'title' in data:
                return data['title']
            elif 'timestamp' in data:
                return f"Conversation - {data['timestamp']}"
            elif 'request' in data and 'model' in data['request']:
                return f"{data['request']['model']} - {datetime.now().isoformat()}"
        
        # Fallback to filename
        return f"Import: {os.path.basename(file_path)}"
    
    async def import_directory(self, directory, pattern="*.json", source_type="directory"):
        """Import all matching files from a directory"""
        print(f"\n📁 Importing from: {directory}")
        print(f"   Pattern: {pattern}")
        
        files = glob.glob(os.path.join(directory, "**", pattern), recursive=True)
        print(f"   Found {len(files)} files")
        
        for file_path in files:
            await self.import_json_file(file_path, source_type)
    
    async def import_claude_storage(self):
        """Import from Claude local storage"""
        claude_dir = "/home/jarvis/.claude/projects"
        if os.path.exists(claude_dir):
            await self.import_directory(claude_dir, "*.json", "claude_local")
        else:
            print(f"❌ Claude directory not found: {claude_dir}")
    
    async def import_betty_captures(self):
        """Import from Betty proxy captures"""
        # These are already in the database, but check for any file exports
        betty_dir = "/home/jarvis/projects/Betty"
        patterns = ["*conversation*.json", "*capture*.json", "*betty*.json"]
        
        for pattern in patterns:
            files = glob.glob(os.path.join(betty_dir, pattern))
            for file_path in files:
                await self.import_json_file(file_path, "betty_export")
    
    def print_stats(self):
        """Print import statistics"""
        print("\n" + "="*50)
        print("📊 Import Statistics:")
        print(f"  ✅ Imported: {self.stats['imported']}")
        print(f"  ⚠️  Skipped: {self.stats['skipped']}")
        print(f"  ❌ Failed: {self.stats['failed']}")
        print(f"  📁 Total: {self.stats['total']}")
        print("="*50)

async def main():
    parser = argparse.ArgumentParser(description='Import conversations into Betty Memory System')
    parser.add_argument('--claude', action='store_true', help='Import from Claude local storage')
    parser.add_argument('--directory', type=str, help='Import from specific directory')
    parser.add_argument('--file', type=str, help='Import single file')
    parser.add_argument('--all', action='store_true', help='Import from all known sources')
    
    args = parser.parse_args()
    
    print("=== Betty Memory Import Tool ===")
    
    importer = BettyImporter()
    await importer.connect()
    
    try:
        if args.all or args.claude:
            await importer.import_claude_storage()
        
        if args.directory:
            await importer.import_directory(args.directory)
        
        if args.file:
            await importer.import_json_file(args.file, "manual")
        
        if args.all:
            await importer.import_betty_captures()
        
        if not any([args.all, args.claude, args.directory, args.file]):
            print("No import source specified. Use --help for options.")
            
    finally:
        importer.print_stats()
        await importer.close()

if __name__ == "__main__":
    asyncio.run(main())