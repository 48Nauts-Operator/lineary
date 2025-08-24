# ABOUTME: Health check endpoints for BETTY Memory System
# ABOUTME: Provides system health monitoring and database connectivity status

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
import structlog
import time
from datetime import datetime

from core.database import DatabaseManager
from core.dependencies import get_database_manager
from core.config import Settings, get_settings

logger = structlog.get_logger(__name__)
router = APIRouter()

@router.get("/")
async def health_check() -> Dict[str, Any]:
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "service": "BETTY Memory System API",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime": "healthy"
    }

@router.get("/detailed")
async def detailed_health_check(
    db_manager: DatabaseManager = Depends(get_database_manager),
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """Detailed health check including all database connections"""
    start_time = time.time()
    
    try:
        # Get database health status
        db_health = await db_manager.health_check()
        
        # Calculate response time
        response_time = time.time() - start_time
        
        # Determine overall status
        all_healthy = all(
            db_status["status"] == "healthy" 
            for db_status in db_health.values()
        )
        
        overall_status = "healthy" if all_healthy else "degraded"
        
        # Count healthy/unhealthy services
        healthy_count = sum(1 for db in db_health.values() if db["status"] == "healthy")
        total_count = len(db_health)
        
        response = {
            "status": overall_status,
            "service": "BETTY Memory System API",
            "version": "1.0.0",
            "timestamp": datetime.utcnow().isoformat(),
            "response_time_ms": round(response_time * 1000, 2),
            "databases": db_health,
            "summary": {
                "healthy_services": healthy_count,
                "total_services": total_count,
                "success_rate": round((healthy_count / total_count) * 100, 1) if total_count > 0 else 0
            },
            "configuration": {
                "postgres_host": settings.postgres_host,
                "neo4j_uri": settings.neo4j_uri,
                "qdrant_host": settings.qdrant_host,
                "redis_host": settings.redis_host
            }
        }
        
        # Log health check
        logger.info(
            "Detailed health check completed",
            status=overall_status,
            response_time_ms=response["response_time_ms"],
            healthy_services=healthy_count,
            total_services=total_count
        )
        
        return response
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        raise HTTPException(
            status_code=503,
            detail=f"Health check failed: {str(e)}"
        )

@router.get("/databases")
async def database_health_check(
    db_manager: DatabaseManager = Depends(get_database_manager)
) -> Dict[str, Any]:
    """Database-specific health check"""
    start_time = time.time()
    
    try:
        db_health = await db_manager.health_check()
        response_time = time.time() - start_time
        
        # Determine overall database health
        all_healthy = all(
            db_status["status"] == "healthy" 
            for db_status in db_health.values()
        )
        
        return {
            "status": "healthy" if all_healthy else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "response_time_ms": round(response_time * 1000, 2),
            "databases": db_health
        }
        
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        raise HTTPException(
            status_code=503,
            detail=f"Database health check failed: {str(e)}"
        )

@router.get("/postgres")
async def postgres_health_check(
    db_manager: DatabaseManager = Depends(get_database_manager)
) -> Dict[str, Any]:
    """PostgreSQL-specific health check"""
    start_time = time.time()
    
    try:
        async with db_manager.get_postgres_session() as session:
            from sqlalchemy import text
            result = await session.execute(text("SELECT version(), current_database(), current_user"))
            row = result.fetchone()
            
            response_time = time.time() - start_time
            
            return {
                "status": "healthy",
                "database": "postgresql",
                "timestamp": datetime.utcnow().isoformat(),
                "response_time_ms": round(response_time * 1000, 2),
                "info": {
                    "version": row[0] if row else "unknown",
                    "database": row[1] if row else "unknown",
                    "user": row[2] if row else "unknown"
                }
            }
            
    except Exception as e:
        logger.error("PostgreSQL health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "database": "postgresql",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }

@router.get("/neo4j")
async def neo4j_health_check(
    db_manager: DatabaseManager = Depends(get_database_manager)
) -> Dict[str, Any]:
    """Neo4j-specific health check"""
    start_time = time.time()
    
    try:
        async with db_manager.get_neo4j_session() as session:
            result = await session.run("CALL dbms.components() YIELD name, versions")
            records = await result.data()
            
            response_time = time.time() - start_time
            
            return {
                "status": "healthy",
                "database": "neo4j",
                "timestamp": datetime.utcnow().isoformat(),
                "response_time_ms": round(response_time * 1000, 2),
                "info": {
                    "components": records
                }
            }
            
    except Exception as e:
        logger.error("Neo4j health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "database": "neo4j",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }

@router.get("/qdrant")
async def qdrant_health_check(
    db_manager: DatabaseManager = Depends(get_database_manager)
) -> Dict[str, Any]:
    """Qdrant-specific health check"""
    start_time = time.time()
    
    try:
        import asyncio
        qdrant_client = db_manager.get_qdrant_client()
        
        # Get collections info
        collections = await asyncio.to_thread(qdrant_client.get_collections)
        cluster_info = {"status": "ok"}
        
        response_time = time.time() - start_time
        
        return {
            "status": "healthy",
            "database": "qdrant",
            "timestamp": datetime.utcnow().isoformat(),
            "response_time_ms": round(response_time * 1000, 2),
            "info": {
                "cluster_info": cluster_info,
                "collections_count": len(collections.collections) if collections else 0
            }
        }
        
    except Exception as e:
        logger.error("Qdrant health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "database": "qdrant",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }

@router.get("/redis")
async def redis_health_check(
    db_manager: DatabaseManager = Depends(get_database_manager)
) -> Dict[str, Any]:
    """Redis-specific health check"""
    start_time = time.time()
    
    try:
        redis_client = db_manager.get_redis_client()
        
        # Test connection with ping
        pong = await redis_client.ping()
        
        # Get Redis info
        info = await redis_client.info()
        
        response_time = time.time() - start_time
        
        return {
            "status": "healthy" if pong else "unhealthy",
            "database": "redis",
            "timestamp": datetime.utcnow().isoformat(),
            "response_time_ms": round(response_time * 1000, 2),
            "info": {
                "ping": pong,
                "version": info.get("redis_version", "unknown"),
                "memory_used": info.get("used_memory_human", "unknown"),
                "connected_clients": info.get("connected_clients", 0)
            }
        }
        
    except Exception as e:
        logger.error("Redis health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "database": "redis",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }