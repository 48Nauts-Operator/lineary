#!/usr/bin/env python3
"""
Batch import Claude Code JSONL files with rate limiting
Processes files efficiently while respecting API limits
"""

import os
import json
import glob
import requests
from datetime import datetime
import hashlib
import sys
import argparse
import time
from collections import defaultdict

class BatchedImporter:
    def __init__(self):
        self.api_url = "http://localhost:3034/api/knowledge"
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        self.stats = {
            'imported': 0,
            'skipped': 0,
            'failed': 0,
            'total_files': 0,
            'total_conversations': 0
        }
        self.batch_delay = 2.0  # Seconds between batches
        self.max_retries = 3
        
    def process_directory(self, directory):
        """Process all JSONL files in directory"""
        pattern = os.path.join(directory, "**/*.jsonl")
        files = glob.glob(pattern, recursive=True)
        
        print(f"📁 Found {len(files)} JSONL files")
        
        if not files:
            print("No files to import")
            return
        
        # Group by project for better organization
        projects = defaultdict(list)
        for file_path in files:
            project = os.path.basename(os.path.dirname(file_path))
            projects[project].append(file_path)
        
        print(f"📊 Projects to import: {len(projects)}")
        
        for project_name, project_files in projects.items():
            print(f"\n🚀 Processing project: {project_name}")
            print(f"   Files: {len(project_files)}")
            
            for file_path in sorted(project_files, key=lambda f: os.path.getsize(f)):
                self.process_file(file_path)
                # Delay between files
                time.sleep(self.batch_delay)
    
    def process_file(self, file_path):
        """Process a single JSONL file"""
        self.stats['total_files'] += 1
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        
        print(f"\n📄 {file_name} ({file_size / 1024 / 1024:.1f} MB)")
        
        conversations = self.parse_jsonl(file_path)
        
        if not conversations:
            print("  No conversations found")
            return
        
        print(f"  Found {len(conversations)} conversations")
        self.stats['total_conversations'] += len(conversations)
        
        # Process each conversation with rate limiting
        for idx, (session_id, conv_data) in enumerate(conversations.items(), 1):
            success = self.import_conversation(session_id, conv_data, file_path)
            
            if success:
                self.stats['imported'] += 1
            else:
                self.stats['failed'] += 1
            
            # Progress indicator
            if idx % 10 == 0:
                print(f"  Progress: {idx}/{len(conversations)}")
            
            # Rate limiting
            time.sleep(1.0)
    
    def parse_jsonl(self, file_path):
        """Parse JSONL file into conversations"""
        conversations = {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    if not line.strip():
                        continue
                    
                    try:
                        data = json.loads(line)
                        
                        # Skip summaries
                        if data.get('type') == 'summary':
                            continue
                        
                        session_id = data.get('sessionId', f'session_{line_num}')
                        
                        if session_id not in conversations:
                            conversations[session_id] = {
                                'messages': [],
                                'metadata': {
                                    'file': os.path.basename(file_path),
                                    'project': data.get('cwd', 'unknown')
                                }
                            }
                        
                        conversations[session_id]['messages'].append(data)
                        
                    except json.JSONDecodeError:
                        continue
                        
        except Exception as e:
            print(f"  ❌ Error reading file: {e}")
            
        return conversations
    
    def import_conversation(self, session_id, conv_data, source_file):
        """Import a single conversation with retry logic"""
        
        # Generate title
        title = self.generate_title(conv_data)
        
        # Prepare payload
        payload = {
            'title': title,
            'content': json.dumps({
                'sessionId': session_id,
                'messages': conv_data['messages'][:50],  # Limit for API
                'total_messages': len(conv_data['messages']),
                'metadata': conv_data['metadata']
            }),
            'knowledge_type': 'conversation',
            'source_type': 'import',  # Must be from the enum: chat, file, api, import, user_input
            'tags': ['claude-code', 'imported', 'jsonl'],
            'confidence': 'high'  # high confidence for actual conversations
        }
        
        # Try to import with retries
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    self.api_url,
                    json=payload,
                    headers=self.headers,
                    timeout=10
                )
                
                if response.status_code in [200, 201]:
                    return True
                elif response.status_code == 429:
                    # Rate limited
                    wait_time = min(30, 2 ** attempt)  # Exponential backoff
                    print(f"    ⏸️ Rate limited, waiting {wait_time}s...")
                    time.sleep(wait_time)
                elif response.status_code == 409:
                    # Already exists
                    self.stats['skipped'] += 1
                    return True
                else:
                    print(f"    ⚠️ Error {response.status_code}")
                    return False
                    
            except requests.exceptions.Timeout:
                print(f"    ⚠️ Timeout on attempt {attempt + 1}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
            except Exception as e:
                print(f"    ❌ Error: {str(e)[:50]}")
                return False
        
        return False
    
    def generate_title(self, conv_data):
        """Generate conversation title"""
        for msg in conv_data['messages']:
            if msg.get('type') == 'user':
                text = msg.get('text') or msg.get('content') or ''
                if text:
                    return f"Claude: {text[:60]}..."
        
        project = conv_data['metadata'].get('project', 'Unknown').split('/')[-1]
        return f"Claude Session - {project}"
    
    def print_stats(self):
        """Print import statistics"""
        print("\n" + "="*50)
        print("📊 Import Complete!")
        print(f"  📁 Files processed: {self.stats['total_files']}")
        print(f"  💬 Conversations found: {self.stats['total_conversations']}")
        print(f"  ✅ Successfully imported: {self.stats['imported']}")
        print(f"  ⚠️  Skipped (duplicates): {self.stats['skipped']}")
        print(f"  ❌ Failed: {self.stats['failed']}")
        
        success_rate = (self.stats['imported'] / max(1, self.stats['total_conversations'])) * 100
        print(f"  📈 Success rate: {success_rate:.1f}%")
        print("="*50)

def main():
    parser = argparse.ArgumentParser(description='Batch import JSONL files')
    parser.add_argument('--directory', type=str,
                        default='/home/jarvis/projects/Betty/claude-code-data/projects',
                        help='Directory with JSONL files')
    parser.add_argument('--project', type=str, help='Specific project to import')
    
    args = parser.parse_args()
    
    print("=== Betty Batch Import Tool ===")
    print("Rate-limited import with retry logic\n")
    
    # Suppress SSL warnings
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    importer = BatchedImporter()
    
    try:
        if args.project:
            project_dir = os.path.join(args.directory, args.project)
            importer.process_directory(project_dir)
        else:
            importer.process_directory(args.directory)
    finally:
        importer.print_stats()

if __name__ == "__main__":
    main()