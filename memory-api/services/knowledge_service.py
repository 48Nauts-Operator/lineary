# ABOUTME: Knowledge service for BETTY Memory System
# ABOUTME: Business logic for knowledge item management, search, and vector operations

import asyncio
import json
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID, uuid4
import structlog
from sqlalchemy import select, update, delete, func, text, or_, and_
from sqlalchemy.orm import selectinload

from models.knowledge import (
    KnowledgeItem,
    KnowledgeItemCreate,
    KnowledgeItemUpdate,
    SearchQuery,
    KnowledgeStats,
    BulkImportRequest,
    BulkImportResponse,
    ConfidenceLevel
)
from models.base import PaginationParams
from services.base_service import BaseService
from services.vector_service import VectorService

logger = structlog.get_logger(__name__)

class KnowledgeService(BaseService):
    """Service for knowledge item operations"""
    
    def __init__(self, databases):
        super().__init__(databases)
        # Only initialize vector service if qdrant is available
        self.vector_service = VectorService(databases) if databases.qdrant else None
    
    def _confidence_to_quality_score(self, confidence: ConfidenceLevel) -> float:
        """Convert confidence level to quality score (0.0-1.0)"""
        mapping = {
            ConfidenceLevel.LOW: 0.25,
            ConfidenceLevel.MEDIUM: 0.5,
            ConfidenceLevel.HIGH: 0.75,
            ConfidenceLevel.VERIFIED: 1.0
        }
        return mapping.get(confidence, 0.5)
    
    def _confidence_to_complexity_level(self, confidence: ConfidenceLevel) -> str:
        """Convert confidence level to complexity level"""
        mapping = {
            ConfidenceLevel.LOW: 'simple',
            ConfidenceLevel.MEDIUM: 'medium',
            ConfidenceLevel.HIGH: 'complex',
            ConfidenceLevel.VERIFIED: 'expert'
        }
        return mapping.get(confidence, 'medium')
    
    def _quality_score_to_confidence(self, quality_score: float) -> ConfidenceLevel:
        """Convert quality score back to confidence level"""
        if quality_score >= 0.9:
            return ConfidenceLevel.VERIFIED
        elif quality_score >= 0.65:
            return ConfidenceLevel.HIGH
        elif quality_score >= 0.35:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW
    
    def _row_to_knowledge_item(self, row, include_content: bool = True, 
                               children_count: int = 0, related_count: int = 0) -> KnowledgeItem:
        """Convert database row to KnowledgeItem, handling missing columns"""
        metadata = row.metadata or {}
        return KnowledgeItem(
            id=row.id,
            title=row.title,
            content=row.content if include_content else None,
            knowledge_type=row.knowledge_type,
            source_type=metadata.get("source_type", "conversation"),
            tags=metadata.get("tags", []),
            summary=metadata.get("summary"),
            confidence=self._quality_score_to_confidence(row.quality_score or 0.5),
            session_id=row.session_id,
            user_id=str(row.user_id) if row.user_id else None,
            project_id=str(row.project_id) if row.project_id else None,
            parent_id=UUID(metadata["parent_id"]) if metadata.get("parent_id") else None,
            metadata=row.metadata or {},
            created_at=row.created_at,
            updated_at=row.updated_at,
            embedding_id=getattr(row, 'embedding_id', None),
            access_count=0,  # Not stored in current schema
            last_accessed_at=None,  # Not stored in current schema
            children_count=children_count,
            related_count=related_count
        )
    
    async def create_knowledge_item(self, item_data: KnowledgeItemCreate) -> KnowledgeItem:
        """Create a new knowledge item with vector embedding"""
        try:
            # Generate UUID
            item_id = uuid4()
            
            # Create database record
            db_item = await self._insert_knowledge_item(item_id, item_data)
            
            # Generate and store vector embedding if vector service is available
            embedding_id = None
            if self.vector_service:
                try:
                    embedding_id = await self.vector_service.create_embedding(
                        item_id=str(item_id),
                        content=item_data.content,
                        metadata={
                            "title": item_data.title,
                            "knowledge_type": item_data.knowledge_type,
                            "source_type": item_data.source_type,
                            "tags": item_data.tags,
                            "session_id": str(item_data.session_id) if item_data.session_id else None
                        },
                        collection_name="knowledge_items"
                    )
                    
                    # Update record with embedding_id
                    await self._update_embedding_id(item_id, embedding_id)
                    db_item.embedding_id = embedding_id
                    
                except Exception as e:
                    logger.warning(
                        "Failed to create vector embedding",
                        item_id=str(item_id),
                        error=str(e)
                    )
            
            # Create temporal graph relationships (disabled for minimal version)
            # TODO: Re-enable when graphiti-core is available
            # try:
            #     await self._create_graph_relationships(item_id, item_data)
            # except Exception as e:
            #     logger.warning(
            #         "Failed to create graph relationships",
            #         item_id=str(item_id),
            #         error=str(e)
            #     )
            
            # Invalidate cache
            await self.invalidate_related_cache("knowledge:*")
            
            await self.log_operation(
                "create_knowledge_item",
                "knowledge_items",
                str(item_id)
            )
            
            return db_item
            
        except Exception as e:
            logger.error("Failed to create knowledge item", error=str(e))
            raise
    
    async def _insert_knowledge_item(
        self,
        item_id: UUID,
        item_data: KnowledgeItemCreate
    ) -> KnowledgeItem:
        """Insert knowledge item into PostgreSQL"""
        from sqlalchemy import insert
        
        # This would use SQLAlchemy models - creating placeholder for now
        stmt = text("""
            INSERT INTO knowledge_items (
                id, title, content, knowledge_type, quality_score, complexity_level, 
                session_id, user_id, project_id, metadata, content_hash, created_at, updated_at
            ) VALUES (
                :id, :title, :content, :knowledge_type, :quality_score, :complexity_level,
                :session_id, :user_id, :project_id, :metadata, :content_hash, :created_at, :updated_at
            )
            RETURNING *
        """)
        
        now = datetime.utcnow()
        
        # Build metadata including missing fields
        metadata = item_data.metadata or {}
        metadata.update({
            "source_type": item_data.source_type.value,  # Convert enum to string
            "tags": item_data.tags or [],
            "summary": item_data.summary,
            "parent_id": str(item_data.parent_id) if item_data.parent_id else None
        })
        
        import json
        import hashlib
        
        # Generate content hash for deduplication
        content_hash = hashlib.sha256(item_data.content.encode('utf-8')).hexdigest()
        
        result = await self.postgres.execute(stmt, {
            "id": item_id,
            "title": item_data.title,
            "content": item_data.content,
            "knowledge_type": item_data.knowledge_type.value,  # Convert enum to string
            "quality_score": self._confidence_to_quality_score(item_data.confidence),
            "complexity_level": self._confidence_to_complexity_level(item_data.confidence),
            "session_id": item_data.session_id,
            "user_id": item_data.user_id or "95fd614f-7da8-4650-bf23-ed53acba34c2",  # Default system user
            "project_id": item_data.project_id or "c5d0c92a-d609-4a9d-bb59-473b7dc12d3a",  # Use default BETTY project
            "content_hash": content_hash,
            "metadata": json.dumps(metadata),  # Convert dict to JSON string
            "created_at": now,
            "updated_at": now
        })
        
        await self.postgres.commit()
        row = result.fetchone()
        
        # Convert to Pydantic model
        return self._row_to_knowledge_item(row)
    
    async def _update_embedding_id(self, item_id: UUID, embedding_id: str) -> None:
        """Update embedding_id in database"""
        stmt = text("""
            UPDATE knowledge_items 
            SET embedding_id = :embedding_id, updated_at = :updated_at
            WHERE id = :id
        """)
        
        await self.postgres.execute(stmt, {
            "embedding_id": embedding_id,
            "updated_at": datetime.utcnow(),
            "id": item_id
        })
        await self.postgres.commit()
    
    async def _create_graph_relationships(
        self,
        item_id: UUID,
        item_data: KnowledgeItemCreate
    ) -> None:
        """Create relationships in Neo4j temporal graph"""
        # Create knowledge node
        create_node_query = """
        CREATE (k:KnowledgeItem {
            id: $id,
            title: $title,
            knowledge_type: $knowledge_type,
            source_type: $source_type,
            created_at: datetime($created_at)
        })
        """
        
        await self.neo4j.run(create_node_query, {
            "id": str(item_id),
            "title": item_data.title,
            "knowledge_type": item_data.knowledge_type,
            "source_type": item_data.source_type,
            "created_at": datetime.utcnow().isoformat()
        })
        
        # Create relationships to session if exists
        if item_data.session_id:
            session_rel_query = """
            MATCH (k:KnowledgeItem {id: $item_id})
            MATCH (s:Session {id: $session_id})
            CREATE (k)-[:BELONGS_TO {created_at: datetime()}]->(s)
            """
            
            await self.neo4j.run(session_rel_query, {
                "item_id": str(item_id),
                "session_id": str(item_data.session_id)
            })
        
        # Create parent-child relationship if exists
        if item_data.parent_id:
            parent_rel_query = """
            MATCH (child:KnowledgeItem {id: $child_id})
            MATCH (parent:KnowledgeItem {id: $parent_id})
            CREATE (child)-[:CHILD_OF {created_at: datetime()}]->(parent)
            """
            
            await self.neo4j.run(parent_rel_query, {
                "child_id": str(item_id),
                "parent_id": str(item_data.parent_id)
            })
    
    async def get_knowledge_item(self, item_id: UUID) -> Optional[KnowledgeItem]:
        """Get knowledge item by ID"""
        cache_key = self.generate_cache_key("knowledge", "item", str(item_id))
        
        async def fetch_item():
            stmt = text("""
                SELECT * FROM knowledge_items 
                WHERE id = :id AND system_time_until IS NULL
            """)
            
            result = await self.postgres.execute(stmt, {"id": item_id})
            row = result.fetchone()
            
            if not row:
                return None
            
            # Get additional computed fields
            children_count = await self._get_children_count(item_id)
            related_count = await self._get_related_count(item_id)
            
            # Convert to knowledge item with computed fields
            return self._row_to_knowledge_item(row, children_count=children_count, related_count=related_count)
        
        return await self.execute_with_cache(cache_key, fetch_item)
    
    async def _get_children_count(self, item_id: UUID) -> int:
        """Get count of child knowledge items"""
        stmt = text("""
            SELECT COUNT(*) FROM knowledge_items 
            WHERE metadata->>'parent_id' = :parent_id AND system_time_until IS NULL
        """)
        
        result = await self.postgres.execute(stmt, {"parent_id": str(item_id)})
        return result.scalar() or 0
    
    async def _get_related_count(self, item_id: UUID) -> int:
        """Get count of related knowledge items from graph"""
        # Disabled for minimal version - return 0
        # TODO: Re-enable when graphiti-core is available
        return 0
    
    async def update_knowledge_item(
        self,
        item_id: UUID,
        updates: KnowledgeItemUpdate
    ) -> Optional[KnowledgeItem]:
        """Update knowledge item"""
        try:
            # Build update statement
            update_fields = []
            params = {"id": item_id, "updated_at": datetime.utcnow()}
            
            if updates.title is not None:
                update_fields.append("title = :title")
                params["title"] = updates.title
            
            if updates.content is not None:
                update_fields.append("content = :content")
                params["content"] = updates.content
            
            if updates.tags is not None:
                update_fields.append("tags = :tags")
                params["tags"] = updates.tags
            
            if updates.summary is not None:
                update_fields.append("summary = :summary")
                params["summary"] = updates.summary
            
            if updates.confidence is not None:
                update_fields.append("quality_score = :quality_score")
                update_fields.append("complexity_level = :complexity_level")
                params["quality_score"] = self._confidence_to_quality_score(updates.confidence)
                params["complexity_level"] = self._confidence_to_complexity_level(updates.confidence)
            
            if updates.metadata is not None:
                update_fields.append("metadata = :metadata")
                params["metadata"] = updates.metadata
            
            if not update_fields:
                # No updates provided
                return await self.get_knowledge_item(item_id)
            
            stmt = text(f"""
                UPDATE knowledge_items 
                SET {', '.join(update_fields)}, updated_at = :updated_at
                WHERE id = :id AND system_time_until IS NULL
                RETURNING *
            """)
            
            result = await self.postgres.execute(stmt, params)
            await self.postgres.commit()
            
            row = result.fetchone()
            if not row:
                return None
            
            # Update vector embedding if content changed
            if updates.content is not None and row.embedding_id:
                try:
                    await self.vector_service.update_embedding(
                        row.embedding_id,
                        updates.content,
                        collection_name="knowledge_items"
                    )
                except Exception as e:
                    logger.warning("Failed to update vector embedding", error=str(e))
            
            # Invalidate cache
            await self.cache_delete(self.generate_cache_key("knowledge", "item", str(item_id)))
            await self.invalidate_related_cache("knowledge:*")
            
            await self.log_operation("update_knowledge_item", "knowledge_items", str(item_id))
            
            return await self.get_knowledge_item(item_id)
            
        except Exception as e:
            logger.error("Failed to update knowledge item", item_id=str(item_id), error=str(e))
            raise
    
    async def delete_knowledge_item(self, item_id: UUID) -> bool:
        """Delete knowledge item (soft delete)"""
        try:
            stmt = text("""
                UPDATE knowledge_items 
                SET system_time_until = :system_time_until, updated_at = :updated_at
                WHERE id = :id AND system_time_until IS NULL
            """)
            
            result = await self.postgres.execute(stmt, {
                "system_time_until": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "id": item_id
            })
            await self.postgres.commit()
            
            if result.rowcount == 0:
                return False
            
            # Delete vector embedding
            try:
                # Get embedding_id first
                get_stmt = text("SELECT embedding_id FROM knowledge_items WHERE id = :id")
                get_result = await self.postgres.execute(get_stmt, {"id": item_id})
                row = get_result.fetchone()
                
                if row and row.embedding_id:
                    await self.vector_service.delete_embedding(
                        row.embedding_id,
                        collection_name="knowledge_items"
                    )
            except Exception as e:
                logger.warning("Failed to delete vector embedding", error=str(e))
            
            # Delete graph relationships (disabled for minimal version)
            # TODO: Re-enable when graphiti-core is available
            # try:
            #     delete_graph_query = """
            #     MATCH (k:KnowledgeItem {id: $item_id})
            #     DETACH DELETE k
            #     """
            #     await self.neo4j.run(delete_graph_query, {"item_id": str(item_id)})
            # except Exception as e:
            #     logger.warning("Failed to delete graph relationships", error=str(e))
            
            # Invalidate cache
            await self.cache_delete(self.generate_cache_key("knowledge", "item", str(item_id)))
            await self.invalidate_related_cache("knowledge:*")
            
            await self.log_operation("delete_knowledge_item", "knowledge_items", str(item_id))
            
            return True
            
        except Exception as e:
            logger.error("Failed to delete knowledge item", item_id=str(item_id), error=str(e))
            raise
    
    async def update_access_tracking(self, item_id: UUID) -> None:
        """Update access tracking for knowledge item"""
        try:
            stmt = text("""
                UPDATE knowledge_items 
                SET access_count = COALESCE(access_count, 0) + 1,
                    last_accessed_at = :accessed_at,
                    updated_at = :updated_at
                WHERE id = :id AND system_time_until IS NULL
            """)
            
            await self.postgres.execute(stmt, {
                "accessed_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "id": item_id
            })
            await self.postgres.commit()
            
        except Exception as e:
            logger.warning("Failed to update access tracking", item_id=str(item_id), error=str(e))
    
    async def list_knowledge_items(
        self,
        pagination: PaginationParams,
        filters: Dict[str, Any] = None
    ) -> Tuple[List[KnowledgeItem], int]:
        """List knowledge items with filtering and pagination"""
        cache_key = self.generate_cache_key(
            "knowledge", "list", 
            str(pagination.page), str(pagination.page_size),
            str(hash(str(filters))) if filters else "no_filters"
        )
        
        async def fetch_items():
            # Build WHERE conditions
            where_conditions = ["system_time_until IS NULL"]
            params = {
                "limit": pagination.limit,
                "offset": pagination.offset
            }
            
            if filters:
                if filters.get("knowledge_type"):
                    where_conditions.append("knowledge_type = :knowledge_type")
                    params["knowledge_type"] = filters["knowledge_type"]
                
                if filters.get("session_id"):
                    where_conditions.append("session_id = :session_id")
                    params["session_id"] = filters["session_id"]
                
                if filters.get("project_id"):
                    where_conditions.append("project_id = :project_id")
                    params["project_id"] = filters["project_id"]
                
                if filters.get("tags"):
                    where_conditions.append("metadata->'tags' @> :tags::jsonb")
                    params["tags"] = filters["tags"]
            
            where_clause = " AND ".join(where_conditions)
            
            # Get total count
            count_stmt = text(f"""
                SELECT COUNT(*) FROM knowledge_items 
                WHERE {where_clause}
            """)
            
            count_result = await self.postgres.execute(count_stmt, params)
            total_count = count_result.scalar()
            
            # Get items
            stmt = text(f"""
                SELECT * FROM knowledge_items 
                WHERE {where_clause}
                ORDER BY updated_at DESC
                LIMIT :limit OFFSET :offset
            """)
            
            result = await self.postgres.execute(stmt, params)
            rows = result.fetchall()
            
            items = []
            for row in rows:
                try:
                    item = self._row_to_knowledge_item(row)
                    # Ensure it's actually a KnowledgeItem object
                    if not isinstance(item, KnowledgeItem):
                        logger.error("Created item is not a KnowledgeItem", item_type=type(item), item_repr=str(item))
                        continue
                    items.append(item)
                except Exception as e:
                    logger.error("Failed to convert row to KnowledgeItem", error=str(e), row_id=getattr(row, 'id', 'unknown'))
                    continue
            
            return items, total_count
        
        # Temporarily disable cache to debug serialization issue
        return await fetch_items()
        # return await self.execute_with_cache(cache_key, fetch_items, ttl=300)  # 5 minute cache
    
    async def search_knowledge(self, query: SearchQuery) -> List[KnowledgeItem]:
        """Search knowledge items using hybrid semantic + keyword search"""
        try:
            if query.search_type == "semantic" or query.search_type == "hybrid":
                # Vector similarity search
                vector_results = await self.vector_service.search_similar(
                    query=query.query,
                    collection_name="knowledge_items",
                    limit=query.limit,
                    similarity_threshold=query.similarity_threshold
                )
                
                if query.search_type == "semantic":
                    # Return only vector results
                    return await self._build_search_results(vector_results, query)
            
            # Combine with keyword search for hybrid approach
            if query.search_type == "keyword" or query.search_type == "hybrid":
                keyword_results = await self._keyword_search(query)
                
                if query.search_type == "keyword":
                    return keyword_results
                
                # Merge results for hybrid search
                return await self._merge_search_results(vector_results, keyword_results, query)
            
            return []
            
        except Exception as e:
            logger.error("Knowledge search failed", error=str(e))
            raise
    
    async def _keyword_search(self, query: SearchQuery) -> List[KnowledgeItem]:
        """Perform keyword search in PostgreSQL"""
        where_conditions = ["system_time_until IS NULL"]
        params = {"limit": query.limit}
        
        # Full text search - using actual database columns
        where_conditions.append("""
            (title ILIKE :search_term OR content ILIKE :search_term 
             OR problem_description ILIKE :search_term OR solution_description ILIKE :search_term
             OR metadata->>'summary' ILIKE :search_term)
        """)
        params["search_term"] = f"%{query.query}%"
        
        # Apply filters
        if query.knowledge_types:
            where_conditions.append("knowledge_type = ANY(:knowledge_types)")
            params["knowledge_types"] = query.knowledge_types
        
        if query.tags:
            where_conditions.append("metadata->'tags' @> :tags::jsonb")
            params["tags"] = query.tags
        
        if query.session_id:
            where_conditions.append("session_id = :session_id")
            params["session_id"] = query.session_id
        
        if query.project_id:
            where_conditions.append("project_id = :project_id")
            params["project_id"] = query.project_id
        
        if query.date_from:
            where_conditions.append("created_at >= :date_from")
            params["date_from"] = query.date_from
        
        if query.date_to:
            where_conditions.append("created_at <= :date_to")
            params["date_to"] = query.date_to
        
        where_clause = " AND ".join(where_conditions)
        
        stmt = text(f"""
            SELECT * FROM knowledge_items 
            WHERE {where_clause}
            ORDER BY 
                CASE 
                    WHEN title ILIKE :search_term THEN 1
                    WHEN problem_description ILIKE :search_term THEN 2
                    WHEN solution_description ILIKE :search_term THEN 3
                    WHEN metadata->>'summary' ILIKE :search_term THEN 4
                    ELSE 5
                END, 
                updated_at DESC
            LIMIT :limit
        """)
        
        result = await self.postgres.execute(stmt, params)
        rows = result.fetchall()
        
        items = []
        for row in rows:
            # Extract values from metadata for fields that are stored there
            metadata = row.metadata or {}
            item = KnowledgeItem(
                id=row.id,
                title=row.title,
                content=row.content if query.include_content else None,
                knowledge_type=row.knowledge_type,
                source_type=metadata.get("source_type", "conversation"),
                tags=metadata.get("tags", []),
                summary=metadata.get("summary"),
                confidence=self._quality_score_to_confidence(row.quality_score or 0.5),
                session_id=row.session_id,
                user_id=str(row.user_id) if row.user_id else None,
                project_id=str(row.project_id) if row.project_id else None,
                parent_id=UUID(metadata["parent_id"]) if metadata.get("parent_id") else None,
                metadata=metadata,
                created_at=row.created_at,
                updated_at=row.updated_at,
                embedding_id=row.embedding_id,
                access_count=getattr(row, 'access_count', 0) or getattr(row, 'usage_count', 0),
                last_accessed_at=getattr(row, 'last_accessed_at', None) or getattr(row, 'last_used_at', None),
                children_count=0,
                related_count=0
            )
            items.append(item)
        
        return items
    
    async def _build_search_results(
        self, 
        vector_results: List[Dict], 
        query: SearchQuery
    ) -> List[KnowledgeItem]:
        """Build KnowledgeItem objects from vector search results"""
        if not vector_results:
            return []
        
        # Extract item IDs from vector results
        item_ids = [result["payload"]["item_id"] for result in vector_results]
        similarity_scores = {
            result["payload"]["item_id"]: result["score"] 
            for result in vector_results
        }
        
        # Fetch full items from database
        placeholders = ",".join([f":id_{i}" for i in range(len(item_ids))])
        params = {f"id_{i}": item_id for i, item_id in enumerate(item_ids)}
        
        stmt = text(f"""
            SELECT * FROM knowledge_items 
            WHERE id IN ({placeholders}) AND system_time_until IS NULL
            ORDER BY updated_at DESC
        """)
        
        result = await self.postgres.execute(stmt, params)
        rows = result.fetchall()
        
        items = []
        for row in rows:
            # Extract values from metadata for fields that are stored there
            metadata = row.metadata or {}
            item = KnowledgeItem(
                id=row.id,
                title=row.title,
                content=row.content if query.include_content else None,
                knowledge_type=row.knowledge_type,
                source_type=metadata.get("source_type", "conversation"),
                tags=metadata.get("tags", []),
                summary=metadata.get("summary"),
                confidence=self._quality_score_to_confidence(row.quality_score or 0.5),
                session_id=row.session_id,
                user_id=str(row.user_id) if row.user_id else None,
                project_id=str(row.project_id) if row.project_id else None,
                parent_id=UUID(metadata["parent_id"]) if metadata.get("parent_id") else None,
                metadata=metadata,
                created_at=row.created_at,
                updated_at=row.updated_at,
                embedding_id=row.embedding_id,
                similarity_score=similarity_scores.get(str(row.id)),
                access_count=getattr(row, 'access_count', 0) or getattr(row, 'usage_count', 0),
                last_accessed_at=getattr(row, 'last_accessed_at', None) or getattr(row, 'last_used_at', None),
                children_count=0,
                related_count=0
            )
            items.append(item)
        
        return items
    
    async def _merge_search_results(
        self,
        vector_results: List[Dict],
        keyword_results: List[KnowledgeItem],
        query: SearchQuery
    ) -> List[KnowledgeItem]:
        """Merge vector and keyword search results"""
        # Convert vector results to KnowledgeItems
        vector_items = await self._build_search_results(vector_results, query)
        
        # Combine and deduplicate results
        seen_ids = set()
        merged_results = []
        
        # Add vector results first (higher priority)
        for item in vector_items:
            if item.id not in seen_ids:
                merged_results.append(item)
                seen_ids.add(item.id)
        
        # Add keyword results
        for item in keyword_results:
            if item.id not in seen_ids:
                merged_results.append(item)
                seen_ids.add(item.id)
        
        # Limit results
        if len(merged_results) > query.limit:
            merged_results = merged_results[:query.limit]
        
        return merged_results
    
    async def get_knowledge_stats(self) -> KnowledgeStats:
        """Get knowledge base statistics"""
        cache_key = "knowledge:stats"
        
        async def fetch_stats():
            # Get basic counts
            basic_stats = await self.postgres.execute(text("""
                SELECT 
                    COUNT(*) as total_items,
                    SUM(LENGTH(content)) as total_size_bytes,
                    AVG(quality_score) as avg_confidence
                FROM knowledge_items 
                WHERE system_time_until IS NULL
            """))
            
            basic_row = basic_stats.fetchone()
            
            # Get items by type
            type_stats = await self.postgres.execute(text("""
                SELECT knowledge_type, COUNT(*) as count
                FROM knowledge_items 
                WHERE system_time_until IS NULL
                GROUP BY knowledge_type
                ORDER BY count DESC
            """))
            
            items_by_type = {row.knowledge_type: row.count for row in type_stats.fetchall()}
            
            # Get items by source (from metadata)
            source_stats = await self.postgres.execute(text("""
                SELECT 
                    COALESCE(metadata->>'source_type', 'conversation') as source_type, 
                    COUNT(*) as count
                FROM knowledge_items 
                WHERE system_time_until IS NULL
                GROUP BY COALESCE(metadata->>'source_type', 'conversation')
                ORDER BY count DESC
            """))
            
            items_by_source = {row.source_type: row.count for row in source_stats.fetchall()}
            
            # Get most common tags (from metadata)
            tag_stats = await self.postgres.execute(text("""
                SELECT tag, COUNT(*) as count
                FROM (
                    SELECT jsonb_array_elements_text(metadata->'tags') as tag
                    FROM knowledge_items 
                    WHERE system_time_until IS NULL 
                    AND metadata->'tags' IS NOT NULL 
                    AND jsonb_array_length(metadata->'tags') > 0
                ) t
                GROUP BY tag
                ORDER BY count DESC
                LIMIT 10
            """))
            
            most_common_tags = [
                {"tag": row.tag, "count": row.count} 
                for row in tag_stats.fetchall()
            ]
            
            # Get recent activity
            recent_stats = await self.postgres.execute(text("""
                SELECT 
                    DATE_TRUNC('day', created_at) as date,
                    COUNT(*) as items_created
                FROM knowledge_items 
                WHERE system_time_until IS NULL AND created_at > NOW() - INTERVAL '30 days'
                GROUP BY DATE_TRUNC('day', created_at)
                ORDER BY date DESC
                LIMIT 30
            """))
            
            recent_activity = [
                {
                    "date": row.date.isoformat(),
                    "items_created": row.items_created
                }
                for row in recent_stats.fetchall()
            ]
            
            return KnowledgeStats(
                total_items=basic_row.total_items or 0,
                items_by_type=items_by_type,
                items_by_source=items_by_source,
                total_size_bytes=basic_row.total_size_bytes or 0,
                avg_confidence=float(basic_row.avg_confidence or 2.0),
                most_common_tags=most_common_tags,
                recent_activity=recent_activity
            )
        
        # Cache disabled due to issues - direct execution
        return await fetch_stats()
    
    async def bulk_import_knowledge(self, request: BulkImportRequest) -> BulkImportResponse:
        """Bulk import knowledge items"""
        batch_id = uuid4()
        total_items = len(request.items)
        imported_items = 0
        skipped_items = 0
        failed_items = 0
        errors = []
        
        try:
            for i, item_data in enumerate(request.items):
                try:
                    # Check for duplicates if requested
                    if request.skip_duplicates:
                        existing = await self._check_duplicate(item_data)
                        if existing:
                            if request.update_existing:
                                # Update existing item
                                await self.update_knowledge_item(existing.id, KnowledgeItemUpdate(
                                    content=item_data.content,
                                    tags=item_data.tags,
                                    metadata=item_data.metadata
                                ))
                                imported_items += 1
                            else:
                                skipped_items += 1
                            continue
                    
                    # Set project_id if provided
                    if request.project_id and not item_data.project_id:
                        item_data.project_id = request.project_id
                    
                    # Create knowledge item
                    await self.create_knowledge_item(item_data)
                    imported_items += 1
                    
                except Exception as e:
                    failed_items += 1
                    errors.append({
                        "index": i,
                        "title": item_data.title,
                        "error": str(e)
                    })
                    
                    logger.warning(
                        "Failed to import knowledge item",
                        index=i,
                        title=item_data.title,
                        error=str(e)
                    )
            
            return BulkImportResponse(
                message=f"Bulk import completed: {imported_items} imported, {skipped_items} skipped, {failed_items} failed",
                total_items=total_items,
                imported_items=imported_items,
                skipped_items=skipped_items,
                failed_items=failed_items,
                errors=errors,
                batch_id=batch_id
            )
            
        except Exception as e:
            logger.error("Bulk import failed", error=str(e))
            raise
    
    async def _check_duplicate(self, item_data: KnowledgeItemCreate) -> Optional[KnowledgeItem]:
        """Check for duplicate knowledge item"""
        stmt = text("""
            SELECT id FROM knowledge_items 
            WHERE title = :title AND content = :content AND system_time_until IS NULL
            LIMIT 1
        """)
        
        result = await self.postgres.execute(stmt, {
            "title": item_data.title,
            "content": item_data.content
        })
        
        row = result.fetchone()
        if row:
            return await self.get_knowledge_item(row.id)
        
        return None