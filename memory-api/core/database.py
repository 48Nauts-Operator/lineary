# ABOUTME: Multi-database connection manager for BETTY Memory System
# ABOUTME: Handles PostgreSQL, Neo4j, Qdrant, and Redis connections with health monitoring

import asyncio
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any, AsyncGenerator
import structlog
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import text
from neo4j import AsyncGraphDatabase, AsyncDriver
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
import redis.asyncio as redis

from core.config import Settings

logger = structlog.get_logger(__name__)

class DatabaseManager:
    """Centralized database connection manager for all database systems"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        
        # Database connections
        self.postgres_engine = None
        self.postgres_session_factory = None
        self.neo4j_driver: Optional[AsyncDriver] = None
        self.qdrant_client: Optional[QdrantClient] = None
        self.redis_client: Optional[redis.Redis] = None
        
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize all database connections"""
        if self._initialized:
            return
        
        logger.info("Initializing database connections")
        
        try:
            # Initialize PostgreSQL
            await self._init_postgres()
            
            # Initialize Neo4j
            await self._init_neo4j()
            
            # Initialize Qdrant
            await self._init_qdrant()
            
            # Initialize Redis
            await self._init_redis()
            
            # Verify all connections
            await self.health_check()
            
            self._initialized = True
            logger.info("All database connections initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize database connections", error=str(e))
            await self.close()
            raise
    
    async def _init_postgres(self) -> None:
        """Initialize PostgreSQL connection"""
        logger.info("Initializing PostgreSQL connection", host=self.settings.postgres_host)
        
        self.postgres_engine = create_async_engine(
            self.settings.postgres_url,
            pool_size=self.settings.postgres_pool_size,
            max_overflow=self.settings.postgres_max_overflow,
            pool_pre_ping=True,
            pool_recycle=3600,  # Recycle connections every hour
            echo=self.settings.debug
        )
        
        self.postgres_session_factory = async_sessionmaker(
            self.postgres_engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        # Test connection
        async with self.postgres_engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        
        logger.info("PostgreSQL connection established")
    
    async def _init_neo4j(self) -> None:
        """Initialize Neo4j connection"""
        logger.info("Initializing Neo4j connection", uri=self.settings.neo4j_uri)
        
        self.neo4j_driver = AsyncGraphDatabase.driver(
            self.settings.neo4j_uri,
            auth=(self.settings.neo4j_user, self.settings.neo4j_password),
            max_connection_lifetime=self.settings.neo4j_max_connection_lifetime,
            max_connection_pool_size=self.settings.neo4j_max_connection_pool_size
        )
        
        # Test connection
        await self.neo4j_driver.verify_connectivity()
        
        logger.info("Neo4j connection established")
    
    async def _init_qdrant(self) -> None:
        """Initialize Qdrant connection"""
        logger.info("Initializing Qdrant connection", host=self.settings.qdrant_host)
        
        self.qdrant_client = QdrantClient(
            host=self.settings.qdrant_host,
            port=self.settings.qdrant_port,
            timeout=self.settings.qdrant_timeout,
            prefer_grpc=self.settings.qdrant_prefer_grpc
        )
        
        # Test connection
        info = await asyncio.to_thread(self.qdrant_client.get_collections)
        
        logger.info("Qdrant connection established", cluster_info=info)
    
    async def _init_redis(self) -> None:
        """Initialize Redis connection"""
        logger.info("Initializing Redis connection", host=self.settings.redis_host)
        
        self.redis_client = redis.from_url(
            self.settings.redis_url,
            max_connections=self.settings.redis_max_connections,
            retry_on_timeout=self.settings.redis_retry_on_timeout,
            decode_responses=True
        )
        
        # Test connection
        await self.redis_client.ping()
        
        logger.info("Redis connection established")
    
    @asynccontextmanager
    async def get_postgres_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get PostgreSQL session with automatic cleanup"""
        if not self.postgres_session_factory:
            raise RuntimeError("PostgreSQL not initialized")
        
        async with self.postgres_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    
    @asynccontextmanager
    async def get_neo4j_session(self):
        """Get Neo4j session with automatic cleanup"""
        if not self.neo4j_driver:
            raise RuntimeError("Neo4j not initialized")
        
        async with self.neo4j_driver.session() as session:
            yield session
    
    def get_qdrant_client(self) -> QdrantClient:
        """Get Qdrant client"""
        if not self.qdrant_client:
            raise RuntimeError("Qdrant not initialized")
        return self.qdrant_client
    
    def get_redis_client(self) -> redis.Redis:
        """Get Redis client"""
        if not self.redis_client:
            raise RuntimeError("Redis not initialized")
        return self.redis_client
    
    @property
    def redis(self) -> redis.Redis:
        """Redis client property for convenience"""
        return self.get_redis_client()
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of all database connections"""
        health_status = {
            "postgres": {"status": "unknown", "error": None},
            "neo4j": {"status": "unknown", "error": None},
            "qdrant": {"status": "unknown", "error": None},
            "redis": {"status": "unknown", "error": None}
        }
        
        # Check PostgreSQL
        try:
            if self.postgres_engine:
                async with self.postgres_engine.begin() as conn:
                    result = await conn.execute(text("SELECT 1"))
                    if result.scalar() == 1:
                        health_status["postgres"]["status"] = "healthy"
                    else:
                        health_status["postgres"]["status"] = "unhealthy"
            else:
                health_status["postgres"]["status"] = "not_initialized"
        except Exception as e:
            health_status["postgres"]["status"] = "unhealthy"
            health_status["postgres"]["error"] = str(e)
        
        # Check Neo4j
        try:
            if self.neo4j_driver:
                await self.neo4j_driver.verify_connectivity()
                health_status["neo4j"]["status"] = "healthy"
            else:
                health_status["neo4j"]["status"] = "not_initialized"
        except Exception as e:
            health_status["neo4j"]["status"] = "unhealthy"
            health_status["neo4j"]["error"] = str(e)
        
        # Check Qdrant
        try:
            if self.qdrant_client:
                await asyncio.to_thread(self.qdrant_client.get_collections)
                health_status["qdrant"]["status"] = "healthy"
            else:
                health_status["qdrant"]["status"] = "not_initialized"
        except Exception as e:
            health_status["qdrant"]["status"] = "unhealthy"
            health_status["qdrant"]["error"] = str(e)
        
        # Check Redis
        try:
            if self.redis_client:
                await self.redis_client.ping()
                health_status["redis"]["status"] = "healthy"
            else:
                health_status["redis"]["status"] = "not_initialized"
        except Exception as e:
            health_status["redis"]["status"] = "unhealthy"
            health_status["redis"]["error"] = str(e)
        
        return health_status
    
    async def close(self) -> None:
        """Close all database connections"""
        logger.info("Closing database connections")
        
        # Close PostgreSQL
        if self.postgres_engine:
            await self.postgres_engine.dispose()
            self.postgres_engine = None
            self.postgres_session_factory = None
        
        # Close Neo4j
        if self.neo4j_driver:
            await self.neo4j_driver.close()
            self.neo4j_driver = None
        
        # Close Qdrant (synchronous close)
        if self.qdrant_client:
            self.qdrant_client.close()
            self.qdrant_client = None
        
        # Close Redis
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None
        
        self._initialized = False
        logger.info("All database connections closed")

# Import text for SQLAlchemy queries
from sqlalchemy import text