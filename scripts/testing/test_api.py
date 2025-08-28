#!/usr/bin/env python3
"""
Quick test script to check if the API can start locally
"""

import sys
import os
sys.path.append('/home/jarvis/projects/Betty/memory-api')

try:
    print("Testing imports...")
    
    # Test basic imports
    print("1. Testing FastAPI import...")
    from fastapi import FastAPI
    print("   ✓ FastAPI imported successfully")
    
    print("2. Testing structured logging...")
    import structlog
    print("   ✓ structlog imported successfully")
    
    print("3. Testing database clients...")
    from sqlalchemy.ext.asyncio import create_async_engine
    print("   ✓ SQLAlchemy async imported successfully")
    
    from neo4j import AsyncGraphDatabase
    print("   ✓ Neo4j driver imported successfully")
    
    from qdrant_client import QdrantClient
    print("   ✓ Qdrant client imported successfully")
    
    import redis.asyncio as redis
    print("   ✓ Redis async imported successfully")
    
    print("4. Testing core modules...")
    from core.config import get_settings
    print("   ✓ Config module imported successfully")
    
    from core.database import DatabaseManager
    print("   ✓ Database manager imported successfully")
    
    print("5. Testing main application...")
    from main import app
    print("   ✓ Main application imported successfully")
    
    print("\n✅ All imports successful! API should start properly.")
    
    # Test configuration
    settings = get_settings()
    print(f"\nConfiguration test:")
    print(f"   - PostgreSQL URL: {settings.postgres_url}")
    print(f"   - Neo4j URI: {settings.neo4j_uri}")
    print(f"   - Qdrant URL: {settings.qdrant_url}")
    print(f"   - Redis URL: {settings.redis_url}")

except Exception as e:
    print(f"\n❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)