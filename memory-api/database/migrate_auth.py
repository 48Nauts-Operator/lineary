#!/usr/bin/env python3
# ABOUTME: Database migration script for BETTY authentication system
# ABOUTME: Applies auth schema and creates initial admin user

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from core.config import get_settings
from core.database import DatabaseManager
import structlog

logger = structlog.get_logger(__name__)

async def apply_auth_migration():
    """Apply authentication schema migration"""
    try:
        settings = get_settings()
        db_manager = DatabaseManager(settings)
        
        logger.info("Starting authentication schema migration")
        
        # Initialize database connections
        await db_manager.initialize()
        
        # Read the auth schema SQL
        auth_schema_path = Path(__file__).parent / "auth_schema.sql"
        with open(auth_schema_path, 'r') as f:
            schema_sql = f.read()
        
        # Execute the schema
        async with db_manager.postgres_pool.acquire() as conn:
            # Execute schema in a transaction
            async with conn.transaction():
                logger.info("Applying authentication schema")
                await conn.execute(schema_sql)
                logger.info("Authentication schema applied successfully")
        
        logger.info("Migration completed successfully")
        return True
        
    except Exception as e:
        logger.error("Migration failed", error=str(e))
        return False
        
    finally:
        # Close database connections
        if 'db_manager' in locals():
            await db_manager.close()

async def verify_migration():
    """Verify that the migration was applied correctly"""
    try:
        settings = get_settings()
        db_manager = DatabaseManager(settings)
        
        await db_manager.initialize()
        
        # Check if auth tables exist
        auth_tables = [
            'auth_users', 'auth_project_permissions', 'auth_api_keys',
            'auth_refresh_tokens', 'auth_token_blacklist', 'auth_audit_log',
            'auth_rate_limits'
        ]
        
        async with db_manager.postgres_pool.acquire() as conn:
            for table in auth_tables:
                result = await conn.fetchval(
                    "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = $1)",
                    table
                )
                if result:
                    logger.info(f"✓ Table {table} exists")
                else:
                    logger.error(f"✗ Table {table} missing")
                    return False
            
            # Check if admin user exists
            admin_count = await conn.fetchval(
                "SELECT COUNT(*) FROM auth_users WHERE role = 'admin'"
            )
            logger.info(f"Admin users found: {admin_count}")
        
        await db_manager.close()
        logger.info("Migration verification completed successfully")
        return True
        
    except Exception as e:
        logger.error("Migration verification failed", error=str(e))
        return False

async def main():
    """Main migration function"""
    logger.info("BETTY Authentication System Migration")
    logger.info("=====================================")
    
    # Apply migration
    success = await apply_auth_migration()
    if not success:
        logger.error("Migration failed")
        return 1
    
    # Verify migration
    success = await verify_migration()
    if not success:
        logger.error("Migration verification failed")
        return 1
    
    logger.info("Migration completed successfully!")
    logger.info("")
    logger.info("Default admin credentials:")
    logger.info("Email: admin@betty.memory")
    logger.info("Password: ChangeMe123!")
    logger.info("")
    logger.info("⚠️  IMPORTANT: Change the default password immediately!")
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)