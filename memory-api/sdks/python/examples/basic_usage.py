#!/usr/bin/env python3
"""
BETTY Memory System Python SDK - Basic Usage Example

This example demonstrates the basic functionality of the BETTY Python SDK,
including advanced search, knowledge management, and error handling.
"""

import asyncio
import os
from typing import List
from betty_client import BettyClient, ClientConfig
from betty_client.exceptions import (
    BettyAPIException, 
    AuthenticationException,
    ValidationException
)


async def basic_search_example(client: BettyClient):
    """Demonstrate basic search functionality."""
    
    print("🔍 Basic Search Example")
    print("-" * 50)
    
    try:
        # Simple search
        results = await client.advanced_search(
            query="machine learning optimization",
            search_type="hybrid",
            max_results=10,
            similarity_threshold=0.7
        )
        
        if results.success:
            print(f"Found {results.data.total_results} results")
            print(f"Execution time: {results.data.query_analysis.execution_time_ms}ms")
            print(f"Search type used: {results.data.query_analysis.search_type_used}")
            
            print("\nTop Results:")
            for i, result in enumerate(results.data.results[:5], 1):
                print(f"{i}. {result.title}")
                print(f"   Type: {result.knowledge_type}")
                print(f"   Score: {result.similarity_score:.3f}")
                print(f"   Content: {result.content[:100]}...")
                print()
        else:
            print(f"Search failed: {results.message}")
            
    except Exception as e:
        print(f"Search error: {e}")


async def filtered_search_example(client: BettyClient):
    """Demonstrate search with filters."""
    
    print("🎯 Filtered Search Example")
    print("-" * 50)
    
    try:
        # Search with filters
        results = await client.advanced_search(
            query="neural networks deep learning",
            search_type="semantic",
            similarity_threshold=0.8,
            max_results=15,
            filters=[
                {
                    "field": "knowledge_type",
                    "operator": "in",
                    "value": ["research_paper", "documentation", "tutorial"]
                },
                {
                    "field": "quality_score",
                    "operator": "gte",
                    "value": 0.8
                }
            ],
            time_range={
                "start": "2024-01-01T00:00:00Z"
            }
        )
        
        if results.success:
            print(f"Found {results.data.total_results} high-quality results")
            
            # Show facets if available
            if results.data.facets:
                print("\nResult Breakdown:")
                if results.data.facets.knowledge_type:
                    for ktype, count in results.data.facets.knowledge_type.items():
                        print(f"  {ktype}: {count}")
            
            print(f"\nFiltered Results:")
            for result in results.data.results[:3]:
                print(f"- {result.title}")
                print(f"  Quality: {result.metadata.quality_score if result.metadata else 'N/A'}")
                print(f"  Tags: {', '.join(result.metadata.tags) if result.metadata and result.metadata.tags else 'None'}")
                print()
        else:
            print(f"Filtered search failed: {results.message}")
            
    except Exception as e:
        print(f"Filtered search error: {e}")


