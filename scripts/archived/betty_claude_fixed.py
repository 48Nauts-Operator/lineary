#!/usr/bin/env python3

# ABOUTME: BETTY-Enhanced Claude Code Wrapper - Fixed version with correct API endpoints
# ABOUTME: Provides full functionality with working BETTY integration

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

class BettyClaudeCodeFixed:
    """Fixed BETTY-Enhanced Claude Code Wrapper"""
    
    def __init__(self):
        self.session_id = str(uuid.uuid4())
        self.conversation_history = []
        self.working_directory = os.getcwd()
        
        # BETTY configuration
        self.betty_base_url = "http://localhost:8001"
        self.user_id = "e8e3f2de-070d-4dbd-b899-e49745f1d29b"  # Andre's UUID
        
        # Check for API key
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            print("❌ Error: ANTHROPIC_API_KEY environment variable not set")
            print("   Please set your Anthropic API key:")
            print("   export ANTHROPIC_API_KEY='your-api-key-here'")
            sys.exit(1)
        
        print(f"🤖 BETTY Claude Code (Fixed) initialized")
        print(f"   Session ID: {self.session_id}")
        print(f"   Working Directory: {self.working_directory}")
        print(f"   BETTY URL: {self.betty_base_url}")
    
    def load_betty_context(self, user_input: str) -> List[Dict[str, Any]]:
        """Load relevant context from BETTY using correct API endpoints"""
        try:
            # Search BETTY for relevant knowledge
            search_query = urllib.parse.quote(user_input[:100])
            search_url = f"{self.betty_base_url}/api/knowledge/?search={search_query}"
            
            print(f"🔄 Searching BETTY: {user_input[:50]}...")
            
            req = urllib.request.Request(search_url)
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    items = data.get('data', [])
                    
                    if items:
                        print(f"📚 Found {len(items)} relevant items from BETTY")
                        return items[:5]  # Return top 5 most relevant
                    else:
                        print("📭 No relevant context found in BETTY")
                        return []
                else:
                    print(f"⚠️ BETTY search failed: HTTP {response.status}")
                    return []
                    
        except Exception as e:
            print(f"⚠️ BETTY unavailable ({str(e)}), using fallback context")
            return []
    
    def store_conversation_in_betty(self, user_input: str, claude_response: str):
        """Store conversation in BETTY using correct API endpoints"""
        try:
            # Create knowledge item from conversation
            knowledge_item = {
                "title": f"Conversation - {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}",
                "content": f"USER: {user_input}\n\nASSISTANT: {claude_response}",
                "knowledge_type": "conversation",
                "source_type": "conversation",
                "user_id": self.user_id,
                "confidence": "medium",
                "summary": f"Conversation about: {user_input[:100]}",
                "tags": ["conversation", "betty-enhanced", "claude-code"]
            }
            
            data = json.dumps(knowledge_item).encode('utf-8')
            req = urllib.request.Request(
                f"{self.betty_base_url}/api/knowledge/",
                data=data,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status in [200, 201]:
                    print("✅ Conversation stored in BETTY")
                else:
                    print(f"⚠️ Failed to store in BETTY: HTTP {response.status}")
                    
        except Exception as e:
            print(f"⚠️ Failed to store in BETTY: {str(e)}")
    
    def build_enhanced_prompt(self, user_input: str, context_items: List[Dict[str, Any]]) -> str:
        """Build enhanced prompt with BETTY context"""
        if not context_items:
            return user_input
        
        context_text = ""
        for i, item in enumerate(context_items, 1):
            title = item.get('title', 'No title')
            content = item.get('content', '')[:200] + "..." if len(item.get('content', '')) > 200 else item.get('content', '')
            summary = item.get('summary', 'No summary')
            
            context_text += f"{i}. **{title}**\n   {summary}\n   Content: {content}\n\n"
        
        enhanced_prompt = f"""## BETTY Memory Context (Previous Knowledge)
Here's relevant knowledge from your previous work:

{context_text}---

## Current User Request
{user_input}

Please respond taking into account the relevant context above. If the context helps answer the question, reference it appropriately."""

        return enhanced_prompt
    
    def call_claude_api(self, enhanced_prompt: str) -> str:
        """Call Claude API directly using urllib (no external dependencies)"""
        try:
            # Prepare the request
            data = {
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 4000,
                "messages": [
                    {"role": "user", "content": enhanced_prompt}
                ]
            }
            
            json_data = json.dumps(data).encode('utf-8')
            
            req = urllib.request.Request(
                "https://api.anthropic.com/v1/messages",
                data=json_data,
                headers={
                    'Content-Type': 'application/json',
                    'x-api-key': self.api_key,
                    'anthropic-version': '2023-06-01'
                }
            )
            
            with urllib.request.urlopen(req, timeout=30) as response:
                if response.status == 200:
                    result = json.loads(response.read().decode('utf-8'))
                    return result['content'][0]['text']
                else:
                    return f"Error: Claude API returned status {response.status}"
                    
        except Exception as e:
            return f"Error calling Claude API: {str(e)}"
    
    def execute_tool(self, tool_name: str, args: str) -> str:
        """Execute basic tools (Bash, Read, Write)"""
        try:
            if tool_name.lower() == "bash":
                result = subprocess.run(
                    args, shell=True, capture_output=True, text=True,
                    cwd=self.working_directory, timeout=30
                )
                output = f"Exit code: {result.returncode}\n"
                if result.stdout:
                    output += f"STDOUT:\n{result.stdout}\n"
                if result.stderr:
                    output += f"STDERR:\n{result.stderr}\n"
                return output
                
            elif tool_name.lower() == "read":
                try:
                    with open(args, 'r', encoding='utf-8') as f:
                        content = f.read()
                    return f"File content of {args}:\n{content}"
                except Exception as e:
                    return f"Error reading file {args}: {str(e)}"
                    
            elif tool_name.lower() == "write":
                # Format: filename:content
                if ":" in args:
                    filename, content = args.split(":", 1)
                    try:
                        with open(filename, 'w', encoding='utf-8') as f:
                            f.write(content)
                        return f"✅ Successfully wrote to {filename}"
                    except Exception as e:
                        return f"Error writing to {filename}: {str(e)}"
                else:
                    return "Error: Write command format should be filename:content"
                    
            else:
                return f"Tool '{tool_name}' not implemented yet"
                
        except Exception as e:
            return f"Error executing tool '{tool_name}': {str(e)}"
    
    def process_input(self, user_input: str) -> str:
        """Process user input and return Claude's response"""
        # Handle tool commands
        if user_input.startswith("/"):
            parts = user_input[1:].split(" ", 1)
            tool_name = parts[0]
            args = parts[1] if len(parts) > 1 else ""
            return self.execute_tool(tool_name, args)
        
        # Load BETTY context
        context_items = self.load_betty_context(user_input)
        
        # Build enhanced prompt
        enhanced_prompt = self.build_enhanced_prompt(user_input, context_items)
        
        print("📝 Enhanced prompt built with BETTY context")
        
        # Call Claude API
        print("🤖 Calling Claude API...")
        claude_response = self.call_claude_api(enhanced_prompt)
        
        # Store conversation in BETTY
        self.store_conversation_in_betty(user_input, claude_response)
        
        return claude_response
    
    def run_interactive_session(self):
        """Run interactive session"""
        print("\n" + "="*80)
        print("🧠 BETTY-Enhanced Claude Code (Fixed Version)")
        print("   Unlimited memory across conversations")
        print("   Type 'quit' to exit, '/bash command' for bash, '/read file' to read files")
        print("="*80)
        
        # Test BETTY connection
        try:
            req = urllib.request.Request(f"{self.betty_base_url}/health")
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    print("✅ BETTY Memory System connected")
                else:
                    print("⚠️ BETTY connection issues")
        except:
            print("❌ BETTY Memory System unavailable")
        
        print("\n💡 Try asking: 'What's the code word?' or 'What's the PI formula?'")
        print()
        
        while True:
            try:
                try:
                    user_input = input("🔵 You: ").strip()
                except EOFError:
                    print("\n👋 Goodbye! Your conversations are saved in BETTY.")
                    break
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye! Your conversations are saved in BETTY.")
                    break
                elif not user_input:
                    continue
                
                print()
                response = self.process_input(user_input)
                print("🟢 Claude (BETTY-Enhanced):")
                print("-" * 40)
                print(response)
                print()
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye! Your conversations are saved in BETTY.")
                break
            except Exception as e:
                print(f"❌ Error: {str(e)}")

def main():
    """Main entry point"""
    try:
        claude = BettyClaudeCodeFixed()
        claude.run_interactive_session()
    except Exception as e:
        print(f"❌ Failed to start: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()