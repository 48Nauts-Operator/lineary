#!/usr/bin/env python3
"""
Import Claude Code JSONL files via Betty Memory API
Uses HTTP API to avoid database driver dependencies
"""

import os
import json
import glob
import requests
from datetime import datetime
import hashlib
import uuid
import sys
import argparse
import time

class BettyAPIImporter:
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
            'total_lines': 0,
            'total_files': 0,
            'api_errors': 0
        }
        self.batch_size = 50  # Smaller batch for API calls
        self.processed_hashes = set()  # Track what we've already processed
        
    def process_jsonl_file(self, file_path):
        """Process a JSONL file and send to API"""
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
                        
                        # Skip summary entries
                        if data.get('type') == 'summary':
                            continue
                            
                        # Create a session key
                        session_id = data.get('sessionId', f'session_{line_num}')
                        
                        if session_id not in conversations:
                            conversations[session_id] = {
                                'messages': [],
                                'metadata': {
                                    'file': file_name,
                                    'project': data.get('cwd', 'unknown'),
                                    'version': data.get('version', 'unknown'),
                                    'timestamp': data.get('timestamp', datetime.now().isoformat())
                                }
                            }
                        
                        # Add message data
                        conversations[session_id]['messages'].append(data)
                        
                        # Show progress
                        if line_count % 100 == 0:
                            print(f"  Read {line_count} lines...", end='\r')
                            
                    except json.JSONDecodeError as e:
                        continue
            
            print(f"  Found {len(conversations)} conversations in {line_count} lines")
            
            # Send each conversation to API
            for session_id, conversation_data in conversations.items():
                if conversation_data['messages']:
                    self.send_to_api(session_id, conversation_data, file_path)
                    # Rate limit to avoid overwhelming the API
                    time.sleep(1.0)  # Increased delay to respect rate limits
                
        except Exception as e:
            print(f"  ❌ Error processing {file_name}: {str(e)}")
            self.stats['failed'] += 1
    
    def send_to_api(self, session_id, conversation_data, source_file):
        """Send conversation to Betty Memory API"""
        try:
            # Generate title
            title = self._generate_title(conversation_data)
            
            # Create content
            content = {
                'sessionId': session_id,
                'messages': conversation_data['messages'][:100],  # Limit messages to avoid huge payloads
                'metadata': conversation_data['metadata'],
                'message_count': len(conversation_data['messages'])
            }
            
            # Create hash for deduplication
            content_str = json.dumps(content, sort_keys=True)
            content_hash = hashlib.sha256(content_str.encode()).hexdigest()
            
            # Skip if already processed
            if content_hash in self.processed_hashes:
                self.stats['skipped'] += 1
                return
                
            self.processed_hashes.add(content_hash)
            
            # Prepare API payload
            payload = {
                'title': title,
                'content': content_str,
                'knowledge_type': 'conversation',
                'source_type': 'claude_code_jsonl',
                'tags': ['claude-code', 'imported', 'jsonl'],
                'metadata': {
                    'source_file': os.path.basename(source_file),
                    'session_id': session_id[:50],  # Truncate long IDs
                    'import_date': datetime.now().isoformat()
                }
            }
            
            # Send to API with timeout
            response = requests.post(
                self.api_url,
                json=payload,
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                self.stats['imported'] += 1
                print(f"  ✅ Imported: {title[:50]}...")
            elif response.status_code == 409:
                self.stats['skipped'] += 1
            elif response.status_code == 429:
                # Rate limit hit - wait and retry
                retry_after = response.json().get('retry_after', 5)
                print(f"  ⏸️ Rate limited. Waiting {retry_after} seconds...")
                time.sleep(retry_after)
                # Retry once
                retry_response = requests.post(
                    self.api_url,
                    json=payload,
                    headers=self.headers,
                    timeout=10
                )
                if retry_response.status_code in [200, 201]:
                    self.stats['imported'] += 1
                    print(f"  ✅ Imported on retry: {title[:50]}...")
                else:
                    self.stats['api_errors'] += 1
            else:
                print(f"  ⚠️ API Error {response.status_code}: {response.text[:100]}")
                self.stats['api_errors'] += 1
                
        except requests.exceptions.Timeout:
            print(f"  ⚠️ API timeout for session {session_id[:8]}")
            self.stats['api_errors'] += 1
        except Exception as e:
            print(f"  ❌ Failed: {str(e)[:100]}")
            self.stats['failed'] += 1
    
    def _generate_title(self, conversation_data):
        """Generate meaningful title"""
        messages = conversation_data['messages']
        metadata = conversation_data['metadata']
        
        # Find first user text
        for msg in messages:
            if msg.get('type') == 'user':
                # Extract text from various possible fields
                text = (msg.get('text') or msg.get('content') or 
                       msg.get('message') or '')
                if text:
                    text = str(text).strip()[:80]
                    return f"Claude: {text}"
        
        # Fallback
        project = metadata.get('project', 'Unknown').split('/')[-1]
        return f"Claude Session - {project}"
    
    def import_directory(self, directory):
        """Import all JSONL files from directory"""
        pattern = os.path.join(directory, "**/*.jsonl")
        files = glob.glob(pattern, recursive=True)
        
        print(f"\n📁 Found {len(files)} JSONL files")
        
        if not files:
            print("No files to import")
            return
        
        # Sort by size (smaller first)
        files.sort(key=lambda f: os.path.getsize(f))
        
        for file_path in files:
            self.process_jsonl_file(file_path)
    
    def print_stats(self):
        """Print statistics"""
        print("\n" + "="*50)
        print("📊 Import Statistics:")
        print(f"  📁 Files: {self.stats['total_files']}")
        print(f"  📝 Lines: {self.stats['total_lines']}")
        print(f"  ✅ Imported: {self.stats['imported']}")
        print(f"  ⚠️  Skipped: {self.stats['skipped']}")
        print(f"  🔌 API Errors: {self.stats['api_errors']}")
        print(f"  ❌ Failed: {self.stats['failed']}")
        print("="*50)

def main():
    parser = argparse.ArgumentParser(description='Import JSONL via API')
    parser.add_argument('--directory', type=str,
                        default='/home/jarvis/projects/Betty/claude-code-data/projects',
                        help='Directory with JSONL files')
    parser.add_argument('--file', type=str, help='Single file to import')
    parser.add_argument('--project', type=str, help='Specific project directory')
    
    args = parser.parse_args()
    
    print("=== Betty API Import Tool ===")
    
    # Suppress SSL warnings for local dev
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    importer = BettyAPIImporter()
    
    try:
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
    finally:
        importer.print_stats()

if __name__ == "__main__":
    main()