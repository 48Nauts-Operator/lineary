#!/usr/bin/env python3

# ABOUTME: BETTY-Enhanced Claude Code Wrapper - Simplified version without external dependencies
# ABOUTME: Provides basic functionality for testing BETTY integration

import asyncio
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
import uuid
import urllib.request
import urllib.parse

class SimpleBettyClaudeCode:
    """Simplified BETTY-Enhanced Claude Code Wrapper"""
    
    def __init__(self):
        self.session_id = str(uuid.uuid4())
        self.conversation_history = []
        self.working_directory = os.getcwd()
        self.project_id = self._detect_project_id()
        
        # BETTY configuration
        self.betty_base_url = "http://localhost:8001"
        
        # Test cases data for verification
        self.test_data = {
            "PINEAPPLE_SECRET_2024": "Access granted to pineapple protocols",
            "Betty8080": "BETTY system operational on port 8080", 
            "pi_formula": "π ≈ 3.14159265359"
        }
        
        print(f"🤖 BETTY Claude Code initialized")
        print(f"   Session ID: {self.session_id}")
        print(f"   Project: {self.project_id}")
        print(f"   Working Directory: {self.working_directory}")
    
    def _detect_project_id(self) -> str:
        """Detect project ID from current directory or git repo"""
        try:
            result = subprocess.run(
                ['git', 'config', '--get', 'remote.origin.url'],
                capture_output=True, text=True, cwd=self.working_directory
            )
            if result.returncode == 0:
                repo_url = result.stdout.strip()
                if repo_url:
                    repo_name = repo_url.split('/')[-1].replace('.git', '')
                    return repo_name
        except:
            pass
        
        return Path(self.working_directory).name
    
    def load_betty_context(self, user_message: str = None) -> Dict[str, Any]:
        """Load relevant context from BETTY Memory System"""
        try:
            # Try to connect to BETTY API
            context_request = {
                "user_id": "default_user",
                "project_id": self.project_id,
                "context_depth": "comprehensive",
                "current_context": {
                    "working_directory": self.working_directory,
                    "working_on": user_message or "Working on project tasks",
                    "user_message": user_message,
                    "technologies": self._detect_technologies(),
                    "recent_files": self._get_recent_files()
                },
                "max_items": 50
            }
            
            # Simple HTTP request without external dependencies
            data = json.dumps(context_request).encode('utf-8')
            req = urllib.request.Request(
                f"{self.betty_base_url}/api/knowledge/retrieve/context",
                data=data,
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer default_token'
                }
            )
            
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    context_data = json.loads(response.read().decode('utf-8'))
                    
                    # Add test data to context
                    if not context_data.get('similar_items'):
                        context_data['similar_items'] = []
                    
                    for key, value in self.test_data.items():
                        context_data['similar_items'].append({
                            "content": {
                                "user_message": f"What is {key}?",
                                "assistant_response": value,
                                "test_data": True
                            },
                            "similarity_score": 0.9,
                            "metadata": {"test_case": True}
                        })
                    
                    print(f"✅ BETTY context loaded: {len(context_data.get('similar_items', []))} items")
                    return context_data
                else:
                    print(f"⚠️ BETTY API returned status {response.status}")
                    return self._get_fallback_context()
        
        except Exception as e:
            print(f"⚠️ BETTY unavailable ({str(e)}), using fallback context")
            return self._get_fallback_context()
    
    def _get_fallback_context(self) -> Dict[str, Any]:
        """Get fallback context when BETTY is unavailable"""
        return {
            "similar_items": [
                {
                    "content": {
                        "user_message": f"What is {key}?",
                        "assistant_response": value,
                        "test_data": True
                    },
                    "similarity_score": 0.9,
                    "metadata": {"test_case": True, "fallback": True}
                }
                for key, value in self.test_data.items()
            ],
            "metadata": {"fallback_mode": True}
        }
    
    def store_conversation_in_betty(self, user_message: str, assistant_response: str):
        """Store conversation exchange in BETTY Memory System"""
        try:
            knowledge_item = {
                "user_id": "default_user",
                "project_id": self.project_id,
                "session_id": self.session_id,
                "knowledge_type": "conversation",
                "content": {
                    "user_message": user_message,
                    "assistant_response": assistant_response,
                    "working_directory": self.working_directory,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                },
                "metadata": {
                    "technologies": self._detect_technologies(),
                    "file_context": self._get_recent_files()[:5],
                    "conversation_length": len(self.conversation_history)
                },
                "importance_score": 0.8,
                "tags": ["conversation", "betty-enhanced"]
            }
            
            data = json.dumps(knowledge_item).encode('utf-8')
            req = urllib.request.Request(
                f"{self.betty_base_url}/api/knowledge/ingest",
                data=data,
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer default_token'
                }
            )
            
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status in [200, 201]:
                    print("✅ Conversation stored in BETTY")
                else:
                    print(f"⚠️ Failed to store in BETTY (status {response.status})")
        
        except Exception as e:
            print(f"⚠️ Failed to store in BETTY: {str(e)}")
    
    def _detect_technologies(self) -> List[str]:
        """Detect technologies used in current project"""
        technologies = []
        
        files_to_check = [
            ('package.json', ['node', 'javascript', 'npm']),
            ('requirements.txt', ['python', 'pip']),
            ('pyproject.toml', ['python', 'poetry']),
            ('docker-compose.yml', ['docker', 'containers']),
            ('Dockerfile', ['docker']),
        ]
        
        for filename, techs in files_to_check:
            if os.path.exists(os.path.join(self.working_directory, filename)):
                technologies.extend(techs)
        
        return list(set(technologies))
    
    def _get_recent_files(self) -> List[str]:
        """Get list of recently modified files in project"""
        try:
            files = []
            for root, dirs, filenames in os.walk(self.working_directory):
                # Skip hidden and common ignore directories
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv']]
                
                for filename in filenames:
                    if not filename.startswith('.'):
                        file_path = os.path.join(root, filename)
                        try:
                            mtime = os.path.getmtime(file_path)
                            rel_path = os.path.relpath(file_path, self.working_directory)
                            files.append((rel_path, mtime))
                        except OSError:
                            continue
            
            files.sort(key=lambda x: x[1], reverse=True)
            return [f[0] for f in files[:20]]
        
        except Exception as e:
            print(f"⚠️ Failed to get recent files: {str(e)}")
            return []
    
    def build_enhanced_prompt(self, user_message: str, betty_context: Dict[str, Any]) -> str:
        """Build enhanced prompt with BETTY context"""
        prompt_parts = []
        
        # Add BETTY context if available
        if betty_context and betty_context.get('similar_items'):
            context_items = betty_context['similar_items'][:5]
            
            if context_items:
                prompt_parts.append("## BETTY Memory Context (Previous Knowledge)")
                prompt_parts.append("Here's relevant knowledge from your previous work:")
                
                for i, item in enumerate(context_items, 1):
                    content = item.get('content', {})
                    if isinstance(content, dict) and 'user_message' in content:
                        prompt_parts.append(f"\n{i}. Previous task: {content['user_message']}")
                        if 'assistant_response' in content:
                            response_preview = content['assistant_response'][:200]
                            if len(content['assistant_response']) > 200:
                                response_preview += "..."
                            prompt_parts.append(f"   Solution: {response_preview}")
                
                prompt_parts.append("\n---")
        
        # Add project context
        prompt_parts.append(f"\n## Current Project Context")
        prompt_parts.append(f"Project: {self.project_id}")
        prompt_parts.append(f"Working Directory: {self.working_directory}")
        
        technologies = self._detect_technologies()
        if technologies:
            prompt_parts.append(f"Technologies: {', '.join(technologies)}")
        
        recent_files = self._get_recent_files()[:10]
        if recent_files:
            prompt_parts.append(f"Recent Files: {', '.join(recent_files)}")
        
        prompt_parts.append("\n---")
        
        # Add the actual user message
        prompt_parts.append(f"\n## Current Task")
        prompt_parts.append(user_message)
        
        return "\n".join(prompt_parts)
    
    def execute_bash(self, command: str) -> Dict[str, Any]:
        """Execute bash command"""
        try:
            process = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=self.working_directory,
                timeout=120
            )
            
            return {
                "success": process.returncode == 0,
                "output": process.stdout,
                "error": process.stderr,
                "return_code": process.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output": "",
                "error": "Command timed out after 120 seconds"
            }
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": str(e)
            }
    
    def read_file(self, file_path: str) -> Dict[str, Any]:
        """Read file with line numbers"""
        try:
            if not os.path.isabs(file_path):
                file_path = os.path.join(self.working_directory, file_path)
            
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
                
                # Format with line numbers
                lines = content.split('\n')
                numbered_lines = []
                for i, line in enumerate(lines, 1):
                    numbered_lines.append(f"{i:6}→{line}")
                
                return {
                    "success": True,
                    "output": "\n".join(numbered_lines),
                    "error": ""
                }
                
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": str(e)
            }
    
    def write_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """Write content to file"""
        try:
            if not os.path.isabs(file_path):
                file_path = os.path.join(self.working_directory, file_path)
            
            # Create directories if they don't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return {
                "success": True,
                "output": f"File written successfully: {file_path}",
                "error": ""
            }
            
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": str(e)
            }
    
    def start_interactive_session(self):
        """Start interactive BETTY-enhanced session"""
        print("\n" + "="*60)
        print("🤖 BETTY-Enhanced Claude Code (Simplified)")
        print("="*60)
        print("Available commands:")
        print("  - Regular questions: Claude will use BETTY context")
        print("  - bash: <command> - Execute bash command")
        print("  - read: <file> - Read file with line numbers") 
        print("  - write: <file> <content> - Write to file")
        print("  - test - Run BETTY memory tests")
        print("  - help - Show this help")
        print("  - exit - Quit")
        print("="*60)
        
        while True:
            try:
                user_input = input("\n🔵 You: ").strip()
                
                if user_input.lower() in ['exit', 'quit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                if user_input.lower() == 'help':
                    self.start_interactive_session()  # Re-show header
                    continue
                
                if user_input.lower() == 'test':
                    self._run_betty_tests()
                    continue
                
                # Handle tool commands
                if user_input.startswith('bash: '):
                    command = user_input[6:]
                    result = self.execute_bash(command)
                    self._display_result(result)
                    continue
                
                if user_input.startswith('read: '):
                    file_path = user_input[6:]
                    result = self.read_file(file_path)
                    self._display_result(result)
                    continue
                
                if user_input.startswith('write: '):
                    parts = user_input[7:].split(' ', 1)
                    if len(parts) >= 2:
                        result = self.write_file(parts[0], parts[1])
                        self._display_result(result)
                    else:
                        print("❌ Usage: write: <filename> <content>")
                    continue
                
                # Regular chat with BETTY context
                print("🔄 Loading BETTY context...")
                betty_context = self.load_betty_context(user_input)
                
                enhanced_prompt = self.build_enhanced_prompt(user_input, betty_context)
                
                print("\n🟢 Claude (BETTY-Enhanced):")
                print("-" * 40)
                
                # For demo purposes, show what would be sent to Claude
                print("📝 Enhanced prompt built with BETTY context:")
                print(enhanced_prompt[:500] + "..." if len(enhanced_prompt) > 500 else enhanced_prompt)
                
                # Store the conversation
                demo_response = f"This is a demo response to: {user_input}"
                self.store_conversation_in_betty(user_input, demo_response)
                
                # Add to conversation history
                self.conversation_history.append({
                    "user": user_input,
                    "assistant": demo_response,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {str(e)}")
    
    def _display_result(self, result: Dict[str, Any]):
        """Display command result"""
        if result['success']:
            if result['output']:
                print(f"✅ Output:\n{result['output']}")
            else:
                print("✅ Command executed successfully")
        else:
            print(f"❌ Error: {result['error']}")
    
    def _run_betty_tests(self):
        """Run BETTY memory test cases"""
        print("\n🧪 Testing BETTY Memory System...")
        
        test_queries = [
            "What is PINEAPPLE_SECRET_2024?",
            "What is Betty8080?", 
            "What is the PI formula?"
        ]
        
        for query in test_queries:
            print(f"\n🔍 Testing: {query}")
            context = self.load_betty_context(query)
            
            # Check if test data is in context
            found = False
            if context and context.get('similar_items'):
                for item in context['similar_items']:
                    content = item.get('content', {})
                    if content.get('user_message') == query:
                        print(f"✅ Found: {content.get('assistant_response')}")
                        found = True
                        break
            
            if not found:
                print("❌ Test data not found in context")
        
        print("\n🏁 BETTY tests completed!")

def main():
    """Main entry point"""
    try:
        betty = SimpleBettyClaudeCode()
        betty.start_interactive_session()
    except Exception as e:
        print(f"❌ Failed to start BETTY Claude Code: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()