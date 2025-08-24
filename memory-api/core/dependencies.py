# ABOUTME: FastAPI dependency injection for BETTY Memory System
# ABOUTME: Provides database connections and services to API endpoints

from typing import AsyncGenerator, Any, Dict
from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from neo4j import AsyncSession as Neo4jSession
from qdrant_client import QdrantClient
import redis.asyncio as redis
import structlog

from core.database import DatabaseManager
from core.config import Settings, get_settings

logger = structlog.get_logger(__name__)

class DatabaseSessionWrapper:
    """Wrapper that provides session-like interface for database operations"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self._current_session = None
    
    async def execute(self, stmt, parameters=None):
        """Execute a statement using a managed session"""
        async with self.db_manager.get_postgres_session() as session:
            if parameters is None:
                result = await session.execute(stmt)
            else:
                result = await session.execute(stmt, parameters)
            return result
    
    async def commit(self):
        """Commit current transaction (no-op as sessions are auto-committed)"""
        # Sessions created via get_postgres_session() auto-commit on exit
        pass
    
    async def rollback(self):
        """Rollback current transaction (no-op as each operation gets its own session)"""
        # Each operation gets its own session, so no rollback needed
        pass

async def get_database_manager(request: Request) -> DatabaseManager:
    """Get database manager from app state"""
    if not hasattr(request.app.state, 'db_manager'):
        raise HTTPException(
            status_code=503,
            detail="Database manager not initialized"
        )
    return request.app.state.db_manager

async def get_postgres_session(
    db_manager: DatabaseManager = Depends(get_database_manager)
) -> AsyncGenerator[AsyncSession, None]:
    """Get PostgreSQL session dependency"""
    try:
        async with db_manager.get_postgres_session() as session:
            yield session
    except Exception as e:
        logger.error("Failed to get PostgreSQL session", error=str(e))
        raise HTTPException(
            status_code=503,
            detail="Database connection unavailable"
        )

async def get_neo4j_session(
    db_manager: DatabaseManager = Depends(get_database_manager)
) -> AsyncGenerator[Neo4jSession, None]:
    """Get Neo4j session dependency"""
    try:
        async with db_manager.get_neo4j_session() as session:
            yield session
    except Exception as e:
        logger.error("Failed to get Neo4j session", error=str(e))
        raise HTTPException(
            status_code=503,
            detail="Graph database connection unavailable"
        )

async def get_qdrant_client(
    db_manager: DatabaseManager = Depends(get_database_manager)
) -> QdrantClient:
    """Get Qdrant client dependency"""
    try:
        return db_manager.get_qdrant_client()
    except Exception as e:
        logger.error("Failed to get Qdrant client", error=str(e))
        raise HTTPException(
            status_code=503,
            detail="Vector database connection unavailable"
        )

async def get_redis_client(
    db_manager: DatabaseManager = Depends(get_database_manager)
) -> redis.Redis:
    """Get Redis client dependency"""
    try:
        return db_manager.get_redis_client()
    except Exception as e:
        logger.error("Failed to get Redis client", error=str(e))
        raise HTTPException(
            status_code=503,
            detail="Cache connection unavailable"
        )

async def get_settings_dependency() -> Settings:
    """Get application settings dependency"""
    return get_settings()

class DatabaseDependencies:
    """Collection of database dependencies for complex operations"""
    
    def __init__(
        self,
        postgres: DatabaseSessionWrapper,
        neo4j: Neo4jSession,
        qdrant: QdrantClient,
        redis_client: redis.Redis,
        settings: Settings
    ):
        self.postgres = postgres
        self.neo4j = neo4j
        self.qdrant = qdrant
        self.redis = redis_client
        self.settings = settings

async def get_all_databases(
    request: Request,
    settings: Settings = Depends(get_settings_dependency)
) -> DatabaseDependencies:
    """Get all database connections for complex operations with graceful degradation"""
    try:
        db_manager = await get_database_manager(request)
        
        # Create session wrapper for proper async database operations
        postgres_wrapper = DatabaseSessionWrapper(db_manager)
        
        return DatabaseDependencies(
            postgres=postgres_wrapper,
            neo4j=db_manager.neo4j_driver if hasattr(db_manager, 'neo4j_driver') else None,
            qdrant=db_manager.qdrant_client if hasattr(db_manager, 'qdrant_client') else None,
            redis_client=db_manager.redis_client if hasattr(db_manager, 'redis_client') else None,
            settings=settings
        )
        
    except Exception as e:
        logger.error("Failed to get database connections", error=str(e))
        raise HTTPException(
            status_code=503,
            detail="Database connection unavailable"
        )

async def get_core_databases(
    request: Request,
    redis_client: redis.Redis = Depends(get_redis_client),
    settings: Settings = Depends(get_settings_dependency)
) -> DatabaseDependencies:
    """Get core database connections (PostgreSQL + Redis only) for basic operations"""
    try:
        db_manager = await get_database_manager(request)
        
        # Create session wrapper for proper async database operations
        postgres_wrapper = DatabaseSessionWrapper(db_manager)
        
        # For basic operations, we can provide None for neo4j and qdrant
        # The services should handle these gracefully
        return DatabaseDependencies(
            postgres=postgres_wrapper,
            neo4j=None,
            qdrant=None,
            redis_client=redis_client,
            settings=settings
        )
    except Exception as e:
        logger.error("Failed to get core database connections", error=str(e))
        raise HTTPException(
            status_code=503,
            detail="Core database connections unavailable"
        )

# Alias for backward compatibility and cleaner imports
get_databases = get_all_databases

# Additional aliases for source validation system
get_db_manager = get_database_manager

async def get_vector_service(
    db_manager: DatabaseManager = Depends(get_database_manager)
):
    """Get vector service dependency (placeholder for integration)"""
    try:
        # Import vector service dynamically to avoid circular imports
        from services.vector_service import VectorService
        
        # Create vector service with database manager
        qdrant_client = db_manager.get_qdrant_client()
        return VectorService(qdrant_client)
        
    except ImportError:
        logger.warning("Vector service not available - using mock implementation")
        # Return mock vector service if not available
        class MockVectorService:
            async def generate_embedding(self, text: str):
                import hashlib
                # Simple hash-based embedding for testing
                hash_obj = hashlib.md5(text.encode())
                hash_hex = hash_obj.hexdigest()
                return [float(int(hash_hex[i:i+2], 16)) / 255.0 for i in range(0, 32, 2)]
            
            async def search_similar(self, embedding, limit=10, threshold=0.5):
                return []  # Return empty results for mock
        
        return MockVectorService()
    except Exception as e:
        logger.error("Failed to get vector service", error=str(e))
        raise HTTPException(
            status_code=503,
            detail="Vector service unavailable"
        )

# Authentication dependencies for compatibility
async def get_current_user_optional():
    """Optional user authentication - returns None if not authenticated"""
    return None

async def require_auth():
    """Require authentication - placeholder for compatibility"""
    return {"user_id": "system", "username": "system"}