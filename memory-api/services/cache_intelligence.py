# ABOUTME: Intelligent caching service for BETTY Memory System
# ABOUTME: Smart caching strategies for knowledge retrieval with predictive pre-loading

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from collections import defaultdict, Counter
import structlog
from dataclasses import dataclass
import pickle
import hashlib

from services.base_service import BaseService

logger = structlog.get_logger(__name__)

@dataclass
class CacheStats:
    """Cache statistics tracking"""
    total_requests: int
    cache_hits: int
    cache_misses: int
    hit_rate: float
    avg_response_time_ms: float
    popular_queries: List[Dict[str, Any]]
    cache_size_mb: float

@dataclass
class AccessPattern:
    """User access pattern tracking"""
    user_id: str
    query_patterns: List[str]
    frequent_projects: List[str]
    preferred_context_depth: str
    technology_preferences: List[str]
    peak_usage_hours: List[int]
    session_duration_avg: float

class CacheIntelligence(BaseService):
    """Intelligent caching service with predictive capabilities"""
    
    def __init__(self, databases):
        super().__init__(databases)
        self.cache_prefix = "betty:intelligent:"
        self.stats_prefix = "betty:stats:"
        self.pattern_prefix = "betty:patterns:"
        
        # Cache configuration
        self.default_ttl = 3600  # 1 hour
        self.hot_cache_ttl = 7200  # 2 hours for frequently accessed items
        self.cold_cache_ttl = 1800  # 30 minutes for rarely accessed items
        self.max_cache_size = 1000  # Maximum number of cached items per type
        
    async def get_cached_context(self, cache_key: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get cached context with access tracking"""
        try:
            # Track access
            await self._track_cache_access(cache_key, user_id, "request")
            
            # Get from cache
            cached_data = await self.cache_get(cache_key)
            
            if cached_data:
                # Track cache hit
                await self._track_cache_access(cache_key, user_id, "hit")
                
                # Update access frequency for intelligent TTL
                await self._update_access_frequency(cache_key, user_id)
                
                # Trigger predictive loading if needed
                asyncio.create_task(self._predictive_preload(user_id, cache_key))
                
                logger.info("Cache hit", cache_key=cache_key, user_id=user_id)
                return json.loads(cached_data)
            else:
                # Track cache miss
                await self._track_cache_access(cache_key, user_id, "miss")
                logger.info("Cache miss", cache_key=cache_key, user_id=user_id)
                return None
                
        except Exception as e:
            logger.error("Failed to get cached context", cache_key=cache_key, error=str(e))
            return None
    
    async def set_cached_context(
        self, 
        cache_key: str, 
        data: Dict[str, Any], 
        user_id: str,
        context_type: str = "general"
    ) -> bool:
        """Set cached context with intelligent TTL"""
        try:
            # Determine intelligent TTL based on access patterns
            ttl = await self._calculate_intelligent_ttl(cache_key, user_id, context_type)
            
            # Serialize data
            serialized_data = json.dumps(data, default=str)
            
            # Check cache size limits
            await self._enforce_cache_limits(context_type)
            
            # Set cache with TTL
            success = await self.cache_set(cache_key, serialized_data, ttl)
            
            if success:
                # Track cache set
                await self._track_cache_operation(cache_key, user_id, "set", len(serialized_data))
                
                # Update cache metadata
                await self._update_cache_metadata(cache_key, user_id, context_type, ttl)
                
                logger.info(
                    "Cache set", 
                    cache_key=cache_key, 
                    user_id=user_id, 
                    ttl=ttl,
                    size_bytes=len(serialized_data)
                )
            
            return success
            
        except Exception as e:
            logger.error("Failed to set cached context", cache_key=cache_key, error=str(e))
            return False
    
    async def warm_cache_for_user(self, user_id: str) -> Dict[str, Any]:
        """Warm cache based on user's access patterns"""
        try:
            # Get user access patterns
            patterns = await self._get_user_access_patterns(user_id)
            
            if not patterns:
                return {"message": "No access patterns found", "preloaded": 0}
            
            preloaded_count = 0
            
            # Preload frequent queries
            for query_pattern in patterns.frequent_queries[:10]:  # Top 10 queries
                cache_key = self._generate_predictive_cache_key(user_id, query_pattern)
                
                # Check if already cached
                if not await self.cache_get(cache_key):
                    # Generate context for this query
                    context_data = await self._generate_predictive_context(user_id, query_pattern)
                    
                    if context_data:
                        await self.set_cached_context(cache_key, context_data, user_id, "predictive")
                        preloaded_count += 1
            
            # Preload project-specific context
            for project in patterns.frequent_projects[:5]:  # Top 5 projects
                cache_key = self._generate_project_cache_key(user_id, project)
                
                if not await self.cache_get(cache_key):
                    project_context = await self._generate_project_context(user_id, project)
                    
                    if project_context:
                        await self.set_cached_context(cache_key, project_context, user_id, "project")
                        preloaded_count += 1
            
            logger.info("Cache warmed for user", user_id=user_id, preloaded=preloaded_count)
            
            return {
                "message": f"Cache warmed with {preloaded_count} items",
                "preloaded": preloaded_count,
                "patterns_analyzed": len(patterns.frequent_queries)
            }
            
        except Exception as e:
            logger.error("Failed to warm cache for user", user_id=user_id, error=str(e))
            return {"message": "Cache warming failed", "error": str(e)}
    
    async def get_cache_statistics(self, user_id: Optional[str] = None) -> CacheStats:
        """Get comprehensive cache statistics"""
        try:
            # Get basic cache stats
            stats_key = f"{self.stats_prefix}global" if not user_id else f"{self.stats_prefix}user:{user_id}"
            
            stats_data = await self.cache_get(stats_key)
            if stats_data:
                base_stats = json.loads(stats_data)
            else:
                base_stats = {"total_requests": 0, "cache_hits": 0, "cache_misses": 0}
            
            # Calculate hit rate
            total_requests = base_stats["total_requests"]
            cache_hits = base_stats["cache_hits"]
            hit_rate = (cache_hits / total_requests) if total_requests > 0 else 0.0
            
            # Get popular queries
            popular_queries = await self._get_popular_queries(user_id)
            
            # Calculate cache size
            cache_size_mb = await self._calculate_cache_size()
            
            # Get average response time
            avg_response_time = await self._get_average_response_time(user_id)
            
            return CacheStats(
                total_requests=total_requests,
                cache_hits=cache_hits,
                cache_misses=base_stats["cache_misses"],
                hit_rate=hit_rate,
                avg_response_time_ms=avg_response_time,
                popular_queries=popular_queries,
                cache_size_mb=cache_size_mb
            )
            
        except Exception as e:
            logger.error("Failed to get cache statistics", error=str(e))
            return CacheStats(0, 0, 0, 0.0, 0.0, [], 0.0)
    
    async def optimize_cache_performance(self) -> Dict[str, Any]:
        """Optimize cache performance based on usage patterns"""
        try:
            optimization_results = {
                "actions_taken": [],
                "performance_improvements": {},
                "recommendations": []
            }
            
            # 1. Remove stale cache entries
            stale_removed = await self._remove_stale_entries()
            optimization_results["actions_taken"].append(f"Removed {stale_removed} stale entries")
            
            # 2. Adjust TTL for frequently accessed items
            ttl_adjusted = await self._optimize_ttl_settings()
            optimization_results["actions_taken"].append(f"Optimized TTL for {ttl_adjusted} items")
            
            # 3. Preload popular queries
            preloaded = await self._preload_popular_queries()
            optimization_results["actions_taken"].append(f"Preloaded {preloaded} popular queries")
            
            # 4. Compress large cache entries
            compressed = await self._compress_large_entries()
            optimization_results["actions_taken"].append(f"Compressed {compressed} large entries")
            
            # 5. Generate recommendations
            recommendations = await self._generate_cache_recommendations()
            optimization_results["recommendations"] = recommendations
            
            # 6. Calculate performance improvements
            performance_gains = await self._measure_performance_gains()
            optimization_results["performance_improvements"] = performance_gains
            
            logger.info("Cache optimization completed", results=optimization_results)
            
            return optimization_results
            
        except Exception as e:
            logger.error("Failed to optimize cache performance", error=str(e))
            return {"error": str(e)}
    
    async def invalidate_intelligent_cache(self, patterns: List[str], user_id: Optional[str] = None) -> int:
        """Intelligently invalidate cache based on patterns"""
        try:
            invalidated_count = 0
            
            for pattern in patterns:
                # Get all cache keys matching pattern
                if user_id:
                    cache_pattern = f"{self.cache_prefix}{user_id}:{pattern}"
                else:
                    cache_pattern = f"{self.cache_prefix}*:{pattern}"
                
                # Get matching keys (implementation depends on Redis)
                matching_keys = await self._get_matching_cache_keys(cache_pattern)
                
                # Invalidate matching keys
                for key in matching_keys:
                    await self.cache_delete(key)
                    invalidated_count += 1
                
                # Track invalidation
                await self._track_cache_operation(pattern, user_id or "system", "invalidate", invalidated_count)
            
            logger.info(
                "Intelligent cache invalidation completed",
                patterns=patterns,
                user_id=user_id,
                invalidated=invalidated_count
            )
            
            return invalidated_count
            
        except Exception as e:
            logger.error("Failed to invalidate intelligent cache", error=str(e))
            return 0
    
    # Private helper methods
    
    async def _track_cache_access(self, cache_key: str, user_id: str, access_type: str) -> None:
        """Track cache access for analytics"""
        try:
            timestamp = datetime.utcnow()
            
            # Update global stats
            global_stats_key = f"{self.stats_prefix}global"
            await self._increment_counter(global_stats_key, f"cache_{access_type}s")
            
            # Update user-specific stats
            user_stats_key = f"{self.stats_prefix}user:{user_id}"
            await self._increment_counter(user_stats_key, f"cache_{access_type}s")
            
            # Track access pattern
            pattern_key = f"{self.pattern_prefix}user:{user_id}"
            pattern_data = {
                "cache_key": cache_key,
                "access_type": access_type,
                "timestamp": timestamp.isoformat()
            }
            
            await self._add_to_access_history(pattern_key, pattern_data)
            
        except Exception as e:
            logger.warning("Failed to track cache access", error=str(e))
    
    async def _calculate_intelligent_ttl(self, cache_key: str, user_id: str, context_type: str) -> int:
        """Calculate intelligent TTL based on access patterns"""
        try:
            # Get access frequency for this cache key
            access_frequency = await self._get_access_frequency(cache_key, user_id)
            
            # Base TTL by context type
            base_ttl = {
                "context": 3600,      # 1 hour
                "similarity": 1800,   # 30 minutes
                "patterns": 7200,     # 2 hours
                "recommendations": 3600,  # 1 hour
                "predictive": 14400,  # 4 hours
                "project": 7200       # 2 hours
            }.get(context_type, self.default_ttl)
            
            # Adjust based on access frequency
            if access_frequency > 10:  # High frequency
                return int(base_ttl * 1.5)  # Extend TTL
            elif access_frequency > 5:  # Medium frequency
                return base_ttl
            else:  # Low frequency
                return int(base_ttl * 0.75)  # Reduce TTL
                
        except Exception as e:
            logger.warning("Failed to calculate intelligent TTL", error=str(e))
            return self.default_ttl
    
    async def _update_access_frequency(self, cache_key: str, user_id: str) -> None:
        """Update access frequency counter"""
        try:
            frequency_key = f"{self.cache_prefix}frequency:{user_id}:{cache_key}"
            await self._increment_counter(frequency_key, "count", ttl=86400)  # 24 hour window
            
        except Exception as e:
            logger.warning("Failed to update access frequency", error=str(e))
    
    async def _get_access_frequency(self, cache_key: str, user_id: str) -> int:
        """Get access frequency for cache key"""
        try:
            frequency_key = f"{self.cache_prefix}frequency:{user_id}:{cache_key}"
            frequency_data = await self.cache_get(frequency_key)
            
            if frequency_data:
                data = json.loads(frequency_data)
                return data.get("count", 0)
            
            return 0
            
        except Exception as e:
            logger.warning("Failed to get access frequency", error=str(e))
            return 0
    
    async def _predictive_preload(self, user_id: str, accessed_cache_key: str) -> None:
        """Predictively preload related cache entries"""
        try:
            # Analyze access patterns to predict what user might need next
            patterns = await self._get_user_access_patterns(user_id)
            
            if not patterns:
                return
            
            # Generate predictive cache keys based on current access
            predictive_keys = await self._generate_predictive_keys(user_id, accessed_cache_key, patterns)
            
            # Preload up to 3 predictive entries
            for pred_key in predictive_keys[:3]:
                if not await self.cache_get(pred_key):
                    # Generate and cache predictive content
                    pred_content = await self._generate_predictive_content(user_id, pred_key)
                    
                    if pred_content:
                        await self.set_cached_context(pred_key, pred_content, user_id, "predictive")
            
        except Exception as e:
            logger.warning("Failed to predictive preload", error=str(e))
    
    async def _enforce_cache_limits(self, context_type: str) -> None:
        """Enforce cache size limits"""
        try:
            # Get current cache size for this type
            type_pattern = f"{self.cache_prefix}*:{context_type}:*"
            current_keys = await self._get_matching_cache_keys(type_pattern)
            
            if len(current_keys) >= self.max_cache_size:
                # Remove least recently used entries
                lru_keys = await self._get_lru_keys(current_keys, len(current_keys) - self.max_cache_size + 10)
                
                for key in lru_keys:
                    await self.cache_delete(key)
                
                logger.info(f"Removed {len(lru_keys)} LRU cache entries for {context_type}")
            
        except Exception as e:
            logger.warning("Failed to enforce cache limits", error=str(e))
    
    async def _get_user_access_patterns(self, user_id: str) -> Optional[AccessPattern]:
        """Get user access patterns for predictive caching"""
        try:
            pattern_key = f"{self.pattern_prefix}user:{user_id}"
            history_data = await self.cache_get(pattern_key)
            
            if not history_data:
                return None
            
            history = json.loads(history_data)
            
            # Analyze patterns
            queries = [item.get("cache_key", "") for item in history if item.get("access_type") == "request"]
            query_counter = Counter(queries)
            
            # Extract projects and technologies from cache keys
            projects = []
            technologies = []
            
            for query in queries:
                # Parse cache key for project/tech info (implementation specific)
                if ":project:" in query:
                    project = query.split(":project:")[1].split(":")[0]
                    projects.append(project)
            
            return AccessPattern(
                user_id=user_id,
                query_patterns=list(query_counter.keys())[:20],  # Top 20 queries
                frequent_projects=list(Counter(projects).keys())[:10],
                preferred_context_depth="detailed",  # Could be analyzed from patterns
                technology_preferences=list(Counter(technologies).keys())[:10],
                peak_usage_hours=[9, 10, 11, 14, 15, 16],  # Default business hours
                session_duration_avg=45.0  # Default 45 minutes
            )
            
        except Exception as e:
            logger.warning("Failed to get user access patterns", error=str(e))
            return None
    
    # Additional helper methods would be implemented here for:
    # - _generate_predictive_cache_key
    # - _generate_predictive_context
    # - _generate_project_cache_key
    # - _generate_project_context
    # - _get_popular_queries
    # - _calculate_cache_size
    # - _get_average_response_time
    # - _remove_stale_entries
    # - _optimize_ttl_settings
    # - _preload_popular_queries
    # - _compress_large_entries
    # - _generate_cache_recommendations
    # - _measure_performance_gains
    # - _get_matching_cache_keys
    # - _increment_counter
    # - _add_to_access_history
    # - _generate_predictive_keys
    # - _generate_predictive_content
    # - _get_lru_keys
    
    async def _increment_counter(self, key: str, field: str, ttl: Optional[int] = None) -> None:
        """Increment a counter in cache"""
        try:
            current_data = await self.cache_get(key)
            
            if current_data:
                data = json.loads(current_data)
            else:
                data = {}
            
            data[field] = data.get(field, 0) + 1
            data["last_updated"] = datetime.utcnow().isoformat()
            
            await self.cache_set(key, json.dumps(data), ttl or 86400)
            
        except Exception as e:
            logger.warning("Failed to increment counter", key=key, field=field, error=str(e))
    
    async def _add_to_access_history(self, key: str, data: Dict[str, Any]) -> None:
        """Add to access history (keeping last 1000 entries)"""
        try:
            history_data = await self.cache_get(key)
            
            if history_data:
                history = json.loads(history_data)
            else:
                history = []
            
            history.append(data)
            
            # Keep only last 1000 entries
            if len(history) > 1000:
                history = history[-1000:]
            
            await self.cache_set(key, json.dumps(history), 86400 * 7)  # 7 days
            
        except Exception as e:
            logger.warning("Failed to add to access history", error=str(e))
    
    async def get_performance_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        try:
            # Get global cache stats
            global_stats_key = f"{self.stats_prefix}global"
            global_stats_data = await self.cache_get(global_stats_key)
            
            if global_stats_data:
                global_stats = json.loads(global_stats_data)
            else:
                global_stats = {
                    "cache_hits": 0,
                    "cache_misses": 0,
                    "cache_sets": 0,
                    "cache_invalidations": 0
                }
            
            # Calculate hit ratio
            total_requests = global_stats.get("cache_hits", 0) + global_stats.get("cache_misses", 0)
            hit_ratio = global_stats.get("cache_hits", 0) / max(total_requests, 1)
            
            # Get cache size information
            cache_info = {
                "hit_ratio": round(hit_ratio, 3),
                "total_requests": total_requests,
                "cache_hits": global_stats.get("cache_hits", 0),
                "cache_misses": global_stats.get("cache_misses", 0),
                "cache_sets": global_stats.get("cache_sets", 0),
                "cache_invalidations": global_stats.get("cache_invalidations", 0),
                "performance_score": min(100, int(hit_ratio * 100))
            }
            
            # Add Redis-specific stats if available
            if hasattr(self.databases, 'redis') and self.databases.redis:
                try:
                    redis_info = await self.databases.redis.info()
                    cache_info.update({
                        "redis_memory_used": redis_info.get("used_memory_human", "0B"),
                        "redis_keys_count": redis_info.get("db0", {}).get("keys", 0),
                        "redis_connected_clients": redis_info.get("connected_clients", 0),
                        "redis_operations_per_sec": redis_info.get("instantaneous_ops_per_sec", 0)
                    })
                except Exception as redis_error:
                    logger.warning("Failed to get Redis info", error=str(redis_error))
            
            return cache_info
            
        except Exception as e:
            logger.error("Failed to get cache performance stats", error=str(e))
            return {
                "error": str(e),
                "hit_ratio": 0.0,
                "performance_score": 0
            }
    
    def _generate_cache_key(self, user_id: str, context_type: str, identifier: str) -> str:
        """Generate standardized cache key"""
        return f"{self.cache_prefix}{user_id}:{context_type}:{identifier}"