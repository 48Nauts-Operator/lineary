#!/usr/bin/env python3
# ABOUTME: Sample script to register OpenAI GPT agents with BETTY Multi-Agent Platform
# ABOUTME: Demonstrates registration of multiple OpenAI models with different configurations

import asyncio
import httpx
import json
from typing import Dict, Any, List

BETTY_API_URL = "http://localhost:8001"

async def register_openai_agents():
    """Register multiple OpenAI agents with different models"""
    
    # Define different OpenAI agents to register
    agents_config = [
        {
            "name": "gpt-4o-mini",
            "display_name": "GPT-4o Mini",
            "model": "gpt-4o-mini",
            "description": "Fast and efficient GPT-4o model for general tasks",
            "cost_tier": "economy",
            "max_tokens": 16384
        },
        {
            "name": "gpt-4o",
            "display_name": "GPT-4o",
            "model": "gpt-4o",
            "description": "Advanced GPT-4o model with multimodal capabilities",
            "cost_tier": "premium",
            "max_tokens": 8192
        },
        {
            "name": "gpt-4-turbo",
            "display_name": "GPT-4 Turbo",
            "model": "gpt-4-turbo",
            "description": "Latest GPT-4 Turbo with improved performance",
            "cost_tier": "premium",
            "max_tokens": 4096
        }
    ]
    
    registered_agents = []
    
    async with httpx.AsyncClient() as client:
        for agent_config in agents_config:
            registration_data = {
                "name": agent_config["name"],
                "display_name": agent_config["display_name"],
                "agent_type": "api_based",
                "provider": "openai",
                "description": agent_config["description"],
                "version": "1.0.0",
                "capabilities": [
                    "code_generation",
                    "code_analysis", 
                    "debugging",
                    "test_writing",
                    "documentation",
                    "reasoning",
                    "data_analysis",
                    "function_calling" if "gpt-4" in agent_config["model"] else None
                ],
                "config": {
                    "model": agent_config["model"],
                    "max_tokens": agent_config["max_tokens"],
                    "temperature": 0.7,
                    "timeout": 60,
                    "supports_functions": "gpt-4" in agent_config["model"]
                },
                "credentials": {
                    "api_key": "your-openai-api-key-here"  # This will be stored securely in Vault
                },
                "metadata": {
                    "cost_tier": agent_config["cost_tier"],
                    "specialties": ["coding", "analysis", "writing"],
                    "max_context": 128000 if "gpt-4" in agent_config["model"] else 16385
                }
            }
            
            # Remove None values from capabilities
            registration_data["capabilities"] = [cap for cap in registration_data["capabilities"] if cap is not None]
            
            try:
                response = await client.post(
                    f"{BETTY_API_URL}/api/agents/register",
                    json=registration_data,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ {agent_config['display_name']} registered successfully!")
                    print(f"   Agent ID: {result['agent_id']}")
                    
                    registered_agents.append({
                        "id": result['agent_id'],
                        "name": agent_config['name'],
                        "model": agent_config['model']
                    })
                    
                    # Start the agent
                    start_response = await client.post(
                        f"{BETTY_API_URL}/api/agents/{result['agent_id']}/start"
                    )
                    
                    if start_response.status_code == 200:
                        print(f"   ✅ Agent started successfully!")
                    else:
                        print(f"   ⚠️  Failed to start agent: {start_response.text}")
                        
                else:
                    print(f"❌ Failed to register {agent_config['display_name']}: {response.status_code}")
                    print(f"   {response.text}")
                    
            except Exception as e:
                print(f"❌ Error registering {agent_config['display_name']}: {e}")
    
    return registered_agents

async def test_capability_routing():
    """Test the capability-based routing system"""
    
    # Test requests for different capabilities
    test_cases = [
        {
            "capability": "code_generation",
            "request": {
                "messages": [
                    {
                        "role": "user",
                        "content": "Write a Python function to sort a list of dictionaries by a specific key"
                    }
                ],
                "max_tokens": 500
            }
        },
        {
            "capability": "reasoning",
            "request": {
                "messages": [
                    {
                        "role": "user", 
                        "content": "Explain the time complexity of quicksort and when it's optimal to use"
                    }
                ],
                "max_tokens": 800
            }
        }
    ]
    
    async with httpx.AsyncClient() as client:
        for test_case in test_cases:
            try:
                print(f"\n🧪 Testing capability: {test_case['capability']}")
                
                response = await client.post(
                    f"{BETTY_API_URL}/api/agents/chat/capability/{test_case['capability']}",
                    json=test_case['request'],
                    timeout=60.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ Capability routing successful!")
                    print(f"   Response preview: {result['response']['message']['content'][:150]}...")
                    print(f"   Token usage: {result['response']['usage']}")
                    print(f"   Cost: {result['response']['cost_cents']} cents")
                else:
                    print(f"❌ Capability test failed: {response.status_code}")
                    print(f"   {response.text}")
                    
            except Exception as e:
                print(f"❌ Test error for {test_case['capability']}: {e}")

async def list_registered_agents():
    """List all registered agents"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BETTY_API_URL}/api/agents/")
            
            if response.status_code == 200:
                agents = response.json()
                print(f"\n📋 Registered Agents ({len(agents)} total):")
                print("-" * 60)
                
                for agent in agents:
                    print(f"Name: {agent['display_name']}")
                    print(f"ID: {agent['id']}")
                    print(f"Provider: {agent['provider']}")
                    print(f"Status: {agent['status']}")
                    print(f"Capabilities: {', '.join(agent['capabilities'][:3])}{'...' if len(agent['capabilities']) > 3 else ''}")
                    print("-" * 60)
                    
            else:
                print(f"❌ Failed to list agents: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error listing agents: {e}")

async def main():
    """Main function"""
    print("🤖 BETTY Multi-Agent Platform - OpenAI Registration")
    print("=" * 55)
    
    print("\n1. Registering OpenAI agents...")
    registered_agents = await register_openai_agents()
    
    if registered_agents:
        print(f"\n✅ Successfully registered {len(registered_agents)} OpenAI agents")
        
        print("\n2. Listing all registered agents...")
        await list_registered_agents()
        
        print("\n3. Testing capability routing...")
        await asyncio.sleep(2)  # Give agents time to initialize
        await test_capability_routing()
    else:
        print("\n❌ No agents were registered successfully")

if __name__ == "__main__":
    asyncio.run(main())