#!/usr/bin/env python3
"""
ABOUTME: Betty-enhanced Claude interface using Anthropic SDK
ABOUTME: Provides continuous memory across conversations by integrating with Betty Memory System
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import uuid4
import httpx
import anthropic
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

console = Console()

class BettyClaudeInterface:
    """Claude interface with Betty memory integration"""
    
    def __init__(self):
        # Initialize Anthropic client
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.anthropic_api_key:
            console.print("[red]Error: ANTHROPIC_API_KEY environment variable not set[/red]")
            sys.exit(1)
            
        self.claude_client = anthropic.Anthropic(api_key=self.anthropic_api_key)
        
        # Betty configuration
        self.betty_base_url = "http://localhost:8001"
        self.user_id = "e8e3f2de-070d-4dbd-b899-e49745f1d29b"  # Andre's UUID
        self.project_id = None  # Will be set from Betty project
        
        # Session management
        self.current_session_id = None
        self.conversation_history = []
        
    async def initialize(self):
        """Initialize Betty connection and get project info"""
        try:
            async with httpx.AsyncClient() as client:
                # Test Betty connection
                response = await client.get(f"{self.betty_base_url}/health")
                if response.status_code != 200:
                    console.print("[red]Error: Betty Memory System not available[/red]")
                    return False
                
                # Get Betty project ID
                projects_response = await client.get(f"{self.betty_base_url}/api/knowledge/")
                if projects_response.status_code == 200:
                    # Betty is working
                    console.print("[green]✓ Connected to Betty Memory System[/green]")
                    return True
                else:
                    console.print("[yellow]⚠ Betty connection issues, continuing without full integration[/yellow]")
                    return True
                    
        except Exception as e:
            console.print(f"[red]Error connecting to Betty: {e}[/red]")
            return False
    
    async def load_context_from_betty(self, user_message: str) -> List[Dict[str, Any]]:
        """Load relevant context from Betty based on user message"""
        try:
            async with httpx.AsyncClient() as client:
                context_request = {
                    "user_id": self.user_id,
                    "current_context": {
                        "working_on": "General conversation with Claude",
                        "user_message": user_message,
                        "problem_type": "general_inquiry"
                    },
                    "context_depth": "basic",
                    "max_items": 10
                }
                
                response = await client.post(
                    f"{self.betty_base_url}/api/knowledge/retrieve/context",
                    json=context_request,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    context = data.get("context", {})
                    relevant_knowledge = context.get("relevant_knowledge", [])
                    
                    if relevant_knowledge:
                        console.print(f"[blue]📚 Loaded {len(relevant_knowledge)} relevant context items from Betty[/blue]")
                    
                    return relevant_knowledge
                else:
                    console.print(f"[yellow]⚠ Context loading failed: {response.status_code}[/yellow]")
                    return []
                    
        except Exception as e:
            console.print(f"[yellow]⚠ Context loading error: {e}[/yellow]")
            return []
    
    async def store_conversation_in_betty(self, user_message: str, claude_response: str):
        """Store the conversation in Betty for future reference"""
        try:
            if not self.current_session_id:
                # Create a new session in Betty
                session_data = {
                    "project_id": "00000000-0000-0000-0000-000000000001",  # Default project
                    "session_title": f"Claude Conversation - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    "session_context": "Interactive conversation with Betty-enhanced Claude interface"
                }
                
                async with httpx.AsyncClient() as client:
                    session_response = await client.post(
                        f"{self.betty_base_url}/api/sessions/",
                        json=session_data,
                        headers={"Content-Type": "application/json"}
                    )
                    
                    if session_response.status_code == 201:
                        session_data = session_response.json()
                        self.current_session_id = session_data["data"]["id"]
                        console.print(f"[green]📝 Created Betty session: {self.current_session_id}[/green]")
            
            if self.current_session_id:
                # Store user message
                async with httpx.AsyncClient() as client:
                    user_msg_data = {
                        "role": "user",
                        "content": user_message,
                        "message_index": len(self.conversation_history)
                    }
                    
                    await client.post(
                        f"{self.betty_base_url}/api/sessions/{self.current_session_id}/messages",
                        json=user_msg_data,
                        headers={"Content-Type": "application/json"}
                    )
                    
                    # Store Claude response
                    claude_msg_data = {
                        "role": "assistant", 
                        "content": claude_response,
                        "message_index": len(self.conversation_history) + 1
                    }
                    
                    await client.post(
                        f"{self.betty_base_url}/api/sessions/{self.current_session_id}/messages",
                        json=claude_msg_data,
                        headers={"Content-Type": "application/json"}
                    )
                    
                    console.print("[green]💾 Conversation stored in Betty[/green]")
                    
        except Exception as e:
            console.print(f"[yellow]⚠ Storage error: {e}[/yellow]")
    
    def build_enhanced_prompt(self, user_message: str, context_items: List[Dict[str, Any]]) -> str:
        """Build an enhanced prompt with Betty context"""
        if not context_items:
            return user_message
        
        context_text = "\n".join([
            f"- {item.get('title', 'No title')}: {item.get('summary', 'No summary')}"
            for item in context_items
        ])
        
        enhanced_prompt = f"""Based on our previous conversations and relevant context from my memory system:

