#!/usr/bin/env python3
# ABOUTME: Sample script to register Claude agent with BETTY Multi-Agent Platform
# ABOUTME: Demonstrates how to register an API-based agent with proper configuration

import asyncio
import httpx
import json
from typing import Dict, Any

BETTY_API_URL = "http://localhost:8001"

async def register_claude_agent():
    """Register Claude agent with BETTY"""
    
    # Agent registration data
    registration_data = {
        "name": "claude-sonnet-3.5",
        "display_name": "Claude 3.5 Sonnet",
        "agent_type": "api_based",
        "provider": "claude",
        "description": "Anthropic's Claude 3.5 Sonnet - Advanced reasoning and coding assistant",
        "version": "1.0.0",
        "capabilities": [
            "code_analysis",
            "code_generation", 
            "debugging",
            "test_writing",
            "documentation",
            "reasoning",
            "data_analysis"
        ],
        "config": {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 8192,
            "temperature": 0.7,
            "timeout": 60
        },
        "credentials": {
            "api_key": "your-claude-api-key-here"  # This will be stored securely in Vault
        },
        "metadata": {
            "cost_tier": "premium",
            "specialties": ["coding", "analysis", "reasoning"],
            "max_context": 200000
        }
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BETTY_API_URL}/api/agents/register",
                json=registration_data,
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Claude agent registered successfully!")
                print(f"Agent ID: {result['agent_id']}")
                print(f"Status: {result['status']}")
                
                # Start the agent
                agent_id = result['agent_id']
                start_response = await client.post(
                    f"{BETTY_API_URL}/api/agents/{agent_id}/start"
                )
                
                if start_response.status_code == 200:
                    print("✅ Claude agent started successfully!")
                else:
                    print(f"⚠️  Failed to start agent: {start_response.text}")
                
            else:
                print(f"❌ Registration failed: {response.status_code}")
                print(response.text)
                
        except Exception as e:
            print(f"❌ Error: {e}")

async def test_claude_agent():
    """Test the registered Claude agent"""
    
    # First, get list of agents to find Claude
    async with httpx.AsyncClient() as client:
        try:
            # List agents
            response = await client.get(f"{BETTY_API_URL}/api/agents/")
            agents = response.json()
            
            claude_agent = None
            for agent in agents:
                if agent['provider'] == 'claude':
                    claude_agent = agent
                    break
            
            if not claude_agent:
                print("❌ Claude agent not found")
                return
            
            agent_id = claude_agent['id']
            print(f"Found Claude agent: {agent_id}")
            
            # Test chat
            chat_request = {
                "messages": [
                    {
                        "role": "user",
                        "content": "Hello! Can you write a simple Python function to calculate fibonacci numbers?"
                    }
                ],
                "max_tokens": 1000,
                "temperature": 0.7
            }
            
            response = await client.post(
                f"{BETTY_API_URL}/api/agents/{agent_id}/chat",
                json=chat_request,
                timeout=60.0
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Chat test successful!")
                print(f"Response: {result['response']['message']['content'][:200]}...")
                print(f"Usage: {result['response']['usage']}")
                print(f"Cost: {result['response']['cost_cents']} cents")
            else:
                print(f"❌ Chat test failed: {response.status_code}")
                print(response.text)
                
        except Exception as e:
            print(f"❌ Test error: {e}")

async def main():
    """Main function"""
    print("🤖 BETTY Multi-Agent Platform - Claude Registration")
    print("=" * 50)
    
    print("\n1. Registering Claude agent...")
    await register_claude_agent()
    
    print("\n2. Testing Claude agent...")
    await asyncio.sleep(2)  # Give it a moment to initialize
    await test_claude_agent()

if __name__ == "__main__":
    asyncio.run(main())