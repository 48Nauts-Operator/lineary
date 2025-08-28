#!/usr/bin/env python3
"""
Import Claude Code JSONL conversation files into Betty Memory System
Uses psycopg2 for PostgreSQL connection (standard library approach)
"""

import os
import json
import glob
from datetime import datetime
from pathlib import Path
import hashlib
import uuid
import psycopg2
from psycopg2.extras import Json
import sys
import argparse

class BettyJSONLImporter:
    def __init__(self):
        self.db_params = {
            'host': 'localhost',
            'port': 5434,
            'database': 'betty_memory',
            'user': 'betty',
            'password': 'betty_memory_2024'
        }
        self.stats = {
            'imported': 0,
            'skipped': 0, 
            'failed': 0,
            'total_lines': 0,
            'total_files': 0
        }
        self.batch_size = 100
        
    def connect(self):
        """Create database connection"""
        self.conn = psycopg2.connect(**self.db_params)
        self.conn.autocommit = True
        self.cursor = self.conn.cursor()
        
    def close(self):
        """Close database connection"""
        if hasattr(self, 'cursor'):
            self.cursor.close()
        if hasattr(self, 'conn'):
            self.conn.close()
    
    def process_jsonl_file(self, file_path):
        """Process a JSONL file line by line"""
        self.stats['total_files'] += 1
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        
        print(f"\n📄 Processing: {file_name} ({file_size / 1024 / 1024:.1f} MB)")
        
        # Group messages by conversation
        conversations = {}
        line_count = 0
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    if not line.strip():
                        continue
                        
                    line_count += 1
                    self.stats['total_lines'] += 1
                    
                    try:
                        data = json.loads(line)
                        
                        # Skip summary entries, focus on actual messages
                        if data.get('type') == 'summary':
                            continue
                            
                        # Group by sessionId or create a unique session
                        session_id = data.get('sessionId', f'unknown_{line_num}')
                        if session_id not in conversations:
                            conversations[session_id] = {
                                'messages': [],
                                'metadata': {
                                    'file': file_name,
                                    'project': data.get('cwd', 'unknown'),
                                    'version': data.get('version', 'unknown')
                                }
                            }
                        
                        # Add message to conversation
                        conversations[session_id]['messages'].append(data)
                        
                        # Show progress
                        if line_count % self.batch_size == 0:
                            print(f"  Processing line {line_count}...", end='\r')
                            
                    except json.JSONDecodeError as e:
                        print(f"  ⚠️ Invalid JSON at line {line_num}: {str(e)[:50]}")
                        continue
            
            # Import each conversation
            for session_id, conversation_data in conversations.items():
                if conversation_data['messages']:  # Only import if there are messages
                    self.import_conversation(session_id, conversation_data, file_path)
                
            print(f"  ✅ Processed {line_count} lines from {file_name}")
            
        except Exception as e:
            print(f"  ❌ Error processing {file_name}: {str(e)}")
            self.stats['failed'] += 1
    
    def import_conversation(self, session_id, conversation_data, source_file):
        """Import a conversation into the database"""
        try:
            # Create a meaningful title
            title = self._generate_title(conversation_data)
            
            # Prepare content
            content = json.dumps({
                'sessionId': session_id,
                'messages': conversation_data['messages'],
                'metadata': conversation_data['metadata']
            })
            
            # Generate hash for deduplication
            content_hash = hashlib.sha256(content.encode()).hexdigest()
            
            # Check if already exists
            self.cursor.execute(
                "SELECT id FROM knowledge_items WHERE content_hash = %s",
                (content_hash,)
            )
            existing = self.cursor.fetchone()
            
            if existing:
                self.stats['skipped'] += 1
                return
            
            # Insert into database
            item_id = str(uuid.uuid4())
            
            self.cursor.execute("""
                INSERT INTO knowledge_items (
                    id, title, content, knowledge_type, quality_score, complexity_level,
                    user_id, project_id, content_hash, metadata, created_at, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                )
            """, (
                item_id,
                title,
                content,
                'conversation',
                0.9,  # High quality for actual conversations
                'high',  # Complex conversation data
                '95fd614f-7da8-4650-bf23-ed53acba34c2',  # Default system user
                'c5d0c92a-d609-4a9d-bb59-473b7dc12d3a',  # Betty project
                content_hash,
                Json({
                    'source': 'claude_code_jsonl',
                    'source_file': str(source_file),
                    'session_id': session_id,
                    'message_count': len(conversation_data['messages']),
                    'import_date': datetime.now().isoformat()
                })
            ))
            
            self.stats['imported'] += 1
            
        except Exception as e:
            print(f"    ❌ Failed to import session {session_id[:8]}...: {str(e)[:100]}")
            self.stats['failed'] += 1
    
    def _generate_title(self, conversation_data):
        """Generate a meaningful title from conversation data"""
        messages = conversation_data['messages']
        metadata = conversation_data['metadata']
        
        # Try to find first user message
        for msg in messages:
            if msg.get('type') == 'user':
                # Try to extract text from different possible fields
                text = None
                if isinstance(msg.get('text'), str):
                    text = msg['text']
                elif isinstance(msg.get('content'), str):
                    text = msg['content']
                elif msg.get('message'):
                    text = str(msg['message'])
                
                if text:
                    # Clean and truncate
                    text = text.strip()[:100]
                    return f"Claude: {text}..." if len(text) == 100 else f"Claude: {text}"
        
        # Fallback to metadata
        project = metadata.get('project', 'Unknown')
        project_name = project.split('/')[-1] if '/' in project else project
        timestamp = messages[0].get('timestamp', '') if messages else ''
        
        if timestamp:
            return f"Claude Session - {project_name} - {timestamp[:10]}"
        return f"Claude Session - {project_name}"
    
    def import_directory(self, directory):
        """Import all JSONL files from a directory"""
        pattern = os.path.join(directory, "**/*.jsonl")
        files = glob.glob(pattern, recursive=True)
        
        print(f"\n📁 Found {len(files)} JSONL files in {directory}")
        
        if not files:
            print("No JSONL files to import.")
            return
        
        # Sort files by size (smaller first for faster initial feedback)
        files.sort(key=lambda f: os.path.getsize(f))
        
        for file_path in files:
            self.process_jsonl_file(file_path)
    
    def print_stats(self):
        """Print import statistics"""
        print("\n" + "="*50)
        print("📊 Import Statistics:")
        print(f"  📁 Files processed: {self.stats['total_files']}")
        print(f"  📝 Lines processed: {self.stats['total_lines']}")
        print(f"  ✅ Conversations imported: {self.stats['imported']}")
        print(f"  ⚠️  Skipped (duplicates): {self.stats['skipped']}")
        print(f"  ❌ Failed: {self.stats['failed']}")
        print("="*50)

def main():
    parser = argparse.ArgumentParser(description='Import Claude Code JSONL conversations into Betty Memory System')
    parser.add_argument('--directory', type=str, 
                        default='/home/jarvis/projects/Betty/claude-code-data/projects',
                        help='Directory containing JSONL files')
    parser.add_argument('--file', type=str, help='Import single JSONL file')
    parser.add_argument('--project', type=str, help='Import specific project directory')
    
    args = parser.parse_args()
    
    print("=== Betty JSONL Import Tool ===")
    print(f"Processing Claude Code conversation history")
    
    importer = BettyJSONLImporter()
    
    try:
        importer.connect()
        print("✅ Connected to Betty Memory database")
        
        if args.file:
            importer.process_jsonl_file(args.file)
        elif args.project:
            project_dir = os.path.join(
                '/home/jarvis/projects/Betty/claude-code-data/projects',
                args.project
            )
            importer.import_directory(project_dir)
        else:
            importer.import_directory(args.directory)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    finally:
        importer.print_stats()
        importer.close()

if __name__ == "__main__":
    main()