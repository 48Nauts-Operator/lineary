# ABOUTME: Base service class for BETTY Memory System
# ABOUTME: Common service functionality and database operation utilities

from datetime import datetime
from typing import Any, Dict, List, Optional, Type, TypeVar
from uuid import UUID
import structlog

from core.dependencies import DatabaseDependencies

logger = structlog.get_logger(__name__)
T = TypeVar('T')

class BaseService:
    """Base service class with common database operations"""
    
    def __init__(self, databases: DatabaseDependencies):
        self.databases = databases
        self.postgres = databases.postgres
        self.neo4j = databases.neo4j  # Can be None for basic operations
        self.qdrant = databases.qdrant  # Can be None for basic operations
        self.redis = databases.redis
        self.settings = databases.settings
        
    async def log_operation(
        self,
        operation: str,
        table: str = None,
        record_id: str = None,
        **kwargs
    ) -> None:
        """Log database operation"""
        logger.info(
            "Database operation",
            operation=operation,
            table=table,
            record_id=record_id,
            **kwargs
        )
    
    async def cache_get(self, key: str) -> Optional[Any]:
        """Get value from Redis cache"""
        try:
            value = await self.redis.get(key)
            if value:
                import json
                return json.loads(value)
            return None
        except Exception as e:
            logger.warning("Cache get failed", key=key, error=str(e))
            return None
    
    async def cache_set(
        self,
        key: str,
        value: Any,
        ttl: int = None
    ) -> None:
        """Set value in Redis cache"""
        try:
            import json
            ttl = ttl or self.settings.cache_ttl
            await self.redis.setex(
                key,
                ttl,
                json.dumps(value, default=str)  # Handle datetime serialization
            )
        except Exception as e:
            logger.warning("Cache set failed", key=key, error=str(e))
    
    async def cache_delete(self, key: str) -> None:
        """Delete key from Redis cache"""
        try:
            await self.redis.delete(key)
        except Exception as e:
            logger.warning("Cache delete failed", key=key, error=str(e))
    
    async def cache_delete_pattern(self, pattern: str) -> None:
        """Delete all keys matching pattern"""
        try:
            keys = await self.redis.keys(pattern)
            if keys:
                await self.redis.delete(*keys)
        except Exception as e:
            logger.warning("Cache pattern delete failed", pattern=pattern, error=str(e))
    
    def generate_cache_key(self, *parts: str) -> str:
        """Generate cache key from parts"""
        return ":".join(str(part) for part in parts)
    
    async def execute_with_cache(
        self,
        cache_key: str,
        fetch_func,
        ttl: int = None,
        force_refresh: bool = False
    ) -> Any:
        """Execute function with caching"""
        if not force_refresh:
            cached_value = await self.cache_get(cache_key)
            if cached_value is not None:
                return cached_value
        
        # Fetch fresh data
        value = await fetch_func()
        
        # Cache the result
        await self.cache_set(cache_key, value, ttl)
        
        return value
    
    def serialize_for_cache(self, obj: Any) -> Dict[str, Any]:
        """Serialize object for cache storage"""
        if hasattr(obj, 'dict'):
            # Pydantic model
            return obj.dict()
        elif hasattr(obj, '__dict__'):
            # Regular object
            return {
                key: self._serialize_value(value)
                for key, value in obj.__dict__.items()
                if not key.startswith('_')
            }
        else:
            return obj
    
    def _serialize_value(self, value: Any) -> Any:
        """Serialize individual value for cache"""
        if isinstance(value, datetime):
            return value.isoformat()
        elif isinstance(value, UUID):
            return str(value)
        elif isinstance(value, (list, tuple)):
            return [self._serialize_value(item) for item in value]
        elif isinstance(value, dict):
            return {
                key: self._serialize_value(val)
                for key, val in value.items()
            }
        else:
            return value
    
    async def invalidate_related_cache(self, *patterns: str) -> None:
        """Invalidate cache entries matching patterns"""
        for pattern in patterns:
            await self.cache_delete_pattern(pattern)
    
    async def get_or_404(
        self,
        query_func,
        identifier: Any,
        error_message: str = "Record not found"
    ) -> Any:
        """Execute query and raise 404 if not found"""
        result = await query_func(identifier)
        if not result:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_message
            )
        return result
    
    async def paginate_query(
        self,
        query,
        pagination,
        count_query=None
    ) -> tuple:
        """Execute paginated query"""
        from sqlalchemy import func
        
        # Get total count
        if count_query is not None:
            total_result = await self.postgres.execute(count_query)
            total_count = total_result.scalar()
        else:
            # Create count query from main query
            count_query = query.statement.with_only_columns(func.count()).order_by(None)
            total_result = await self.postgres.execute(count_query)
            total_count = total_result.scalar()
        
        # Apply pagination
        paginated_query = query.offset(pagination.offset).limit(pagination.limit)
        result = await self.postgres.execute(paginated_query)
        items = result.scalars().all()
        
        return items, total_count
    
    async def bulk_insert(
        self,
        model_class: Type[T],
        data_list: List[Dict[str, Any]]
    ) -> List[T]:
        """Bulk insert records"""
        if not data_list:
            return []
        
        try:
            # Add timestamps
            now = datetime.utcnow()
            for data in data_list:
                data.setdefault('created_at', now)
                data.setdefault('updated_at', now)
            
            # Bulk insert
            stmt = model_class.__table__.insert().values(data_list)
            result = await self.postgres.execute(stmt)
            
            await self.log_operation(
                "bulk_insert",
                table=model_class.__tablename__,
                record_count=len(data_list)
            )
            
            return result.inserted_primary_key
            
        except Exception as e:
            logger.error(
                "Bulk insert failed",
                table=model_class.__tablename__,
                error=str(e)
            )
            raise
    
    async def update_timestamp(
        self,
        model_class: Type[T],
        record_id: UUID,
        field: str = "updated_at"
    ) -> None:
        """Update timestamp field"""
        from sqlalchemy import update
        
        stmt = update(model_class).where(
            model_class.id == record_id
        ).values({field: datetime.utcnow()})
        
        await self.postgres.execute(stmt)
        await self.postgres.commit()
    
    async def soft_delete(
        self,
        model_class: Type[T],
        record_id: UUID
    ) -> bool:
        """Soft delete record by setting deleted_at timestamp"""
        from sqlalchemy import update
        
        try:
            stmt = update(model_class).where(
                model_class.id == record_id
            ).values(deleted_at=datetime.utcnow())
            
            result = await self.postgres.execute(stmt)
            await self.postgres.commit()
            
            return result.rowcount > 0
            
        except Exception as e:
            logger.error("Soft delete failed", record_id=str(record_id), error=str(e))
            raise