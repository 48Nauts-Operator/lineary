#!/bin/bash
# ABOUTME: Demonstration script showing Betty memory integration concept
# ABOUTME: Proves that Betty can store and retrieve conversation context

echo "🧠 Betty Memory Integration Demo"
echo "=================================="

BETTY_URL="http://localhost:8001"
USER_ID="e8e3f2de-070d-4dbd-b899-e49745f1d29b"

echo
echo "📝 Step 1: Storing knowledge item with code word..."

# Store a knowledge item with our "code word"
KNOWLEDGE_RESPONSE=$(curl -s -X POST ${BETTY_URL}/api/knowledge/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Code Word for Memory Test",
    "content": "The secret code word that Andre shared is: PINEAPPLE_SECRET_2024. This was shared during our conversation about testing Betty memory integration. The code word should be remembered across all future conversations.",
    "knowledge_type": "memory",
    "source_type": "conversation",
    "tags": ["code_word", "memory_test", "claude", "betty"],
    "summary": "Secret code word PINEAPPLE_SECRET_2024 shared by Andre for memory testing",
    "confidence": "high"
  }')

if echo "$KNOWLEDGE_RESPONSE" | grep -q "success.*true"; then
    echo "✅ Successfully stored code word in Betty!"
    KNOWLEDGE_ID=$(echo "$KNOWLEDGE_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['data']['id'])" 2>/dev/null || echo "unknown")
    echo "   📚 Knowledge ID: $KNOWLEDGE_ID"
else
    echo "❌ Failed to store knowledge item"
    echo "   Response: $KNOWLEDGE_RESPONSE"
fi

echo
echo "🔍 Step 2: Testing context retrieval..."

# Test context retrieval for code word query
CONTEXT_RESPONSE=$(curl -s -X POST ${BETTY_URL}/api/knowledge/retrieve/context \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "'${USER_ID}'",
    "current_context": {
      "working_on": "Testing memory system integration",
      "user_message": "What was the code word we discussed earlier?",
      "problem_type": "memory_retrieval"
    },
    "max_items": 5
  }')

echo "Context Response:"
echo "$CONTEXT_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    context = data.get('context', {})
    knowledge = context.get('relevant_knowledge', [])
    
    if knowledge:
        print(f'✅ Found {len(knowledge)} relevant items!')
        for item in knowledge:
            title = item.get('title', 'No title')
            summary = item.get('summary', 'No summary')
            print(f'   📚 {title}')
            print(f'      {summary}')
    else:
        print('❌ No relevant knowledge found')
        print('   Available context keys:', list(context.keys()))
except Exception as e:
    print(f'❌ Error parsing response: {e}')
    print('Raw response:', file=sys.stderr)
    sys.stdin.seek(0)
    print(sys.stdin.read(), file=sys.stderr)
" 2>&1

echo
echo "🔎 Step 3: Testing knowledge search..."

# Test knowledge search
SEARCH_RESPONSE=$(curl -s -X POST ${BETTY_URL}/api/knowledge/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "code word PINEAPPLE_SECRET_2024",
    "search_type": "hybrid",
    "max_results": 5
  }')

echo "Search Response:"
echo "$SEARCH_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    results = data.get('results', [])
    
    if results:
        print(f'✅ Found {len(results)} search results!')
        for item in results:
            title = item.get('title', 'No title')
            score = item.get('relevance_score', 0)
            content = item.get('content', '')[:100] + '...' if len(item.get('content', '')) > 100 else item.get('content', '')
            print(f'   🎯 {title} (score: {score:.2f})')
            print(f'      {content}')
    else:
        print('❌ No search results found')
        print('   Available keys:', list(data.keys()))
except Exception as e:
    print(f'❌ Error parsing response: {e}')
    print('Raw response:', file=sys.stderr)
    sys.stdin.seek(0)
    print(sys.stdin.read(), file=sys.stderr)
" 2>&1

echo
echo "📊 Betty Memory Demo Complete!"
echo "This demonstrates that Betty can:"
echo "  ✓ Store conversation context"
echo "  ✓ Retrieve relevant context based on queries"
echo "  ✓ Search across stored knowledge"
echo
echo "The next step would be to integrate this with Claude API"
echo "using the Anthropic SDK to create the continuous memory experience."