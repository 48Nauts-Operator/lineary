# ABOUTME: Database initialization and management service for BETTY Memory System
# ABOUTME: Handles schema creation, migrations, and database operations

import asyncio
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import structlog
from sqlalchemy import text

from core.dependencies import DatabaseDependencies

logger = structlog.get_logger(__name__)

class DatabaseService:
    """Service for database initialization and management operations"""
    
    def __init__(self, databases: DatabaseDependencies):
        self.databases = databases
    
    async def initialize_schema(self) -> Dict[str, Any]:
        """Initialize database schema from SQL files"""
        result = {
            "postgres": {"status": "unknown", "error": None},
            "created_tables": [],
            "created_functions": []
        }
        
        try:
            # Load and execute schema file
            schema_path = Path(__file__).parent.parent / "database" / "schema.sql"
            
            if not schema_path.exists():
                raise FileNotFoundError(f"Schema file not found: {schema_path}")
            
            with open(schema_path, 'r') as f:
                schema_sql = f.read()
            
            # Execute schema creation using the injected session
            session = self.databases.postgres
            
            # Split schema into individual statements
            statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
            
            created_tables = []
            created_functions = []
            
            for statement in statements:
                if statement:
                    try:
                        await session.execute(text(statement))
                        
                        # Track what was created
                        if 'CREATE TABLE' in statement.upper():
                            table_name = self._extract_table_name(statement)
                            if table_name:
                                created_tables.append(table_name)
                        elif 'CREATE FUNCTION' in statement.upper() or 'CREATE OR REPLACE FUNCTION' in statement.upper():
                            function_name = self._extract_function_name(statement)
                            if function_name:
                                created_functions.append(function_name)
                        
                    except Exception as e:
                        # Log individual statement errors but continue
                        logger.warning(
                            "Failed to execute schema statement",
                            statement_preview=statement[:100],
                            error=str(e)
                        )
            
            # Note: Session commit handled by dependency injection context
            
            result["postgres"]["status"] = "initialized"
            result["created_tables"] = created_tables
            result["created_functions"] = created_functions
            
            logger.info(
                "Database schema initialized successfully",
                tables_created=len(created_tables),
                functions_created=len(created_functions)
            )
        
        except Exception as e:
            result["postgres"]["status"] = "failed"
            result["postgres"]["error"] = str(e)
            logger.error("Failed to initialize database schema", error=str(e))
        
        return result
    
    async def verify_schema(self) -> Dict[str, Any]:
        """Verify that all required tables and functions exist"""
        required_tables = [
            'batch_ingestion_status',
            'claude_sessions',
            'knowledge_ingestion_logs',
            'project_knowledge_stats',
            'tool_usage_patterns',
            'decision_impacts',
            'solution_effectiveness',
            'conversation_contexts',
            'code_change_impacts'
        ]
        
        required_functions = [
            'increment_project_stats',
            'update_tool_usage_pattern'
        ]
        
        result = {
            "tables": {},
            "functions": {},
            "all_verified": True
        }
        
        try:
            session = self.databases.postgres
            
            # Check tables
            for table in required_tables:
                query = text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = :table_name
                    )
                """)
                
                exists = await session.execute(query, {"table_name": table})
                table_exists = exists.scalar()
                
                result["tables"][table] = table_exists
                if not table_exists:
                    result["all_verified"] = False
            
            # Check functions
            for function in required_functions:
                query = text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.routines 
                        WHERE routine_schema = 'public' 
                        AND routine_name = :function_name
                    )
                """)
                
                exists = await session.execute(query, {"function_name": function})
                function_exists = exists.scalar()
                
                result["functions"][function] = function_exists
                if not function_exists:
                    result["all_verified"] = False
        
        except Exception as e:
            logger.error("Failed to verify database schema", error=str(e))
            result["all_verified"] = False
            result["error"] = str(e)
        
        return result
    
    async def get_database_info(self) -> Dict[str, Any]:
        """Get comprehensive database information"""
        info = {
            "postgres": {"status": "unknown", "tables": [], "size": None},
            "neo4j": {"status": "unknown", "nodes": 0, "relationships": 0},
            "qdrant": {"status": "unknown", "collections": []},
            "redis": {"status": "unknown", "keys": 0}
        }
        
        # PostgreSQL info
        try:
            session = self.databases.postgres
            
            # Get table list
            tables_query = text("""
                SELECT table_name, 
                       pg_total_relation_size(quote_ident(table_name)::regclass) as size_bytes
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            
            tables_result = await session.execute(tables_query)
            tables = []
            total_size = 0
            
            for row in tables_result:
                table_info = {
                    "name": row.table_name,
                    "size_bytes": row.size_bytes or 0
                }
                tables.append(table_info)
                total_size += row.size_bytes or 0
            
            info["postgres"]["status"] = "healthy"
            info["postgres"]["tables"] = tables
            info["postgres"]["total_size_bytes"] = total_size
            
        except Exception as e:
            info["postgres"]["status"] = "error"
            info["postgres"]["error"] = str(e)
        
        # Neo4j info
        try:
            session = self.databases.neo4j
            
            # Get node and relationship counts
            node_result = await session.run("MATCH (n) RETURN count(n) as node_count")
            node_count = await node_result.single()
            
            rel_result = await session.run("MATCH ()-[r]->() RETURN count(r) as rel_count")
            rel_count = await rel_result.single()
            
            info["neo4j"]["status"] = "healthy"
            info["neo4j"]["nodes"] = node_count["node_count"] if node_count else 0
            info["neo4j"]["relationships"] = rel_count["rel_count"] if rel_count else 0
            
        except Exception as e:
            info["neo4j"]["status"] = "error"
            info["neo4j"]["error"] = str(e)
        
        # Qdrant info
        try:
            qdrant_client = self.databases.qdrant
            collections = await asyncio.to_thread(qdrant_client.get_collections)
            
            collection_info = []
            for collection in collections.collections:
                try:
                    collection_details = await asyncio.to_thread(
                        qdrant_client.get_collection, collection.name
                    )
                    collection_info.append({
                        "name": collection.name,
                        "vectors_count": collection_details.vectors_count if hasattr(collection_details, 'vectors_count') else 0
                    })
                except Exception as e:
                    collection_info.append({
                        "name": collection.name,
                        "vectors_count": 0,
                        "error": str(e)
                    })
            
            info["qdrant"]["status"] = "healthy"
            info["qdrant"]["collections"] = collection_info
            
        except Exception as e:
            info["qdrant"]["status"] = "error"
            info["qdrant"]["error"] = str(e)
        
        # Redis info
        try:
            redis_client = self.databases.redis
            db_info = await redis_client.info()
            
            info["redis"]["status"] = "healthy"
            info["redis"]["keys"] = db_info.get("db0", {}).get("keys", 0)
            info["redis"]["memory_used"] = db_info.get("used_memory", 0)
            
        except Exception as e:
            info["redis"]["status"] = "error"
            info["redis"]["error"] = str(e)
        
        return info
    
    def _extract_table_name(self, statement: str) -> Optional[str]:
        """Extract table name from CREATE TABLE statement"""
        try:
            statement_upper = statement.upper()
            if 'CREATE TABLE' in statement_upper:
                # Find table name after CREATE TABLE or CREATE TABLE IF NOT EXISTS
                parts = statement.split()
                table_idx = -1
                
                for i, part in enumerate(parts):
                    if part.upper() == 'TABLE':
                        table_idx = i
                        break
                
                if table_idx != -1:
                    # Skip IF NOT EXISTS if present
                    next_idx = table_idx + 1
                    while next_idx < len(parts) and parts[next_idx].upper() in ['IF', 'NOT', 'EXISTS']:
                        next_idx += 1
                    
                    if next_idx < len(parts):
                        table_name = parts[next_idx].strip('();')
                        return table_name
        except Exception:
            pass
        return None
    
    def _extract_function_name(self, statement: str) -> Optional[str]:
        """Extract function name from CREATE FUNCTION statement"""
        try:
            statement_upper = statement.upper()
            if 'FUNCTION' in statement_upper:
                # Find function name after FUNCTION keyword
                parts = statement.split()
                function_idx = -1
                
                for i, part in enumerate(parts):
                    if part.upper() == 'FUNCTION':
                        function_idx = i
                        break
                
                if function_idx != -1 and function_idx + 1 < len(parts):
                    function_name = parts[function_idx + 1].split('(')[0].strip()
                    return function_name
        except Exception:
            pass
        return None
    
    async def log_ingestion_operation(
        self,
        session_id: Optional[str],
        batch_id: Optional[str],
        project_id: str,
        user_id: str,
        ingestion_type: str,
        knowledge_item_id: Optional[str],
        success: bool,
        processing_time_ms: Optional[float] = None,
        entities_extracted: int = 0,
        relationships_created: int = 0,
        embeddings_generated: int = 0,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Log an ingestion operation to the database"""
        try:
            session = self.databases.postgres
            
            query = text("""
                INSERT INTO knowledge_ingestion_logs (
                    session_id, batch_id, project_id, user_id, ingestion_type,
                    knowledge_item_id, success, processing_time_ms,
                    entities_extracted, relationships_created, embeddings_generated,
                    error_message, metadata
                ) VALUES (
                    :session_id, :batch_id, :project_id, :user_id, :ingestion_type,
                    :knowledge_item_id, :success, :processing_time_ms,
                    :entities_extracted, :relationships_created, :embeddings_generated,
                    :error_message, :metadata
                )
            """)
            
            await session.execute(query, {
                "session_id": session_id,
                "batch_id": batch_id,
                "project_id": project_id,
                "user_id": user_id,
                "ingestion_type": ingestion_type,
                "knowledge_item_id": knowledge_item_id,
                "success": success,
                "processing_time_ms": processing_time_ms,
                "entities_extracted": entities_extracted,
                "relationships_created": relationships_created,
                "embeddings_generated": embeddings_generated,
                "error_message": error_message,
                "metadata": json.dumps(metadata) if metadata else None
            })
            
            return True
            
        except Exception as e:
            logger.error(
                "Failed to log ingestion operation",
                session_id=session_id,
                ingestion_type=ingestion_type,
                error=str(e)
            )
            return False
    
    async def update_project_statistics(
        self,
        project_id: str,
        ingestion_type: str,
        entities_count: int = 0,
        relationships_count: int = 0,
        processing_time_ms: float = 0
    ) -> bool:
        """Update project statistics using database function"""
        try:
            session = self.databases.postgres
            
            query = text("""
                SELECT increment_project_stats(
                    :project_id,
                    :ingestion_type,
                    :entities_count,
                    :relationships_count,
                    :processing_time_ms
                )
            """)
            
            await session.execute(query, {
                "project_id": project_id,
                "ingestion_type": ingestion_type,
                "entities_count": entities_count,
                "relationships_count": relationships_count,
                "processing_time_ms": processing_time_ms
            })
            
            return True
            
        except Exception as e:
            logger.error(
                "Failed to update project statistics",
                project_id=project_id,
                ingestion_type=ingestion_type,
                error=str(e)
            )
            return False
    
    async def update_tool_usage_statistics(
        self,
        project_id: str,
        tool_name: str,
        success: bool,
        execution_time_ms: Optional[float] = None,
        parameters: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update tool usage statistics using database function"""
        try:
            session = self.databases.postgres
            
            query = text("""
                SELECT update_tool_usage_pattern(
                    :project_id,
                    :tool_name,
                    :success,
                    :execution_time_ms,
                    :parameters,
                    :context
                )
            """)
            
            await session.execute(query, {
                "project_id": project_id,
                "tool_name": tool_name,
                "success": success,
                "execution_time_ms": execution_time_ms,
                "parameters": json.dumps(parameters) if parameters else '{}',
                "context": json.dumps(context) if context else '{}'
            })
            
            return True
            
        except Exception as e:
            logger.error(
                "Failed to update tool usage statistics",
                project_id=project_id,
                tool_name=tool_name,
                error=str(e)
            )
            return False