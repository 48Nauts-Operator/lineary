#!/usr/bin/env python3

import asyncio
import asyncpg
import json
from datetime import datetime
from uuid import uuid4

async def test_simple_insert():
    """Test inserting into the existing knowledge_items table structure"""
    
    conn = await asyncpg.connect(
        host="localhost",
        port=5433,
        user="betty",
        password="bettypassword", 
        database="betty_memory"
    )
    
    try:
        # First, check if we need project and user entries
        project_id = uuid4()
        user_id = uuid4()
        
        # Insert a project if it doesn't exist
        await conn.execute("""
            INSERT INTO projects (id, name, description, metadata)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (id) DO NOTHING
        """, project_id, "betty_test", "Test project for BETTY ingestion", {})
        
        # Insert a user if it doesn't exist
        await conn.execute("""
            INSERT INTO users (id, username, email, metadata)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (id) DO NOTHING
        """, user_id, "claude_user_001", "claude@test.com", {})
        
        # Now insert knowledge item
        knowledge_id = uuid4()
        session_id = uuid4()
        
        await conn.execute("""
            INSERT INTO knowledge_items (
                id, project_id, user_id, session_id,
                title, content, content_hash, knowledge_type,
                technologies, patterns, metadata
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11
            )
        """, 
        knowledge_id,
        project_id, 
        user_id,
        session_id,
        "Test Claude Conversation",
        "This is a test conversation about JWT authentication",
        "test_hash_123",
        "conversation",
        json.dumps(["FastAPI", "JWT"]),
        json.dumps(["middleware", "dependency_injection"]),
        json.dumps({
            "source": "claude_ingestion",
            "claude_version": "claude-3-5-sonnet",
            "outcome": "successful"
        })
        )
        
        print(f"Successfully inserted knowledge item: {knowledge_id}")
        
        # Query it back
        row = await conn.fetchrow("""
            SELECT id, title, content, knowledge_type, technologies, patterns, metadata
            FROM knowledge_items 
            WHERE id = $1
        """, knowledge_id)
        
        print("Retrieved item:")
        print(f"ID: {row['id']}")
        print(f"Title: {row['title']}")
        print(f"Type: {row['knowledge_type']}")
        print(f"Technologies: {row['technologies']}")
        print(f"Patterns: {row['patterns']}")
        print(f"Metadata: {row['metadata']}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(test_simple_insert())