#!/usr/bin/env python3
"""
ABOUTME: Database migration runner for enhanced task system
ABOUTME: Executes SQL migrations with proper connection handling
"""

import asyncio
import asyncpg
import os
from pathlib import Path

async def run_migration():
    """Run the enhanced task system migration"""
    
    # Get database connection details from environment
    db_host = os.getenv('POSTGRES_HOST', 'postgres')
    db_port = os.getenv('POSTGRES_PORT', '5432')
    db_name = os.getenv('POSTGRES_DB', 'betty_memory')
    db_user = os.getenv('POSTGRES_USER', 'betty')
    db_password = os.getenv('POSTGRES_PASSWORD', 'bettypassword')
    
    # Build connection URL for asyncpg
    db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    print(f"Connecting to database: {db_host}:{db_port}/{db_name}")
    
    # Migration files to run in order
    migration_files = [
        "migrations/000_base_task_system.sql",
        "migrations/001_enhanced_task_system.sql"
    ]
    
    # Connect to database and run migrations
    try:
        conn = await asyncpg.connect(db_url)
        print("Connected to database successfully")
        
        for migration_file_path in migration_files:
            migration_file = Path(migration_file_path)
            if not migration_file.exists():
                print(f"Migration file not found: {migration_file}")
                continue
            
            with open(migration_file, 'r') as f:
                migration_sql = f.read()
            
            print(f"Running migration: {migration_file.name} ({len(migration_sql)} characters)")
            
            # Execute migration
            await conn.execute(migration_sql)
            print(f"✅ Migration {migration_file.name} executed successfully")
        
        # Verify tables were created
        tables_query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND (table_name LIKE 'task%' OR table_name LIKE 'sprint%' OR table_name LIKE 'git%' OR table_name LIKE 'workflow%')
        ORDER BY table_name
        """
        
        tables = await conn.fetch(tables_query)
        print(f"✅ Task system tables ({len(tables)} total):")
        for table in tables:
            print(f"  - {table['table_name']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if 'conn' in locals():
            await conn.close()
            print("Database connection closed")

if __name__ == "__main__":
    success = asyncio.run(run_migration())
    exit(0 if success else 1)