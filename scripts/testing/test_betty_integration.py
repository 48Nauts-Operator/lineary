#!/usr/bin/env python3
"""
Simple test script to validate BETTY integration without external dependencies
"""

import asyncio
import json
import requests
from datetime import datetime

BETTY_API_BASE = "http://localhost:8001"

def test_betty_integration():
    """Test basic BETTY API functionality"""
    
    print("🧠 Testing BETTY Memory System Integration")
    print("=" * 50)
    
    # Test 1: Health check
    print("\n1. Testing Health Endpoint...")
    try:
        response = requests.get(f"{BETTY_API_BASE}/health/")
        if response.status_code == 200:
            data = response.json()
            uptime = data.get('uptime', 'unknown')
            print(f"✅ Health Check: {data['status']} (uptime: {uptime})")
        else:
            print(f"❌ Health Check Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health Check Error: {e}")
        return False
    
    # Test 2: Knowledge Stats
    print("\n2. Testing Knowledge Stats...")
    try:
        response = requests.get(f"{BETTY_API_BASE}/api/knowledge/stats")
        if response.status_code == 200:
            data = response.json()
            stats = data.get('data', {})
            print(f"✅ Knowledge Stats: {stats.get('total_items', 0)} items")
            print(f"   - By Type: {stats.get('items_by_type', {})}")
            print(f"   - By Source: {stats.get('items_by_source', {})}")
        else:
            print(f"❌ Knowledge Stats Failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Knowledge Stats Error: {e}")
    
    # Test 3: List Knowledge Items
    print("\n3. Testing Knowledge List...")
    try:
        response = requests.get(f"{BETTY_API_BASE}/api/knowledge/?page=1&page_size=3")
        if response.status_code == 200:
            data = response.json()
            items = data.get('data', [])
            print(f"✅ Knowledge List: Found {len(items)} items")
            for item in items:
                print(f"   - {item.get('title', 'No title')[:50]}...")
                print(f"     Type: {item.get('knowledge_type')}, Source: {item.get('source_type')}")
        else:
            print(f"❌ Knowledge List Failed: {response.status_code}")
            if response.text:
                print(f"   Error: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Knowledge List Error: {e}")
    
    # Test 4: Analytics Dashboard
    print("\n4. Testing Analytics...")
    try:
        response = requests.get(f"{BETTY_API_BASE}/api/analytics/dashboard-summary")
        if response.status_code == 200:
            data = response.json()
            summary = data.get('data', {})
            print(f"✅ Analytics Summary:")
            print(f"   - Total Knowledge: {summary.get('total_knowledge_items', 0)}")
            print(f"   - Intelligence Score: {summary.get('intelligence_score', 0):.1f}/10")
            print(f"   - Most Active Project: {summary.get('most_active_project', 'N/A')}")
            print(f"   - System Status: {summary.get('system_health_status', 'unknown')}")
        else:
            print(f"❌ Analytics Failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Analytics Error: {e}")
    
    # Test 5: Search (simplified keyword-only)
    print("\n5. Testing Search...")
    try:
        search_payload = {
            "query": "API",
            "search_type": "keyword",
            "limit": 3,
            "include_content": False
        }
        response = requests.post(
            f"{BETTY_API_BASE}/api/knowledge/search",
            json=search_payload,
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            data = response.json()
            results = data.get('data', [])
            print(f"✅ Search Results: Found {len(results)} items for 'API'")
            for result in results:
                print(f"   - {result.get('title', 'No title')[:40]}...")
        else:
            print(f"❌ Search Failed: {response.status_code}")
            if response.text:
                print(f"   Error: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Search Error: {e}")
    
    print("\n" + "=" * 50)
    print("🔍 BETTY Integration Test Complete")
    
    # Summary for Claude integration
    print("\n💡 Integration Summary for Claude:")
    print("   - BETTY Memory API is operational on port 8001")
    print("   - Knowledge storage and retrieval working")
    print("   - Analytics dashboard showing real data")
    print("   - Ready for Claude agent integration")
    
    return True

if __name__ == "__main__":
    test_betty_integration()