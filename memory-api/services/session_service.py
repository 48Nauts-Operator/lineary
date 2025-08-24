# ABOUTME: Session service for BETTY Memory System
# ABOUTME: Business logic for chat session and message management

from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID, uuid4
import json
import structlog
from sqlalchemy import select, update, delete, func, text, or_, and_

from models.session import (
    Session,
    SessionCreate,
    SessionUpdate,
    Message,
    MessageCreate,
    MessageUpdate,
    SessionStats,
    SessionSearchQuery,
    MessageSearchQuery,
    ContextRequest
)
from models.base import PaginationParams
from services.base_service import BaseService
from services.vector_service import VectorService

logger = structlog.get_logger(__name__)

class SessionService(BaseService):
    """Service for session and message operations"""
    
    def __init__(self, databases):
        super().__init__(databases)
        self.vector_service = VectorService(databases)
    
    async def create_session(self, session_data: SessionCreate) -> Session:
        """Create a new chat session"""
        try:
            session_id = uuid4()
            
            # Create database record
            stmt = text("""
                INSERT INTO sessions (
                    id, title, description, status, tags, user_id, project_id,
                    parent_session_id, metadata, created_at, updated_at
                ) VALUES (
                    :id, :title, :description, :status, :tags, :user_id, :project_id,
                    :parent_session_id, :metadata, :created_at, :updated_at
                )
                RETURNING *
            """)
            
            now = datetime.utcnow()
            result = await self.postgres.execute(stmt, {
                "id": session_id,
                "title": session_data.title,
                "description": session_data.description,
                "status": session_data.status.value if hasattr(session_data.status, 'value') else session_data.status,
                "tags": json.dumps(session_data.tags) if session_data.tags else json.dumps([]),
                "user_id": session_data.user_id,
                "project_id": session_data.project_id,
                "parent_session_id": session_data.parent_session_id,
                "metadata": json.dumps(session_data.metadata) if session_data.metadata else json.dumps({}),
                "created_at": now,
                "updated_at": now
            })
            
            await self.postgres.commit()
            row = result.fetchone()
            
            # Create session node in Neo4j
            try:
                await self._create_session_graph_node(session_id, session_data)
            except Exception as e:
                logger.warning("Failed to create session graph node", error=str(e))
            
            # Invalidate cache
            await self.invalidate_related_cache("sessions:*")
            
            await self.log_operation("create_session", "sessions", str(session_id))
            
            return Session(
                id=row.id,
                title=row.title,
                description=row.description,
                status=row.status,
                tags=row.tags or [],
                user_id=row.user_id,
                project_id=row.project_id,
                parent_session_id=row.parent_session_id,
                metadata=row.metadata or {},
                created_at=row.created_at,
                updated_at=row.updated_at,
                message_count=0,
                token_count=0,
                access_count=0
            )
            
        except Exception as e:
            logger.error("Failed to create session", error=str(e))
            raise
    
    async def _create_session_graph_node(
        self,
        session_id: UUID,
        session_data: SessionCreate
    ) -> None:
        """Create session node in Neo4j graph"""
        query = """
        CREATE (s:Session {
            id: $id,
            title: $title,
            status: $status,
            created_at: datetime($created_at)
        })
        """
        
        await self.neo4j.run(query, {
            "id": str(session_id),
            "title": session_data.title,
            "status": session_data.status,
            "created_at": datetime.utcnow().isoformat()
        })
        
        # Create relationship to parent session if exists
        if session_data.parent_session_id:
            parent_rel_query = """
            MATCH (child:Session {id: $child_id})
            MATCH (parent:Session {id: $parent_id})
            CREATE (child)-[:BRANCHES_FROM {created_at: datetime()}]->(parent)
            """
            
            await self.neo4j.run(parent_rel_query, {
                "child_id": str(session_id),
                "parent_id": str(session_data.parent_session_id)
            })
    
    async def get_session(self, session_id: UUID) -> Optional[Session]:
        """Get session by ID"""
        cache_key = self.generate_cache_key("sessions", "session", str(session_id))
        
        async def fetch_session():
            stmt = text("""
                SELECT s.*, 
                       COALESCE(m.message_count, 0) as message_count,
                       COALESCE(m.token_count, 0) as token_count,
                       COALESCE(m.last_message_at, s.created_at) as last_message_at
                FROM sessions s
                LEFT JOIN (
                    SELECT session_id,
                           COUNT(*) as message_count,
                           SUM(COALESCE(token_count, 0)) as token_count,
                           MAX(created_at) as last_message_at
                    FROM messages 
                    WHERE deleted_at IS NULL
                    GROUP BY session_id
                ) m ON s.id = m.session_id
                WHERE s.id = :id AND s.deleted_at IS NULL
            """)
            
            result = await self.postgres.execute(stmt, {"id": session_id})
            row = result.fetchone()
            
            if not row:
                return None
            
            return Session(
                id=row.id,
                title=row.title,
                description=row.description,
                status=row.status,
                tags=row.tags or [],
                user_id=row.user_id,
                project_id=row.project_id,
                parent_session_id=row.parent_session_id,
                metadata=row.metadata or {},
                created_at=row.created_at,
                updated_at=row.updated_at,
                message_count=row.message_count,
                token_count=row.token_count,
                last_message_at=row.last_message_at,
                access_count=row.access_count or 0,
                last_accessed_at=row.last_accessed_at
            )
        
        return await self.execute_with_cache(cache_key, fetch_session)
    
    async def update_session(
        self,
        session_id: UUID,
        updates: SessionUpdate
    ) -> Optional[Session]:
        """Update session"""
        try:
            # Build update statement
            update_fields = []
            params = {"id": session_id, "updated_at": datetime.utcnow()}
            
            if updates.title is not None:
                update_fields.append("title = :title")
                params["title"] = updates.title
            
            if updates.description is not None:
                update_fields.append("description = :description")
                params["description"] = updates.description
            
            if updates.status is not None:
                update_fields.append("status = :status")
                params["status"] = updates.status
            
            if updates.tags is not None:
                update_fields.append("tags = :tags")
                params["tags"] = updates.tags
            
            if updates.metadata is not None:
                update_fields.append("metadata = :metadata")
                params["metadata"] = updates.metadata
            
            if not update_fields:
                return await self.get_session(session_id)
            
            stmt = text(f"""
                UPDATE sessions 
                SET {', '.join(update_fields)}, updated_at = :updated_at
                WHERE id = :id AND deleted_at IS NULL
                RETURNING *
            """)
            
            result = await self.postgres.execute(stmt, params)
            await self.postgres.commit()
            
            row = result.fetchone()
            if not row:
                return None
            
            # Invalidate cache
            await self.cache_delete(self.generate_cache_key("sessions", "session", str(session_id)))
            await self.invalidate_related_cache("sessions:*")
            
            await self.log_operation("update_session", "sessions", str(session_id))
            
            return await self.get_session(session_id)
            
        except Exception as e:
            logger.error("Failed to update session", session_id=str(session_id), error=str(e))
            raise
    
    async def delete_session(self, session_id: UUID) -> bool:
        """Delete session and all its messages (soft delete)"""
        try:
            # Soft delete session
            session_stmt = text("""
                UPDATE sessions 
                SET deleted_at = :deleted_at, updated_at = :updated_at
                WHERE id = :id AND deleted_at IS NULL
            """)
            
            now = datetime.utcnow()
            session_result = await self.postgres.execute(session_stmt, {
                "deleted_at": now,
                "updated_at": now,
                "id": session_id
            })
            
            if session_result.rowcount == 0:
                return False
            
            # Soft delete all messages in the session
            messages_stmt = text("""
                UPDATE messages 
                SET deleted_at = :deleted_at, updated_at = :updated_at
                WHERE session_id = :session_id AND deleted_at IS NULL
            """)
            
            await self.postgres.execute(messages_stmt, {
                "deleted_at": now,
                "updated_at": now,
                "session_id": session_id
            })
            
            await self.postgres.commit()
            
            # Delete graph relationships
            try:
                delete_graph_query = """
                MATCH (s:Session {id: $session_id})
                DETACH DELETE s
                """
                await self.neo4j.run(delete_graph_query, {"session_id": str(session_id)})
            except Exception as e:
                logger.warning("Failed to delete session graph relationships", error=str(e))
            
            # Invalidate cache
            await self.cache_delete(self.generate_cache_key("sessions", "session", str(session_id)))
            await self.invalidate_related_cache("sessions:*")
            
            await self.log_operation("delete_session", "sessions", str(session_id))
            
            return True
            
        except Exception as e:
            logger.error("Failed to delete session", session_id=str(session_id), error=str(e))
            raise
    
    async def update_access_tracking(self, session_id: UUID) -> None:
        """Update access tracking for session"""
        try:
            stmt = text("""
                UPDATE sessions 
                SET access_count = COALESCE(access_count, 0) + 1,
                    last_accessed_at = :accessed_at,
                    updated_at = :updated_at
                WHERE id = :id AND deleted_at IS NULL
            """)
            
            await self.postgres.execute(stmt, {
                "accessed_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "id": session_id
            })
            await self.postgres.commit()
            
        except Exception as e:
            logger.warning("Failed to update session access tracking", session_id=str(session_id), error=str(e))
    
    async def list_sessions(
        self,
        pagination: PaginationParams,
        filters: Dict[str, Any] = None
    ) -> Tuple[List[Session], int]:
        """List sessions with filtering and pagination"""
        try:
            # Build WHERE conditions
            where_conditions = ["deleted_at IS NULL"]
            params = {
                "limit": pagination.limit,
                "offset": pagination.offset
            }
            
            if filters:
                if filters.get("status"):
                    where_conditions.append("status = :status")
                    params["status"] = filters["status"]
                
                if filters.get("user_id"):
                    where_conditions.append("user_id = :user_id")
                    params["user_id"] = filters["user_id"]
                
                if filters.get("project_id"):
                    where_conditions.append("project_id = :project_id")
                    params["project_id"] = filters["project_id"]
                
                if filters.get("tags"):
                    where_conditions.append("tags && :tags")
                    params["tags"] = filters["tags"]
            
            where_clause = " AND ".join(where_conditions)
            
            # Get total count
            count_stmt = text(f"""
                SELECT COUNT(*) FROM sessions 
                WHERE {where_clause}
            """)
            
            count_result = await self.postgres.execute(count_stmt, params)
            total_count = count_result.scalar()
            
            # Get sessions with message stats
            stmt = text(f"""
                SELECT s.*, 
                       COALESCE(m.message_count, 0) as message_count,
                       COALESCE(m.token_count, 0) as token_count,
                       COALESCE(m.last_message_at, s.created_at) as last_message_at
                FROM sessions s
                LEFT JOIN (
                    SELECT session_id,
                           COUNT(*) as message_count,
                           SUM(COALESCE(token_count, 0)) as token_count,
                           MAX(created_at) as last_message_at
                    FROM messages 
                    WHERE deleted_at IS NULL
                    GROUP BY session_id
                ) m ON s.id = m.session_id
                WHERE {where_clause}
                ORDER BY s.updated_at DESC
                LIMIT :limit OFFSET :offset
            """)
            
            result = await self.postgres.execute(stmt, params)
            rows = result.fetchall()
            
            sessions = []
            for row in rows:
                session = Session(
                    id=row.id,
                    title=row.title,
                    description=row.description,
                    status=row.status,
                    tags=row.tags or [],
                    user_id=row.user_id,
                    project_id=row.project_id,
                    parent_session_id=row.parent_session_id,
                    metadata=row.metadata or {},
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                    message_count=row.message_count,
                    token_count=row.token_count,
                    last_message_at=row.last_message_at,
                    access_count=row.access_count or 0,
                    last_accessed_at=row.last_accessed_at
                )
                sessions.append(session)
            
            return sessions, total_count
            
        except Exception as e:
            logger.error("Failed to list sessions", error=str(e))
            raise
    
    async def create_message(self, message_data: MessageCreate) -> Message:
        """Create a new message in a session"""
        try:
            message_id = uuid4()
            
            # Calculate token count (simple approximation)
            token_count = len(message_data.content.split()) * 1.3  # Rough approximation
            
            # Get the next message index for this session
            index_stmt = text("SELECT COALESCE(MAX(message_index), -1) + 1 FROM messages WHERE session_id = :session_id")
            index_result = await self.postgres.execute(index_stmt, {"session_id": message_data.session_id})
            message_index = index_result.scalar() or 0
            
            stmt = text("""
                INSERT INTO messages (
                    id, session_id, content, role, message_type, function_name,
                    function_args, attachments, parent_message_id, context_window,
                    prompt_tokens, completion_tokens, token_count, message_index, metadata,
                    created_at, updated_at
                ) VALUES (
                    :id, :session_id, :content, :role, :message_type, :function_name,
                    :function_args, :attachments, :parent_message_id, :context_window,
                    :prompt_tokens, :completion_tokens, :token_count, :message_index, :metadata,
                    :created_at, :updated_at
                )
                RETURNING *
            """)
            
            now = datetime.utcnow()
            result = await self.postgres.execute(stmt, {
                "id": message_id,
                "session_id": message_data.session_id,
                "content": message_data.content,
                "role": message_data.role.value if hasattr(message_data.role, 'value') else message_data.role,
                "message_type": message_data.message_type.value if hasattr(message_data.message_type, 'value') else message_data.message_type,
                "function_name": message_data.function_name,
                "function_args": json.dumps(message_data.function_args) if message_data.function_args else None,
                "attachments": json.dumps(message_data.attachments) if message_data.attachments else json.dumps([]),
                "parent_message_id": message_data.parent_message_id,
                "context_window": json.dumps(message_data.context_window) if message_data.context_window else json.dumps([]),
                "prompt_tokens": message_data.prompt_tokens,
                "completion_tokens": message_data.completion_tokens,
                "token_count": int(token_count),
                "message_index": message_index,
                "metadata": json.dumps(message_data.metadata) if message_data.metadata else json.dumps({}),
                "created_at": now,
                "updated_at": now
            })
            
            await self.postgres.commit()
            row = result.fetchone()
            
            # Update session last_message_at
            await self._update_session_last_message(message_data.session_id, now)
            
            # Create vector embedding for searchable messages
            if message_data.role in ["user", "assistant"] and len(message_data.content) > 50:
                try:
                    embedding_id = await self.vector_service.create_embedding(
                        item_id=str(message_id),
                        content=message_data.content,
                        metadata={
                            "session_id": str(message_data.session_id),
                            "role": message_data.role,
                            "message_type": message_data.message_type
                        },
                        collection_name="messages"
                    )
                    
                    # Update message with embedding_id
                    await self._update_message_embedding_id(message_id, embedding_id)
                    
                except Exception as e:
                    logger.warning("Failed to create message embedding", error=str(e))
            
            # Invalidate cache
            await self.invalidate_related_cache("sessions:*")
            
            await self.log_operation("create_message", "messages", str(message_id))
            
            return Message(
                id=row.id,
                session_id=row.session_id,
                content=row.content,
                role=row.role,
                message_type=row.message_type,
                function_name=row.function_name,
                function_args=row.function_args,
                attachments=row.attachments or [],
                parent_message_id=row.parent_message_id,
                context_window=row.context_window or [],
                prompt_tokens=row.prompt_tokens,
                completion_tokens=row.completion_tokens,
                token_count=row.token_count,
                metadata=row.metadata or {},
                created_at=row.created_at,
                updated_at=row.updated_at,
                children_count=0
            )
            
        except Exception as e:
            logger.error("Failed to create message", error=str(e))
            raise
    
    async def _update_session_last_message(self, session_id: UUID, timestamp: datetime) -> None:
        """Update session's last message timestamp"""
        stmt = text("""
            UPDATE sessions 
            SET last_message_at = :timestamp, updated_at = :timestamp
            WHERE id = :session_id
        """)
        
        await self.postgres.execute(stmt, {
            "timestamp": timestamp,
            "session_id": session_id
        })
        await self.postgres.commit()
    
    async def _update_message_embedding_id(self, message_id: UUID, embedding_id: str) -> None:
        """Update message embedding_id in database"""
        stmt = text("""
            UPDATE messages 
            SET embedding_id = :embedding_id, updated_at = :updated_at
            WHERE id = :id
        """)
        
        await self.postgres.execute(stmt, {
            "embedding_id": embedding_id,
            "updated_at": datetime.utcnow(),
            "id": message_id
        })
        await self.postgres.commit()
    
    async def get_session_messages(
        self,
        session_id: UUID,
        pagination: PaginationParams,
        include_context: bool = False
    ) -> Tuple[List[Message], int]:
        """Get messages for a session"""
        try:
            # Get total count
            count_stmt = text("""
                SELECT COUNT(*) FROM messages 
                WHERE session_id = :session_id AND deleted_at IS NULL
            """)
            
            count_result = await self.postgres.execute(count_stmt, {"session_id": session_id})
            total_count = count_result.scalar()
            
            # Get messages
            stmt = text("""
                SELECT * FROM messages 
                WHERE session_id = :session_id AND deleted_at IS NULL
                ORDER BY created_at ASC
                LIMIT :limit OFFSET :offset
            """)
            
            result = await self.postgres.execute(stmt, {
                "session_id": session_id,
                "limit": pagination.limit,
                "offset": pagination.offset
            })
            
            rows = result.fetchall()
            
            messages = []
            for row in rows:
                # Get children count if needed
                children_count = 0
                if include_context:
                    children_count = await self._get_message_children_count(row.id)
                
                message = Message(
                    id=row.id,
                    session_id=row.session_id,
                    content=row.content,
                    role=row.role,
                    message_type=row.message_type,
                    function_name=row.function_name,
                    function_args=row.function_args,
                    attachments=row.attachments or [],
                    parent_message_id=row.parent_message_id,
                    context_window=row.context_window or [],
                    prompt_tokens=row.prompt_tokens,
                    completion_tokens=row.completion_tokens,
                    token_count=row.token_count,
                    metadata=row.metadata or {},
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                    embedding_id=row.embedding_id,
                    children_count=children_count
                )
                messages.append(message)
            
            return messages, total_count
            
        except Exception as e:
            logger.error("Failed to get session messages", session_id=str(session_id), error=str(e))
            raise
    
    async def _get_message_children_count(self, message_id: UUID) -> int:
        """Get count of child messages"""
        stmt = text("""
            SELECT COUNT(*) FROM messages 
            WHERE parent_message_id = :parent_id AND deleted_at IS NULL
        """)
        
        result = await self.postgres.execute(stmt, {"parent_id": message_id})
        return result.scalar() or 0
    
    async def get_conversation(self, session_id: UUID, include_stats: bool = True) -> Dict[str, Any]:
        """Get complete conversation for a session"""
        try:
            # Get session
            session = await self.get_session(session_id)
            if not session:
                return {"session": None, "messages": [], "total_messages": 0, "total_tokens": 0}
            
            # Get all messages
            stmt = text("""
                SELECT * FROM messages 
                WHERE session_id = :session_id AND deleted_at IS NULL
                ORDER BY created_at ASC
            """)
            
            result = await self.postgres.execute(stmt, {"session_id": session_id})
            rows = result.fetchall()
            
            messages = []
            total_tokens = 0
            
            for row in rows:
                message = Message(
                    id=row.id,
                    session_id=row.session_id,
                    content=row.content,
                    role=row.role,
                    message_type=row.message_type,
                    function_name=row.function_name,
                    function_args=row.function_args,
                    attachments=row.attachments or [],
                    parent_message_id=row.parent_message_id,
                    context_window=row.context_window or [],
                    prompt_tokens=row.prompt_tokens,
                    completion_tokens=row.completion_tokens,
                    token_count=row.token_count or 0,
                    metadata=row.metadata or {},
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                    embedding_id=row.embedding_id,
                    children_count=0
                )
                messages.append(message)
                total_tokens += message.token_count
            
            return {
                "session": session,
                "messages": messages,
                "total_messages": len(messages),
                "total_tokens": total_tokens
            }
            
        except Exception as e:
            logger.error("Failed to get conversation", session_id=str(session_id), error=str(e))
            raise
    
    async def build_context(self, request: ContextRequest) -> Dict[str, Any]:
        """Build conversation context for AI processing"""
        try:
            # Get recent messages within token limit
            messages = []
            total_tokens = 0
            truncated = False
            
            # Get messages in reverse chronological order
            stmt = text("""
                SELECT * FROM messages 
                WHERE session_id = :session_id AND deleted_at IS NULL
                ORDER BY created_at DESC
                LIMIT :message_limit
            """)
            
            result = await self.postgres.execute(stmt, {
                "session_id": request.session_id,
                "message_limit": request.message_limit
            })
            
            rows = result.fetchall()
            
            # Build context within token limit
            for row in reversed(rows):  # Reverse to get chronological order
                message_tokens = row.token_count or 0
                
                # Check token limit
                if total_tokens + message_tokens > request.token_limit:
                    truncated = True
                    break
                
                # Skip system messages if not requested
                if row.role == "system" and not request.include_system:
                    continue
                
                message = Message(
                    id=row.id,
                    session_id=row.session_id,
                    content=row.content,
                    role=row.role,
                    message_type=row.message_type,
                    function_name=row.function_name,
                    function_args=row.function_args,
                    attachments=row.attachments or [],
                    parent_message_id=row.parent_message_id,
                    context_window=row.context_window or [],
                    prompt_tokens=row.prompt_tokens,
                    completion_tokens=row.completion_tokens,
                    token_count=row.token_count or 0,
                    metadata=row.metadata or {},
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                    embedding_id=row.embedding_id,
                    children_count=0
                )
                
                messages.append(message)
                total_tokens += message_tokens
            
            return {
                "messages": messages,
                "total_tokens": total_tokens,
                "truncated": truncated,
                "relevance_scores": None  # Could implement relevance scoring
            }
            
        except Exception as e:
            logger.error("Failed to build context", session_id=str(request.session_id), error=str(e))
            raise
    
    async def get_session_stats(self, user_id: str = None) -> SessionStats:
        """Get session statistics"""
        cache_key = f"sessions:stats:{user_id or 'all'}"
        
        async def fetch_stats():
            # Base WHERE condition
            user_filter = "user_id = :user_id AND" if user_id else ""
            params = {"user_id": user_id} if user_id else {}
            
            # Get basic session stats
            session_stats = await self.postgres.execute(text(f"""
                SELECT 
                    COUNT(*) as total_sessions,
                    COUNT(CASE WHEN status = 'active' THEN 1 END) as active_sessions
                FROM sessions 
                WHERE {user_filter} deleted_at IS NULL
            """), params)
            
            session_row = session_stats.fetchone()
            
            # Get message stats
            message_stats = await self.postgres.execute(text(f"""
                SELECT 
                    COUNT(*) as total_messages,
                    SUM(COALESCE(token_count, 0)) as total_tokens
                FROM messages m
                JOIN sessions s ON m.session_id = s.id
                WHERE {user_filter} m.deleted_at IS NULL AND s.deleted_at IS NULL
            """), params)
            
            message_row = message_stats.fetchone()
            
            # Calculate averages
            total_sessions = session_row.total_sessions or 0
            total_messages = message_row.total_messages or 0
            total_tokens = message_row.total_tokens or 0
            
            avg_messages_per_session = total_messages / total_sessions if total_sessions > 0 else 0
            avg_tokens_per_message = total_tokens / total_messages if total_messages > 0 else 0
            
            # Get sessions by status
            status_stats = await self.postgres.execute(text(f"""
                SELECT status, COUNT(*) as count
                FROM sessions 
                WHERE {user_filter} deleted_at IS NULL
                GROUP BY status
            """), params)
            
            sessions_by_status = {row.status: row.count for row in status_stats.fetchall()}
            
            # Get recent activity
            recent_stats = await self.postgres.execute(text(f"""
                SELECT 
                    DATE_TRUNC('day', created_at) as date,
                    COUNT(*) as sessions_created
                FROM sessions 
                WHERE {user_filter} deleted_at IS NULL AND created_at > NOW() - INTERVAL '30 days'
                GROUP BY DATE_TRUNC('day', created_at)
                ORDER BY date DESC
                LIMIT 30
            """), params)
            
            recent_activity = [
                {
                    "date": row.date.isoformat(),
                    "sessions_created": row.sessions_created
                }
                for row in recent_stats.fetchall()
            ]
            
            return SessionStats(
                total_sessions=total_sessions,
                active_sessions=session_row.active_sessions or 0,
                total_messages=total_messages,
                total_tokens=total_tokens,
                avg_messages_per_session=avg_messages_per_session,
                avg_tokens_per_message=avg_tokens_per_message,
                sessions_by_status=sessions_by_status,
                recent_activity=recent_activity
            )
        
        return await self.execute_with_cache(cache_key, fetch_stats, ttl=600)  # 10 minute cache
    
    async def search_sessions(
        self,
        query: SessionSearchQuery,
        pagination: PaginationParams
    ) -> Tuple[List[Session], int]:
        """Search sessions"""
        try:
            # Build WHERE conditions
            where_conditions = ["deleted_at IS NULL"]
            params = {
                "limit": pagination.limit,
                "offset": pagination.offset
            }
            
            # Text search
            if query.query:
                where_conditions.append("(title ILIKE :search_term OR description ILIKE :search_term)")
                params["search_term"] = f"%{query.query}%"
            
            # Status filter
            if query.status:
                where_conditions.append("status = :status")
                params["status"] = query.status
            
            # User filter
            if query.user_id:
                where_conditions.append("user_id = :user_id")
                params["user_id"] = query.user_id
            
            # Project filter
            if query.project_id:
                where_conditions.append("project_id = :project_id")
                params["project_id"] = query.project_id
            
            # Tag filter
            if query.tags:
                where_conditions.append("tags && :tags")
                params["tags"] = query.tags
            
            # Date filters
            if query.date_from:
                where_conditions.append("created_at >= :date_from")
                params["date_from"] = query.date_from
            
            if query.date_to:
                where_conditions.append("created_at <= :date_to")
                params["date_to"] = query.date_to
            
            where_clause = " AND ".join(where_conditions)
            
            # Get total count
            count_stmt = text(f"""
                SELECT COUNT(*) FROM sessions 
                WHERE {where_clause}
            """)
            
            count_result = await self.postgres.execute(count_stmt, params)
            total_count = count_result.scalar()
            
            # Get sessions
            order_by = f"ORDER BY {query.sort_by} {query.sort_order.upper()}"
            
            stmt = text(f"""
                SELECT s.*, 
                       COALESCE(m.message_count, 0) as message_count,
                       COALESCE(m.token_count, 0) as token_count,
                       COALESCE(m.last_message_at, s.created_at) as last_message_at
                FROM sessions s
                LEFT JOIN (
                    SELECT session_id,
                           COUNT(*) as message_count,
                           SUM(COALESCE(token_count, 0)) as token_count,
                           MAX(created_at) as last_message_at
                    FROM messages 
                    WHERE deleted_at IS NULL
                    GROUP BY session_id
                ) m ON s.id = m.session_id
                WHERE {where_clause}
                {order_by}
                LIMIT :limit OFFSET :offset
            """)
            
            result = await self.postgres.execute(stmt, params)
            rows = result.fetchall()
            
            sessions = []
            for row in rows:
                session = Session(
                    id=row.id,
                    title=row.title,
                    description=row.description,
                    status=row.status,
                    tags=row.tags or [],
                    user_id=row.user_id,
                    project_id=row.project_id,
                    parent_session_id=row.parent_session_id,
                    metadata=row.metadata or {},
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                    message_count=row.message_count,
                    token_count=row.token_count,
                    last_message_at=row.last_message_at,
                    access_count=row.access_count or 0,
                    last_accessed_at=row.last_accessed_at
                )
                sessions.append(session)
            
            return sessions, total_count
            
        except Exception as e:
            logger.error("Session search failed", error=str(e))
            raise