RELEVANT CONTEXT:
{context_text}

CURRENT QUESTION:
{user_message}

Please respond taking into account the relevant context above. If the context helps answer the question, reference it appropriately."""

        return enhanced_prompt
    
    async def chat_with_claude(self, user_message: str) -> str:
        """Send message to Claude with Betty context enhancement"""
        try:
            # Load relevant context from Betty
            context_items = await self.load_context_from_betty(user_message)
            
            # Build enhanced prompt
            enhanced_message = self.build_enhanced_prompt(user_message, context_items)
            
            # Add to conversation history
            self.conversation_history.append({"role": "user", "content": user_message})
            
            # Prepare messages for Claude API
            messages = []
            for msg in self.conversation_history[:-1]:  # All but the current message
                messages.append(msg)
            
            # Add the enhanced current message
            messages.append({"role": "user", "content": enhanced_message})
            
            # Call Claude API
            response = self.claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                messages=messages
            )
            
            claude_response = response.content[0].text
            
            # Add Claude's response to history
            self.conversation_history.append({"role": "assistant", "content": claude_response})
            
            # Store in Betty for future context
            await self.store_conversation_in_betty(user_message, claude_response)
            
            return claude_response
            
        except Exception as e:
            return f"Error communicating with Claude: {e}"
    
    async def start_interactive_session(self):
        """Start interactive chat session"""
        console.print(Panel.fit(
            "[bold blue]Betty-Enhanced Claude Interface[/bold blue]\n"
            "Continuous memory across conversations\n"
            "Type 'quit' to exit, 'clear' to clear history",
            title="🧠 Betty + Claude"
        ))
        
        if not await self.initialize():
            console.print("[red]Failed to initialize. Exiting.[/red]")
            return
        
        while True:
            try:
                # Get user input
                user_input = console.input("\n[bold cyan]You:[/bold cyan] ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    break
                elif user_input.lower() == 'clear':
                    self.conversation_history = []
                    self.current_session_id = None
                    console.print("[yellow]Conversation history cleared[/yellow]")
                    continue
                elif not user_input:
                    continue
                
                # Show thinking indicator
                with console.status("[bold green]Claude is thinking..."):
                    response = await self.chat_with_claude(user_input)
                
                # Display Claude's response
                console.print("\n[bold green]Claude:[/bold green]")
                console.print(Markdown(response))
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
        
        console.print("\n[blue]Goodbye! Your conversations are saved in Betty.[/blue]")

async def main():
    """Main entry point"""
    interface = BettyClaudeInterface()
    await interface.start_interactive_session()

if __name__ == "__main__":
    asyncio.run(main())