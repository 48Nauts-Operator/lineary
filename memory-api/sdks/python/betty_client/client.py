"""
BETTY Memory System Python SDK - Main Client

This module provides the main BettyClient class for interacting with
the BETTY Memory System v2.0 API.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Union, Any, AsyncGenerator
from contextlib import asynccontextmanager

import aiohttp
from aiohttp import ClientSession, ClientTimeout, TCPConnector
import backoff
from asyncio_throttle import Throttler

from .config import ClientConfig
from .models import (
    AdvancedSearchRequest, AdvancedSearchResponse,
    PatternMatchRequest, PatternMatchResponse,
    SemanticClusteringRequest, SemanticClusteringResponse,
    BatchImportRequest, BatchImportResponse,
    KnowledgeItem, BaseResponse
)
from .exceptions import (
    BettyAPIException, AuthenticationException,
    PermissionException, RateLimitException,
    ValidationException
)
from .utils import validate_jwt_token, format_filters

logger = logging.getLogger(__name__)


class BettyClient:
    """
    Main client for BETTY Memory System v2.0 API.
    
    Provides async access to all BETTY v2.0 features including:
    - Advanced search with semantic, keyword, and hybrid modes
    - Pattern matching and discovery in knowledge graphs
    - Semantic clustering of knowledge items
    - Batch operations with progress tracking
    - Cross-project intelligence and knowledge transfer
    - Real-time WebSocket connections
    - Comprehensive error handling with retries
    
    Example:
        async with BettyClient(api_key="your-jwt-token") as client:
            results = await client.advanced_search(
                query="machine learning optimization",
                search_type="hybrid",
                max_results=20
            )
    """
    
    def __init__(self, 
                 api_key: str = None,
                 base_url: str = "http://localhost:3034/api/v2",
                 config: ClientConfig = None,
                 connector: TCPConnector = None,
                 timeout: ClientTimeout = None,
                 **kwargs):
        """
        Initialize BETTY client.
        
        Args:
            api_key: JWT token for authentication
            base_url: Base URL for BETTY API
            config: Complete client configuration object
            connector: Custom aiohttp connector
            timeout: Custom timeout configuration
            **kwargs: Additional configuration options
        """
        
        # Use provided config or create from parameters
        if config:
            self.config = config
        else:
            self.config = ClientConfig(
                api_key=api_key,
                base_url=base_url,
                **kwargs
            )
        
        # Validate API key
        if self.config.api_key:
            validate_jwt_token(self.config.api_key)
        
        # Setup HTTP client configuration
        self.connector = connector or TCPConnector(
            limit=self.config.connection_pool_size,
            limit_per_host=max(10, self.config.connection_pool_size // 4),
            ttl_dns_cache=300,
            use_dns_cache=True,
            keepalive_timeout=60
        )
        
        self.timeout = timeout or ClientTimeout(
            total=self.config.timeout,
            connect=10,
            sock_read=self.config.timeout - 10
        )
        
        # Rate limiting
        self.throttler = Throttler(
            rate_limit=self.config.rate_limit_per_minute,
            period=60
        )
        
        # HTTP session (will be created when needed)
        self._session: Optional[ClientSession] = None
        self._closed = False
        
        logger.info(f"Initialized BETTY client for {self.config.base_url}")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def _ensure_session(self):
        """Ensure HTTP session is created and ready."""
        if self._session is None or self._session.closed:
            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
                "User-Agent": f"betty-python-sdk/2.0.0",
                "Accept": "application/json"
            }
            
            self._session = ClientSession(
                connector=self.connector,
                timeout=self.timeout,
                headers=headers,
                raise_for_status=False
            )
            
            logger.debug("Created new HTTP session")
    
    async def close(self):
        """Close the HTTP session and cleanup resources."""
        if self._session and not self._session.closed:
            await self._session.close()
            logger.debug("Closed HTTP session")
        
        if hasattr(self, 'connector') and not self.connector.closed:
            await self.connector.close()
            
        self._closed = True
    
    @property
    def closed(self) -> bool:
        """Check if client is closed."""
        return self._closed or (self._session and self._session.closed)
    
    @backoff.on_exception(
        backoff.expo,
        (aiohttp.ClientError, asyncio.TimeoutError),
        max_tries=3,
        max_time=30
    )
    async def _make_request(self, method: str, endpoint: str, 
                          data: Dict = None, params: Dict = None) -> Dict:
        """
        Make HTTP request with retry logic and error handling.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            data: Request body data
            params: Query parameters
            
        Returns:
            Response data as dictionary
            
        Raises:
            BettyAPIException: For API errors
            AuthenticationException: For auth errors
            PermissionException: For permission errors
            RateLimitException: For rate limit errors
        """
        
        if self.closed:
            raise BettyAPIException("Client is closed")
        
        await self._ensure_session()
        
        # Rate limiting
        await self.throttler.acquire()
        
        url = f"{self.config.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        try:
            async with self._session.request(
                method=method,
                url=url,
                json=data if data else None,
                params=params
            ) as response:
                
                # Log request details
                logger.debug(f"{method} {url} -> {response.status}")
                
                # Parse response
                try:
                    response_data = await response.json()
                except (aiohttp.ContentTypeError, json.JSONDecodeError):
                    response_data = {"text": await response.text()}
                
                # Handle different status codes
                if response.status == 200:
                    return response_data
                    
                elif response.status == 401:
                    raise AuthenticationException(
                        message=response_data.get("message", "Authentication required"),
                        details=response_data.get("details", {})
                    )
                    
                elif response.status == 403:
                    missing_perms = []
                    if "details" in response_data:
                        missing_perms = response_data["details"].get("missing_permissions", [])
                    
                    raise PermissionException(
                        message=response_data.get("message", "Permission denied"),
                        missing_permissions=missing_perms,
                        details=response_data.get("details", {})
                    )
                    
                elif response.status == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    
                    raise RateLimitException(
                        message=response_data.get("message", "Rate limit exceeded"),
                        retry_after=retry_after,
                        details=response_data.get("details", {})
                    )
                    
                elif response.status == 422:
                    field_errors = {}
                    if "details" in response_data:
                        field_errors = response_data["details"].get("field_errors", {})
                    
                    raise ValidationException(
                        message=response_data.get("message", "Validation failed"),
                        field_errors=field_errors,
                        details=response_data.get("details", {})
                    )
                    
                else:
                    raise BettyAPIException(
                        message=response_data.get("message", "API request failed"),
                        status_code=response.status,
                        details=response_data.get("details", {}),
                        request_id=response_data.get("request_id")
                    )
                    
        except aiohttp.ClientError as e:
            logger.error(f"HTTP client error: {e}")
            raise BettyAPIException(f"HTTP client error: {e}")
        
        except asyncio.TimeoutError:
            logger.error("Request timeout")
            raise BettyAPIException("Request timeout")
    
    # Advanced Search Methods
    
    async def advanced_search(self, 
                            query: str,
                            search_type: str = "hybrid",
                            similarity_threshold: float = 0.7,
                            max_results: int = 20,
                            filters: List[Dict] = None,
                            time_range: Dict = None,
                            ranking_algorithm: str = "bm25_semantic_hybrid",
                            include_metadata: bool = True,
                            group_by: str = None,
                            project_ids: List[str] = None) -> AdvancedSearchResponse:
        """
        Perform advanced search with semantic, keyword, or hybrid modes.
        
        Args:
            query: Search query text
            search_type: Type of search ('semantic', 'keyword', 'hybrid')
            similarity_threshold: Minimum similarity score (0-1)
            max_results: Maximum number of results to return
            filters: List of filter conditions
            time_range: Time range filter with start/end dates
            ranking_algorithm: Ranking algorithm to use
            include_metadata: Whether to include item metadata
            group_by: Field to group results by
            project_ids: Filter by specific project IDs
            
        Returns:
            AdvancedSearchResponse with results and analysis
            
        Example:
            results = await client.advanced_search(
                query="neural network optimization",
                search_type="semantic",
                similarity_threshold=0.8,
                filters=[
                    {
                        "field": "knowledge_type",
                        "operator": "eq", 
                        "value": "research_paper"
                    }
                ]
            )
        """
        
        request_data = {
            "query": query,
            "search_type": search_type,
            "similarity_threshold": similarity_threshold,
            "max_results": max_results,
            "ranking_algorithm": ranking_algorithm,
            "include_metadata": include_metadata
        }
        
        if filters:
            request_data["filters"] = format_filters(filters)
        
        if time_range:
            request_data["time_range"] = time_range
        
        if group_by:
            request_data["group_by"] = group_by
            
        if project_ids:
            request_data["project_ids"] = project_ids
        
        response_data = await self._make_request("POST", "query/advanced-search", request_data)
        return AdvancedSearchResponse(**response_data)
    
    async def pattern_matching(self,
                             pattern_type: str,
                             pattern_definition: Dict = None,
                             max_depth: int = 5,
                             min_confidence: float = 0.6,
                             max_results: int = 50,
                             project_ids: List[str] = None) -> PatternMatchResponse:
        """
        Find patterns in knowledge graphs using advanced algorithms.
        
        Args:
            pattern_type: Type of pattern to find ('path', 'subgraph', 'temporal', etc.)
            pattern_definition: Specific pattern definition
            max_depth: Maximum path depth for pattern matching
            min_confidence: Minimum pattern confidence score
            max_results: Maximum number of patterns to return
            project_ids: Filter by specific project IDs
            
        Returns:
            PatternMatchResponse with discovered patterns
            
        Example:
            patterns = await client.pattern_matching(
                pattern_type="path",
                pattern_definition={
                    "path_structure": "A->B->C",
                    "relationship_types": ["influences", "leads_to"],
                    "node_constraints": {
                        "A": {"knowledge_type": "concept"},
                        "B": {"knowledge_type": "method"}
                    }
                },
                min_confidence=0.7
            )
        """
        
        request_data = {
            "pattern_type": pattern_type,
            "max_depth": max_depth,
            "min_confidence": min_confidence,
            "max_results": max_results
        }
        
        if pattern_definition:
            request_data["pattern_definition"] = pattern_definition
            
        if project_ids:
            request_data["project_ids"] = project_ids
        
        response_data = await self._make_request("POST", "query/pattern-match", request_data)
        return PatternMatchResponse(**response_data)
    
    async def semantic_clustering(self,
                                algorithm: str = "hierarchical",
                                num_clusters: int = None,
                                auto_clusters: bool = True,
                                min_cluster_size: int = 5,
                                max_cluster_size: int = 100,
                                similarity_threshold: float = 0.6,
                                project_ids: List[str] = None,
                                knowledge_types: List[str] = None,
                                use_content: bool = True,
                                use_metadata: bool = True,
                                use_relationships: bool = False,
                                include_visualization: bool = False,
                                include_topics: bool = True,
                                max_items_per_cluster: int = 100) -> SemanticClusteringResponse:
        """
        Organize knowledge items into semantic clusters.
        
        Args:
            algorithm: Clustering algorithm ('hierarchical', 'kmeans', 'dbscan', etc.)
            num_clusters: Desired number of clusters (auto-detected if None)
            auto_clusters: Automatically determine optimal cluster count
            min_cluster_size: Minimum items per cluster
            max_cluster_size: Maximum items per cluster
            similarity_threshold: Minimum intra-cluster similarity
            project_ids: Filter by specific project IDs
            knowledge_types: Filter by knowledge types
            use_content: Use content for clustering
            use_metadata: Use metadata features
            use_relationships: Use relationship information
            include_visualization: Generate cluster visualization
            include_topics: Extract cluster topics
            max_items_per_cluster: Maximum items per cluster
            
        Returns:
            SemanticClusteringResponse with clusters and analysis
            
        Example:
            clusters = await client.semantic_clustering(
                algorithm="hierarchical",
                auto_clusters=True,
                min_cluster_size=5,
                include_topics=True,
                include_visualization=True
            )
        """
        
        request_data = {
            "algorithm": algorithm,
            "auto_clusters": auto_clusters,
            "min_cluster_size": min_cluster_size,
            "max_cluster_size": max_cluster_size,
            "similarity_threshold": similarity_threshold,
            "use_content": use_content,
            "use_metadata": use_metadata,
            "use_relationships": use_relationships,
            "include_visualization": include_visualization,
            "include_topics": include_topics,
            "max_items_per_cluster": max_items_per_cluster
        }
        
        if num_clusters:
            request_data["num_clusters"] = num_clusters
            
        if project_ids:
            request_data["project_ids"] = project_ids
            
        if knowledge_types:
            request_data["knowledge_types"] = knowledge_types
        
        response_data = await self._make_request("POST", "query/semantic-clusters", request_data)
        return SemanticClusteringResponse(**response_data)
    
    # Batch Operation Methods
    
    async def batch_import(self,
                         source_type: str,
                         format: str,
                         source_config: Dict,
                         target_project_id: str,
                         duplicate_handling: str = "skip",
                         validation_rules: Dict = None,
                         processing_options: Dict = None,
                         batch_size: int = 100,
                         max_errors: int = 50,
                         notify_webhook: str = None) -> BatchImportResponse:
        """
        Start batch import operation with progress tracking.
        
        Args:
            source_type: Type of source ('file', 'url', 'database', 'api')
            format: Data format ('json', 'csv', 'xml', 'yaml', 'markdown')
            source_config: Source-specific configuration
            target_project_id: Target project UUID
            duplicate_handling: How to handle duplicates ('skip', 'overwrite', 'merge')
            validation_rules: Validation rules for imported data
            processing_options: Processing options (embeddings, categorization, etc.)
            batch_size: Items per batch
            max_errors: Maximum errors before stopping
            notify_webhook: Webhook URL for completion notification
            
        Returns:
            BatchImportResponse with operation details
            
        Example:
            operation = await client.batch_import(
                source_type="file",
                format="json",
                source_config={"file_path": "/uploads/data.json"},
                target_project_id="project-uuid",
                processing_options={
                    "generate_embeddings": True,
                    "auto_categorize": True
                }
            )
        """
        
        request_data = {
            "source_type": source_type,
            "format": format,
            "source_config": source_config,
            "target_project_id": target_project_id,
            "duplicate_handling": duplicate_handling,
            "batch_size": batch_size,
            "max_errors": max_errors
        }
        
        if validation_rules:
            request_data["validation_rules"] = validation_rules
            
        if processing_options:
            request_data["processing_options"] = processing_options
            
        if notify_webhook:
            request_data["notify_webhook"] = notify_webhook
        
        response_data = await self._make_request("POST", "batch/knowledge/import", request_data)
        return BatchImportResponse(**response_data)
    
    async def get_batch_progress(self, operation_id: str) -> BaseResponse:
        """
        Get progress of a batch operation.
        
        Args:
            operation_id: UUID of the batch operation
            
        Returns:
            BaseResponse with progress information
        """
        
        response_data = await self._make_request("GET", f"batch/operations/{operation_id}/progress")
        return BaseResponse(**response_data)
    
    async def track_progress(self, operation_id: str, 
                           poll_interval: float = 5.0) -> AsyncGenerator[Dict, None]:
        """
        Track batch operation progress with async generator.
        
        Args:
            operation_id: UUID of the batch operation
            poll_interval: Polling interval in seconds
            
        Yields:
            Progress updates as dictionaries
            
        Example:
            async for progress in client.track_progress(operation_id):
                print(f"Progress: {progress.progress_percentage}%")
                if progress.status in ["completed", "failed"]:
                    break
        """
        
        while True:
            try:
                progress_response = await self.get_batch_progress(operation_id)
                
                if progress_response.success:
                    progress_data = progress_response.data
                    yield progress_data
                    
                    # Stop if operation is finished
                    if progress_data.get("status") in ["completed", "failed", "cancelled"]:
                        break
                else:
                    logger.error(f"Failed to get progress: {progress_response.message}")
                    break
                    
            except Exception as e:
                logger.error(f"Error tracking progress: {e}")
                break
            
            await asyncio.sleep(poll_interval)
    
    # Knowledge Management Methods
    
    async def add_knowledge(self,
                          title: str,
                          content: str,
                          knowledge_type: str = "document",
                          project_id: str = None,
                          tags: List[str] = None,
                          metadata: Dict = None) -> BaseResponse:
        """
        Add a new knowledge item.
        
        Args:
            title: Knowledge item title
            content: Main content
            knowledge_type: Type of knowledge item
            project_id: Target project UUID
            tags: List of tags
            metadata: Additional metadata
            
        Returns:
            BaseResponse with created knowledge item info
        """
        
        request_data = {
            "title": title,
            "content": content,
            "knowledge_type": knowledge_type
        }
        
        if project_id:
            request_data["project_id"] = project_id
            
        item_metadata = metadata or {}
        if tags:
            item_metadata["tags"] = tags
        
        if item_metadata:
            request_data["metadata"] = item_metadata
        
        response_data = await self._make_request("POST", "knowledge/add", request_data)
        return BaseResponse(**response_data)
    
    async def get_knowledge(self, knowledge_id: str) -> BaseResponse:
        """
        Get a knowledge item by ID.
        
        Args:
            knowledge_id: UUID of the knowledge item
            
        Returns:
            BaseResponse with knowledge item details
        """
        
        response_data = await self._make_request("GET", f"knowledge/{knowledge_id}")
        return BaseResponse(**response_data)
    
    async def update_knowledge(self, 
                             knowledge_id: str,
                             title: str = None,
                             content: str = None,
                             knowledge_type: str = None,
                             tags: List[str] = None,
                             metadata: Dict = None) -> BaseResponse:
        """
        Update a knowledge item.
        
        Args:
            knowledge_id: UUID of the knowledge item
            title: New title (if updating)
            content: New content (if updating)
            knowledge_type: New type (if updating)
            tags: New tags (if updating)
            metadata: New metadata (if updating)
            
        Returns:
            BaseResponse with update confirmation
        """
        
        request_data = {}
        
        if title is not None:
            request_data["title"] = title
        if content is not None:
            request_data["content"] = content
        if knowledge_type is not None:
            request_data["knowledge_type"] = knowledge_type
            
        if tags is not None or metadata is not None:
            item_metadata = metadata or {}
            if tags is not None:
                item_metadata["tags"] = tags
            request_data["metadata"] = item_metadata
        
        response_data = await self._make_request("PUT", f"knowledge/{knowledge_id}", request_data)
        return BaseResponse(**response_data)
    
    async def delete_knowledge(self, knowledge_id: str) -> BaseResponse:
        """
        Delete a knowledge item.
        
        Args:
            knowledge_id: UUID of the knowledge item
            
        Returns:
            BaseResponse with deletion confirmation
        """
        
        response_data = await self._make_request("DELETE", f"knowledge/{knowledge_id}")
        return BaseResponse(**response_data)
    
    # Cross-Project Intelligence Methods
    
    async def cross_project_search(self,
                                 query: str,
                                 project_ids: List[str] = None,
                                 search_type: str = "hybrid",
                                 similarity_threshold: float = 0.7,
                                 max_results_per_project: int = 20,
                                 max_total_results: int = 100,
                                 merge_strategy: str = "relevance",
                                 include_project_context: bool = True,
                                 filters: List[Dict] = None) -> AdvancedSearchResponse:
        """
        Search across multiple connected projects.
        
        Args:
            query: Search query text
            project_ids: Specific projects to search
            search_type: Type of search ('semantic', 'keyword', 'hybrid')
            similarity_threshold: Minimum similarity score
            max_results_per_project: Max results per project
            max_total_results: Max total results
            merge_strategy: Strategy for merging results
            include_project_context: Include project information
            filters: Additional filters
            
        Returns:
            AdvancedSearchResponse with cross-project results
        """
        
        request_data = {
            "query": query,
            "search_type": search_type,
            "similarity_threshold": similarity_threshold,
            "max_results_per_project": max_results_per_project,
            "max_total_results": max_total_results,
            "merge_strategy": merge_strategy,
            "include_project_context": include_project_context
        }
        
        if project_ids:
            request_data["project_ids"] = project_ids
            
        if filters:
            request_data["filters"] = format_filters(filters)
        
        response_data = await self._make_request("POST", "cross-project/search", request_data)
        return AdvancedSearchResponse(**response_data)
    
    # Utility Methods
    
    async def health_check(self) -> BaseResponse:
        """
        Check API health status.
        
        Returns:
            BaseResponse with health status
        """
        
        response_data = await self._make_request("GET", "../../health")
        return BaseResponse(**response_data)
    
    async def get_api_version(self) -> BaseResponse:
        """
        Get API version information.
        
        Returns:
            BaseResponse with version details
        """
        
        response_data = await self._make_request("GET", "../version/info")
        return BaseResponse(**response_data)