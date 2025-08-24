#!/usr/bin/env python3

# Debug version - let's see what BETTY is returning

import json
import urllib.request
import urllib.parse

def debug_betty_search(query):
    betty_url = "http://localhost:8001"
    
    print(f"🔍 Testing BETTY search for: '{query}'")
    print("-" * 50)
    
    # Test the search
    search_query = urllib.parse.quote(query)
    search_url = f"{betty_url}/api/knowledge/?search={search_query}"
    
    print(f"Search URL: {search_url}")
    
    try:
        req = urllib.request.Request(search_url)
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
            items = data.get('data', [])
            
            print(f"Found {len(items)} total items")
            
            for i, item in enumerate(items, 1):
                title = item.get('title', 'No title')
                content = item.get('content', '')
                print(f"\n{i}. {title}")
                print(f"   Content preview: {content[:100]}...")
                print(f"   Full length: {len(content)} chars")
                
                # Check for code words
                has_pineapple = 'PINEAPPLE_SECRET_2024' in content
                has_betty8080 = 'Betty8080' in content
                has_pi = 'π' in content
                has_error = 'Error calling Claude API' in content
                
                print(f"   Contains PINEAPPLE_SECRET_2024: {has_pineapple}")
                print(f"   Contains Betty8080: {has_betty8080}")
                print(f"   Contains π: {has_pi}")
                print(f"   Contains API errors: {has_error}")
                
            # Test what would be filtered
            print(f"\n📊 FILTERING RESULTS:")
            relevant_items = []
            for item in items:
                content = item.get('content', '')
                if ('Error calling Claude API' not in content and 
                    'HTTP Error' not in content and
                    len(content.strip()) > 50):
                    
                    if ('PINEAPPLE_SECRET_2024' in content or 
                        'Betty8080' in content or 
                        'π' in content or
                        'code word' in content.lower()):
                        relevant_items.insert(0, item)
                    else:
                        relevant_items.append(item)
            
            print(f"After filtering: {len(relevant_items)} relevant items")
            
            if relevant_items:
                print(f"\nTop relevant item:")
                top_item = relevant_items[0]
                print(f"Title: {top_item.get('title', 'No title')}")
                print(f"Content: {top_item.get('content', '')[:200]}...")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Test different queries
    debug_betty_search("code word")
    print("\n" + "="*60 + "\n")
    debug_betty_search("PINEAPPLE_SECRET_2024")
    print("\n" + "="*60 + "\n") 
    debug_betty_search("Betty8080")