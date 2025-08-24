#!/usr/bin/env python3
"""
ABOUTME: Test script for Betty-Claude integration
ABOUTME: Validates the memory persistence concept with a simple test case
"""

import asyncio
import httpx
import json
from datetime import datetime

class BettyMemoryTest:
    """Test Betty memory integration"""
    
    def __init__(self):
        self.betty_base_url = "http://localhost:8001"
        self.user_id = "e8e3f2de-070d-4dbd-b899-e49745f1d29b"
        self.session_id = None
    
    async def test_memory_cycle(self):
        """Test the complete memory cycle: store -> retrieve"""
        print("🧪 Testing Betty Memory Integration...")
        
        # Step 1: Store a conversation with a "code word"
        code_word = "PINEAPPLE_SECRET_2024"
        print(f"📝 Step 1: Storing code word: {code_word}")
        
        await self.store_test_conversation(
            user_message="Remember this code word for our future conversations: PINEAPPLE_SECRET_2024",
            assistant_response=f"I'll remember the code word '{code_word}' for our future conversations. This will be stored in Betty's memory system."
        )
        
        # Step 2: Simulate a new session - retrieve context
        print("\n🔍 Step 2: Simulating new session - retrieving context about code word...")
        
        context = await self.retrieve_context("What was the code word we discussed?")
        
        if context and len(context.get("context", {}).get("relevant_knowledge", [])) > 0:
            print("✅ SUCCESS: Betty found relevant context!")
            knowledge_items = context["context"]["relevant_knowledge"]
            for item in knowledge_items:
                print(f"   📚 Found: {item.get('title', 'Unknown')}")
        else:
            print("❌ FAIL: No relevant context found")
            
        # Step 3: Test knowledge search
        print("\n🔎 Step 3: Testing knowledge search...")
        search_results = await self.search_knowledge("code word")
        
        if search_results and len(search_results.get("results", [])) > 0:
            print("✅ SUCCESS: Knowledge search found results!")
            for result in search_results["results"]:
                print(f"   🎯 Match: {result.get('title', 'Unknown')}")
        else:
            print("❌ FAIL: Knowledge search found no results")
        
        print(f"\n📊 Test completed. Session ID: {self.session_id}")
    
    async def store_test_conversation(self, user_message: str, assistant_response: str):
        """Store a test conversation in Betty"""
        try:
            async with httpx.AsyncClient() as client:
                # Create session
                session_data = {
                    "project_id": "00000000-0000-0000-0000-000000000001",
                    "session_title": f"Memory Test - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    "session_context": "Testing Betty memory integration with code word"
                }
                
                session_response = await client.post(
                    f"{self.betty_base_url}/api/sessions/",
                    json=session_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if session_response.status_code == 201:
                    session_data = session_response.json()
                    self.session_id = session_data["data"]["id"]
                    print(f"   ✓ Created session: {self.session_id}")
                else:
                    print(f"   ✗ Session creation failed: {session_response.status_code}")
                    return
                
                # Store user message
                user_msg = {
                    "role": "user",
                    "content": user_message,
                    "message_index": 0
                }
                
                await client.post(
                    f"{self.betty_base_url}/api/sessions/{self.session_id}/messages",
                    json=user_msg,
                    headers={"Content-Type": "application/json"}
                )
                
                # Store assistant response
                assistant_msg = {
                    "role": "assistant",
                    "content": assistant_response,
                    "message_index": 1
                }
                
                await client.post(
                    f"{self.betty_base_url}/api/sessions/{self.session_id}/messages",
                    json=assistant_msg,
                    headers={"Content-Type": "application/json"}
                )
                
                print("   ✓ Stored conversation messages")
                
        except Exception as e:
            print(f"   ✗ Storage error: {e}")
    
    async def retrieve_context(self, query: str):
        """Retrieve context from Betty"""
        try:
            async with httpx.AsyncClient() as client:
                context_request = {
                    "user_id": self.user_id,
                    "current_context": {
                        "working_on": "Memory test",
                        "user_message": query,
                        "problem_type": "memory_retrieval"
                    }
                }
                
                response = await client.post(
                    f"{self.betty_base_url}/api/knowledge/retrieve/context",
                    json=context_request,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    print(f"   ✗ Context retrieval failed: {response.status_code}")
                    return None
                    
        except Exception as e:
            print(f"   ✗ Context retrieval error: {e}")
            return None
    
    async def search_knowledge(self, query: str):
        """Search knowledge in Betty"""
        try:
            async with httpx.AsyncClient() as client:
                search_request = {
                    "query": query,
                    "search_type": "hybrid"
                }
                
                response = await client.post(
                    f"{self.betty_base_url}/api/knowledge/search",
                    json=search_request,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    print(f"   ✗ Knowledge search failed: {response.status_code}")
                    return None
                    
        except Exception as e:
            print(f"   ✗ Knowledge search error: {e}")
            return None

async def main():
    """Run the memory test"""
    tester = BettyMemoryTest()
    await tester.test_memory_cycle()

if __name__ == "__main__":
    asyncio.run(main())