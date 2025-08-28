# ABOUTME: Database management API endpoints for BETTY Memory System
# ABOUTME: Schema initialization, verification, and database information endpoints

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
import structlog

from core.dependencies import DatabaseDependencies, get_all_databases
from core.security import get_current_user
from services.database_service import DatabaseService

logger = structlog.get_logger(__name__)
router = APIRouter()

@router.post("/initialize-schema")
async def initialize_database_schema(
    databases: DatabaseDependencies = Depends(get_all_databases),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Initialize database schema with all required tables and functions"""
    try:
        database_service = DatabaseService(databases)
        result = await database_service.initialize_schema()
        
        if result["postgres"]["status"] == "failed":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Schema initialization failed: {result['postgres']['error']}"
            )
        
        logger.info(
            "Database schema initialized via API",
            tables_created=len(result["created_tables"]),
            functions_created=len(result["created_functions"])
        )
        
        return {
            "message": "Database schema initialized successfully",
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to initialize database schema via API", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize schema: {str(e)}"
        )

@router.get("/verify-schema")
async def verify_database_schema(
    databases: DatabaseDependencies = Depends(get_all_databases),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Verify that all required database tables and functions exist"""
    try:
        database_service = DatabaseService(databases)
        result = await database_service.verify_schema()
        
        logger.info(
            "Database schema verification completed",
            all_verified=result["all_verified"]
        )
        
        return {
            "message": "Schema verification completed",
            "data": result
        }
        
    except Exception as e:
        logger.error("Failed to verify database schema", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to verify schema: {str(e)}"
        )

@router.get("/info")
async def get_database_info(
    databases: DatabaseDependencies = Depends(get_all_databases),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get comprehensive database information and statistics"""
    try:
        database_service = DatabaseService(databases)
        info = await database_service.get_database_info()
        
        logger.info("Database information retrieved")
        
        return {
            "message": "Database information retrieved successfully",
            "data": info
        }
        
    except Exception as e:
        logger.error("Failed to get database information", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get database info: {str(e)}"
        )

@router.get("/health/detailed")
async def get_detailed_health_check(
    databases: DatabaseDependencies = Depends(get_all_databases),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get detailed health check including schema verification"""
    try:
        # Get basic health check
        health_status = await databases.health_check()
        
        # Add schema verification
        database_service = DatabaseService(databases)
        schema_status = await database_service.verify_schema()
        
        # Combine results
        detailed_health = {
            "connections": health_status,
            "schema": {
                "verified": schema_status["all_verified"],
                "tables": schema_status["tables"],
                "functions": schema_status["functions"]
            },
            "overall_status": "healthy" if all(
                db["status"] == "healthy" for db in health_status.values()
            ) and schema_status["all_verified"] else "degraded"
        }
        
        logger.info(
            "Detailed health check completed",
            overall_status=detailed_health["overall_status"]
        )
        
        return {
            "message": "Detailed health check completed",
            "data": detailed_health
        }
        
    except Exception as e:
        logger.error("Failed to perform detailed health check", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform health check: {str(e)}"
        )

@router.get("/stats/ingestion")
async def get_ingestion_statistics(
    project_id: str = None,
    days: int = 7,
    databases: DatabaseDependencies = Depends(get_all_databases),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get detailed ingestion statistics from the database"""
    try:
        database_service = DatabaseService(databases)
        
        # Get ingestion logs statistics  
        session = databases.postgres
        from sqlalchemy import text
        
        base_query = """
        SELECT 
            ingestion_type,
            COUNT(*) as total_operations,
            SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_operations,
            SUM(CASE WHEN success THEN 0 ELSE 1 END) as failed_operations,
            AVG(processing_time_ms) as avg_processing_time_ms,
            SUM(entities_extracted) as total_entities_extracted,
            SUM(relationships_created) as total_relationships_created,
            SUM(embeddings_generated) as total_embeddings_generated
        FROM knowledge_ingestion_logs
        WHERE created_at >= NOW() - INTERVAL '%s days'
        """ % days
        
        params = []
        if project_id:
            base_query += " AND project_id = $1"
            params.append(project_id)
        
        base_query += " GROUP BY ingestion_type ORDER BY total_operations DESC"
        
        result = await session.execute(text(base_query), params)
        ingestion_stats = [dict(row) for row in result]
        
        # Get project statistics
        project_query = """
        SELECT 
            project_id,
            total_knowledge_items,
            total_conversations,
            total_code_changes,
            total_decisions,
            total_problem_solutions,
            total_tool_usages,
            total_entities,
            total_relationships,
            avg_processing_time_ms,
            last_activity_at
        FROM project_knowledge_stats
        """
        
        if project_id:
            project_query += " WHERE project_id = $1"
            project_result = await session.execute(text(project_query), [project_id])
        else:
            project_result = await session.execute(text(project_query))
        
        project_stats = [dict(row) for row in project_result]
        
        # Get tool usage patterns
        tool_query = """
        SELECT 
            tool_name,
            usage_count,
            success_count,
            failure_count,
            avg_execution_time_ms,
            last_used_at
        FROM tool_usage_patterns
        """
        
        if project_id:
            tool_query += " WHERE project_id = $1"
            tool_result = await session.execute(text(tool_query), [project_id])
        else:
            tool_result = await session.execute(text(tool_query))
        
        tool_stats = [dict(row) for row in tool_result]
        
        statistics = {
            "ingestion_operations": ingestion_stats,
            "project_statistics": project_stats,
            "tool_usage_patterns": tool_stats,
            "query_parameters": {
                "project_id": project_id,
                "days": days
            }
        }
        
        logger.info(
            "Ingestion statistics retrieved",
            project_id=project_id,
            days=days,
            operations_count=len(ingestion_stats)
        )
        
        return {
            "message": "Ingestion statistics retrieved successfully",
            "data": statistics
        }
        
    except Exception as e:
        logger.error("Failed to get ingestion statistics", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get ingestion statistics: {str(e)}"
        )