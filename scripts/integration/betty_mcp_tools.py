#!/usr/bin/env python3
"""
BETTY Memory System MCP Tools for Claude Integration
Provides Claude with direct access to BETTY's memory, knowledge, and session management.
"""

import asyncio
import json
import httpx
from typing import Dict, List, Any, Optional
from datetime import datetime

# BETTY API Configuration
BETTY_API_BASE = "http://localhost:8001"
BETTY_USER_ID = "claude-agent"  # Default user ID for Claude
BETTY_PROJECT_ID = "betty-system"  # Default project for Claude conversations

class BETTYIntegration:
    """Integration layer between Claude and BETTY Memory System"""
    
    def __init__(self):
        self.api_base = BETTY_API_BASE
        self.user_id = BETTY_USER_ID
        self.project_id = BETTY_PROJECT_ID
        self.current_session_id = None
        
    async def load_context(self, working_on: str, user_message: str) -> Dict[str, Any]:
        """Load relevant context from BETTY memory for current conversation"""
        try:
            async with httpx.AsyncClient() as client:
                # Search for relevant knowledge
                search_response = await client.post(
                    f"{self.api_base}/api/knowledge/search",
                    json={
                        "query": user_message,
                        "search_type": "hybrid",
                        "limit": 5,
                        "include_content": True,
                        "project_id": self.project_id
                    }
                )
                
                if search_response.status_code == 200:
                    search_data = search_response.json()
                    relevant_knowledge = search_data.get("data", [])
                    
                    return {
                        "success": True,
                        "relevant_knowledge": relevant_knowledge,
                        "context_loaded": len(relevant_knowledge),
                        "message": f"Loaded {len(relevant_knowledge)} relevant knowledge items"
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Failed to load context: {search_response.status_code}",
                        "relevant_knowledge": [],
                        "context_loaded": 0
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": f"Context loading failed: {str(e)}",
                "relevant_knowledge": [],
                "context_loaded": 0
            }
    
    async def search_knowledge(self, query: str, project_id: Optional[str] = None) -> Dict[str, Any]:
        """Search BETTY's knowledge base for specific information"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base}/api/knowledge/search",
                    json={
                        "query": query,
                        "search_type": "hybrid",
                        "limit": 10,
                        "include_content": True,
                        "project_id": project_id or self.project_id
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "knowledge_items": data.get("data", []),
                        "total_found": len(data.get("data", [])),
                        "query": query
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Search failed: {response.status_code}",
                        "knowledge_items": [],
                        "total_found": 0
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": f"Knowledge search failed: {str(e)}",
                "knowledge_items": [],
                "total_found": 0
            }
    
    async def store_conversation(self, messages: List[Dict], session_title: str = None) -> Dict[str, Any]:
        """Store current conversation in BETTY memory system"""
        try:
            async with httpx.AsyncClient() as client:
                # Create or update session
                session_data = {
                    "title": session_title or f"Claude Conversation - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    "user_id": self.user_id,
                    "project_id": self.project_id,
                    "messages": messages,
                    "context": {
                        "agent_type": "claude",
                        "session_type": "conversation",
                        "auto_captured": True
                    }
                }
                
                # First create the session
                session_response = await client.post(
                    f"{self.api_base}/api/sessions",
                    json=session_data
                )
                
                if session_response.status_code == 200:
                    session_result = session_response.json()
                    session_id = session_result.get("data", {}).get("id")
                    self.current_session_id = session_id
                    
                    # Then ingest the conversation
                    ingest_response = await client.post(
                        f"{self.api_base}/api/knowledge/ingest/conversation",
                        json={
                            "session_id": session_id,
                            "messages": messages,
                            "project_id": self.project_id,
                            "auto_extract_patterns": True,
                            "extract_decisions": True
                        }
                    )
                    
                    return {
                        "success": True,
                        "session_id": session_id,
                        "conversation_stored": True,
                        "knowledge_extracted": ingest_response.status_code == 200,
                        "message": f"Conversation stored in session {session_id}"
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Failed to create session: {session_response.status_code}",
                        "session_id": None
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": f"Conversation storage failed: {str(e)}",
                "session_id": None
            }
    
    async def log_decision(self, title: str, context: str, decision: str, alternatives: List[str] = None) -> Dict[str, Any]:
        """Log a decision made during conversation to BETTY"""
        try:
            async with httpx.AsyncClient() as client:
                knowledge_data = {
                    "title": title,
                    "content": f"Context: {context}\n\nDecision: {decision}\n\nAlternatives Considered: {alternatives or 'None specified'}",
                    "knowledge_type": "decision",
                    "source_type": "claude_decision",
                    "confidence": "high",
                    "tags": ["decision", "claude", "conversation"],
                    "project_id": self.project_id,
                    "user_id": self.user_id,
                    "session_id": self.current_session_id,
                    "metadata": {
                        "decision_context": context,
                        "decision_made": decision,
                        "alternatives": alternatives or [],
                        "decided_by": "claude",
                        "decision_timestamp": datetime.now().isoformat()
                    }
                }
                
                response = await client.post(
                    f"{self.api_base}/api/knowledge",
                    json=knowledge_data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "success": True,
                        "decision_id": result.get("data", {}).get("id"),
                        "message": f"Decision '{title}' logged to BETTY memory"
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Failed to log decision: {response.status_code}",
                        "decision_id": None
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": f"Decision logging failed: {str(e)}",
                "decision_id": None
            }
    
    async def store_code_change(self, files_modified: List[str], tool_used: str, intent: str, changes_summary: str) -> Dict[str, Any]:
        """Store code changes and tool usage in BETTY"""
        try:
            async with httpx.AsyncClient() as client:
                knowledge_data = {
                    "title": f"Code Change: {intent}",
                    "content": f"Intent: {intent}\n\nFiles Modified: {', '.join(files_modified)}\n\nTool Used: {tool_used}\n\nChanges: {changes_summary}",
                    "knowledge_type": "code_pattern",
                    "source_type": "claude_code_change",
                    "confidence": "high",
                    "tags": ["code_change", "claude", tool_used.lower()],
                    "project_id": self.project_id,
                    "user_id": self.user_id,
                    "session_id": self.current_session_id,
                    "metadata": {
                        "files_modified": files_modified,
                        "tool_used": tool_used,
                        "change_intent": intent,
                        "change_timestamp": datetime.now().isoformat(),
                        "automated_capture": True
                    }
                }
                
                response = await client.post(
                    f"{self.api_base}/api/knowledge",
                    json=knowledge_data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "success": True,
                        "code_change_id": result.get("data", {}).get("id"),
                        "message": f"Code change '{intent}' logged to BETTY memory"
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Failed to store code change: {response.status_code}",
                        "code_change_id": None
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": f"Code change storage failed: {str(e)}",
                "code_change_id": None
            }
    
    async def get_session_stats(self) -> Dict[str, Any]:
        """Get current session and memory statistics"""
        try:
            async with httpx.AsyncClient() as client:
                # Get knowledge stats
                stats_response = await client.get(
                    f"{self.api_base}/api/knowledge/stats"
                )
                
                if stats_response.status_code == 200:
                    stats_data = stats_response.json()
                    return {
                        "success": True,
                        "current_session_id": self.current_session_id,
                        "memory_stats": stats_data.get("data", {}),
                        "integration_active": True
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Failed to get stats: {stats_response.status_code}",
                        "current_session_id": self.current_session_id,
                        "integration_active": False
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": f"Stats retrieval failed: {str(e)}",
                "current_session_id": self.current_session_id,
                "integration_active": False
            }

# Global instance for Claude to use
betty = BETTYIntegration()

# Convenience functions for Claude
async def betty_load_context(working_on: str, user_message: str) -> Dict[str, Any]:
    """Load relevant context from BETTY memory"""
    return await betty.load_context(working_on, user_message)

async def betty_search_knowledge(query: str, project_id: Optional[str] = None) -> Dict[str, Any]:
    """Search BETTY's knowledge base"""
    return await betty.search_knowledge(query, project_id)

