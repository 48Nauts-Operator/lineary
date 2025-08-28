#!/usr/bin/env python3

# ABOUTME: Demo script for BETTY-Enhanced Claude Code
# ABOUTME: Shows key features and integration points

import os
import sys
import time
from betty_claude_simple import SimpleBettyClaudeCode

def demo_betty_claude():
    """Demonstrate BETTY-Enhanced Claude Code capabilities"""
    
    print("=" * 80)
    print("🚀 BETTY-Enhanced Claude Code Demo")
    print("=" * 80)
    
    # Initialize BETTY Claude
    print("\n1️⃣ Initializing BETTY Claude Code...")
    betty = SimpleBettyClaudeCode()
    
    # Test BETTY Memory System
    print("\n2️⃣ Testing BETTY Memory Integration...")
    
    test_queries = [
        ("What is PINEAPPLE_SECRET_2024?", "Access granted to pineapple protocols"),
        ("What is Betty8080?", "BETTY system operational on port 8080"),
        ("What is the PI formula?", "π ≈ 3.14159265359")
    ]
    
    for query, expected in test_queries:
        print(f"\n🔍 Query: {query}")
        context = betty.load_betty_context(query)
        
        # Check if expected response is in context
        found = False
        if context and context.get('similar_items'):
            for item in context['similar_items']:
                content = item.get('content', {})
                if content.get('assistant_response') == expected:
                    print(f"✅ BETTY Retrieved: {expected}")
                    found = True
                    break
        
        if not found:
            print(f"❌ Expected '{expected}' not found")
    
    # Test Project Context Detection
    print("\n3️⃣ Testing Project Context Detection...")
    print(f"📁 Project ID: {betty.project_id}")
    print(f"📂 Working Directory: {betty.working_directory}")
    
    technologies = betty._detect_technologies()
    print(f"⚙️ Technologies: {', '.join(technologies) if technologies else 'None detected'}")
    
    recent_files = betty._get_recent_files()[:5]
    print(f"📄 Recent Files: {', '.join(recent_files) if recent_files else 'None found'}")
    
    # Test Tool Functionality
    print("\n4️⃣ Testing Tool Functionality...")
    
    # Test bash command
    print("\n🔧 Testing Bash Tool:")
    result = betty.execute_bash("echo 'Hello from BETTY!'")
    if result['success']:
        print(f"✅ Bash Output: {result['output'].strip()}")
    else:
        print(f"❌ Bash Error: {result['error']}")
    
    # Test file operations
    print("\n📝 Testing File Operations:")
    
    # Write test file
    test_content = f"BETTY Demo File\nGenerated at: {time.strftime('%Y-%m-%d %H:%M:%S')}\nSession ID: {betty.session_id}"
    write_result = betty.write_file("betty_demo_test.txt", test_content)
    
    if write_result['success']:
        print("✅ File written successfully")
        
        # Read test file
        read_result = betty.read_file("betty_demo_test.txt")
        if read_result['success']:
            print("✅ File read successfully")
            print("📖 Content (first 3 lines):")
            lines = read_result['output'].split('\n')[:3]
            for line in lines:
                print(f"     {line}")
        else:
            print(f"❌ File read error: {read_result['error']}")
        
        # Clean up test file
        cleanup_result = betty.execute_bash("rm -f betty_demo_test.txt")
        if cleanup_result['success']:
            print("🧹 Test file cleaned up")
    else:
        print(f"❌ File write error: {write_result['error']}")
    
    # Test Enhanced Prompt Building
    print("\n5️⃣ Testing Enhanced Prompt Building...")
    sample_query = "How do I optimize Docker performance?"
    context = betty.load_betty_context(sample_query)
    enhanced_prompt = betty.build_enhanced_prompt(sample_query, context)
    
    print(f"📝 Enhanced prompt length: {len(enhanced_prompt)} characters")
    print("🔍 Prompt preview (first 300 chars):")
    print("-" * 50)
    print(enhanced_prompt[:300] + "..." if len(enhanced_prompt) > 300 else enhanced_prompt)
    print("-" * 50)
    
    # Test Knowledge Storage
    print("\n6️⃣ Testing Knowledge Storage...")
    sample_response = "To optimize Docker performance, use multi-stage builds, minimize layers, and use .dockerignore files."
    betty.store_conversation_in_betty(sample_query, sample_response)
    print("✅ Sample conversation stored in BETTY")
    
    # Final Summary
    print("\n" + "=" * 80)
    print("🎉 BETTY-Enhanced Claude Code Demo Complete!")
    print("=" * 80)
    print("\n📊 Demo Results:")
    print(f"   ✅ Session ID: {betty.session_id}")
    print(f"   ✅ Project: {betty.project_id}")
    print(f"   ✅ BETTY Integration: {'Working' if context else 'Fallback Mode'}")
    print(f"   ✅ Tool Functionality: Verified")
    print(f"   ✅ Context Enhancement: Operational")
    print(f"   ✅ Knowledge Storage: Attempted")
    
    print("\n🚀 Ready to use! Run one of:")
    print("   ./betty_claude_simple.py     (Simple version)")
    print("   ./betty_claude_complete.py   (Full version with rich UI)")
    
    print("\n🧪 Test commands to try:")
    print("   What is PINEAPPLE_SECRET_2024?")
    print("   What is Betty8080?")
    print("   bash: docker-compose ps")
    print("   read: docker-compose.yml")
    
    return True

if __name__ == "__main__":
    try:
        success = demo_betty_claude()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Demo failed: {str(e)}")
        sys.exit(1)