async def knowledge_management_example(client: BettyClient):
    """Demonstrate knowledge item management."""
    
    print("📚 Knowledge Management Example")
    print("-" * 50)
    
    try:
        # Add new knowledge item
        add_result = await client.add_knowledge(
            title="Python Async Best Practices",
            content="""
            When working with async Python code, follow these best practices:
            
            1. Use async/await syntax consistently
            2. Handle exceptions properly in async functions
            3. Use asyncio.gather() for concurrent operations
            4. Close resources properly with async context managers
            5. Avoid blocking operations in async functions
            """.strip(),
            knowledge_type="best_practices",
            tags=["python", "async", "programming", "best-practices"],
            metadata={
                "source": "python-sdk-example",
                "language": "en",
                "difficulty": "intermediate"
            }
        )
        
        if add_result.success:
            knowledge_id = add_result.data.get("id")
            print(f"✅ Added knowledge item: {knowledge_id}")
            
            # Retrieve the knowledge item
            get_result = await client.get_knowledge(knowledge_id)
            if get_result.success:
                item = get_result.data
                print(f"📖 Retrieved: {item['title']}")
                print(f"   Type: {item['knowledge_type']}")
                print(f"   Tags: {', '.join(item.get('metadata', {}).get('tags', []))}")
            
            # Update the knowledge item
            update_result = await client.update_knowledge(
                knowledge_id,
                tags=["python", "async", "programming", "best-practices", "updated"],
                metadata={
                    "source": "python-sdk-example",
                    "language": "en", 
                    "difficulty": "intermediate",
                    "last_updated": "2024-08-08T12:00:00Z"
                }
            )
            
            if update_result.success:
                print(f"✏️  Updated knowledge item with new tags")
            
            # Search for our newly added item
            search_result = await client.advanced_search(
                query="Python async best practices",
                search_type="semantic",
                max_results=5
            )
            
            if search_result.success:
                found_our_item = False
                for result in search_result.data.results:
                    if result.id == knowledge_id:
                        found_our_item = True
                        print(f"🔍 Found our item in search results (score: {result.similarity_score:.3f})")
                        break
                
                if not found_our_item:
                    print("❓ Our item not found in search results (may need time for indexing)")
            
            # Clean up - delete the test item
            delete_result = await client.delete_knowledge(knowledge_id)
            if delete_result.success:
                print(f"🗑️  Cleaned up test knowledge item")
        
        else:
            print(f"Failed to add knowledge: {add_result.message}")
            
    except Exception as e:
        print(f"Knowledge management error: {e}")


async def error_handling_example(client: BettyClient):
    """Demonstrate error handling."""
    
    print("⚠️  Error Handling Example")
    print("-" * 50)
    
    # Test authentication error (if token is invalid)
    try:
        # This might fail if token is invalid
        await client.health_check()
        print("✅ API health check passed")
        
    except AuthenticationException as e:
        print(f"🔑 Authentication error: {e.message}")
        print(f"   Details: {e.details}")
        
    except BettyAPIException as e:
        print(f"🌐 API error: {e.message}")
        if e.status_code:
            print(f"   Status code: {e.status_code}")
        if e.request_id:
            print(f"   Request ID: {e.request_id}")
    
    # Test validation error
    try:
        # This should fail due to empty query
        await client.advanced_search(query="")
        
    except ValidationException as e:
        print(f"📝 Validation error: {e.message}")
        if e.field_errors:
            print("   Field errors:")
            for field, errors in e.field_errors.items():
                print(f"     {field}: {', '.join(errors)}")
    
    except Exception as e:
        print(f"Validation test failed differently: {e}")
    
    # Test with invalid knowledge ID
    try:
        await client.get_knowledge("invalid-uuid")
        
    except BettyAPIException as e:
        print(f"🔍 Invalid ID error: {e.message}")
    
    except Exception as e:
        print(f"Invalid ID test failed: {e}")


async def main():
    """Main example function."""
    
    print("🚀 BETTY Python SDK - Basic Usage Examples")
    print("=" * 60)
    
    # Get API key from environment or prompt
    api_key = os.getenv("BETTY_API_KEY")
    if not api_key:
        print("❌ Please set BETTY_API_KEY environment variable")
        print("   export BETTY_API_KEY='your-jwt-token'")
        return
    
    # Initialize client
    try:
        config = ClientConfig(
            api_key=api_key,
            base_url=os.getenv("BETTY_BASE_URL", "http://localhost:3034/api/v2"),
            timeout=30,
            log_level="INFO"
        )
        
        async with BettyClient(config=config) as client:
            print(f"🔧 Connected to BETTY API: {config.base_url}")
            print()
            
            # Run examples
            await basic_search_example(client)
            print()
            
            await filtered_search_example(client)
            print()
            
            await knowledge_management_example(client)
            print()
            
            await error_handling_example(client)
            print()
            
            print("✅ All examples completed successfully!")
    
    except Exception as e:
        print(f"❌ Failed to initialize client: {e}")
        print("\nTroubleshooting:")
        print("1. Check that BETTY API is running")
        print("2. Verify your API key is valid")
        print("3. Ensure you have the required permissions")


if __name__ == "__main__":
    # Run the examples
    asyncio.run(main())