async def betty_store_conversation(messages: List[Dict], session_title: str = None) -> Dict[str, Any]:
    """Store conversation in BETTY"""
    return await betty.store_conversation(messages, session_title)

async def betty_log_decision(title: str, context: str, decision: str, alternatives: List[str] = None) -> Dict[str, Any]:
    """Log a decision to BETTY"""
    return await betty.log_decision(title, context, decision, alternatives)

async def betty_store_code_change(files_modified: List[str], tool_used: str, intent: str, changes_summary: str) -> Dict[str, Any]:
    """Store code changes in BETTY"""
    return await betty.store_code_change(files_modified, tool_used, intent, changes_summary)

async def betty_get_stats() -> Dict[str, Any]:
    """Get BETTY session and memory stats"""
    return await betty.get_session_stats()

if __name__ == "__main__":
    # Test the integration
    async def test_integration():
        print("Testing BETTY Integration...")
        
        # Test loading context
        context_result = await betty_load_context("testing integration", "How do I integrate Claude with BETTY?")
        print(f"Context Loading: {context_result}")
        
        # Test knowledge search
        search_result = await betty_search_knowledge("dashboard analytics")
        print(f"Knowledge Search: {search_result}")
        
        # Test getting stats
        stats_result = await betty_get_stats()
        print(f"Memory Stats: {stats_result}")
    
    asyncio.run(test_integration())